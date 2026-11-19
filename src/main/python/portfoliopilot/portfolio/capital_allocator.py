class CapitalDistributionEngine:
    @staticmethod
    def balance_cash_tiers(available_liquidity: float, weight_config: float) -> float:
        """Determines the maximum spending ceiling for an architectural tier."""
        return max(0.0, available_liquidity * weight_config)
