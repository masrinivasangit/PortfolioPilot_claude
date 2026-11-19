# portfolio/risk.py
import numpy as np


class PortfolioRiskManager:
    def __init__(self, max_concentration: float = 0.25, max_tolerated_drawdown: float = -0.10):
        self.max_concentration = float(max_concentration)
        self.tolerated_dd = float(max_tolerated_drawdown)

    def inspect_order_safety(self, proposed_allocation: float, total_capital: float) -> bool:
        """Enforces a strict diversification rule blocking order sizes above concentration caps."""
        if total_capital <= 0:
            return False
        return (proposed_allocation / total_capital) <= self.max_concentration

    def adjust_risk_profile(self, historic_drawdown: float) -> float:
        """
        DYNAMIC ALPHA SAFEGUARD: Gracefully and linearly scales down allocation multiplier
        as drawdown deepens. If the maximum tolerated drawdown is breached, exposure scales
        completely to 0.0, shifting 100% of the portfolio into a safe cash buffer.
        """
        # Handle positive inputs or flat lines safely
        if historic_drawdown >= 0:
            return 1.0

        # CRITICAL PROTECTION Hatch: Exit completely to cash if drawdown breaches our risk ceiling
        if historic_drawdown <= self.tolerated_dd:
            return 0.0

        # FULL-SPECTRUM LINEAR DECAY: Calculate a smooth scale gliding from 1.0 down to 0.0
        # This dynamically constrains buying power as downside pressure builds.
        decay_slope = (1.0 - 0.0) / (0.0 - self.tolerated_dd)
        calculated_multiplier = 1.0 + (decay_slope * historic_drawdown)

        return float(np.clip(calculated_multiplier, a_min=0.0, a_max=1.0))
