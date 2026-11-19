# backtesting/trade_costs.py
import pandas as pd
from backtesting.protocols import BaseFrictionEngine

# India's Union Budget of 23 July 2024 changed capital gains rates on listed equity.
_TAX_REGIME_CHANGE = pd.Timestamp("2024-07-23")
_CESS = 1.04  # 4% health & education cess on the tax


class GlobalFrictionAccountingEngine(BaseFrictionEngine):
    """Brokerage, statutory charges, slippage and capital-gains tax.

    slippage_bps: assumed price impact per trade side, in basis points (10 bps = 0.10%).
    Raise it for mid-cap / high-risk names, which are much less liquid than large caps.
    Not modelled: the annual LTCG exemption, loss set-off, surcharge, dividends.
    """

    def __init__(self, region: str = "IN", slippage_bps: float = 10.0):
        self.region = region.upper()
        self.slippage_bps = float(slippage_bps)

    def calculate_trade_leakage(self, ticker: str, trade_value: float, action: str) -> float:
        action = action.upper()
        ticker_clean = str(ticker).strip().upper()
        slippage = trade_value * self.slippage_bps / 10000.0

        if self.region == "IN" or ticker_clean.endswith(".NS") or "^BSESN" in ticker_clean:
            # Derivatives contracts (only when the ticker explicitly says so)
            if "OPTION" in ticker_clean:
                options_brokerage = 20.0
                options_exchange_fees = max(5.0, trade_value * 0.0005)
                options_gst = (options_brokerage + options_exchange_fees) * 0.18
                options_stamp_duty = 3.0 if action == "BUY" else 0.0
                return options_brokerage + options_exchange_fees + options_gst + options_stamp_duty + slippage

            # Equity delivery
            brokerage = min(20.0, trade_value * 0.0003)
            exchange_fees = trade_value * 0.0000322
            stamp_duty = trade_value * 0.00015 if action == "BUY" else 0.0
            stt = trade_value * 0.001  # 0.1% on both buy and sell for delivery
            gst = (brokerage + exchange_fees) * 0.18
            dp_fee = 15.93 if action == "SELL" else 0.0
            return brokerage + exchange_fees + stamp_duty + stt + gst + dp_fee + slippage

        elif self.region == "US" or "." not in ticker_clean:
            return min(5.0, max(0.5, trade_value * 0.0001)) + slippage

        return trade_value * 0.0015 + slippage

    def calculate_capital_gains_tax(self, buy_date, sell_date, buy_price: float, sell_price: float,
                                    shares: int) -> float:
        profit = (sell_price - buy_price) * shares
        if profit <= 0:
            return 0.0

        hold_days = (pd.Timestamp(sell_date) - pd.Timestamp(buy_date)).days
        if self.region == "IN":
            if pd.Timestamp(sell_date) < _TAX_REGIME_CHANGE:
                stcg, ltcg = 0.15, 0.10
            else:
                stcg, ltcg = 0.20, 0.125
            rate = stcg if hold_days <= 365 else ltcg
            return profit * rate * _CESS

        return profit * 0.15
