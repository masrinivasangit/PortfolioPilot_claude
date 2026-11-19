# universes.py - single source of truth for the stock pools used in backtests.
#
# WARNING (survivorship / hindsight bias): these are CURRENT, hand-picked names. Several were big winners
# in 2023-2025. A stock list that only contains survivors makes any strategy look better than it was.
# For a trustworthy test, replace these with point-in-time index constituents for each date.

LARGE_CAPS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS", "LT.NS",
    "BHARTIARTL.NS", "AXISBANK.NS", "MARUTI.NS", "WIPRO.NS", "HINDUNILVR.NS", "KOTAKBANK.NS",
    "BAJAJFINSV.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "M&M.NS", "TITAN.NS", "ULTRACEMCO.NS",
    "NTPC.NS", "POWERGRID.NS", "HCLTECH.NS", "SUNPHARMA.NS", "TATASTEEL.NS", "ONGC.NS",
]

MID_CAPS = [
    "TATAELXSI.NS", "KPITTECH.NS", "POLYCAB.NS", "DIXON.NS", "COFORGE.NS", "MAXHEALTH.NS",
    "PERSISTENT.NS", "CONCOR.NS", "VOLTAS.NS", "CUMMINSIND.NS", "AUBANK.NS", "BANDHANBNK.NS",
    "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BATAINDIA.NS", "BEL.NS", "HAL.NS", "MUTHOOTFIN.NS",
]

RISKY = [
    "YESBANK.NS", "PAYTM.NS", "NYKAA.NS", "POLICYBZR.NS", "IDEA.NS", "SUZLON.NS", "IREDA.NS",
    "RVNL.NS", "IRFC.NS", "JIOFIN.NS", "PNB.NS", "UNIONBANK.NS", "IOB.NS",
]

# Benchmarks / helpers downloaded alongside the pools
BENCHMARK = "^BSESN"
FX = "USDINR=X"

TIER_POOLS = {"LARGE_CAP_TIER": LARGE_CAPS, "MID_CAP_TIER": MID_CAPS, "RISKY_TIER": RISKY}
