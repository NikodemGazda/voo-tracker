import datetime
import os
import requests
import numpy as np
import yfinance as yf

# --- Configuration & Setup ---
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"
STATE_FILE = "last_trigger.txt"
SYMBOL = "VOO"

# Fetch 1 year of daily historical data
ticker = yf.Ticker(SYMBOL)
df = ticker.history(period="1y")

# Extract price series
prices_1y = df["Close"].values
prices_6m = prices_1y[-126:]  # ~6 months
prices_3m = prices_1y[-63:]   # ~3 months
prices_1m = prices_1y[-21:]   # ~1 month (21 trading days)

current_price = prices_1y[-1]

# --- High / Low Calculations ---
high_1m, low_1m = float(np.max(prices_1m)), float(np.min(prices_1m))
high_3m, low_3m = float(np.max(prices_3m)), float(np.min(prices_3m))
high_6m, low_6m = float(np.max(prices_6m)), float(np.min(prices_6m))
high_1y, low_1y = float(np.max(prices_1y)), float(np.min(prices_1y))

# --- Percentile Calculations ---
p5_1m = np.percentile(prices_1m, 5)

# Calculate where current price falls on 0% (month low) to 100% (month high) scale
if high_1m == low_1m:
    price_percentile_1m = 100.0
else:
    price_percentile_1m = ((current_price - low_1m) / (high_1m - low_1m)) * 100

# --- Cooldown Check (Prevents triggering twice in 2 days) ---
def can_trigger():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            last_date_str = f.read().strip()
            if last_date_str:
                last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d").date()
                if (datetime.date.today() - last_date).days < 2:
                    return False
    return True

# --- Trigger Condition & Execution ---
# Note: Retained 'True' override for testing as requested
if True: # (current_price <= p5_1m) and can_trigger():
    message = (
        f"**{SYMBOL} Price Alert**\n"
        f"• **Current Price:** ${current_price:.2f}\n"
        f"• **1-Month Relative Position:** {price_percentile_1m:.1f}%\n\n"
        f"**Range Metrics:**\n"
        f"• **1-Month:** Low: ${low_1m:.2f} | High: ${high_1m:.2f}\n"
        f"• **3-Month:** Low: ${low_3m:.2f} | High: ${high_3m:.2f}\n"
        f"• **6-Month:** Low: ${low_6m:.2f} | High: ${high_6m:.2f}\n"
        f"• **1-Year:** Low: ${low_1y:.2f} | High: ${high_1y:.2f}"
    )

    response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    
    if response.status_code in [200, 204]:
        with open(STATE_FILE, "w") as f:
            f.write(str(datetime.date.today()))
        print("Alert sent successfully.")
