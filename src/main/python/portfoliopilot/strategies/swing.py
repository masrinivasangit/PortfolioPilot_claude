# strategies/swing.py
import pandas as pd
import numpy as np
from backtesting.protocols import BaseInvestmentStrategy


class SwingTradingStrategy(BaseInvestmentStrategy):
    def __init__(self):
        self.active_multipliers = {}

    def set_active_multipliers(self, multipliers: dict):
        self.active_multipliers = multipliers

    def generate_signals(self, historical_data: pd.DataFrame, pool_tickers: list, max_allowed: int) -> pd.DataFrame:
        rankings = []
        for ticker in pool_tickers:
            tk_clean = str(ticker).strip().upper()
            if tk_clean not in historical_data.columns:
                continue

            series = historical_data[tk_clean].dropna()
            horizon_floor = min(20, len(series))
            if horizon_floor < 5:
                continue

            trailing_slice = series.tail(horizon_floor)
            moving_avg = float(
                trailing_slice.rolling(window=min(5, len(trailing_slice)), min_periods=1).mean().iloc[-1])
            current_price = float(trailing_slice.iloc[-1])

            if moving_avg > 0:
                base_deviation = abs(moving_avg - current_price) / moving_avg

                # FIX: Dynamically apply the analyst framework multiplier directly to the core signal
                fused_mult = self.active_multipliers.get(tk_clean, 1.0)
                adjusted_score = base_deviation * float(fused_mult)

                rankings.append({'Ticker': tk_clean, 'Score': adjusted_score, 'Price': current_price})

        if not rankings:
            return pd.DataFrame()

        # FIX: Enforce truncation to max_allowed so the scoring differences alter the final portfolio
        return pd.DataFrame(rankings).sort_values(by='Score', ascending=False).head(max_allowed)
