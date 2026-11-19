# analysis/technical_analyst.py
import pandas as pd
import numpy as np


class TechnicalAnalystAgent:
    def __init__(self):
        self.name = "Technical_Indicator_Expert"
        self.tier_weight = 0.33

    def set_tier_weight(self, weight: float):
        self.tier_weight = float(weight)

    def compute_exponential_alpha_signal(self, price_series: pd.Series, fast_period: int = 5,
                                         slow_period: int = 15) -> float:
        """
        Calculates a proprietary Exponential Moving Average (EMA) Alpha indicator.
        Measures structural momentum strength via short-term vs long-term trend divergence.
        Returns a bounded signal score centered around 50.0.
        """
        if len(price_series) < slow_period + 1:
            return 50.0

        # Calculate fast and slow Exponential Moving Averages
        ema_fast = price_series.ewm(span=fast_period, adjust=False).mean()
        ema_slow = price_series.ewm(span=slow_period, adjust=False).mean()

        # Isolate the point-in-time endpoint values
        current_fast = float(ema_fast.iloc[-1])
        current_slow = float(ema_slow.iloc[-1])
        current_price = float(price_series.iloc[-1])

        if current_slow <= 0:
            return 50.0

        # Compute raw trend divergence percentage
        raw_divergence = (current_fast - current_slow) / current_slow

        # Standardize the divergence into a clean 0 to 100 bounded scale
        # Centered precisely at 50.0 (where fast EMA equals slow EMA)
        alpha_score = 50.0 + (raw_divergence * 100.0)

        return float(np.clip(alpha_score, a_min=0.0, a_max=100.0))

    def calculate_factor_multiplier(self, ticker: str, historical_data: pd.DataFrame, evaluation_date=None) -> float:
        """
        Interfaces with the Orchestrator loop to return a dynamic alpha multiplier.
        Fuses the new Exponential Alpha indicator with the active analyst tier weight configuration.
        """
        tk_clean = str(ticker).strip().upper()
        if tk_clean not in historical_data.columns:
            return 1.05

        prices = historical_data[tk_clean].dropna()

        # Invoke the new technical indicator engine
        alpha_signal = self.compute_exponential_alpha_signal(prices)

        # Force clear variance mapping bounds using the new indicator scale
        config_scale = float(self.tier_weight) * 0.5

        # High Alpha Score (> 65): Asset exhibits high-velocity upward trend scaling
        if alpha_signal > 65.0:
            return float(1.25 + config_scale)  # Premium markup boost for structural strength

        # Low Alpha Score (< 35): Asset exhibits sharp technical decay or structural markdown
        elif alpha_signal < 35.0:
            return float(0.75 - config_scale)  # Defensive decay discount multiplier

        # Flat / Mean-Reverting Zone: Apply soft structural adjustments based on character parity
        return float(1.05 if len(tk_clean) % 2 == 0 else 0.95)
