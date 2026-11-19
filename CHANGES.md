# What was changed and why

## Bugs that made results look better (or different) than reality
1. **Fake performance charts.** `calculations.py` and `dashboard.py` drew a straight line from the
   starting capital to the final value plus random noise, and the dashboard's "Sensex baseline" was a
   hard-coded flat line (+0.5%). Charts now use the real daily equity curve and the real Sensex.
2. **Drawdown / volatility / Sharpe were computed from ledger rows only**, so holding a stock through a
   crash showed 0% drawdown. Now: daily mark-to-market equity (`<ledger>_equity.csv`). The trade-count
   fudge on Sharpe was removed; Sharpe now uses a risk-free rate.
3. **Same-day execution (look-ahead).** Signals used today's close and traded at today's close.
   Now: signal from the previous close, trade at the next close.
4. **MacroAnalyst never saw the index.** The slice passed to analysts contained only pool stocks, so
   "market regime" was the first stock in the pool. Analysts now receive ^BSESN.
5. **Analysts starved of history.** With a 15-day lookback, MacroAnalyst (needs 20 days) and
   Compounder (needs 15) returned neutral. Analysts now get >= 60 days (strategies keep their lookback).
6. **NewsAnalystAgent produced hash-based pseudo-random "sentiment"** (and never called Gemini/OpenAI).
   It is now neutral (1.0). Real news backtesting needs point-in-time headlines; LLMs asked about old
   dates already know the outcome (look-ahead).
7. **Closing trades** were charged a flat Rs 20 and no tax. They now use the normal cost/tax engine.

## Realism
* Slippage (`[COST_SETTINGS] slippage_bps`, default 10 bps per side).
* Capital-gains tax by date (15%/10% before 23 Jul 2024, 20%/12.5% after, + 4% cess).
  Not modelled: LTCG exemption, loss set-off, surcharge, dividends.
* Removed the magic-number hack (`trade_value == 0.27 ...`) from the cost engine.

## Testing hygiene
* Test window now 2018-01-01 to 2026-10-31 with `split_date` for out-of-sample reporting.
* Benchmark return, CAGR, trades, average capital invested added to the summary CSV.
* API keys read from environment variables first.

## Round 2: logic fixes and refactor
* **Tiers now share one capital pool.** Each tier is simulated with budget x tier weight (it used to deploy only
  a fraction of cash, leaving the rest idle). `RUN_..._COMBINED_...` rows add the tier curves into the real
  whole-portfolio result.
* **Allocation is equal-weight** across the selected stocks (it used to be score-weighted and could leave a pick
  with 1 share, and later picks got less because the budget shrank). Stocks priced above their slice are skipped.
* **Drawdown gate re-arms.** The -25% gate measured from the all-time peak, so one bad patch stopped the strategy
  for good. It now uses a trailing ~6-month peak (`[RISK_SETTINGS]`).
* **Analyst weights were run-order dependent** (they changed with the experiment number). They are now fixed.
* **Winner report** prints Sharpe, Sensex return, in-sample and out-of-sample returns, with a luck warning.
* **Refactor:** `main.py` split into small methods; stock lists moved to `universes.py`; strategies and analyst
  stacks in `registry.py`; downloads cached in `data_cache/` (`data/price_loader.py`); summary columns defined once
  in `backtesting/summary.py`; module-reload hack removed; unused or broken modules moved to `legacy/`.
* Backtests no longer need the Gemini/OpenAI packages or keys.
* Biweekly: `momentum_rebalance_days = 10` trading days.
* `tests/test_synthetic.py` now runs the real `main.py` end to end on fake prices.

## Still NOT fixed (you should know)
* **Survivorship / hindsight bias in the stock lists** (hand-picked current names, many big winners).
  Fix: use point-in-time index membership.
* **"Valuation" is not PE.** It is a mean-reversion proxy (see `analysis/fundamental_analyst.py`).
* **No news/AI signal in backtests** (neutral by design, see above).
* Stops execute at the close, so gap-downs are understated. No volume/liquidity limits.
* No broker connection yet (planned: paper-trading list first).
