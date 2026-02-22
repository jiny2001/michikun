import streamlit as st
import plotly.express as px
import pandas as pd

from config import load_config, save_config
import data
import db
import metrics

st.set_page_config(page_title="michikun", page_icon="📈", layout="wide")

st.markdown("""
<style>
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child {
    max-height: none;
    overflow-y: visible;
}
</style>
""", unsafe_allow_html=True)

cfg = load_config()

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("michikun")

ticker_input = st.sidebar.text_area(
    "Tickers (one per line)",
    value="\n".join(cfg.tickers),
)
tickers = [t.upper().strip() for t in ticker_input.splitlines() if t.strip()]

risk_free_pct = st.sidebar.number_input(
    "Risk-Free Rate (%)", value=cfg.risk_free_rate * 100, min_value=0.0, max_value=20.0, step=0.1
)
risk_free_rate = risk_free_pct / 100

rolling_window = st.sidebar.number_input(
    "Rolling Window (days)",
    min_value=5,
    max_value=1260,
    value=cfg.rolling_window,
    step=1,
)

if st.sidebar.button("Refresh Data", type="primary", use_container_width=True):
    with st.spinner("Fetching data..."):
        results = data.fetch_and_store(tickers, cfg)
    summary = ", ".join(f"{t}: +{n}" for t, n in results.items())
    st.sidebar.success(f"Done — {summary}")
    st.rerun()

# Show last updated time per ticker
conn = db.get_connection(cfg.db_path)
db.init_db(conn)
last_fetched = {t: db.get_last_fetched(conn, t) for t in tickers}
conn.close()
latest = max((v for v in last_fetched.values() if v), default=None)
if latest:
    st.sidebar.caption(f"Last refreshed: {latest[:19].replace('T', ' ')} UTC")

# ── Main ─────────────────────────────────────────────────────────────────────
st.title("Stock Sharpe Ratio Dashboard")

all_price_data = data.load_all_prices(tickers, cfg.db_path)

if not all_price_data:
    st.info("No data yet. Click **Refresh Data** in the sidebar to fetch prices.")
    st.stop()

# Ticker selector — only shows tickers that have data in the DB
available = sorted(all_price_data.keys())
_saved_selected = sorted(t for t in (cfg.selected_tickers or available) if t in available)
# Tickers newly in the DB that weren't known when the config was last saved → auto-select
_known = set(cfg.known_tickers or [])
_truly_new = [t for t in available if _known and t not in _known]
_default_selected = sorted(set(_saved_selected) | set(_truly_new))
st.sidebar.divider()
selected = st.sidebar.multiselect("Show Tickers", options=available, default=_default_selected)

if not selected:
    st.warning("No tickers selected. Choose at least one in the sidebar.")
    st.stop()

# Auto-save whenever any sidebar value differs from what's on disk
if (
    tickers != cfg.tickers
    or abs(risk_free_rate - cfg.risk_free_rate) > 1e-9
    or int(rolling_window) != cfg.rolling_window
    or sorted(selected) != _saved_selected
    or available != (cfg.known_tickers or [])
):
    save_config(tickers, risk_free_rate, int(rolling_window), sorted(selected), available)

# price_data is filtered for charts; all_price_data is used for Sharpe/Summary
price_data = {t: df for t, df in all_price_data.items() if t in selected}

# ── Price History ─────────────────────────────────────────────────────────────
price_col, toggle_col = st.columns([4, 1])
price_col.subheader("Price History (Close)")
relative = toggle_col.toggle("Relative Price", value=True)

# Date range for the chart — also sets the baseline for relative price
all_dates = sorted({
    d for df in price_data.values()
    for d in df.reset_index()["date"].tolist()
})
date_min, date_max = all_dates[0].date(), all_dates[-1].date()
range_start, range_end = st.slider(
    "Date Range",
    min_value=date_min,
    max_value=date_max,
    value=(date_min, date_max),
    format="YYYY-MM-DD",
    label_visibility="collapsed",
)

frames = []
for ticker, df in price_data.items():
    tmp = df[["Close"]].copy().reset_index()
    tmp.columns = ["date", "close"]
    tmp = tmp[(tmp["date"].dt.date >= range_start) & (tmp["date"].dt.date <= range_end)]
    if tmp.empty:
        continue
    if relative:
        first = tmp["close"].iloc[0]
        tmp["close"] = (tmp["close"] / first - 1) * 100
    tmp["ticker"] = ticker
    frames.append(tmp)

combined = pd.concat(frames)
y_label = "Return from Start (%)" if relative else "Close Price"
fig_price = px.line(combined, x="date", y="close", color="ticker", labels={"close": y_label, "date": "Date"})
fig_price.update_layout(legend_title="Ticker", hovermode="x unified")
if relative:
    fig_price.update_yaxes(ticksuffix="%")
    fig_price.add_hline(y=0, line_dash="dash", line_color="gray")
st.plotly_chart(fig_price, use_container_width=True)

# ── Rolling Sharpe Ratio ──────────────────────────────────────────────────────
st.subheader(f"Rolling Sharpe Ratio ({rolling_window}-day window)")
rolling_df = metrics.compute_all_rolling_sharpe(price_data, window=rolling_window, risk_free_rate=risk_free_rate)

if rolling_df.empty:
    st.warning(f"Not enough data for a {rolling_window}-day rolling window. Try a shorter window or refresh data.")
else:
    rolling_df = rolling_df[
        (rolling_df["date"].dt.date >= range_start) & (rolling_df["date"].dt.date <= range_end)
    ]
    fig_rolling = px.line(
        rolling_df,
        x="date",
        y="sharpe",
        color="ticker",
        labels={"sharpe": "Sharpe Ratio", "date": "Date"},
    )
    fig_rolling.add_hline(y=1, line_dash="dash", line_color="green", annotation_text="Sharpe = 1")
    fig_rolling.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Sharpe = 0")
    fig_rolling.update_layout(legend_title="Ticker", hovermode="x unified")
    st.plotly_chart(fig_rolling, use_container_width=True)

# ── Annualized Sharpe Ratio (all tickers) ────────────────────────────────────
st.subheader("Annualized Sharpe Ratio")
sharpe_df = metrics.compute_all_sharpe(all_price_data, risk_free_rate)

if sharpe_df.empty:
    st.warning("Not enough data to compute Sharpe ratios.")
else:
    fig_sharpe = px.bar(
        sharpe_df,
        x="sharpe",
        y="ticker",
        orientation="h",
        color="sharpe",
        color_continuous_scale=["red", "gold", "green"],
        labels={"sharpe": "Sharpe Ratio", "ticker": "Ticker"},
        text=sharpe_df["sharpe"].round(2),
    )
    fig_sharpe.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    st.plotly_chart(fig_sharpe, use_container_width=True)

    # ── Summary (all tickers) ─────────────────────────────────────────────────
    st.subheader("Summary")
    table = sharpe_df[["ticker", "annual_return", "sharpe"]].copy()
    table = table.rename(columns={"annual_return": "Annual Return (%)", "sharpe": "Sharpe Ratio"})
    table["Annual Return (%)"] = table["Annual Return (%)"].round(2)
    table["Sharpe Ratio"] = table["Sharpe Ratio"].round(3)
    st.dataframe(table, use_container_width=True, hide_index=True)
