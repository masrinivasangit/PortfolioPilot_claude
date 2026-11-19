# strategies/momentum.py
import pandas as pd
import numpy as np
from backtesting.protocols import BaseInvestmentStrategy


class MomentumSignalModule(BaseInvestmentStrategy):
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
            if horizon_floor < 7:
                continue

            sliding_window = series.tail(horizon_floor).to_numpy().flatten()
            p_start = float(sliding_window[0])
            p_end = float(sliding_window[-1])

            # INSTITUTIONAL LIQUIDITY GUARDRAIL
            # Calculate standard deviation of prices over the last week to filter out dead/illiquid assets
            recent_rolling_volatility = np.std(sliding_window[-7:])
            if recent_rolling_volatility <= 0.001:
                continue  # Skip dead or completely illiquid tokens to avoid false breakout traps

            if p_start > 0:
                base_momentum = (p_end - p_start) / p_start

                # Dynamically apply the analyst framework multiplier directly to the core signal
                fused_mult = self.active_multipliers.get(tk_clean, 1.0)
                adjusted_score = base_momentum * float(fused_mult)

                rankings.append({'Ticker': tk_clean, 'Score': adjusted_score, 'Price': p_end})

        if not rankings:
            return pd.DataFrame()

        # Enforce truncation to max_allowed so the scoring differences alter the final portfolio
        return pd.DataFrame(rankings).sort_values(by='Score', ascending=False).head(max_allowed)
