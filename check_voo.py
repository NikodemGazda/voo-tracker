import datetime
import os
import requests
import numpy as np
import yfinance as yf

# --- Configuration & Setup ---
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
STATE_FILE = "last_trigger.txt"
SYMBOL = "VOO"

# Trigger window: 10 trading days (~2 weeks) at the 10th percentile.
# NOTE: on a 10-day window, p10 interpolates to position 0.9 between the
# lowest and second-lowest close, so this condition is exactly "today is a
# new 10-day low". Every percentile <= 10 collapses to the same rule at this
# window length -- p5, p3 and p1 would all behave identically. The percentile
# form is kept so WINDOW_DAYS/PERCENTILE stay independently tunable.
WINDOW_DAYS = 10
PERCENTILE = 10
COOLDOWN_DAYS = 2

if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable is not set.")

# Fetch 1 year of daily historical data.
# auto_adjust=True is the current default but has changed across yfinance
# versions, so it is set explicitly: "Close" is then the dividend/split
# adjusted series.
ticker = yf.Ticker(SYMBOL)
df = ticker.history(period="1y", auto_adjust=True)

if df.empty:
    raise SystemExit(f"No data returned for {SYMBOL}.")

# Extract price series
prices_1y = df["Close"].values
prices_6m = prices_1y[-126:]  # ~6 months
prices_3m = prices_1y[-63:]   # ~3 months
prices_1m = prices_1y[-21:]   # ~1 month (21 trading days)
prices_2w = prices_1y[-WINDOW_DAYS:]  # trigger window (~2 weeks)

if len(prices_1y) < WINDOW_DAYS:
    raise SystemExit(
        f"Only {len(prices_1y)} closes returned; need {WINDOW_DAYS}."
    )

current_price = prices_1y[-1]

# The date of the close being evaluated. Used for the cooldown state instead
# of today's date so that a run on a non-trading day cannot re-alert on a
# stale, unchanged price. On trading days these are the same date, so the
# cooldown behaves exactly as before: alert Mon -> Tue blocked, Wed open;
# alert Fri -> Mon is 3 days out, so Mon is open.
close_date = df.index[-1].date()

# --- High / Low Calculations ---
high_2w, low_2w = float(np.max(prices_2w)), float(np.min(prices_2w))
high_1m, low_1m = float(np.max(prices_1m)), float(np.min(prices_1m))
high_3m, low_3m = float(np.max(prices_3m)), float(np.min(prices_3m))
high_6m, low_6m = float(np.max(prices_6m)), float(np.min(prices_6m))
high_1y, low_1y = float(np.max(prices_1y)), float(np.min(prices_1y))

# --- Percentile Calculations ---
threshold = np.percentile(prices_2w, PERCENTILE)


def relative_position(price, low, high):
    """Where price sits on a 0% (low) to 100% (high) scale."""
    if high == low:
        return 100.0
    return ((price - low) / (high - low)) * 100


price_percentile_2w = relative_position(current_price, low_2w, high_2w)
price_percentile_1m = relative_position(current_price, low_1m, high_1m)


# --- Cooldown Check (at most one alert per COOLDOWN_DAYS calendar days) ---
def can_trigger():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            last_date_str = f.read().strip()
            if last_date_str:
                last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d").date()
                if (close_date - last_date).days < COOLDOWN_DAYS:
                    return False
    return True


# --- Trigger Condition & Execution ---
if (current_price <= threshold) and can_trigger():
    message = (
        f"**{SYMBOL} Price Alert** — new {WINDOW_DAYS}-day low\n"
        f"• **Current Price:** ${current_price:.2f}  ({close_date})\n"
        f"• **2-Week Relative Position:** {price_percentile_2w:.1f}%\n"
        f"• **1-Month Relative Position:** {price_percentile_1m:.1f}%\n\n"
        f"**Range Metrics:**\n"
        f"• **2-Week:** Low: ${low_2w:.2f} | High: ${high_2w:.2f}\n"
        f"• **1-Month:** Low: ${low_1m:.2f} | High: ${high_1m:.2f}\n"
        f"• **3-Month:** Low: ${low_3m:.2f} | High: ${high_3m:.2f}\n"
        f"• **6-Month:** Low: ${low_6m:.2f} | High: ${high_6m:.2f}\n"
        f"• **1-Year:** Low: ${low_1y:.2f} | High: ${high_1y:.2f}"
    )

    response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

    if response.status_code in [200, 204]:
        with open(STATE_FILE, "w") as f:
            f.write(str(close_date))
        print("Alert sent successfully.")
    else:
        print(f"Failed to send alert. HTTP Status: {response.status_code}, Response: {response.text}")
else:
    print("Conditions not met or cooldown active. No alert sent.")
