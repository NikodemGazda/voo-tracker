import os
import sys

print("[1/9] Starting script execution...", flush=True)

try:
    print("[2/9] Importing requests...", flush=True)
    import requests
    
    print("[3/9] Importing yfinance...", flush=True)
    import yfinance as yf

    print("[4/9] Fetching VOO daily historical data from yfinance...", flush=True)
    df = yf.download("VOO", period="1mo", interval="1d", multi_level_index=False)
    print(f"      DataFrame successfully fetched. Shape: {df.shape}", flush=True)

    print("[5/9] Calculating previous 20-trading-day low...", flush=True)
    previous_4_week_low = float(df["Close"].iloc[-21:-1].min())
    print(f"      4-Week Low calculated: {previous_4_week_low:.2f}", flush=True)

    print("[6/9] Extracting latest close price...", flush=True)
    current_price = float(df["Close"].iloc[-1])
    print(f"      Current Price extracted: {current_price:.2f}", flush=True)

    print("[7/9] Fetching DISCORD_WEBHOOK_URL from environment...", flush=True)
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if webhook_url:
        print("      Webhook URL found in environment.", flush=True)
    else:
        print("      WARNING: Webhook URL is missing or empty!", flush=True)

    print("[8/9] Building payload message...", flush=True)
    message = {
        "content": f"🚨 **VOO 4-Week Low Alert!** 🚨\nCurrent Price: **${current_price:.2f}** (Previous 4-Week Low: ${previous_4_week_low:.2f})"
    }

    print("[9/9] Checking trigger condition...", flush=True)
    # Temporarily set to True for testing
    if True:
        print("      Condition met. Sending POST request to Discord...", flush=True)
        res = requests.post(webhook_url, json=message)
        print(f"      Discord HTTP Response Status Code: {res.status_code}", flush=True)
        print(f"      Discord Response Text: {res.text}", flush=True)
    else:
        print("      Condition not met. Skipping alert.", flush=True)

    print("Script finished successfully!", flush=True)

except Exception as e:
    print(f"\n❌ SCRIPT FAILED WITH ERROR:\n{e}", flush=True)
    sys.exit(1)
