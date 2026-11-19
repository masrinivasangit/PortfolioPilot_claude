# analysis/velocity_analyst.py
import pandas as pd
import numpy as np

class VelocityBreakoutAnalyst:
    def __init__(self):
        self.name = "Persistent_Monotonicity_Expert"
        self.tier_weight = 0.33

    def set_tier_weight(self, weight: float):
        self.tier_weight = float(weight)

    # ADDED: evaluation_date=None constraint parameters to bypass runtime crashes
    def calculate_factor_multiplier(self, ticker: str, historical_data: pd.DataFrame, evaluation_date=None) -> float:
        if ticker not in historical_data.columns:
            return 1.00

        prices = historical_data[ticker].dropna()
        if len(prices) < 15:
            return 1.00

        recent_prices = prices.tail(7).to_numpy().flatten()
        daily_diffs = np.diff(recent_prices)
        if len(daily_diffs) == 0:
            return 1.00

        positive_closes = np.sum(daily_diffs > 0)
        monotonicity_ratio = positive_closes / len(daily_diffs)

        if monotonicity_ratio >= 0.70:
            return float(1.40 + (self.tier_weight * 0.5))
        return float(0.60 - (self.tier_weight * 0.3))
