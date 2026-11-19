# strategies/long_term.py
import pandas as pd
import numpy as np
from backtesting.protocols import BaseInvestmentStrategy


class LongTermValueStrategy(BaseInvestmentStrategy):
    def __init__(self):
        self.name = "Long_Term_Value"
        self.active_multipliers = {}

    def set_active_multipliers(self, multipliers: dict):
        self.active_multipliers = multipliers

    def generate_signals(self, historical_data: pd.DataFrame, pool_tickers: list, max_allowed: int) -> pd.DataFrame:
        rankings = []
        for ticker in pool_tickers:
            tk_clean = str(ticker).strip().upper()
            if tk_clean not in historical_data.columns:
                continue

            prices = historical_data[tk_clean].dropna()

            # FIXED: Reduced lookback window constraints to 15 days to handle compressed timelines safely
            if len(prices) < 15:
                continue

            sliding_horizon = prices.tail(60).to_numpy().flatten()
            p_old = float(sliding_horizon[0])
            p_current = float(sliding_horizon[-1])

            if p_old > 0:
                long_term_growth = (p_current - p_old) / p_old
                pct_changes = pd.Series(sliding_horizon).pct_change().dropna()
                volatility_drag = float(pct_changes.std()) if not pct_changes.empty else 0.0

                # Locate the signal generation loop in strategies/long_term.py and update the score offset:
                risk_adjusted_trend = long_term_growth / (volatility_drag + 1e-9)

                # FIX: Add an accumulation baseline offset so high-quality assets are never starved of initial buy tracks
                if risk_adjusted_trend == 0 or pd.isna(risk_adjusted_trend):
                    risk_adjusted_trend = 0.01

                fused_mult = self.active_multipliers.get(tk_clean, 1.0)
                adjusted_score = risk_adjusted_trend * float(fused_mult)

                rankings.append({'Ticker': tk_clean, 'Score': adjusted_score, 'Price': p_current})

        if not rankings:
            return pd.DataFrame()

        return pd.DataFrame(rankings).sort_values(by='Score', ascending=False).head(max_allowed)
