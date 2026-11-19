# backtesting/summary.py - the columns of optimal_strategy_matrix.csv, defined once.
SUMMARY_COLUMNS = [
    "Label", "Zone", "Strategy", "Universe", "Analyst_Layer",
    "Net_Return_Pct", "Sharpe_Ratio", "Max_Drawdown_Pct", "Taxes_Paid_INR",
    "CAGR_Pct", "Benchmark_Return_Pct", "Trades", "Avg_Invested_Pct",
    "InSample_Return_Pct", "OutOfSample_Return_Pct", "OutOfSample_MaxDD_Pct",
]


def metrics_to_row(label, zone, strategy, universe, analyst, metrics: dict) -> list:
    g = metrics.get
    return [
        label, zone, strategy, universe, analyst,
        g("Net Return (%)", 0.0), g("Sharpe Ratio", 0.0), g("Max Drawdown (%)", 0.0), g("Total Taxes Paid (INR)", 0.0),
        g("CAGR (%)", ""), g("Benchmark Return (%)", ""), g("Trades Executed", ""), g("Avg Capital Invested (%)", ""),
        g("In-Sample Return (%)", ""), g("Out-of-Sample Return (%)", ""), g("Out-of-Sample Max Drawdown (%)", ""),
    ]
