# registry.py - what strategies and analyst stacks exist. Fresh instances are built on every call,
# so no state leaks between backtest runs.
from strategies.momentum import MomentumSignalModule
from strategies.swing import SwingTradingStrategy
from strategies.long_term import LongTermValueStrategy
from strategies.options import DerivativesOptionsStrategy

from analysis.technical_analyst import TechnicalAnalystAgent
from analysis.fundamental_analyst import FundamentalAnalystAgent
from analysis.news_analyst import NewsAnalystAgent
from analysis.macro_analyst import MacroAnalystAgent
from analysis.velocity_analyst import VelocityBreakoutAnalyst
from analysis.compounder_analyst import LongTermCompounderAnalyst

STRATEGIES = {
    "MOMENTUM": MomentumSignalModule,
    "SWING": SwingTradingStrategy,
    "LONG_TERM": LongTermValueStrategy,
    "OPTIONS": DerivativesOptionsStrategy,
}


def build_analyst_stacks() -> dict:
    """Name -> list of analyst plugin instances (multipliers are multiplied together).

    NOTE: FundamentalAnalystAgent is a price-vs-20-day-median mean-reversion proxy, NOT a PE/earnings model.
    NewsAnalystAgent is neutral in backtests. See CHANGES.md.
    """
    return {
        "QUANT_CORE_TREND": [TechnicalAnalystAgent(), MacroAnalystAgent()],
        "MEAN_REVERSION": [FundamentalAnalystAgent(), MacroAnalystAgent()],
        "VALUATION_ALPHA": [FundamentalAnalystAgent(), MacroAnalystAgent()],  # legacy name for MEAN_REVERSION
        "SENTIMENT_ROTATION": [NewsAnalystAgent(), TechnicalAnalystAgent()],
        "LTCG_COMPOUNDER": [LongTermCompounderAnalyst(), FundamentalAnalystAgent()],
        "HYBRID_INTELLIGENCE": [VelocityBreakoutAnalyst(), MacroAnalystAgent(), FundamentalAnalystAgent()],
        "GEMINI_AI_TREND": [NewsAnalystAgent(analyst_type="GEMINI_AI"), MacroAnalystAgent()],
        "CHATGPT_AI_TREND": [NewsAnalystAgent(analyst_type="CHATGPT_AI"), TechnicalAnalystAgent()],
    }
