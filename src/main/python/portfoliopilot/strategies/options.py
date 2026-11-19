# strategies/options.py
import pandas as pd
import numpy as np
from backtesting.protocols import BaseInvestmentStrategy


class DerivativesOptionsStrategy(BaseInvestmentStrategy):
    def __init__(self):
        self.strategy_name = "Options_Protective_Collar"
        self.active_multipliers = {}

    # FIXED: Added the missing interface hook to receive orchestrator multiplier caches
    def set_active_multipliers(self, multipliers: dict):
        self.active_multipliers = multipliers

    def generate_signals(self, historical_data: pd.DataFrame, pool_tickers: list, max_allowed: int) -> pd.DataFrame:
        """Scans underlying equity metrics to calculate protective option hedges."""
        derivative_signals = []
        for ticker in pool_tickers:
            tk_clean = str(ticker).strip().upper()
            if tk_clean not in historical_data.columns:
                continue

            prices = historical_data[tk_clean].dropna()
            if len(prices) < 5:
                continue

            pct_changes = prices.pct_change().dropna()
            historical_volatility = float(pct_changes.std()) if not pct_changes.empty else 0.0
            p_end = float(prices.to_numpy().flatten()[-1])

            if historical_volatility > 0.001:
                estimated_option_premium = p_end * 0.015

                # FIXED: Pull and apply active analyst layer multipliers directly into options rankings
                fused_mult = self.active_multipliers.get(tk_clean, 1.0)
                adjusted_score = historical_volatility * float(fused_mult)

                derivative_signals.append({
                    'Ticker': tk_clean,
                    'Score': adjusted_score,
                    'Price': p_end + estimated_option_premium
                })

        if not derivative_signals:
            return pd.DataFrame()

        return pd.DataFrame(derivative_signals).sort_values(by='Score', ascending=False).head(max_allowed)
