import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from app.settings import DB_URL, STOCKS

"""
This is the Streamlist Frond-End. Allows for the following:
    User to pick a stock
    Pull the stocks risk scores, volatility, and sentiment
    Plot them in charts
    Shows a "Top Risk Movers (last 7 days)" section for quick insights
"""

# Connect to your DB once for read-only queries
engine = create_engine(DB_URL, future=True)

st.title("Financial Risk Dashboard — v0 (read-only)")

# Choose which stock’s time series to view
stock = st.selectbox("Select a stock", STOCKS)
days = st.slider("Days to display", 30, 365, 120)

# Plot the risk score line for 1 stock
risk = pd.read_sql(
    text("SELECT date, total_score, vol_20d, news_sent_7d "
         "FROM risk_scores WHERE stock = :s ORDER BY date"),
    engine, params={"s": stock}
)

if risk.empty:
    st.warning("No risk scores yet. Make sure ETLs and risk_engine ran.")
else:
    risk_tail = risk.tail(days).copy()
    risk_tail["date"] = pd.to_datetime(risk_tail["date"])
    st.line_chart(risk_tail.set_index("date")[["total_score"]], height=260)
    st.caption("Total Risk Score (higher = riskier).")

    c1, c2 = st.columns(2)
    with c1:
        st.line_chart(risk_tail.set_index("date")[["vol_20d"]], height=200)
        st.caption("20-day Volatility")
    with c2:
        st.line_chart(risk_tail.set_index("date")[["news_sent_7d"]], height=200)
        st.caption("7-day Avg News Sentiment (VADER)")

# Show Top Risk Movers (7d) to surface insight quickly
st.subheader("Top Risk Movers (last 7 days)")
with engine.connect() as c:
    # Pull recent window for all stocks
    df = pd.read_sql(
        text("SELECT stock, date, total_score FROM risk_scores ORDER BY date"),
        c
    )
if df.empty:
    st.info("No risk data yet across stocks.")
else:
    df["date"] = pd.to_datetime(df["date"])
    cutoff = df["date"].max() - pd.Timedelta(days=60)
    df = df[df["date"] >= cutoff].copy()

    # Compute 7d delta per stock (forward-filled daily index)
    movers = []
    for stck, g in df.groupby("stock"):
        g = g.set_index("date").asfreq("D").ffill()
        if len(g) < 8:  # need at least 7-day gap
            continue
        latest = g.index.max()
        prev = latest - pd.Timedelta(days=7)
        # if exact prev missing, nearest earlier day
        if prev not in g.index:
            prev = g.index[g.index.get_indexer([prev], method="nearest")][0]
        delta = float(g.loc[latest, "total_score"] - g.loc[prev, "total_score"])
        movers.append({"stock": stck, "latest": latest.date(),
                       "now": float(g.loc[latest, "total_score"]),
                       "prev": float(g.loc[prev, "total_score"]),
                       "delta_7d": delta})
    mv = pd.DataFrame(movers).sort_values("delta_7d", ascending=False)

    if mv.empty:
        st.info("Not enough recent data to compute movers.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Biggest Risers**")
            st.dataframe(mv.head(5).reset_index(drop=True))
        with c2:
            st.markdown("**Biggest Fallers**")
            st.dataframe(mv.tail(5).sort_values("delta_7d").reset_index(drop=True))

        top5 = mv.head(5).set_index("stock")["delta_7d"]
        if not top5.empty:
            st.bar_chart(top5)
