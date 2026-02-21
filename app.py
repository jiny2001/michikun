import streamlit as st
import plotly.express as px
import pandas as pd

from config import load_config
import data
import db
import metrics

st.set_page_config(page_title="michikun", page_icon="📈", layout="wide")

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

if st.sidebar.button("Refresh Data", type="primary"):
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

price_data = data.load_all_prices(tickers, cfg.db_path)

if not price_data:
    st.info("No data yet. Click **Refresh Data** in the sidebar to fetch prices.")
    st.stop()

# Price history chart
st.subheader("Price History (Close)")
frames = []
for ticker, df in price_data.items():
    tmp = df[["Close"]].copy().reset_index()
    tmp.columns = ["date", "close"]
    tmp["ticker"] = ticker
    frames.append(tmp)

combined = pd.concat(frames)
fig_price = px.line(combined, x="date", y="close", color="ticker", labels={"close": "Close Price", "date": "Date"})
fig_price.update_layout(legend_title="Ticker", hovermode="x unified")
st.plotly_chart(fig_price, use_container_width=True)

# Sharpe ratio chart
st.subheader("Annualized Sharpe Ratio")
sharpe_df = metrics.compute_all_sharpe(price_data, risk_free_rate)

if sharpe_df.empty:
    st.warning("Not enough data to compute Sharpe ratios.")
else:
    def _color(v):
        if v >= 1:
            return "green"
        elif v >= 0:
            return "gold"
        else:
            return "red"

    sharpe_df["color"] = sharpe_df["sharpe"].apply(_color)
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

    # Summary table
    st.subheader("Summary")
    table = sharpe_df[["ticker", "sharpe"]].copy()
    table["sharpe"] = table["sharpe"].round(3)
    st.dataframe(table, use_container_width=True, hide_index=True)
