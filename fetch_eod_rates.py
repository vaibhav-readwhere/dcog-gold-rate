#!/usr/bin/env python3
"""
End-of-Day rate snapshot — runs at 6 PM UAE time via GitHub Actions cron.

Purpose: save today's official closing rates to last_rates.json so the
8 AM video generation the next morning can compute accurate change indicators.

Does NOT generate any video. Does NOT post anything.
"""
import subprocess, sys, os
from datetime import datetime

import config
from fetcher import fetch_gold_rates
from rates_store import update_and_get_previous

def main():
    if not config.API_KEY:
        print("ERROR: GOLD_API_KEY not set"); sys.exit(1)

    # Refresh token if needed
    if not config.API_TOKEN:
        auth_script = os.path.join(os.path.dirname(__file__), 'auth.py')
        subprocess.run([sys.executable, auth_script], check=True)
        from importlib import reload; reload(config)

    print(f"[EOD] Fetching rates at {datetime.now().strftime('%Y-%m-%d %H:%M')} UAE …")
    rates = fetch_gold_rates(
        api_url=config.API_URL, api_key=config.API_KEY,
        token=config.API_TOKEN, email=config.API_EMAIL, password=config.API_PASSWORD,
    )

    print("\nEnd-of-day rates (AED/gram):")
    for k in ['24K', '22K', '21K', '18K', '14K']:
        print(f"  {k}: AED {rates[k]:,.2f}")
    print(f"  Timestamp: {rates.get('timestamp', 'n/a')}")

    # Save to last_rates.json — tomorrow morning's video will use these
    update_and_get_previous(rates, rates.get('timestamp', ''))
    print("\n[EOD] Rates saved. Tomorrow's video will compare against these.")

if __name__ == '__main__':
    main()
