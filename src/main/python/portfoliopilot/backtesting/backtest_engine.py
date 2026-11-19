# backtesting/backtest_engine.py
import os
import numpy as np
import pandas as pd


class HistoricalSimulationEngine:
    """Computes performance metrics from a DAILY mark-to-market equity curve.

    The previous version rebuilt equity from ledger rows only (buy/sell days), so a position
    held through a crash showed no drawdown and no volatility. This version needs the daily
    equity series produced by the orchestrator.
    """

    def __init__(self, initial_capital: float, risk_free_rate: float = 0.065, split_date=None):
        self.initial_capital = float(initial_capital)
        self.risk_free_rate = float(risk_free_rate)
        self.split_date = pd.to_datetime(split_date) if split_date else None

    @staticmethod
    def _max_drawdown(series: pd.Series) -> float:
        if series is None or series.empty:
            return 0.0
        peak = series.cummax()
        return float(((series - peak) / peak).min())

    @staticmethod
    def _cagr(series: pd.Series) -> float:
        if series is None or len(series) < 2:
            return 0.0
        days = (series.index[-1] - series.index[0]).days
        if days < 30 or series.iloc[0] <= 0 or series.iloc[-1] <= 0:
            return float("nan")
        return float((series.iloc[-1] / series.iloc[0]) ** (365.25 / days) - 1.0)

    def compute_metrics(self, equity_df: pd.DataFrame, ledger_file_path: str, benchmark: pd.Series = None) -> dict:
        if equity_df is None or equity_df.empty:
            return {}
        equity = equity_df["Equity"].astype(float)
        final_value = float(equity.iloc[-1])
        total_return = final_value / self.initial_capital - 1.0

        daily_returns = equity.pct_change().dropna()
        std = float(daily_returns.std()) if len(daily_returns) > 1 else 0.0
        if std > 0 and not np.isnan(std):
            vol = std * np.sqrt(252)
            excess = daily_returns.mean() - self.risk_free_rate / 252.0
            sharpe = float(excess / std * np.sqrt(252))
        else:
            vol, sharpe = 0.0, 0.0

        trades, frictions = 0, 0.0
        if os.path.exists(ledger_file_path):
            df = pd.read_csv(ledger_file_path)
            df.columns = [c.strip() for c in df.columns]
            if not df.empty:
                trades = len(df)
                frictions = float(df["Friction_Cost"].sum())

        avg_exposure = float("nan")
        if "Cash" in equity_df.columns:
            avg_exposure = float(1.0 - (equity_df["Cash"] / equity_df["Equity"]).mean())

        report = {
            "Initial Capital": round(self.initial_capital, 2),
            "Final Valuation": round(final_value, 2),
            "Net Return (%)": round(total_return * 100, 2),
            "CAGR (%)": round(self._cagr(equity) * 100, 2),
            "Total Friction Fees Paid": round(frictions, 2),
            "Annualized Volatility (%)": round(vol * 100, 2),
            "Sharpe Ratio": round(sharpe, 2),
            "Max Drawdown (%)": round(self._max_drawdown(equity) * 100, 2),
            "Trades Executed": trades,
            "Avg Capital Invested (%)": round(avg_exposure * 100, 1),
        }

        if benchmark is not None and not benchmark.dropna().empty:
            b = benchmark.dropna()
            report["Benchmark Return (%)"] = round((b.iloc[-1] / b.iloc[0] - 1.0) * 100, 2)
            report["Benchmark Max Drawdown (%)"] = round(self._max_drawdown(b) * 100, 2)
            report["Excess vs Benchmark (%)"] = round(report["Net Return (%)"] - report["Benchmark Return (%)"], 2)

        if self.split_date is not None:
            is_part = equity[equity.index <= self.split_date]
            oos_part = equity[equity.index >= self.split_date]
            if len(is_part) > 1 and len(oos_part) > 1:
                report["In-Sample Return (%)"] = round((is_part.iloc[-1] / is_part.iloc[0] - 1.0) * 100, 2)
                report["Out-of-Sample Return (%)"] = round((oos_part.iloc[-1] / oos_part.iloc[0] - 1.0) * 100, 2)
                report["Out-of-Sample Max Drawdown (%)"] = round(self._max_drawdown(oos_part) * 100, 2)

        self.display_report_card(report)
        return report

    def display_report_card(self, metrics: dict):
        print("\n==================================================================")
        print("    PORTFOLIO PILOT PERFORMANCE REPORT CARD (daily mark-to-market)")
        print("==================================================================")
        for key, value in metrics.items():
            if "(%)" in key:
                print(f"  {key:<34} : {value}%")
            elif "Ratio" in key or "Trades" in key:
                print(f"  {key:<34} : {value}")
            else:
                print(f"  {key:<34} : {value:,.2f}")
        print("==================================================================\n")
