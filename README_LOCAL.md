# PortfolioPilot: run locally (Windows)

1. Install Python 3.10+ from python.org (tick "Add Python to PATH").
2. Open a terminal in this folder and run:

       python -m venv .venv
       .venv\Scripts\activate
       pip install -r requirements.txt

3. Offline sanity test (no internet, synthetic prices, takes ~1 min):

       python tests\test_synthetic.py   (runs the real main.py on fake prices)

4. Real backtest (needs internet; downloads prices from Yahoo Finance):

       cd src\main\python\portfoliopilot
       python main.py

   Results go to `reports\` (summary CSV, per-run ledger, per-run `_equity.csv`, PNG charts).

5. Dashboard:

       streamlit run dashboard.py

API keys: do NOT put them in config.properties (it is in a git repo). Use environment variables
GEMINI_API_KEY / OPENAI_API_KEY. In backtests the AI analysts are neutral anyway (see CHANGES.md).

## How to read the results
* Compare `Net_Return_Pct` with `Benchmark_Return_Pct` (Sensex buy & hold). If you cannot beat it
  after costs and tax, the strategy adds nothing.
* Look at `Max_Drawdown_Pct`. A strategy that is +60% but fell -45 % on the way will be hard to hold.
* Tune only on data before `split_date`. Judge on `OutOfSample_Return_Pct`.
  If in-sample looks great and out-of-sample does not, you are overfitting.
* Many strategy x universe x analyst combinations are tested. The best one is partly luck.
