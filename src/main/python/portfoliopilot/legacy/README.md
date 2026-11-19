# legacy/

Modules moved out of the active code path because they were unused, broken or misleading:

* `engine.py` - old standalone engine; calls `compute_rsi`, which no longer exists.
* `performance_plotter.py` - plotted cash only (ignored holdings), unused.
* `fundamentals.py` - hard-coded PE/margin numbers for 2 stocks only, default 22 for the rest. Not real data.
* `market_data.py` - index scraper pointing at `https://wikipedia.org` (invalid page), unused.
* `rebalancing.py` - duplicate of `portfolio/rebalancing.py`.

Nothing imports these. Delete them if you do not need them.
