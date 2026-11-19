# analysis/news_analyst.py
import pandas as pd

_WARNED = False


class NewsAnalystAgent:
    """Placeholder sentiment analyst.

    The previous version generated "sentiment" from a hash of ticker + date, which is
    deterministic random noise and was mistaken for AI/news analysis. This version is
    deliberately NEUTRAL (multiplier 1.0) so it cannot inject fake signal into a backtest.

    Real news sentiment in a backtest needs point-in-time historical headlines (what was
    published BEFORE each date). Asking an LLM about an old date does not work either: the
    model was trained on data after that date and already knows what happened (look-ahead).
    Use this class only for LIVE trading, with today's headlines, once you have a news feed.
    """

    def __init__(self, ai_provider=None, analyst_type: str = "NEWS_KEYWORD"):
        self.ai_provider = ai_provider
        self.analyst_type = str(analyst_type).strip().upper()
        self.name = "AI_Sentiment_Analyst"
        self.sentiment_cache = {}

    def calculate_factor_multiplier(self, ticker: str, historical_data: pd.DataFrame, evaluation_date=None) -> float:
        global _WARNED
        if not _WARNED:
            print("   NOTE: NewsAnalystAgent is neutral (1.0) in backtests: no point-in-time news data available.")
            _WARNED = True
        return 1.0
