# export_report_card.py
import os
import pandas as pd

def generate_excel_report_card():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    matrix_path = os.path.join(current_dir, "reports", "optimal_strategy_matrix.csv")
    output_path = os.path.join(current_dir, "reports", "PortfolioPilot_Discovery_Report.xlsx")

    if not os.path.exists(matrix_path):
        print(f"❌ Error: Matrix file not found at {matrix_path}. Run main.py first.")
        return

    # Read data streams cleanly
    df = pd.read_csv(matrix_path)
    df.columns = [col.strip() for col in df.columns]

    print("🏁 Compiling multi-agent leaderboard records...")

    # Establish an Excel writer with explicit layout formatting engines
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Sheet 1: Master Consolidated Leaderboard ranked by Sharpe Ratio
        df_sorted = df.sort_values(by="Sharpe_Ratio", ascending=False)
        df_sorted.to_excel(writer, sheet_name="Master Leaderboard", index=False)

        # Sheet 2: Isolated High-Performance Momentum Tracks
        df_momentum = df[df["Strategy"] == "MOMENTUM"].sort_values(by="Net_Return_Pct", ascending=False)
        df_momentum.to_excel(writer, sheet_name="Momentum Strategy Profile", index=False)

        # Sheet 3: Isolated Tactical Swing Protection Tracks
        df_swing = df[df["Strategy"] == "SWING"].sort_values(by="Net_Return_Pct", ascending=False)
        df_swing.to_excel(writer, sheet_name="Swing Strategy Profile", index=False)

        # Sheet 4: High-Level Executive Summary Analysis Matrix
        best_run = df_sorted.iloc[0]
        summary_metrics = {
            "Performance Metric Parameter": [
                "Top Alpha Configuration Track",
                "Optimal Intelligence Layer",
                "Target Deployment Sector",
                "Peak Net Absolute Return (%)",
                "Max Bounded Portfolio Sharpe Ratio",
                "Controlled Downside Max Drawdown (%)",
                "Total Regulatory Cost Drag Accrued (INR)"
            ],
            "Discovery Discovery Value Value": [
                best_run["Label"],
                best_run["Analyst_Layer"],
                f"{best_run['Universe']} ({best_run['Zone']})",
                f"{best_run['Net_Return_Pct']}%",
                best_run["Sharpe_Ratio"],
                f"{best_run['Max_Drawdown_Pct']}%",
                f"₹{best_run['Taxes_Paid_INR']:,.2f}"
            ]
        }
        pd.DataFrame(summary_metrics).to_excel(writer, sheet_name="Executive Summary Brief", index=False)

    print(f"✨ Institutional PortfolioPilot report card saved to: {output_path}")

if __name__ == "__main__":
    generate_excel_report_card()
