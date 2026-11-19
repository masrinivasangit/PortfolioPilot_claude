# backtesting/combine.py - builds the COMBINED portfolio (large + mid + risky tiers together).
import os
import csv
import pandas as pd
from backtesting.backtest_engine import HistoricalSimulationEngine
from backtesting.summary import metrics_to_row


def combine_tier_runs(reports_dir: str, summary_path: str, zone: str, split_date: str, risk_free_rate: float):
    """Each tier is simulated on its own slice of capital (budget x tier weight). The real portfolio is the
    SUM of the tiers, so add their daily equity curves and score the total as one portfolio."""
    df = pd.read_csv(summary_path)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["Universe"] != "COMBINED"]
    if df.empty:
        return

    for (strategy, analyst), group in df.groupby(["Strategy", "Analyst_Layer"]):
        frames, ledgers = [], []
        for label in group["Label"]:
            eq_path = os.path.join(reports_dir, f"backtest_ledger_{label}_equity.csv")
            led_path = os.path.join(reports_dir, f"backtest_ledger_{label}.csv")
            if os.path.exists(eq_path):
                frames.append(pd.read_csv(eq_path, index_col=0, parse_dates=True))
            if os.path.exists(led_path):
                ledgers.append(pd.read_csv(led_path))
        if len(frames) < 2:
            continue

        index = frames[0].index
        combined = sum(f.reindex(index).ffill().bfill() for f in frames)
        label = f"RUN_{strategy}_COMBINED_{analyst}"
        combined.to_csv(os.path.join(reports_dir, f"backtest_ledger_{label}_equity.csv"))
        ledger_path = os.path.join(reports_dir, f"backtest_ledger_{label}.csv")
        pd.concat(ledgers, ignore_index=True).to_csv(ledger_path, index=False)

        benchmark = combined["Benchmark"] if "Benchmark" in combined.columns else None
        engine = HistoricalSimulationEngine(float(combined["Equity"].iloc[0]), risk_free_rate, split_date or None)
        metrics = engine.compute_metrics(combined, ledger_path, benchmark)
        metrics["Total Taxes Paid (INR)"] = round(float(group["Taxes_Paid_INR"].sum()), 2)
        with open(summary_path, "a", newline="") as f:
            csv.writer(f).writerow(metrics_to_row(label, zone, strategy, "COMBINED", analyst, metrics))
