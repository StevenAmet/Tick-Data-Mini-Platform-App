# -------------------------------
# run: streamlit run app.py
# -------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Tick Data Mini-Platform", layout="wide")

# -------------------------------
# TITLE
# -------------------------------
st.title("📈 Tick Data Mini-Platform")
st.caption("Synthetic Market Data | Tick Store | Spread, VWAP & Volume Analytics")
st.markdown("**Created by Steven Amet**")

st.markdown(
    """
This app is a trading-style mini-platform that simulates tick data, stores it in a simple
intraday/historical structure, and runs basic market microstructure analytics.

- Generate tick-style market data
- Store and query intraday ticks
- Analyse spread, VWAP, returns and volume bursts
- Build toward TCA and order-book analytics later
"""
)

# -------------------------------
# SIDEBAR SETTINGS
# -------------------------------
st.sidebar.header("⚙️ Data Settings")

symbols = st.sidebar.multiselect(
    "Symbols",
    ["EURUSD", "GBPUSD", "USDJPY", "AAPL", "MSFT", "ES_F"],
    default=["EURUSD", "GBPUSD"]
)

num_ticks = st.sidebar.slider("Ticks per symbol", 500, 10000, 2000, step=500)
seed = st.sidebar.number_input("Random seed", min_value=0, max_value=99999, value=42)
base_date = st.sidebar.date_input("Trading date", value=datetime.today().date())


# -------------------------------
# DATA GENERATION
# -------------------------------
@st.cache_data
def generate_synthetic_ticks(symbols, num_ticks, seed, base_date):
    rng = np.random.default_rng(seed)
    all_frames = []

    base_prices = {
        "EURUSD": 1.08,
        "GBPUSD": 1.27,
        "USDJPY": 151.5,
        "AAPL": 210.0,
        "MSFT": 425.0,
        "ES_F": 5250.0,
    }

    start_dt = datetime.combine(base_date, datetime.min.time()) + timedelta(hours=8)

    for sym in symbols:
        base = base_prices.get(sym, 100.0)
        timestamps = [
            start_dt + timedelta(milliseconds=int(i * 250 + rng.integers(0, 80)))
            for i in range(num_ticks)
        ]

        mid_moves = rng.normal(0, base * 0.00015, size=num_ticks)
        mids = base + np.cumsum(mid_moves)
        spreads = np.abs(rng.normal(base * 0.00008, base * 0.00003, size=num_ticks))
        bids = mids - spreads / 2
        asks = mids + spreads / 2
        bid_sizes = rng.integers(1, 25, size=num_ticks) * 100
        ask_sizes = rng.integers(1, 25, size=num_ticks) * 100
        last_prices = mids + rng.normal(0, spreads / 4, size=num_ticks)
        trade_sizes = rng.integers(1, 40, size=num_ticks) * 100

        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "symbol": sym,
                "bid": bids,
                "ask": asks,
                "bid_size": bid_sizes,
                "ask_size": ask_sizes,
                "trade_price": last_prices,
                "trade_size": trade_sizes,
            }
        )
        df["mid"] = (df["bid"] + df["ask"]) / 2
        df["spread"] = df["ask"] - df["bid"]
        all_frames.append(df)

    ticks = pd.concat(all_frames, ignore_index=True).sort_values(["symbol", "timestamp"])
    return ticks


# -------------------------------
# SIMPLE STORAGE LAYERS
# -------------------------------
@st.cache_data
def build_storage_layers(ticks):
    ticks = ticks.copy()
    ticks["date"] = pd.to_datetime(ticks["timestamp"]).dt.date

    intraday = ticks.copy()
    historical = (
        ticks.groupby(["date", "symbol"], as_index=False)
        .agg(
            open_price=("trade_price", "first"),
            high_price=("trade_price", "max"),
            low_price=("trade_price", "min"),
            close_price=("trade_price", "last"),
            total_volume=("trade_size", "sum"),
            avg_spread=("spread", "mean"),
            tick_count=("trade_price", "count"),
        )
    )
    return intraday, historical


def calc_vwap(df):
    vol = df["trade_size"].sum()
    if vol == 0:
        return np.nan
    return (df["trade_price"] * df["trade_size"]).sum() / vol


def calc_volume_bursts(df, window=25, threshold=2.0):
    rolling = df["trade_size"].rolling(window=window, min_periods=5).mean()
    baseline = df["trade_size"].expanding(min_periods=5).mean()
    signal = rolling / baseline
    bursts = signal > threshold
    out = df[["timestamp", "trade_size"]].copy()
    out["rolling_ratio"] = signal
    out["burst"] = bursts
    return out


# -------------------------------
# LOAD DATA
# -------------------------------
if not symbols:
    st.warning("Please select at least one symbol.")
    st.stop()

ticks = generate_synthetic_ticks(symbols, num_ticks, seed, base_date)
intraday, historical = build_storage_layers(ticks)

st.markdown("### 🗃️ Data Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Total Ticks", f"{len(intraday):,}")
col2.metric("Symbols", f"{intraday['symbol'].nunique()}")
col3.metric("Trading Date", str(base_date))

st.markdown(
    """
**What this section does:**
Creates a simplified tick-data store with:
- **Intraday layer** for full tick-by-tick data
- **Historical layer** for end-of-day summaries

This mirrors the type of separation often used in kdb+/q environments.
"""
)

# -------------------------------
# TABLE VIEWS
# -------------------------------
st.markdown("### 🔎 Intraday Tick Store")
st.dataframe(intraday.head(50), use_container_width=True)

st.markdown("### 📚 Historical Summary Store")
st.dataframe(historical, use_container_width=True)

# -------------------------------
# SYMBOL SELECTION
# -------------------------------
st.markdown("### 🎯 Symbol Analytics")
selected_symbol = st.selectbox("Choose symbol", sorted(intraday["symbol"].unique()))
selected = intraday[intraday["symbol"] == selected_symbol].copy().sort_values("timestamp")
selected["return_bps"] = selected["trade_price"].pct_change() * 10000
selected["cum_volume"] = selected["trade_size"].cumsum()
selected["vwap_running"] = (
    (selected["trade_price"] * selected["trade_size"]).cumsum()
    / selected["trade_size"].cumsum()
)

vwap_value = calc_vwap(selected)
avg_spread = selected["spread"].mean()
realized_vol_bps = selected["return_bps"].std()

m1, m2, m3 = st.columns(3)
m1.metric("VWAP", f"{vwap_value:,.4f}")
m2.metric("Average Spread", f"{avg_spread:,.5f}")
m3.metric("Realized Vol (bps)", f"{realized_vol_bps:,.2f}")

# -------------------------------
# PRICE CHART
# -------------------------------
st.markdown("### 📉 Trade Price")
fig1, ax1 = plt.subplots(figsize=(10, 4))
ax1.plot(selected["timestamp"], selected["trade_price"])
ax1.set_xlabel("Time")
ax1.set_ylabel("Trade Price")
ax1.set_title(f"{selected_symbol} Trade Price")
st.pyplot(fig1)

# -------------------------------
# SPREAD CHART
# -------------------------------
st.markdown("### ↔️ Bid-Ask Spread")
fig2, ax2 = plt.subplots(figsize=(10, 4))
ax2.plot(selected["timestamp"], selected["spread"])
ax2.set_xlabel("Time")
ax2.set_ylabel("Spread")
ax2.set_title(f"{selected_symbol} Spread")
st.pyplot(fig2)

# -------------------------------
# VWAP VS PRICE
# -------------------------------
st.markdown("### 📊 Price vs Running VWAP")
fig3, ax3 = plt.subplots(figsize=(10, 4))
ax3.plot(selected["timestamp"], selected["trade_price"], label="Trade Price")
ax3.plot(selected["timestamp"], selected["vwap_running"], label="Running VWAP")
ax3.set_xlabel("Time")
ax3.set_ylabel("Price")
ax3.set_title(f"{selected_symbol} Price vs VWAP")
ax3.legend()
st.pyplot(fig3)

# -------------------------------
# VOLUME BURSTS
# -------------------------------
st.markdown("### 🚨 Volume Burst Detection")
burst_window = st.slider("Burst rolling window", 10, 100, 25)
burst_threshold = st.slider("Burst threshold", 1.1, 5.0, 2.0, step=0.1)

bursts = calc_volume_bursts(selected, window=burst_window, threshold=burst_threshold)
burst_events = bursts[bursts["burst"]].copy()

b1, b2 = st.columns(2)
b1.metric("Burst Events", f"{len(burst_events)}")
b2.metric("Max Burst Ratio", f"{bursts['rolling_ratio'].max():.2f}")

fig4, ax4 = plt.subplots(figsize=(10, 4))
ax4.plot(bursts["timestamp"], bursts["rolling_ratio"])
ax4.set_xlabel("Time")
ax4.set_ylabel("Rolling / Baseline Volume")
ax4.set_title(f"{selected_symbol} Volume Burst Signal")
st.pyplot(fig4)

if not burst_events.empty:
    st.dataframe(burst_events.head(20), use_container_width=True)
else:
    st.info("No burst events detected with current settings.")

# -------------------------------
# QUERY SECTION
# -------------------------------
st.markdown("### 🧮 Query Console (Predefined)")
query_type = st.selectbox(
    "Choose analysis",
    [
        "Last 10 ticks",
        "Largest trades",
        "Widest spreads",
        "Summary stats",
    ],
)

if query_type == "Last 10 ticks":
    result = selected.tail(10)
elif query_type == "Largest trades":
    result = selected.nlargest(10, "trade_size")
elif query_type == "Widest spreads":
    result = selected.nlargest(10, "spread")
else:
    result = pd.DataFrame(
        {
            "metric": ["rows", "vwap", "avg_spread", "total_volume", "max_trade"],
            "value": [
                len(selected),
                calc_vwap(selected),
                selected["spread"].mean(),
                selected["trade_size"].sum(),
                selected["trade_size"].max(),
            ],
        }
    )

st.dataframe(result, use_container_width=True)

# -------------------------------
# EXECUTIVE SUMMARY
# -------------------------------
st.markdown("### 🧠 Executive Summary")
st.write(
    f"""
This mini-platform simulates a basic trading-data environment for **{selected_symbol}**.

- Tick data is generated and stored in an **intraday layer**
- Daily aggregates are stored in a **historical layer**
- Core analytics include **spread analysis**, **VWAP tracking**, **returns**, and **volume burst detection**

This is a solid first version for GitHub and interviews, and can later be extended into:
- transaction cost analysis,
- order-book reconstruction,
- live feed ingestion,
- or a proper kdb+/q backend.
"""
)
