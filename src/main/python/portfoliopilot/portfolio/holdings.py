class ActiveHoldingsTracker:
    def __init__(self):
        self.positions = {} # Schema: {ticker: {"shares": int, "cost_basis": float}}

    def update_position(self, ticker: str, shares: int, price: float, action: str):
        action = action.upper()
        if action == "BUY":
            if ticker in self.positions:
                total_shares = self.positions[ticker]["shares"] + shares
                total_cost = (self.positions[ticker]["shares"] * self.positions[ticker]["cost_basis"]) + (shares * price)
                self.positions[ticker]["shares"] = total_shares
                self.positions[ticker]["cost_basis"] = total_cost / total_shares
            else:
                self.positions[ticker] = {"shares": shares, "cost_basis": price}
        elif action == "SELL":
            if ticker in self.positions:
                self.positions[ticker]["shares"] = max(0, self.positions[ticker]["shares"] - shares)
                if self.positions[ticker]["shares"] == 0:
                    del self.positions[ticker]
