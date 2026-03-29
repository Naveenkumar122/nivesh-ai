"""
NiveshAI — Indian Stock & ETF Investment Advisor
"""
from flask import Flask, render_template, request, jsonify
from data_fetcher import get_scored_stocks, get_etf_data, calculate_sip, fetch_stock_data
from config import ALLOCATION, ETFS, NIFTY_50, NIFTY_NEXT_50, SECTORS
import json

app = Flask(__name__)

# Cache for scored stocks (fetched on demand)
stock_cache = {}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/risk-profile", methods=["POST"])
def risk_profile():
    """Calculate risk profile from quiz answers."""
    answers = request.json
    score = 0

    # Q1: Age
    age = int(answers.get("age", 30))
    if age < 25:
        score += 3
    elif age < 35:
        score += 2
    elif age < 50:
        score += 1

    # Q2: Investment horizon
    horizon = answers.get("horizon", "medium")
    if horizon == "long":
        score += 3
    elif horizon == "medium":
        score += 2
    else:
        score += 1

    # Q3: Risk tolerance
    risk = answers.get("risk", "moderate")
    if risk == "high":
        score += 3
    elif risk == "moderate":
        score += 2
    else:
        score += 1

    # Q4: If market drops 20%, what do you do?
    reaction = answers.get("reaction", "hold")
    if reaction == "buy_more":
        score += 3
    elif reaction == "hold":
        score += 2
    else:
        score += 0

    # Determine profile
    if score >= 10:
        profile = "aggressive"
    elif score >= 6:
        profile = "moderate"
    else:
        profile = "conservative"

    return jsonify({
        "profile": profile,
        "score": score,
        **ALLOCATION[profile]
    })


@app.route("/etf-guide")
def etf_guide():
    return render_template("etf_guide.html", etfs=ETFS)


@app.route("/api/etf-data")
def api_etf_data():
    """Fetch live ETF data."""
    data = get_etf_data()
    # Remove non-serializable history
    for d in data:
        d.pop("history", None)
    return jsonify(data)


@app.route("/stocks/<category>")
def stocks(category):
    if category not in ("nifty50", "niftynext50"):
        category = "nifty50"
    title = "NIFTY 50 — Large Cap" if category == "nifty50" else "NIFTY NEXT 50 — Mid Cap"
    return render_template("stocks.html", category=category, title=title)


@app.route("/api/stocks/<category>")
def api_stocks(category):
    """Fetch and score stocks. Cached in memory."""
    if category not in stock_cache:
        stock_cache[category] = get_scored_stocks(category)

    stocks = stock_cache[category]
    # Remove non-serializable history
    result = []
    for s in stocks:
        d = {k: v for k, v in s.items() if k != "history"}
        result.append(d)
    return jsonify(result)


@app.route("/api/stock/<ticker>")
def api_stock_detail(ticker):
    """Fetch detailed data for a single stock."""
    data = fetch_stock_data(ticker)
    if not data:
        return jsonify({"error": "Stock not found"}), 404
    data.pop("history", None)
    return jsonify(data)


@app.route("/api/sip-calculate", methods=["POST"])
def api_sip_calculate():
    """Calculate SIP returns with optional yearly breakdown."""
    params = request.json
    result = calculate_sip(
        monthly_amount=float(params["amount"]),
        years=int(params["years"]),
        expected_return_pct=float(params["return_pct"]),
        include_yearly=params.get("include_yearly", False),
    )
    return jsonify(result)


@app.route("/api/sip-comparison")
def api_sip_comparison():
    """Pre-computed SIP comparison table for fixed Rs.5000/month."""
    types = [
        {"name": "Fixed Deposit", "rate": 7, "css_class": ""},
        {"name": "Gold ETF", "rate": 9, "css_class": "orange"},
        {"name": "Nifty 50 ETF", "rate": 12, "css_class": "green"},
        {"name": "Nifty Next 50 ETF", "rate": 14, "css_class": "green"},
        {"name": "Mid Cap Fund", "rate": 16, "css_class": "green"},
    ]
    periods = [5, 10, 15, 20, 25]
    rows = []
    for t in types:
        values = {}
        for yr in periods:
            r = calculate_sip(5000, yr, t["rate"])
            values[str(yr)] = r["future_value"]
        rows.append({"name": t["name"], "rate": t["rate"], "css_class": t["css_class"], "values": values})

    invested = {str(yr): 5000 * yr * 12 for yr in periods}
    return jsonify({"rows": rows, "invested": invested, "periods": periods})


@app.route("/api/refresh/<category>")
def api_refresh(category):
    """Force refresh stock data."""
    if category in stock_cache:
        del stock_cache[category]
    return jsonify({"status": "cache cleared", "category": category})


@app.route("/sip-calculator")
def sip_calculator():
    return render_template("sip_calculator.html")


if __name__ == "__main__":
    print("\n NiveshAI running at http://localhost:5000")
    print("  /              — Home + Risk Profiler")
    print("  /etf-guide     — ETF Education")
    print("  /stocks/nifty50 — NIFTY 50 Analysis")
    print("  /stocks/niftynext50 — NIFTY NEXT 50 Analysis")
    print("  /sip-calculator — SIP Calculator\n")
    app.run(debug=True, port=5000)
