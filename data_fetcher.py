"""
Fetches real stock data from Yahoo Finance and caches it.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import NIFTY_50, NIFTY_NEXT_50, ETFS, SECTORS

# In-memory cache
_cache = {}
_cache_time = {}
CACHE_DURATION = timedelta(hours=1)


def _is_cached(key):
    return key in _cache and datetime.now() - _cache_time.get(key, datetime.min) < CACHE_DURATION


def fetch_stock_data(ticker):
    """Fetch 1 year of data + info for a single stock."""
    if _is_cached(ticker):
        return _cache[ticker]

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        info = stock.info

        if hist.empty:
            return None

        current_price = hist["Close"].iloc[-1]
        price_1y_ago = hist["Close"].iloc[0]
        price_1m_ago = hist["Close"].iloc[-22] if len(hist) > 22 else price_1y_ago
        price_6m_ago = hist["Close"].iloc[-126] if len(hist) > 126 else price_1y_ago

        # Calculate metrics
        returns_1y = ((current_price - price_1y_ago) / price_1y_ago) * 100
        returns_1m = ((current_price - price_1m_ago) / price_1m_ago) * 100
        returns_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100

        # Volatility (annualized std of daily returns)
        daily_returns = hist["Close"].pct_change().dropna()
        volatility = daily_returns.std() * (252 ** 0.5) * 100

        # Max drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = ((cumulative - running_max) / running_max) * 100
        max_drawdown = drawdown.min()

        data = {
            "ticker": ticker,
            "name": NIFTY_50.get(ticker) or NIFTY_NEXT_50.get(ticker) or info.get("shortName", ticker),
            "sector": SECTORS.get(ticker, "Other"),
            "current_price": round(current_price, 2),
            "returns_1m": round(returns_1m, 2),
            "returns_6m": round(returns_6m, 2),
            "returns_1y": round(returns_1y, 2),
            "volatility": round(volatility, 2),
            "max_drawdown": round(max_drawdown, 2),
            "pe_ratio": info.get("trailingPE"),
            "market_cap": info.get("marketCap"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
            "history": hist,
        }

        _cache[ticker] = data
        _cache_time[ticker] = datetime.now()
        return data

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def fetch_multiple_stocks(tickers, progress_callback=None):
    """Fetch data for multiple stocks."""
    results = []
    total = len(tickers)
    for i, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(i + 1, total, ticker)
        data = fetch_stock_data(ticker)
        if data:
            results.append(data)
    return results


def score_stock(data):
    """
    Score a stock 0-100 based on multiple factors.
    Higher = more attractive.
    """
    score = 50  # base score

    # 1-year returns (max 25 pts)
    r = data["returns_1y"]
    if r > 30:
        score += 25
    elif r > 15:
        score += 20
    elif r > 5:
        score += 10
    elif r > 0:
        score += 5
    else:
        score -= 10

    # Volatility (lower is better for stability, max 15 pts)
    v = data["volatility"]
    if v < 20:
        score += 15
    elif v < 30:
        score += 10
    elif v < 40:
        score += 5
    else:
        score -= 5

    # PE Ratio (reasonable valuation, max 15 pts)
    pe = data.get("pe_ratio")
    if pe is not None:
        if 10 < pe < 25:
            score += 15
        elif 25 <= pe < 40:
            score += 8
        elif pe >= 40:
            score -= 5
        elif pe < 0:
            score -= 10

    # Max drawdown (less negative = better, max 10 pts)
    dd = data["max_drawdown"]
    if dd > -10:
        score += 10
    elif dd > -20:
        score += 5
    else:
        score -= 5

    # 1-month momentum (max 10 pts)
    m = data["returns_1m"]
    if m > 5:
        score += 10
    elif m > 0:
        score += 5
    elif m < -5:
        score -= 5

    # Dividend yield bonus (max 5 pts)
    dy = data.get("dividend_yield")
    if dy and dy > 0.02:
        score += 5
    elif dy and dy > 0.01:
        score += 3

    return max(0, min(100, score))


def get_scored_stocks(category="nifty50"):
    """Fetch and score all stocks in a category."""
    tickers = NIFTY_50 if category == "nifty50" else NIFTY_NEXT_50

    print(f"\nFetching {category} data...")
    stocks = fetch_multiple_stocks(
        list(tickers.keys()),
        progress_callback=lambda i, t, tk: print(f"  [{i}/{t}] {tk}")
    )

    for stock in stocks:
        stock["score"] = score_stock(stock)

    # Sort by score descending
    stocks.sort(key=lambda x: x["score"], reverse=True)
    return stocks


def get_etf_data():
    """Fetch data for all tracked ETFs."""
    results = []
    for ticker, info in ETFS.items():
        data = fetch_stock_data(ticker)
        if data:
            data.update(info)
            results.append(data)
    return results


def _sip_future_value(monthly_amount, months, monthly_rate):
    """Core SIP future value calculation."""
    if monthly_rate == 0:
        return monthly_amount * months
    return monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)


def calculate_sip(monthly_amount, years, expected_return_pct, include_yearly=False):
    """Calculate SIP returns with optional year-by-year breakdown."""
    monthly_rate = expected_return_pct / 100 / 12
    months = years * 12
    total_invested = monthly_amount * months
    future_value = _sip_future_value(monthly_amount, months, monthly_rate)
    returns = future_value - total_invested

    result = {
        "monthly_amount": monthly_amount,
        "years": years,
        "expected_return": expected_return_pct,
        "total_invested": round(total_invested, 2),
        "future_value": round(future_value, 2),
        "total_returns": round(returns, 2),
        "wealth_multiplier": round(future_value / total_invested, 2),
    }

    if include_yearly:
        yearly = []
        for y in range(1, years + 1):
            m = y * 12
            inv = monthly_amount * m
            fv = _sip_future_value(monthly_amount, m, monthly_rate)
            gain_pct = round((fv - inv) / inv * 100) if inv else 0
            yearly.append({
                "year": y,
                "total_invested": round(inv, 2),
                "future_value": round(fv, 2),
                "gain_pct": gain_pct,
            })
        result["yearly"] = yearly

    return result
