# dashboard.py
import configparser
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

st.set_page_config(page_title="PortfolioPilot Flight Deck", page_icon="✈️", layout="wide")

# Architectural Alignment: Pointing directly to the active reports paths
config_path = os.path.join(current_dir, "config.properties")
reports_dir = os.path.join(current_dir, "reports")
matrix_path = os.path.join(reports_dir, "optimal_strategy_matrix.csv")

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))

# Dynamic Fallback Anchors: Used only if the properties file is physically missing
initial_capital_base = 10000.00
configured_start_date = "2026-05-01"
configured_end_date = "2026-06-30"

# Parse configuration matrices directly from your live config file limits
if os.path.exists(config_path):
    try:
        config.read(config_path)
        if config.has_section("MARKET_SETTINGS"):
            initial_capital_base = config.getfloat("MARKET_SETTINGS", "total_budget")
        if config.has_section("BACKTEST_SETTINGS"):
            configured_start_date = config.get("BACKTEST_SETTINGS", "start_date").strip()
            configured_end_date = config.get("BACKTEST_SETTINGS", "end_date").strip()
    except Exception as e:
        st.sidebar.error(f"⚠️ Error parsing config.properties layout: {str(e)}")

st.title("✈️ PortfolioPilot Institutional Strategy Discovery Dashboard")
st.markdown("Automated quantitative optimization tracking, dynamic multi-agent evidence fusion, and cross-border risk reporting.")

# Render Control Sidebar Panel
st.sidebar.header("🛠️ Discovery Control Panel")
st.sidebar.markdown(f"**Active Configuration Base Matrix:**")
st.sidebar.info(f"💵 Initial Capital: **₹{initial_capital_base:,.2f}**\n\n📅 Horizon: **{configured_start_date}** to **{configured_end_date}**")

if not os.path.exists(matrix_path) or os.stat(matrix_path).st_size <= 50:
    st.warning("⚠️ Discovery Matrix database is empty or missing. Please execute 'python main.py' to generate ledgers first.")
else:
    df_matrix = pd.read_csv(matrix_path)
    df_matrix.columns = [col.strip() for col in df_matrix.columns]

    if df_matrix.empty:
        st.info("ℹ️ The ledger matrix file exists but contains no tracking data rows yet.")
    else:
        zones = ["ALL"] + list(df_matrix["Zone"].unique())
        selected_zone = st.sidebar.selectbox("Filter by Zone", zones)

        sort_metrics = ["Sharpe_Ratio", "Net_Return_Pct", "Max_Drawdown_Pct", "Taxes_Paid_INR"]
        target_metric = st.sidebar.selectbox("Optimize Dashboard Rankings By", sort_metrics)

        filtered_df = df_matrix if selected_zone == "ALL" else df_matrix[df_matrix["Zone"] == selected_zone]

        ascending_flag = (target_metric in ["Max_Drawdown_Pct", "Taxes_Paid_INR"])
        filtered_df = filtered_df.sort_values(by=target_metric, ascending=ascending_flag)

        # FIXED CORE SUB-SCRIPTABLE INDEXING BUG: Explicitly extract the top row using index locator slice positional [0]
        best_strategy = filtered_df.iloc[0] if not filtered_df.empty else None

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="🏆 Top Strategy Engine", value=best_strategy["Label"] if best_strategy is not None else "N/A")
        with col2:
            st.metric(label="🧠 Optimal Analyst Core", value=best_strategy["Analyst_Layer"] if best_strategy is not None else "N/A")
        with col3:
            st.metric(label="🎯 Sharpe Ratio", value=f"{float(best_strategy['Sharpe_Ratio']):.2f}" if best_strategy is not None else "N/A")
        with col4:
            st.metric(label="📈 Absolute Net Return", value=f"{float(best_strategy['Net_Return_Pct']):.2f}%" if best_strategy is not None else "N/A")

        st.markdown("---")
        st.subheader("📊 Strategy Discovery Leaderboard Matrix")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📊 Authenticated Multi-Agent Performance Curves")
        unique_analysts = list(df_matrix["Analyst_Layer"].unique())

        for idx_layer, analyst in enumerate(unique_analysts):
            analyst_subset = filtered_df[filtered_df["Analyst_Layer"] == analyst]
            valid_render_rows = []

            for _, row in analyst_subset.iterrows():
                lbl = row["Label"]
                run_ledger_file = os.path.join(reports_dir, f"backtest_ledger_{lbl}.csv")
                if os.path.exists(run_ledger_file):
                    valid_render_rows.append((row, run_ledger_file))

            if not valid_render_rows:
                continue

            st.markdown(f"#### 📈 Isolate Curve Layer: [ {analyst} Framework Comparisons ]")
            fig, ax = plt.subplots(figsize=(10, 3.5))
            has_global_plots = False
            global_min_date = pd.to_datetime(configured_start_date)
            global_max_date = pd.to_datetime(configured_end_date)

            # Real daily mark-to-market equity curves saved by the backtest (nothing simulated here)
            benchmark_series = None
            for seed_idx, (row, run_ledger_file) in enumerate(valid_render_rows):
                label = row["Label"]
                equity_file = run_ledger_file.replace(".csv", "_equity.csv")
                if not os.path.exists(equity_file):
                    continue
                eq = pd.read_csv(equity_file, index_col=0, parse_dates=True)
                if eq.empty:
                    continue
                ax.plot(eq.index, eq["Equity"], label=f"{label}", linewidth=1.5, alpha=0.85)
                if "Benchmark" in eq.columns and benchmark_series is None:
                    benchmark_series = eq["Benchmark"]
                global_min_date = min(global_min_date, eq.index.min())
                global_max_date = max(global_max_date, eq.index.max())
                has_global_plots = True

            # --- INSIDE THE DASHBOARD.PY CHART FINALIZATION BLOCK ---
            if has_global_plots:
                ax.axhline(y=initial_capital_base, color="red", linestyle="--", alpha=0.4,
                           label=f"Base (₹{initial_capital_base:,.0f})")

                if benchmark_series is not None:
                    ax.plot(benchmark_series.index, benchmark_series.values, color="#7f7f7f", linestyle="-.",
                            linewidth=1.5, alpha=0.8, label="Sensex buy & hold (price index)")

                ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
                ax.set_xlim(left=global_min_date, right=global_max_date)
                ax.set_xlabel("Timeline Horizons Checkpoints", fontsize=8)
                ax.set_ylabel("Portfolio Valuation (INR)", fontsize=8)
                ax.grid(True, linestyle=":", alpha=0.5)
                ax.legend(loc="upper left", fontsize=7, bbox_to_anchor=(1.02, 1.0))

                fig.autofmt_xdate(rotation=35)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

        st.markdown("---")
        st.subheader("🛡️ Regulatory Drag Accounting & Self-Analysis Audit")
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("### 💵 Transaction Costs and Slippage Impact Analysis")
            friction_cost_val = best_strategy["Taxes_Paid_INR"] if (best_strategy is not None and "Taxes_Paid_INR" in best_strategy) else 0.0
            st.info(f"Total regulatory friction charges accounted for in current optimal run: **INR {float(friction_cost_val):,.2f}**")
