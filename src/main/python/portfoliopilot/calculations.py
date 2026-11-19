# calculations.py - PART 1
import os
import csv
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from backtesting.trade_costs import GlobalFrictionAccountingEngine
from portfolio.risk import PortfolioRiskManager
from backtesting.orchestrator import BacktestOrchestrator
from backtesting.summary import metrics_to_row


class QuantitativeMathEngine:
    @staticmethod
    def generate_isolated_analyst_diagrams(summary_matrix_path, reports_dir, initial_budget, end_date_str,
                                           current_pkg_dir):
        """Plots the REAL daily equity curves saved by the orchestrator (<ledger>_equity.csv),
        plus the real Sensex buy-and-hold benchmark. Nothing here is interpolated or simulated."""
        if not os.path.exists(summary_matrix_path): return
        df = pd.read_csv(summary_matrix_path)
        if df.empty: return

        df.columns = [col.strip() for col in df.columns]
        os.makedirs(reports_dir, exist_ok=True)

        for analyst in df["Analyst_Layer"].unique():
            fig, ax = plt.subplots(figsize=(10, 4.5))
            subset = df[df["Analyst_Layer"] == analyst]
            has_data = False
            benchmark_plotted = False

            for _, row in subset.iterrows():
                label = row["Label"]
                equity_file = os.path.join(reports_dir, f"backtest_ledger_{label}_equity.csv")
                if not os.path.exists(equity_file): continue

                eq = pd.read_csv(equity_file, index_col=0, parse_dates=True)
                if eq.empty: continue

                ax.plot(eq.index, eq["Equity"], label=f"{label} (Final: Rs {eq['Equity'].iloc[-1]:,.0f})", linewidth=1.6)
                has_data = True
                if "Benchmark" in eq.columns and not benchmark_plotted:
                    ax.plot(eq.index, eq["Benchmark"], color="#7f7f7f", linestyle="-.", linewidth=1.8,
                            label="Sensex buy & hold (price index)")
                    benchmark_plotted = True

            if has_data:
                ax.axhline(y=initial_budget, color="red", linestyle="--", alpha=0.5, label="Initial Capital")
                ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
                ax.set_xlabel("Date", fontsize=9)
                ax.set_ylabel("Portfolio value (INR), daily mark-to-market", fontsize=9)
                ax.grid(True, linestyle=":", alpha=0.5)
                ax.legend(loc="upper left", fontsize=7)
                plt.title(f"Equity curves: {analyst}", fontsize=10, fontweight='bold')
                plt.tight_layout()

                chart_out_path = os.path.join(reports_dir, f"master_{analyst}_comparison.png")
                plt.savefig(chart_out_path, dpi=150)
                plt.close()
                print(f"Chart exported: {chart_out_path}")
            else:
                plt.close(fig)

    @staticmethod
    def run_single_simulation_safely(run_label, market_zone, s_plugin, active_analyst_list, assets_pool, preloaded_data,
                                     runtime_payload, ledger_file, summary_matrix_path):
        """Runs ONE backtest (strategy x universe x analyst stack) and appends its row to the summary CSV."""
        os.makedirs(os.path.dirname(ledger_file), exist_ok=True)
        with open(ledger_file, mode="w", newline="") as file:
            csv.writer(file).writerow(
                ["Cycle_Num", "Date", "Ticker", "Asset_Tier", "Quantity", "Price", "Friction_Cost", "Action"])

        gate = abs(float(runtime_payload.get("max_drawdown_gate", 0.25)))
        orchestrator = BacktestOrchestrator(
            settings=runtime_payload,
            strategy_plugin=s_plugin,
            analyst_plugins=active_analyst_list,
            friction_engine=GlobalFrictionAccountingEngine(
                region=market_zone, slippage_bps=float(runtime_payload.get("slippage_bps", 10.0))),
            risk_engine=PortfolioRiskManager(max_concentration=0.45, max_tolerated_drawdown=-gate),
        )

        try:
            metrics = orchestrator.execute_simulation_timeline(
                raw_market_pool=assets_pool, preloaded_data=preloaded_data, ledger_file_path=ledger_file)
            if metrics:
                with open(summary_matrix_path, mode="a", newline="") as file:
                    csv.writer(file).writerow(metrics_to_row(
                        run_label, market_zone, runtime_payload["s_name"], runtime_payload["u_name"],
                        runtime_payload["a_name"], metrics))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"   WARNING: combination skipped: {e}")
