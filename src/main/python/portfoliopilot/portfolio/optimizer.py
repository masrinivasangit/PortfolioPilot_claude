# portfolio/optimizer.py
import pandas as pd
from backtesting.trade_costs import GlobalFrictionAccountingEngine


class PortfolioWeightAllocator:
    def __init__(self, region: str = "IN"):
        # slippage excluded here: the gate below only filters trades whose FIXED costs are disproportionate
        self.friction_calculator = GlobalFrictionAccountingEngine(region=region, slippage_bps=0.0)

    def generate_optimal_allocations(self, sorted_picks: pd.DataFrame, available_budget: float,
                                     max_allowed: int) -> list:
        return self.compute_share_bounds(sorted_picks, available_budget)

    def compute_share_bounds(self, sorted_picks: pd.DataFrame, available_budget: float, mode: str = "equal",
                             *args, **kwargs) -> list:
        """Turns ranked picks into share counts.

        mode="equal" (default): every selected stock gets the same slice of cash. Simple and robust.
        mode="score": slice proportional to score (old behaviour; it could leave a pick with 1 share).
        A stock whose price exceeds its slice is skipped (no forced 1-share buys).
        Orders whose fixed costs exceed 0.25% of the position value are dropped.
        """
        if sorted_picks.empty:
            return []

        picks = sorted_picks.reset_index(drop=True)
        total_budget = float(available_budget)
        total_score = float(picks["Score"].sum())
        if mode == "score" and total_score <= 0:
            return []

        orders = []
        remaining = total_budget
        for _, row in picks.iterrows():
            tk = row["Ticker"]
            raw_pr = row["Price"]
            pr = float(raw_pr.iloc[-1]) if isinstance(raw_pr, pd.Series) else float(raw_pr)
            if pr <= 0 or pd.isna(pr):
                continue

            slice_cash = total_budget / len(picks) if mode == "equal" else total_budget * row["Score"] / total_score
            shares_to_buy = int(min(slice_cash, remaining) // pr)
            if shares_to_buy <= 0:
                continue

            position_value = shares_to_buy * pr
            estimated_friction = self.friction_calculator.calculate_trade_leakage(
                ticker=tk, trade_value=position_value, action="BUY")
            if estimated_friction / position_value > 0.0025:
                continue

            if remaining >= position_value + estimated_friction:
                orders.append({"Ticker": tk, "Price": pr, "Shares": shares_to_buy, "Friction_Cost": estimated_friction})
                remaining -= position_value + estimated_friction
        return orders
