# Tick Data Mini-Platform

A Streamlit-based trading analytics project for simulating, storing, and analysing high-frequency tick data.

Link to site https://tick-data-mini-platform-sa.streamlit.app/

**Created by Steven Amet**

## Overview

This project is designed as a **mini trading-data platform** that mirrors the type of workflow often seen in market-data and trading analytics environments.

It combines:

- **live market anchors** from external sources
- **synthetic intraday tick generation**
- **intraday and historical data layers**
- **market microstructure analytics**
- **post-trade execution analysis / TCA**

The app does **not** stream a real exchange feed. Instead, it pulls recent live market prices and uses them as the starting point for a simulated intraday tick path. This keeps the project realistic, lightweight, and suitable for GitHub and interviews.

## Why This Project Matters

A good kdb+/q-style project is valuable when it mirrors real trading use cases. This project is built around those ideas:

- ingesting **real-time and historical market data**
- building a **tick architecture**
- doing **post-trade analytics / TCA**
- analysing **price, spread, liquidity, and order behaviour**

This makes it a practical portfolio project for roles in:

- trading technology
- market-data engineering
- execution analytics
- quantitative support
- electronic trading infrastructure

## Features

### 1. Live Market Anchors
The app can fetch recent live market levels and use them as the base for the simulated tick series.

Examples:
- FX rates via live FX sources
- equities and futures via Yahoo Finance

### 2. Synthetic Tick Generation
The app generates realistic tick-style data for instruments such as:

- EURUSD
- GBPUSD
- USDJPY
- AAPL
- MSFT
- ES futures

Each tick includes quote and trade-style fields such as bid, ask, trade price, trade size, spread, and more.

### 3. Tick Architecture
The platform separates the data into two layers:

#### Intraday Layer
Stores full tick-by-tick market data for session-level analysis.

#### Historical Layer
Stores aggregated daily summaries including:

- open
- high
- low
- close
- total volume
- average spread
- average liquidity score
- average order imbalance
- tick count

This mirrors the type of separation often used in kdb+/q environments.

### 4. Market Microstructure Analytics
The app includes:

- **Trade price analysis**
- **Bid-ask spread analysis**
- **VWAP tracking**
- **Tick-to-tick return analysis**
- **Volume burst detection**
- **Liquidity score**
- **Order imbalance**

These help the user understand market quality, trading conditions, and instrument behaviour.

### 5. Post-Trade Analytics / TCA
The app also simulates a simple post-trade execution framework.

For each tick, it generates:
- a synthetic trade side
- an arrival mid-price
- an execution price
- slippage in basis points

This supports basic **Transaction Cost Analysis (TCA)**, including:

- average slippage
- weighted slippage
- worst slippage
- total notional traded

## Data Model

Each tick record may include:

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
- `trade_side`
- `arrival_mid`
- `execution_price`
- `liquidity_score`
- `order_imbalance`

## Dashboard Sections

The app is structured to be intuitive for the user and explain what each section is doing.

### App Introduction
Explains:
- what a tick is
- what the app simulates
- how synthetic and live data are combined

### Data Settings
Lets the user choose:
- symbols
- tick count
- random seed
- trading date
- whether to use live market anchors

### Live Market Anchors
Shows the latest market reference prices used to initialise the simulation.

### Data Overview
Displays:
- total ticks
- number of symbols
- trading date

### Intraday Tick Store
Shows the raw tick-by-tick market data.

### Historical Summary Store
Shows aggregated daily summaries.

### Symbol Analytics
Lets the user drill into one instrument.

### Core Metrics
Shows:
- VWAP
- average spread
- realized volatility
- liquidity score
- order imbalance

### Charts
Includes:
- trade price over time
- bid-ask spread over time
- trade price vs running VWAP
- liquidity score
- order imbalance
- volume burst signal
- execution slippage

### Query Console
Provides simple predefined views such as:
- last 10 ticks
- largest trades
- widest spreads
- summary statistics

### Executive Summary
Summarises the purpose of the platform and how it relates to trading and kdb+/q-style analytics.

## Tech Stack

- **Python**
- **Streamlit**
- **Pandas**
- **NumPy**
- **Matplotlib**
- **Requests**
- **yfinance**

## Project Structure

```bash
.
├── app.py
├── README.md
└── requirements.txt