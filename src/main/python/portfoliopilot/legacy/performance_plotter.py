# backtesting/performance_plotter.py
import os
import pandas as pd
import matplotlib.pyplot as plt


class PortfolioPerformancePlotter:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        # Isolate the core source execution directory bounds cleanly
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # FIXED: Hardlocked structural output target to the dedicated reports folder path
        self.reports_dir = os.path.join(self.base_dir, "reports")

    def generate_equity_chart(self, ledger_file_path: str, output_image_name: str):
        """Chronologically aggregates asset transaction vectors and saves the line graph to the reports folder."""
        if not os.path.exists(ledger_file_path):
            return

        df = pd.read_csv(ledger_file_path)
        if df.empty:
            return

        # Ensure the structural folder directory targets physically exist on your drive on launch
        os.makedirs(self.reports_dir, exist_ok=True)

        unique_dates = sorted(df['Date'].unique())
        current_cash = self.initial_capital
        open_shares, equity_values, dates = {}, [], []

        for date in unique_dates:
            day_actions = df[df['Date'] == date]

            sells = day_actions[day_actions['Action'] == 'SELL']
            for _, row in sells.iterrows():
                tk = row['Ticker']
                if tk in open_shares:
                    open_shares[tk] = max(0, open_shares[tk] - int(row['Quantity']))
                    if open_shares[tk] == 0:
                        del open_shares[tk]

            buys = day_actions[day_actions['Action'] == 'BUY']
            for _, row in buys.iterrows():
                open_shares[row['Ticker']] = open_shares.get(row['Ticker'], 0) + int(row['Quantity'])

            equity_values.append(current_cash)
            dates.append(pd.to_datetime(date))

        # Render the separate strategy line trajectory plot
        plt.figure(figsize=(10, 4))
        plt.plot(dates, equity_values, label=output_image_name, color="#17becf", linewidth=2.0)
        plt.axhline(y=self.initial_capital, color="red", linestyle="--", alpha=0.5)
        plt.grid(True, linestyle=":", alpha=0.5)
        plt.title(f"PortfolioPilot Visual Experiment Log: {output_image_name}")
        plt.tight_layout()

        # Save output straight into your clean sub-folder layout
        output_path = os.path.join(self.reports_dir, output_image_name)
        plt.savefig(output_path, dpi=150)
        plt.close()
        print(f"📊 Chart tracking record generated successfully: {output_path}")
