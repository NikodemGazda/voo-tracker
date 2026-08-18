import os
import requests
import yfinance as yf

# Fetch last 1 month of daily data (20+ trading days)
df = yf.download("VOO", period="1mo", interval="1d")

# Extract the Close series cleanly
close_prices = df["Close"].squeeze()

# Get the prior 20-trading-day low (excluding current active candle)
previous_4_week_low = float(close_prices.iloc[-21:-1].min())

# Get real-time intraday price
ticker = yf.Ticker("VOO")
current_price = float(ticker.fast_info["last_price"])

# Trigger alert if current price hits or breaks the 4-week low
if current_price <= previous_4_week_low:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    message = {
        "content": f"🚨 **VOO 4-Week Low Alert!** 🚨\nCurrent Price: **${current_price:.2f}** (Previous 4-Week Low: ${previous_4_week_low:.2f})"
    }
    if webhook_url:
        requests.post(webhook_url, json=message)
