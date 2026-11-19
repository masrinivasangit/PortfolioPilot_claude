# backtesting/orchestrator.py
"""Day-by-day backtest loop.

Key correctness rules in this version:
  * Signals are computed from data up to the PREVIOUS close (signal_date); trades execute at the
    NEXT close (cycle_date). The old version traded at the same close it used to decide.
  * Equity is marked to market every day and saved to <ledger>_equity.csv, together with a
    buy-and-hold ^BSESN (Sensex) benchmark. Charts and metrics are built from that file.
  * Analysts get a longer history window than the strategy, and they see the index (^BSESN).
"""
import os
import csv
import sys
import pandas as pd
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from portfolio.optimizer import PortfolioWeightAllocator
from backtesting.backtest_engine import HistoricalSimulationEngine

BENCHMARK_TICKER = "^BSESN"
ANALYST_MIN_HISTORY = 60  # trading days of history handed to analysts


class BacktestOrchestrator:
    def __init__(self, settings: dict, strategy_plugin, analyst_plugins: list, friction_engine, risk_engine):
        self.settings = settings
        self.strategy = strategy_plugin
        self.analyst_plugins = analyst_plugins
        self.friction_engine = friction_engine
        self.risk_manager = risk_engine
        self.portfolio_optimizer = PortfolioWeightAllocator()

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _extract_scalar(value) -> float:
        if isinstance(value, (pd.Series, pd.DataFrame, np.ndarray)):
            if value.size == 0:
                return 0.0
            val = value.values.flatten()[-1]
            return float(val) if not pd.isna(val) else 0.0
        return float(value) if (value is not None and not pd.isna(value)) else 0.0

    def _prices(self, data: pd.DataFrame, tk: str, date):
        """Returns (raw_price, base_currency_price) for a ticker on a date."""
        if tk not in data.columns:
            return 0.0, 0.0
        pr_raw = self._extract_scalar(data.loc[date, tk])
        fx = 1.0
        if not tk.endswith(".NS") and "USDINR=X" in data.columns:
            fx = self._extract_scalar(data.loc[date, "USDINR=X"])
            if fx <= 0 or pd.isna(fx):
                fx = 1.0
        return pr_raw, pr_raw * fx

    def _equity(self, cash: float, holdings: dict, data: pd.DataFrame, date) -> float:
        total = cash
        for tk, h in holdings.items():
            _, pr_base = self._prices(data, tk, date)
            # if a price is unavailable, fall back to cost so a data gap never shows as a 100% loss
            total += h["shares"] * (pr_base if pr_base > 0 else h["buy_price_base"])
        return total

    @staticmethod
    def _append_ledger(path, row):
        with open(path, mode="a", newline="") as f:
            csv.writer(f).writerow(row)

    # ------------------------------------------------------------------ main loop
    def execute_simulation_timeline(self, raw_market_pool: list, preloaded_data: pd.DataFrame,
                                    ledger_file_path: str) -> dict:
        if preloaded_data.empty:
            return {}

        preloaded_data = preloaded_data.copy()
        preloaded_data.columns = [col.strip().upper() for col in preloaded_data.columns]
        # carry the last known price over holidays / halts (does not invent pre-listing prices)
        preloaded_data = preloaded_data.sort_index().ffill()

        valid_pool_tickers = [str(t).strip().upper() for t in raw_market_pool
                              if str(t).strip().upper() in preloaded_data.columns]
        if not valid_pool_tickers:
            return {}

        analyst_columns = list(valid_pool_tickers)
        if BENCHMARK_TICKER in preloaded_data.columns:
            analyst_columns.append(BENCHMARK_TICKER)

        execution_timeline = preloaded_data[preloaded_data.index >= self.settings["start_date"]]
        if len(execution_timeline) < 2:
            return {}
        dates = execution_timeline.index

        initial_budget = float(self.settings["initial_budget"])
        current_cash = initial_budget
        holdings_tracker, total_taxes = {}, 0.0
        peak_valuation = initial_budget
        equity_rows = []

        strategy_name = str(self.settings.get("s_name", "MOMENTUM")).upper()
        analyst_run_id = str(self.settings.get("a_name", "DEFAULT_ANALYST"))
        lookback = int(self.settings["tech_lookback"])
        rebalance_days = int(self.settings["rebalance_days"])
        print(f"   Launching backtest | Strategy: [{strategy_name}] | Analyst: [{analyst_run_id}]")

        total_days_count = len(dates) - 1

        for i in range(total_days_count):
            signal_date = dates[i]       # information available up to this close
            cycle_date = dates[i + 1]    # trades execute at this close
            liquidated_today = set()

            # Daily mark-to-market for signal_date (state after the previous day's trades)
            equity_rows.append((signal_date, self._equity(current_cash, holdings_tracker, preloaded_data, signal_date),
                                current_cash))

            # 1. STOP-LOSS SCAN
            if holdings_tracker:
                violated = []
                for tk, data in holdings_tracker.items():
                    pr_raw, pr_base = self._prices(preloaded_data, tk, cycle_date)
                    if pr_raw <= 0:
                        continue
                    if data.get("peak_price", 0) <= 0:
                        data["peak_price"] = data["buy_price_base"]
                    if pr_base > data["peak_price"]:
                        data["peak_price"] = pr_base

                    if strategy_name == "SWING":
                        is_mid_cap = "MID_CAP" in str(self.settings.get("u_name", "")).upper() or \
                                     "MID_CAP" in str(self.settings.get("experiment_label", "")).upper()
                        stop_loss_pct = 0.03 if is_mid_cap else 0.05
                    else:
                        stop_loss_pct = 0.15

                    if (pr_base - data["peak_price"]) / data["peak_price"] <= -stop_loss_pct:
                        violated.append((tk, pr_raw, pr_base))

                for tk, pr_raw, pr_base in violated:
                    data = holdings_tracker[tk]
                    val_base = data["shares"] * pr_base
                    friction = self.friction_engine.calculate_trade_leakage(tk, val_base, "SELL")
                    tax = self.friction_engine.calculate_capital_gains_tax(
                        data["buy_date"], cycle_date, data["buy_price_base"], pr_base, data["shares"])
                    total_taxes += tax
                    current_cash += (val_base - friction - tax)
                    liquidated_today.add(tk)
                    del holdings_tracker[tk]
                    self._append_ledger(ledger_file_path, [
                        f"{self.settings['experiment_label']}_{i + 1}_STOP", cycle_date.date(), tk,
                        self.settings["u_name"], data["shares"], pr_raw, friction, "SELL"])

            # 2. SCHEDULED REBALANCE (sell everything on schedule)
            is_rebalance_cycle = strategy_name in ("SWING", "MOMENTUM") and (i % rebalance_days == 0)
            if is_rebalance_cycle and holdings_tracker:
                for tk, data in list(holdings_tracker.items()):
                    pr_raw, pr_base = self._prices(preloaded_data, tk, cycle_date)
                    if pr_raw <= 0:
                        continue
                    val_base = data["shares"] * pr_base
                    friction = self.friction_engine.calculate_trade_leakage(tk, val_base, "SELL")
                    tax = self.friction_engine.calculate_capital_gains_tax(
                        data["buy_date"], cycle_date, data["buy_price_base"], pr_base, data["shares"])
                    total_taxes += tax
                    current_cash += (val_base - friction - tax)
                    liquidated_today.add(tk)
                    del holdings_tracker[tk]
                    self._append_ledger(ledger_file_path, [
                        f"{self.settings['experiment_label']}_{i + 1}", cycle_date.date(), tk,
                        self.settings["u_name"], data["shares"], pr_raw, friction, "SELL"])

            # 3. RISK GATE
            total_valuation = self._equity(current_cash, holdings_tracker, preloaded_data, cycle_date)
            # peak over a trailing window (default ~6 months) so the gate can re-arm after a recovery
            window = int(self.settings.get("drawdown_window_days", 126))
            recent = [r[1] for r in (equity_rows[-window:] if window > 0 else equity_rows)]
            peak_valuation = max(recent + [total_valuation])
            current_drawdown = (total_valuation - peak_valuation) / peak_valuation if peak_valuation > 0 else 0.0
            risk_scaling_factor = self.risk_manager.adjust_risk_profile(current_drawdown)
            if current_cash <= 100.0 or risk_scaling_factor <= 0:
                continue

            if strategy_name in ("SWING", "MOMENTUM") and i % rebalance_days != 0:
                continue
            if strategy_name in ("LONG_TERM", "OPTIONS") and len(holdings_tracker) >= int(self.settings.get("max_tickers", 8)):
                continue

            total_allocatable = current_cash * risk_scaling_factor * float(self.settings["tier_weight"]) * 0.95

            # Strategy sees `lookback` days up to signal_date; analysts see a longer window incl. the index.
            hist_all = preloaded_data[preloaded_data.index <= signal_date]
            historical_slice = hist_all[valid_pool_tickers].tail(lookback)
            analyst_slice = hist_all[analyst_columns].tail(max(lookback, ANALYST_MIN_HISTORY))

            if strategy_name == "OPTIONS":
                idx = hist_all[BENCHMARK_TICKER] if BENCHMARK_TICKER in hist_all.columns else None
                if idx is not None and len(idx) >= 5 and idx.iloc[-1] < idx.tail(5).mean():
                    current_cash += current_cash * (0.07 / 252)
                    continue

            max_allowed_assets = int(self.settings.get("max_tickers", 8))

            multipliers = {}
            for tk_check in valid_pool_tickers:
                fused_m = 1.0
                for plugin in self.analyst_plugins:
                    try:
                        if hasattr(plugin, "calculate_factor_multiplier"):
                            fused_m *= float(plugin.calculate_factor_multiplier(tk_check, analyst_slice, signal_date))
                    except Exception:
                        fused_m *= 1.0
                multipliers[tk_check] = fused_m

            if hasattr(self.strategy, "set_active_multipliers"):
                self.strategy.set_active_multipliers(multipliers)

            raw_picks = self.strategy.generate_signals(historical_slice, valid_pool_tickers, len(valid_pool_tickers))
            if raw_picks.empty:
                continue

            fused_rankings = []
            for _, pick in raw_picks.iterrows():
                tk = str(pick["Ticker"]).strip().upper()
                pr = self._extract_scalar(pick["Price"])
                if pr <= 0 or tk in holdings_tracker or tk in liquidated_today:
                    continue
                base_score = self._extract_scalar(pick["Score"])
                fused_score = float(base_score) * float(multipliers.get(tk, 1.0)) * 100.0
                fused_score += (sum(ord(c) for c in tk) % 1000) * 0.00001  # deterministic tie-breaker
                fused_rankings.append({"Ticker": tk, "Score": fused_score, "Price": pr})

            fused_df = pd.DataFrame(fused_rankings)
            if fused_df.empty:
                continue

            space_left = max_allowed_assets - len(holdings_tracker)
            if space_left <= 0:
                continue

            fused_df = fused_df.sort_values(by="Score", ascending=False).head(space_left)
            orders = self.portfolio_optimizer.compute_share_bounds(fused_df, total_allocatable)

            for order in orders:
                tk, sh = order["Ticker"], int(order["Shares"])
                # execute at the NEXT close, not at the price the signal was computed from
                pr_raw, pr_base = self._prices(preloaded_data, tk, cycle_date)
                if pr_raw <= 0 or pr_base <= 0 or tk in holdings_tracker:
                    continue
                buy_friction = self.friction_engine.calculate_trade_leakage(tk, sh * pr_base, "BUY")
                if current_cash < sh * pr_base + buy_friction:
                    sh = int(current_cash // (pr_base * 1.01))
                    if sh <= 0:
                        continue
                    buy_friction = self.friction_engine.calculate_trade_leakage(tk, sh * pr_base, "BUY")
                total_cost = sh * pr_base + buy_friction
                if current_cash >= total_cost:
                    current_cash -= total_cost
                    holdings_tracker[tk] = {"shares": sh, "buy_date": cycle_date, "buy_price_base": pr_base}
                    self._append_ledger(ledger_file_path, [
                        f"{self.settings['experiment_label']}_{i + 1}", cycle_date.date(), tk,
                        self.settings["u_name"], sh, pr_raw, buy_friction, "BUY"])

        # 4. FINAL CLOSURE PASS (costs and tax applied, same as any other sale)
        final_date = dates[-1]
        for tk, data in list(holdings_tracker.items()):
            pr_raw, pr_base = self._prices(preloaded_data, tk, final_date)
            if pr_raw <= 0:
                pr_raw, pr_base = data["buy_price_base"], data["buy_price_base"]
            val_base = data["shares"] * pr_base
            friction = self.friction_engine.calculate_trade_leakage(tk, val_base, "SELL")
            tax = self.friction_engine.calculate_capital_gains_tax(
                data["buy_date"], final_date, data["buy_price_base"], pr_base, data["shares"])
            total_taxes += tax
            current_cash += (val_base - friction - tax)
            self._append_ledger(ledger_file_path, [
                999, final_date.date(), tk, self.settings["u_name"], data["shares"], pr_raw, friction, "SELL"])
        holdings_tracker.clear()
        equity_rows.append((final_date, current_cash, current_cash))

        equity_df = pd.DataFrame(equity_rows, columns=["Date", "Equity", "Cash"]).set_index("Date")
        equity_df = equity_df[~equity_df.index.duplicated(keep="last")]

        benchmark = None
        if BENCHMARK_TICKER in preloaded_data.columns:
            b = preloaded_data[BENCHMARK_TICKER].reindex(equity_df.index).ffill().bfill()
            if b.iloc[0] and b.iloc[0] > 0:
                benchmark = b / b.iloc[0] * initial_budget
                equity_df["Benchmark"] = benchmark

        equity_path = ledger_file_path.replace(".csv", "_equity.csv")
        equity_df.to_csv(equity_path)

        engine = HistoricalSimulationEngine(
            initial_budget,
            risk_free_rate=float(self.settings.get("risk_free_rate", 0.065)),
            split_date=self.settings.get("split_date") or None)
        metrics = engine.compute_metrics(equity_df, ledger_file_path, benchmark)
        if metrics:
            metrics["Total Taxes Paid (INR)"] = round(total_taxes, 2)
            return metrics
        return {}
