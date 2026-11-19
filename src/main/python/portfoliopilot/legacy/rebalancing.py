class PortfolioRebalanceController:
    @staticmethod
    def calculate_drift(current_allocations: dict, target_allocations: dict) -> bool:
        """Determines if allocation deviation metrics require adjustment triggers."""
        for asset, current_w in current_allocations.items():
            target_w = target_allocations.get(asset, 0.0)
            if abs(current_w - target_w) > 0.05:  # Trigger if asset drift exceeds 5%
                return True
        return False
