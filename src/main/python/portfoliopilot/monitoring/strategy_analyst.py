# monitoring/strategy_analyst.py
import os
import pandas as pd


class SelfAnalysisDecisionEngine:
    def __init__(self, summary_matrix_path: str):
        self.matrix_path = summary_matrix_path

    def discover_optimal_configuration(self, priority_metric: str = "Sharpe_Ratio") -> dict:
        if not os.path.exists(self.matrix_path):
            return {"status": "error", "message": "Metrics tracker file missing."}
        df = pd.read_csv(self.matrix_path)
        if df.empty:
            return {"status": "error", "message": "Metrics database is empty."}
        df.columns = [c.strip() for c in df.columns]

        # Judge whole portfolios (COMBINED) when available; tier-only runs only cover part of the capital.
        pool = df[df["Universe"] == "COMBINED"] if (df["Universe"] == "COMBINED").any() else df
        best = pool.sort_values(by=priority_metric, ascending=(priority_metric == "Max_Drawdown_Pct")).iloc[0]

        def fmt(col):
            v = best.get(col, "")
            return "n/a" if pd.isna(v) or v == "" else f"{v}%"

        print("\n==================================================================")
        print("   BEST CONFIGURATION IN THIS GRID (read the caution below)")
        print("==================================================================")
        print(f" Run              : {best['Label']}")
        print(f" Net return       : {best['Net_Return_Pct']}%   (Sensex buy & hold: {fmt('Benchmark_Return_Pct')})")
        print(f" Sharpe ratio     : {best['Sharpe_Ratio']}")
        print(f" Max drawdown     : {best['Max_Drawdown_Pct']}%")
        print(f" In-sample return : {fmt('InSample_Return_Pct')}   Out-of-sample: {fmt('OutOfSample_Return_Pct')}")
        print(" ----------------------------------------------------------------")
        print(" CAUTION: this is the best of many combinations, so it is partly luck.")
        print("          Trust the OUT-OF-SAMPLE number, and only if it beats the Sensex.")
        print("==================================================================\n")
        return best.to_dict()
