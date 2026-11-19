# data/price_loader.py - downloads daily close prices once and caches them on disk.
import os
import hashlib
import pandas as pd


def load_prices(tickers: list, start: str, end: str, cache_dir: str, use_cache: bool = True) -> pd.DataFrame:
    """Returns a DataFrame of adjusted daily closes (index = date, columns = UPPERCASE tickers)."""
    tickers = sorted({str(t).strip().upper() for t in tickers})
    key = hashlib.md5(f"{','.join(tickers)}|{start}|{end}".encode()).hexdigest()[:12]
    cache_path = os.path.join(cache_dir, f"prices_{key}.csv")

    if use_cache and os.path.exists(cache_path):
        print(f"   Using cached prices: {cache_path}")
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)

    import yfinance as yf  # imported lazily so tests can stub it
    print(f"   Downloading {len(tickers)} tickers from {start} to {end} ...")
    raw = yf.download(tickers, start=start, end=end, interval="1d", progress=False, auto_adjust=True)
    if raw is None or raw.empty:
        raise RuntimeError("Price download returned no data (check internet / ticker names).")

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw.xs("Close", axis=1, level=0)
    else:
        prices = raw[["Close"]] if "Close" in raw.columns else raw
    prices = prices.copy()
    if getattr(prices.index, "tz", None) is not None:
        prices.index = prices.index.tz_localize(None)
    prices.columns = [str(c).strip().upper() for c in prices.columns]

    empty_cols = [c for c in prices.columns if prices[c].dropna().empty]
    missing = sorted(set(tickers) - set(prices.columns)) + empty_cols
    if missing:
        print(f"   WARNING: no price data for: {', '.join(missing)} (renamed / delisted / wrong symbol).")
        print("            Dropping them is itself survivorship bias - note it when reading results.")
    prices = prices.drop(columns=empty_cols).sort_index()

    os.makedirs(cache_dir, exist_ok=True)
    prices.to_csv(cache_path)
    return prices
