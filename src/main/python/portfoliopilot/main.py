# main.py - runs the backtest grid: strategies x universes (tiers) x analyst stacks.
import configparser
import csv
import datetime
import os
import shutil
import sys

import pandas as pd

current_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if current_pkg_dir not in sys.path:
    sys.path.insert(0, current_pkg_dir)

from calculations import QuantitativeMathEngine
from registry import STRATEGIES, build_analyst_stacks
from universes import TIER_POOLS, BENCHMARK, FX
from data.price_loader import load_prices
from backtesting.summary import SUMMARY_COLUMNS
from backtesting.combine import combine_tier_runs
from monitoring.strategy_analyst import SelfAnalysisDecisionEngine

PRICE_HISTORY_PADDING_DAYS = 250  # extra history before start_date so indicators are warmed up


class QuantitativeDiscoveryEngine:
    def __init__(self, config_path: str = None, reports_dir: str = None, price_loader=load_prices):
        self.config_path = config_path or os.path.join(current_pkg_dir, "config.properties")
        self.reports_dir = reports_dir or os.path.join(current_pkg_dir, "reports")
        self.cache_dir = os.path.join(current_pkg_dir, "data_cache")
        self.summary_matrix_path = os.path.join(self.reports_dir, "optimal_strategy_matrix.csv")
        self.price_loader = price_loader
        self.config = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))

    # ------------------------------------------------------------------ setup helpers
    def _reset_reports_dir(self):
        if os.path.exists(self.reports_dir):
            for item in os.listdir(self.reports_dir):
                path = os.path.join(self.reports_dir, item)
                try:
                    shutil.rmtree(path) if os.path.isdir(path) else os.unlink(path)
                except Exception as e:
                    print(f"WARNING: could not clear {path}: {e}")
        os.makedirs(self.reports_dir, exist_ok=True)

    def _read_settings(self) -> dict:
        c = self.config
        return {
            "zone": c.get("MARKET_SETTINGS", "market_country", fallback="IN").strip().upper(),
            "budget": c.getfloat("MARKET_SETTINGS", "total_budget", fallback=100000.0),
            "start": c.get("BACKTEST_SETTINGS", "start_date").strip(),
            "end": c.get("BACKTEST_SETTINGS", "end_date").strip(),
            "split": c.get("BACKTEST_SETTINGS", "split_date", fallback="").strip(),
            "rf": c.getfloat("BACKTEST_SETTINGS", "risk_free_rate", fallback=0.065),
            "slippage_bps": c.getfloat("COST_SETTINGS", "slippage_bps", fallback=10.0),
            "gate": c.getfloat("RISK_SETTINGS", "max_drawdown_gate", fallback=0.25),
            "dd_window": c.getint("RISK_SETTINGS", "drawdown_window_days", fallback=126),
            "default_lookback": max(10, c.getint("ANALYST_LOOKBACK_SETTINGS", "technical_lookback_weeks", fallback=2) * 5),
            "default_rebalance": c.getint("SCHEDULE_SETTINGS", "rebalance_days", fallback=5),
        }

    def _pick(self, setting_key: str, registry: dict, fallback: str) -> list:
        raw = self.config.get("MARKET_SETTINGS", setting_key, fallback=fallback)
        wanted = [x.strip().upper() for x in raw.split(",") if x.strip()]
        unknown = [w for w in wanted if w not in registry]
        if unknown:
            print(f"WARNING: unknown {setting_key} ignored: {', '.join(unknown)}")
        chosen = [w for w in wanted if w in registry]
        return chosen or [fallback.split(",")[0].strip()]

    def _universes(self) -> dict:
        universes = {}
        for section, pool in TIER_POOLS.items():
            if not self.config.has_section(section):
                continue
            size = self.config.getint(section, "pool_size", fallback=len(pool))
            universes[section] = {
                "pool": [t.upper() for t in pool[:size]],
                "weight": self.config.getfloat(section, "weight"),
                "max_tickers": self.config.getint(section, "max_tickers", fallback=3),
            }
        total_w = sum(u["weight"] for u in universes.values())
        if universes and abs(total_w - 1.0) > 1e-6:
            print(f"NOTE: tier weights sum to {total_w:.2f}, not 1.00. Only that share of capital is deployed.")
        return universes

    def _timeframes(self, strategy: str, st: dict) -> tuple:
        key = strategy.lower()
        sec = "STRATEGY_TIMEFRAME_OVERRIDES"
        return (self.config.getint(sec, f"{key}_lookback_days", fallback=st["default_lookback"]),
                self.config.getint(sec, f"{key}_rebalance_days", fallback=st["default_rebalance"]))

    # ------------------------------------------------------------------ main entry
    def execute_grid_search(self):
        print("=" * 66)
        print(" PORTFOLIO PILOT - BACKTEST GRID")
        print("=" * 66)

        if not os.path.exists(self.config_path):
            print(f"ERROR: configuration file not found: {self.config_path}")
            return
        self.config.read(self.config_path)
        self._reset_reports_dir()

        st = self._read_settings()
        print(f"Horizon {st['start']} -> {st['end']} | Budget Rs {st['budget']:,.0f} | "
              f"Out-of-sample from {st['split'] or 'n/a'}")

        strategies = self._pick("active_strategies", STRATEGIES, "LONG_TERM, MOMENTUM")
        stack_names = self._pick("active_analysts", build_analyst_stacks(), "QUANT_CORE_TREND")
        universes = self._universes()
        if not universes:
            print("ERROR: no tier sections found in the config.")
            return

        tickers = {BENCHMARK, FX}
        for u in universes.values():
            tickers.update(u["pool"])
        padded_start = (pd.to_datetime(st["start"]) - datetime.timedelta(days=PRICE_HISTORY_PADDING_DAYS)).strftime("%Y-%m-%d")
        prices = self.price_loader(sorted(tickers), padded_start, st["end"], self.cache_dir)
        prices.columns = [str(c).strip().upper() for c in prices.columns]

        with open(self.summary_matrix_path, mode="w", newline="") as f:
            csv.writer(f).writerow(SUMMARY_COLUMNS)

        run_count = 0
        for s_name in strategies:
            lookback, rebalance = self._timeframes(s_name, st)
            for u_name, u in universes.items():
                for a_name in stack_names:
                    run_count += 1
                    label = f"RUN_{s_name}_{u_name}_{a_name}"
                    print(f"[{run_count}] {s_name} | {u_name} | {a_name}")
                    payload = {
                        "start_date": st["start"], "end_date": st["end"],
                        # each tier gets its own slice of the capital; COMBINED sums the tiers afterwards
                        "initial_budget": st["budget"] * u["weight"], "tier_weight": 1.0,
                        "tech_lookback": lookback, "rebalance_days": rebalance, "max_tickers": u["max_tickers"],
                        "experiment_label": label, "s_name": s_name, "u_name": u_name, "a_name": a_name,
                        "split_date": st["split"], "risk_free_rate": st["rf"], "slippage_bps": st["slippage_bps"],
                        "max_drawdown_gate": st["gate"], "drawdown_window_days": st["dd_window"],
                    }
                    QuantitativeMathEngine.run_single_simulation_safely(
                        run_label=label, market_zone=st["zone"], s_plugin=STRATEGIES[s_name](),
                        active_analyst_list=build_analyst_stacks()[a_name], assets_pool=u["pool"],
                        preloaded_data=prices, runtime_payload=payload,
                        ledger_file=os.path.join(self.reports_dir, f"backtest_ledger_{label}.csv"),
                        summary_matrix_path=self.summary_matrix_path)

        print("\nCombining tiers into whole-portfolio results ...")
        combine_tier_runs(self.reports_dir, self.summary_matrix_path, st["zone"], st["split"], st["rf"])

        QuantitativeMathEngine.generate_isolated_analyst_diagrams(
            self.summary_matrix_path, self.reports_dir, st["budget"], st["end"], current_pkg_dir)

        if os.path.exists(self.summary_matrix_path) and os.path.getsize(self.summary_matrix_path) > 0:
            df = pd.read_csv(self.summary_matrix_path)
            if not df.empty:
                SelfAnalysisDecisionEngine(self.summary_matrix_path).discover_optimal_configuration()


if __name__ == "__main__":
    QuantitativeDiscoveryEngine().execute_grid_search()
