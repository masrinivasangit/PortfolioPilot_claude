# analysis/compounder_analyst.py
import pandas as pd
import numpy as np

class LongTermCompounderAnalyst:
    def __init__(self):
        self.name = "Secular_LTCG_Compounder_Expert"
        self.tier_weight = 0.33

    def set_tier_weight(self, weight: float):
        self.tier_weight = float(weight)

    # ADDED: evaluation_date=None signature alignment interface mapping
    def calculate_factor_multiplier(self, ticker: str, historical_data: pd.DataFrame, evaluation_date=None) -> float:
        if ticker not in historical_data.columns:
            return 1.00

        prices = historical_data[ticker].dropna()
        if len(prices) < 15:
            return 1.00

        arr = prices.to_numpy().flatten()
        current_price = float(arr[-1])
        quarterly_ma = float(np.mean(arr[-15:]))

        weight_bonus = float(self.tier_weight) * 0.6

        # Enforce distinct, high-impact structural adjustments
        if current_price > quarterly_ma:
            return float(1.45 + weight_bonus)
        else:
            return float(0.55 - weight_bonus)
