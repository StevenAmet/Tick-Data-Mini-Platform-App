import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import requests
import yfinance as yf

st.set_page_config(page_title="Tick Data Mini-Platform", layout="wide")

# -------------------------------
# TITLE
# -------------------------------
st.title("📈 Tick Data Mini-Platform")
st.caption("Synthetic Market Data | Tick Store | Spread, VWAP & Volume Analytics")
st.markdown("**Created by Steven Amet**")

with st.expander("What this app does", expanded=True):
    st.markdown(
        """
This dashboard is designed to **simulate how trading firms work with high-frequency market data**.

A **tick** is a single market update. It can represent a quote update, a trade, or a change in market conditions at a specific moment in time.

This app helps the user:
- generate realistic synthetic tick data for multiple instruments
- organise it into a simple **intraday** and **historical** structure
- analyse **price behaviour, spreads, VWAP, returns, and volume spikes**
- understand how raw market data becomes usable trading insight

This first version uses **synthetic data**, which means the prices are simulated rather than pulled from a live market feed. That makes it useful for learning, prototyping, and demonstrating market-data analytics.
        """
    )
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
st.sidebar.markdown(
    """
Use these controls to change the simulated market environment.

- **Symbols**: choose which markets or instruments to generate
- **Ticks per symbol**: choose how much intraday data to create
- **Random seed**: keeps the simulation reproducible
- **Trading date**: sets the date for the synthetic session
    """
)

symbols = st.sidebar.multiselect(
    "Symbols",
    ["EURUSD", "GBPUSD", "USDJPY", "AAPL", "MSFT", "ES_F"],
    default=["EURUSD", "GBPUSD"]
)

num_ticks = st.sidebar.slider("Ticks per symbol", 500, 10000, 2000, step=500)
seed = st.sidebar.number_input("Random seed", min_value=0, max_value=99999, value=42)
base_date = st.sidebar.date_input("Trading date", value=datetime.today().date())
use_live_anchors = st.sidebar.checkbox("Use live market anchors", value=True)


# -------------------------------
# LIVE PRICE ENGINE
# -------------------------------
@st.cache_data(ttl=3600)
def fetch_all_fx_rates():
    try:
        url = "https://api.frankfurter.app/latest"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return {}
        data = response.json()
        if not data or "rates" not in data:
            return {}
        rates = data["rates"]
        rates["EUR"] = 1.0
        return rates
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def fetch_yfinance_price(ticker):
    try:
        data = yf.download(ticker, period="5d", progress=False, auto_adjust=False)
        if data.empty:
            return None
        if "Close" in data:
            close_series = data["Close"].dropna()
            if len(close_series) > 0:
                value = close_series.iloc[-1]
                if hasattr(value, "item"):
                    value = value.item()
                return float(value)
        return None
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_fx_rate(from_curr, to_curr):
    if from_curr == to_curr:
        return 1.0

    rates = fetch_all_fx_rates()

    if rates:
        if from_curr == "EUR" and to_curr in rates:
            return rates[to_curr]
        if to_curr == "EUR" and from_curr in rates:
            return 1 / rates[from_curr]
        if from_curr in rates and to_curr in rates:
            return rates[to_curr] / rates[from_curr]

    rate = fetch_yfinance_price(f"{from_curr}{to_curr}=X")
    if rate is not None:
        return rate

    inverse = fetch_yfinance_price(f"{to_curr}{from_curr}=X")
    if inverse is not None:
        return 1 / inverse

    return np.nan


@st.cache_data(ttl=3600)
def get_live_anchor_prices(symbols):
    live_prices = {}

    fx_symbols = [s for s in symbols if len(s) == 6 and s.isalpha()]
    asset_map = {
        "AAPL": "AAPL",
        "MSFT": "MSFT",
        "ES_F": "ES=F",
    }

    for sym in fx_symbols:
        from_curr = sym[:3]
        to_curr = sym[3:]
        fx_rate = get_fx_rate(from_curr, to_curr)
        if not pd.isna(fx_rate):
            live_prices[sym] = float(fx_rate)

    for sym, ticker in asset_map.items():
        if sym in symbols:
            px = fetch_yfinance_price(ticker)
            if px is not None:
                live_prices[sym] = float(px)

    return live_prices


# -------------------------------
# DATA GENERATION
# -------------------------------
@st.cache_data
def generate_synthetic_ticks(symbols, num_ticks, seed, base_date, anchor_prices):
    rng = np.random.default_rng(seed)
    all_frames = []

    default_base_prices = {
        "EURUSD": 1.08,
        "GBPUSD": 1.27,
        "USDJPY": 151.5,
        "AAPL": 210.0,
        "MSFT": 425.0,
        "ES_F": 5250.0,
    }

    base_prices = default_base_prices.copy()
    if anchor_prices:
        base_prices.update(anchor_prices)

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

        trade_side = rng.choice(["BUY", "SELL"], size=num_ticks)
        exec_slippage = rng.normal(0, spreads / 6, size=num_ticks)
        df["trade_side"] = trade_side
        df["arrival_mid"] = mids
        df["execution_price"] = np.where(
            trade_side == "BUY",
            last_prices + np.abs(exec_slippage),
            last_prices - np.abs(exec_slippage),
        )
        df["mid"] = (df["bid"] + df["ask"]) / 2
        df["spread"] = df["ask"] - df["bid"]
        df["liquidity_score"] = (df["bid_size"] + df["ask_size"]) / df["spread"].replace(0, np.nan)
        df["order_imbalance"] = (df["bid_size"] - df["ask_size"]) / (df["bid_size"] + df["ask_size"])
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
            avg_liquidity_score=("liquidity_score", "mean"),
            avg_order_imbalance=("order_imbalance", "mean"),
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


def calc_tca_metrics(df):
    out = df.copy()
    out["signed_cost"] = np.where(
        out["trade_side"] == "BUY",
        out["execution_price"] - out["arrival_mid"],
        out["arrival_mid"] - out["execution_price"],
    )
    out["slippage_bps"] = (out["signed_cost"] / out["arrival_mid"]) * 10000
    out["notional"] = out["execution_price"] * out["trade_size"]

    total_notional = out["notional"].sum()
    weighted_slippage = np.nan
    if total_notional != 0:
        weighted_slippage = (out["slippage_bps"] * out["notional"]).sum() / total_notional

    summary = {
        "avg_slippage_bps": out["slippage_bps"].mean(),
        "weighted_slippage_bps": weighted_slippage,
        "worst_slippage_bps": out["slippage_bps"].max(),
        "total_notional": total_notional,
    }
    return out, summary


# -------------------------------
# LOAD DATA
# -------------------------------
if not symbols:
    st.warning("Please select at least one symbol.")
    st.stop()

anchor_prices = get_live_anchor_prices(tuple(symbols)) if use_live_anchors else {}

ticks = generate_synthetic_ticks(symbols, num_ticks, seed, base_date, anchor_prices)
intraday, historical = build_storage_layers(ticks)

st.markdown("### 💱 Live Market Anchors")
if use_live_anchors:
    if anchor_prices:
        anchor_df = pd.DataFrame.from_dict(anchor_prices, orient="index", columns=["Live Anchor Price"])
        anchor_df.index.name = "Symbol"
        st.dataframe(anchor_df.round(5), use_container_width=True)
        st.markdown(
            """
These are the **live market reference prices** used as the starting level for the synthetic tick simulation.

The app does **not** stream live tick-by-tick data. Instead, it pulls a recent market level and then builds a realistic synthetic intraday path around that level.
This makes the simulation feel more realistic while still keeping the project lightweight.
            """
        )
    else:
        st.warning("Live anchors could not be loaded, so the app is using default static starting prices.")
else:
    st.info("Live market anchors are turned off. The simulation is using default static starting prices.")

st.markdown("### 🗃️ Data Overview")
st.markdown(
    """
This section gives a high-level summary of the dataset that has just been generated.

If live anchors are enabled, the synthetic paths begin from recent market levels fetched from live sources and then evolve as a simulated intraday series.

The overall design now mirrors a more realistic trading workflow:
- **market data ingestion** through live anchor prices and synthetic tick generation
- **tick architecture** through intraday and historical data layers
- **post-trade analytics / TCA** through simulated execution data
- **liquidity and order behavior analysis** through spread, depth, and imbalance metrics
    """
)
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
st.markdown(
    """
This is the **raw tick-level dataset**.

Each row represents a single market event for a symbol at a particular timestamp. The most important fields are:
- **bid**: highest current buying price
- **ask**: lowest current selling price
- **trade_price**: simulated executed trade price
- **trade_size**: simulated trade size
- **mid**: midpoint between bid and ask
- **spread**: difference between ask and bid

In a real trading environment, this is the type of data that would often sit in an intraday kdb+/q table.
    """
)
st.dataframe(intraday.head(50), use_container_width=True)

st.markdown("### 📚 Historical Summary Store")
st.markdown(
    """
This table is a **compressed historical view** of the same market data.

Instead of storing every tick, it aggregates each symbol into daily summary metrics such as:
- opening price
- high and low price
- closing price
- total volume
- average spread
- number of ticks

This helps show the difference between **full-resolution intraday data** and **historical summary data**.
    """
)
st.dataframe(historical, use_container_width=True)

# -------------------------------
# SYMBOL SELECTION
# -------------------------------
st.markdown("### 🎯 Symbol Analytics")
st.markdown(
    """
Choose a single symbol to explore in more detail.

Once selected, the app calculates a focused set of analytics for that instrument. This is similar to how a trader, quant, or market-data analyst would drill into one product at a time.
    """
)
selected_symbol = st.selectbox("Choose symbol", sorted(intraday["symbol"].unique()))
selected = intraday[intraday["symbol"] == selected_symbol].copy().sort_values("timestamp")
selected["return_bps"] = selected["trade_price"].pct_change() * 10000
selected["cum_volume"] = selected["trade_size"].cumsum()
selected["vwap_running"] = (
    (selected["trade_price"] * selected["trade_size"]).cumsum()
    / selected["trade_size"].cumsum()
)

selected_tca, tca_summary = calc_tca_metrics(selected)

vwap_value = calc_vwap(selected)
avg_spread = selected["spread"].mean()
realized_vol_bps = selected["return_bps"].std()
avg_liquidity = selected["liquidity_score"].mean()
avg_imbalance = selected["order_imbalance"].mean()

st.markdown(
    """
The summary metrics below provide a quick interpretation of market quality and trading activity:

- **VWAP**: the average traded price weighted by trade size. This is often used as an execution benchmark.
- **Average Spread**: the average gap between bid and ask. Smaller spreads usually indicate better liquidity.
- **Realized Vol (bps)**: how much the trade price moved from tick to tick, measured in basis points.
- **Liquidity Score**: a simple proxy for how much quoted size is available relative to spread.
- **Order Imbalance**: whether displayed bid size is stronger or weaker than displayed ask size.
    """
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("VWAP", f"{vwap_value:,.4f}")
m2.metric("Average Spread", f"{avg_spread:,.5f}")
m3.metric("Realized Vol (bps)", f"{realized_vol_bps:,.2f}")
m4.metric("Liquidity Score", f"{avg_liquidity:,.0f}")
m5.metric("Order Imbalance", f"{avg_imbalance:,.2f}")

# -------------------------------
# PRICE CHART
# -------------------------------
st.markdown("### 📉 Trade Price")
st.markdown(
    """
This chart shows how the simulated trade price evolves over time.

It helps the user see whether the symbol is trending, stable, or volatile during the session.
    """
)
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
st.markdown(
    """
This chart tracks the **bid-ask spread** over time.

The spread is one of the most important measures of market liquidity. A wider spread often suggests less efficient trading conditions or lower liquidity.
    """
)
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
st.markdown(
    """
This chart compares the live trade price with the **running VWAP**.

This helps the user see whether trades are occurring above or below the average price paid through the session so far.
In execution analysis, this type of comparison can help assess trade quality.
    """
)
fig3, ax3 = plt.subplots(figsize=(10, 4))
ax3.plot(selected["timestamp"], selected["trade_price"], label="Trade Price")
ax3.plot(selected["timestamp"], selected["vwap_running"], label="Running VWAP")
ax3.set_xlabel("Time")
ax3.set_ylabel("Price")
ax3.set_title(f"{selected_symbol} Price vs VWAP")
ax3.legend()
st.pyplot(fig3)

# -------------------------------
# LIQUIDITY AND ORDER BEHAVIOR
# -------------------------------
st.markdown("### 🏦 Liquidity and Order Behaviour")
st.markdown(
    """
This section looks beyond price and examines **market quality**.

- **Liquidity Score** is a simple proxy that combines displayed size and spread
- **Order Imbalance** shows whether buying interest or selling interest appears stronger in the quoted book

In a real trading environment, these measures help assess how easy it may be to execute without moving the market.
    """
)

fig_liq, ax_liq = plt.subplots(figsize=(10, 4))
ax_liq.plot(selected["timestamp"], selected["liquidity_score"])
ax_liq.set_xlabel("Time")
ax_liq.set_ylabel("Liquidity Score")
ax_liq.set_title(f"{selected_symbol} Liquidity Score")
st.pyplot(fig_liq)

fig_imb, ax_imb = plt.subplots(figsize=(10, 4))
ax_imb.plot(selected["timestamp"], selected["order_imbalance"])
ax_imb.set_xlabel("Time")
ax_imb.set_ylabel("Order Imbalance")
ax_imb.set_title(f"{selected_symbol} Order Imbalance")
st.pyplot(fig_imb)

# -------------------------------
# POST-TRADE ANALYTICS / TCA
# -------------------------------
st.markdown("### 🧾 Post-Trade Analytics / TCA")
st.markdown(
    """
This section simulates **post-trade execution analysis**.

For each tick, the app creates a synthetic trade side and execution price, then compares that execution against the **arrival mid-price**.
This gives a simple form of **transaction cost analysis (TCA)**.

Key ideas:
- **Slippage** measures how far execution moved away from the reference price
- **Weighted Slippage** adjusts this by trade notional
- Higher positive slippage generally means worse execution quality
    """
)

t1, t2, t3, t4 = st.columns(4)

t1.metric("Avg Slippage (bps)", f"{tca_summary['avg_slippage_bps']:,.2f}")
t2.metric("Weighted Slippage (bps)", f"{tca_summary['weighted_slippage_bps']:,.2f}")
t3.metric("Worst Slippage (bps)", f"{tca_summary['worst_slippage_bps']:,.2f}")
t4.metric("Total Notional", f"{tca_summary['total_notional']:,.0f}")
    """
This section looks for **unusually large bursts of trading activity**.

The app compares recent trading volume with the broader session average:
- **Burst rolling window** controls how many recent ticks are used
- **Burst threshold** controls how extreme activity must be before it is flagged

A burst may suggest elevated activity, news reaction, execution pressure, or a temporary change in liquidity.
    """
)
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

st.markdown(
    """
- **Burst Events** shows how many periods were flagged as unusually active
- **Max Burst Ratio** shows the highest observed ratio of short-term volume versus baseline volume
    """
)

if not burst_events.empty:
    st.dataframe(burst_events.head(20), use_container_width=True)
else:
    st.info("No burst events detected with current settings.")

# -------------------------------
# QUERY SECTION
# -------------------------------
st.markdown("### 🧮 Query Console (Predefined)")
st.markdown(
    """
This section acts like a simple query tool.

It lets the user inspect different slices of the selected symbol without writing code:
- **Last 10 ticks** for most recent events
- **Largest trades** to find unusually large executions
- **Widest spreads** to identify weaker liquidity moments
- **Summary stats** for a compact overview
    """
)
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
st.markdown(
    """
This final section explains the purpose of the platform in plain English.

It is intended to show not only the outputs, but also **why they matter in a trading or market-data context**.
    """
)
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
