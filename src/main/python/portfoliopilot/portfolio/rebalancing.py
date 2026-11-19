# portfolio/rebalancing.py

class PortfolioRebalanceController:
    def __init__(self, allowed_drift_threshold: float = 0.05):
        """
        Defaults to a 5% allocation variance threshold before flagging realignment.
        """
        self.threshold = allowed_drift_threshold

    def evaluate_allocation_drift(self, current_tier_valuations: dict, total_portfolio_value: float,
                                  target_weights: dict) -> dict:
        """
        Compares real-time tier valuations against targeted structural weights.
        Returns target actions and safety flags if allocation violations are breached.
        """
        drift_report = {}
        rebalance_required = False

        if total_portfolio_value <= 0:
            return {"rebalance_needed": False, "details": "Portfolio contains no assets to evaluate."}

        for tier, current_val in current_tier_valuations.items():
            target_w = target_weights.get(tier, 0.0)
            actual_w = current_val / total_portfolio_value
            drift = actual_w - target_w

            # Identify if drift violates structural safety bounds
            breached = abs(drift) > self.threshold
            if breached:
                rebalance_required = True

            drift_report[tier] = {
                "Target_Weight": round(target_w, 4),
                "Actual_Weight": round(actual_w, 4),
                "Drift_Deviation": round(drift, 4),
                "Trigger_Action": "REDUCE" if drift > 0 else "TOP_UP" if drift < 0 else "HOLD",
                "Threshold_Breached": breached
            }

        return {
            "rebalance_needed": rebalance_required,
            "tier_analytics": drift_report
        }
