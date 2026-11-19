# backtesting/protocols.py
import pandas as pd


class BaseInvestmentStrategy:
    def generate_signals(self, historical_data: pd.DataFrame, pool_tickers: list, max_allowed: int) -> pd.DataFrame:
        """Returns standard DataFrame containing columns: ['Ticker', 'Score', 'Price']."""
        raise NotImplementedError()


class BaseAnalystPlugin:
    def calculate_factor_multiplier(self, ticker: str, historical_slice: pd.DataFrame) -> float:
        """Returns a scalar multiplier representing asset health or narrative conviction."""
        raise NotImplementedError()


class BaseFrictionEngine:
    def calculate_trade_leakage(self, ticker: str, trade_value: float, action: str) -> float:
        """Calculates country-specific brokerage, stamp duties, and exchange overheads."""
        raise NotImplementedError()

    def calculate_capital_gains_tax(self, buy_date, sell_date, buy_price: float, sell_price: float,
                                    shares: int) -> float:
        """Applies region-specific transaction tax thresholds (e.g., Indian STCG vs LTCG)."""
        raise NotImplementedError()
