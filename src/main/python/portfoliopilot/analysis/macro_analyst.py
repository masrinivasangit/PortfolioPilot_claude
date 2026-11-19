# analysis/macro_analyst.py
import pandas as pd


class MacroAnalystAgent:
    def __init__(self):
        self.name = "Macro_Regime_Engine"
        self.tier_weight = 0.33

    def set_tier_weight(self, weight: float):
        self.tier_weight = float(weight)

    # ADDED: evaluation_date=None parameter to prevent dynamic execution failures
    def calculate_factor_multiplier(self, ticker: str, historical_data: pd.DataFrame, evaluation_date=None) -> float:
        tk_clean = str(ticker).strip().upper()

        if "^BSESN" in historical_data.columns:
            benchmark = "^BSESN"
        else:
            benchmark = str(historical_data.columns[0])

        if benchmark not in historical_data.columns or tk_clean not in historical_data.columns:
            return 1.00

        index_prices = pd.Series(historical_data[benchmark].values.flatten(), index=historical_data.index).dropna()
        if len(index_prices) < 20:
            return 1.00

        short_ma = float(index_prices.rolling(window=5).mean().iloc[-1])
        long_ma = float(index_prices.rolling(window=20).mean().iloc[-1])

        weight_scalar = float(self.tier_weight) * 0.4

        # Strongly reward or penalize based on systemic market health triggers
        if short_ma >= long_ma:
            return float(1.35 + weight_scalar)
        else:
            return float(0.65 - weight_scalar)
