"""Offline end-to-end test of the REAL main.py using synthetic prices (no internet, no yfinance needed).

Prices are random walks with no edge, so no strategy should look great here. If one does, something is wrong
(look-ahead, bad accounting). Run from the project root:  python tests/test_synthetic.py
"""
import os, sys, shutil, tempfile
import numpy as np
import pandas as pd

PKG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "python", "portfoliopilot")
sys.path.insert(0, os.path.abspath(PKG))
os.environ.setdefault("MPLBACKEND", "Agg")

import universes
from main import QuantitativeDiscoveryEngine


def fake_price_loader(tickers, start, end, cache_dir, use_cache=True):
    rng = np.random.default_rng(7)
    idx = pd.bdate_range(start, end)
    data = {}
    for t in tickers:
        if t == "^BSESN":
            data[t] = 30000 * np.exp(np.cumsum(rng.normal(0.0004, 0.009, len(idx))))
        elif t == "USDINR=X":
            data[t] = 75 + np.cumsum(rng.normal(0, 0.05, len(idx)))
        else:
            data[t] = 400 * np.exp(np.cumsum(rng.normal(0.0003, 0.017, len(idx))))
    return pd.DataFrame(data, index=idx)


if __name__ == "__main__":
    out = tempfile.mkdtemp(prefix="pp_test_")
    cfg = os.path.join(out, "config.properties")
    shutil.copy(os.path.join(PKG, "config.properties"), cfg)
    text = open(cfg).read()
    text = text.replace("start_date = 2018-01-01", "start_date = 2021-01-01").replace("end_date = 2026-10-31", "end_date = 2024-12-31")
    text = text.replace("split_date = 2023-01-01", "split_date = 2023-06-01")
    open(cfg, "w").write(text)

    reports = os.path.join(out, "reports")
    QuantitativeDiscoveryEngine(config_path=cfg, reports_dir=reports, price_loader=fake_price_loader).execute_grid_search()

    df = pd.read_csv(os.path.join(reports, "optimal_strategy_matrix.csv"))
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(df[["Label", "Net_Return_Pct", "Max_Drawdown_Pct", "Benchmark_Return_Pct", "Trades", "Avg_Invested_Pct", "OutOfSample_Return_Pct"]].to_string(index=False))
    assert (df["Universe"] == "COMBINED").any(), "combined portfolio rows missing"
    print("\nFiles:", sorted(f for f in os.listdir(reports) if f.endswith('.png')))
    print("TEST OK, outputs in", out)
