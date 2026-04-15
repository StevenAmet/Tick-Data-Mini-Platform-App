# Tick Data Mini-Platform

A Streamlit-based trading analytics project for simulating, storing, and analysing high-frequency tick data.

## Overview

This project is designed as a **mini market-data platform** that mirrors a simplified trading-data workflow:

- generate or ingest tick-style data
- store data in **intraday** and **historical** layers
- run **market microstructure analytics**
- visualise outputs in an interactive dashboard

It is intended as a first-stage project that can later be extended with:

- transaction cost analysis (TCA)
- order book reconstruction
- live market data ingestion
- a real **kdb+/q backend**

## Features

- Synthetic tick data generation across multiple symbols
- Intraday tick store for full tick-by-tick data
- Historical summary store for aggregated daily data
- Spread analysis
- VWAP tracking
- Return series analysis
- Volume burst detection
- Predefined query views for exploratory analysis

## Data Model

Each tick record includes:

- `timestamp`
- `symbol`
- `bid`
- `ask`
- `bid_size`
- `ask_size`
- `trade_price`
- `trade_size`
- `mid`
- `spread`

## Architecture

The app uses a simplified two-layer structure:

### Intraday Layer
Stores full tick-by-tick data for current-session analysis.

### Historical Layer
Stores aggregated daily summaries, including:

- open price
- high price
- low price
- close price
- total volume
- average spread
- tick count

This setup is designed to resemble the separation often used in trading and market-data environments.

## Analytics Included

### Spread Analysis
Tracks bid-ask spread behaviour over time.

### VWAP
Calculates running and full-period volume-weighted average price.

### Returns
Measures tick-to-tick returns in basis points.

### Volume Burst Detection
Flags unusual spikes in trading activity using a rolling-volume signal.

### Query Console
Supports quick inspection of:

- latest ticks
- largest trades
- widest spreads
- summary statistics

## Tech Stack

- **Python**
- **Streamlit**
- **Pandas**
- **NumPy**
- **Matplotlib**

## Project Structure

```bash
.
├── app.py
├── README.md
└── requirements.txt
```

## Installation

Clone the repository:

```bash
git clone https://github.com/your-username/tick-data-mini-platform.git
cd tick-data-mini-platform
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the App

```bash
streamlit run app.py
```

## Example Use Cases

This project is relevant to:

- trading analytics
- market-data engineering
- execution analysis
- market microstructure research
- interview project portfolios for trading-tech roles

## Roadmap

Planned next steps:

- [ ] Add CSV upload for external tick data
- [ ] Add transaction cost analysis module
- [ ] Add order-book or L2 simulation
- [ ] Add session-based filtering
- [ ] Add live data ingestion mock
- [ ] Replace simulated store with kdb+/q-compatible backend design

## Why This Project Matters

Trading firms and market-data teams often work with large time-series datasets containing prices, quotes, sizes, and timestamps. This project demonstrates a practical understanding of how that data can be structured, queried, and analysed in a lightweight but relevant format.

Rather than building a generic dashboard, the aim is to create a **trading-style mini-platform** that can evolve into a more realistic analytics system over time.

## Author

**Steven Amet**

---

This project is intended as a practical portfolio piece for trading, data, and quantitative technology roles.
