import os
import requests
import yfinance as yf

# Fetch last 30 calendar days to safely capture 20 trading days
df = yf.download("VOO", period="1m", interval="1d")

# Get closing prices
latest_close = float(df["Close"].iloc[-1])
previous_4_week_low = float(df["Close"].iloc[-21:-1].min())

# Check if latest price broke or matched the 4-week low
# if latest_close <= previous_4_week_low:
if True:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    message = {
        "content": f"🚨 **VOO 4-Week Low Alert!** 🚨\nLatest Close: **${latest_close:.2f}** (4-Week Prior Low: ${previous_4_week_low:.2f})"
    }
    if webhook_url:
        requests.post(webhook_url, json=message)
