import os
import requests
import yfinance as yf

# Force multi_level_index=False to ensure single-level column headers
df = yf.download("VOO", period="1mo", interval="1d", multi_level_index=False)

# Get the prior 20-trading-day low (excluding current active day)
previous_4_week_low = float(df["Close"].iloc[-21:-1].min())

# Fetch real-time price
ticker = yf.Ticker("VOO")
current_price = float(ticker.fast_info["last_price"])

print(f"Current Price: {current_price}")
print(f"4-Week Low: {previous_4_week_low}")

webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

message = {
    "content": f"🚨 **VOO 4-Week Low Alert!** 🚨\nCurrent Price: **${current_price:.2f}** (Previous 4-Week Low: ${previous_4_week_low:.2f})"
}

# Force trigger for testing
if True:
    if webhook_url:
        res = requests.post(webhook_url, json=message)
        print(f"Discord Response Status: {res.status_code}")
    else:
        print("Webhook URL missing.")
