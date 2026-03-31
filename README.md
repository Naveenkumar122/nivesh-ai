# NiveshAI

A data-driven Indian stock and ETF investment advisor built with Flask. Fetches live market data from Yahoo Finance, scores stocks on multiple factors, and helps users build a personalized investment strategy.

## Features

- **Risk Profiler** — 4-question quiz that recommends a Conservative, Moderate, or Aggressive allocation
- **Stock Screener** — NIFTY 50 and NIFTY NEXT 50 stocks scored 0-100 based on returns, volatility, PE ratio, momentum, and dividends
- **ETF Guide** — Live data and comparison for NIFTYBEES, JUNIORBEES, BANKBEES, and GOLDBEES
- **SIP Calculator** — Project future returns with year-by-year breakdown and cross-product comparison
- **User Accounts** — Register/login to save your stock picks
- **Holdings Dashboard** — Track your selected stocks with live prices, returns, PE ratio, and 52-week range

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy (SQLite), Flask-Login
- **Data:** Yahoo Finance via yfinance
- **Frontend:** Vanilla HTML/CSS/JS (dark theme, no frameworks)
- **Auth:** Werkzeug password hashing, session-based login

## Setup

```bash
# Clone and install
cd nivesh-ai
pip install -r requirements.txt

# Run
python app.py
```

The app starts at `http://localhost:5000`. The SQLite database is created automatically on first run.

## Pages

| Route | Description |
|-------|-------------|
| `/` | Home page with risk profiler quiz |
| `/register` | Create a new account |
| `/login` | Sign in |
| `/dashboard` | Your saved holdings with live data |
| `/stocks/nifty50` | NIFTY 50 stock screener |
| `/stocks/niftynext50` | NIFTY NEXT 50 stock screener |
| `/etf-guide` | ETF education and live data |
| `/sip-calculator` | SIP returns calculator |

## How Scoring Works

Each stock is scored 0-100 based on:

- **1Y Returns** (25 pts) — higher is better
- **Volatility** (15 pts) — lower is better
- **PE Ratio** (15 pts) — 10-25 range scores highest
- **Max Drawdown** (10 pts) — smaller drawdowns score higher
- **1M Momentum** (10 pts) — positive short-term trend
- **Dividend Yield** (5 pts) — bonus for yield > 1%

## Disclaimer

This is for educational purposes only. Not financial advice. Always consult a SEBI-registered financial advisor before making investment decisions.
