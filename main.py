#!/usr/bin/env python3
"""
Gold Rates Video Generator

Usage:
  python main.py                         # fetch live rates, generate video
  python main.py --output /path/out.mp4  # custom output path
  python main.py --dry-run               # fetch rates and print without generating
  python main.py --mock                  # skip API, use sample rates (dev/test)
"""
import argparse, os, subprocess, sys
from datetime import datetime

import config
from fetcher import fetch_gold_rates
from generator import generate_video
from rates_store import update_and_get_previous, compute_changes

SAMPLE_RATES = {
    '24K': 644.25,
    '22K': 604.00,
    '21K': 483.25,
    '18K': 414.25,
    '14K': 323.00,
    'timestamp': datetime.now().astimezone().isoformat(),
}

def main():
    parser = argparse.ArgumentParser(description='Generate daily gold rates video')
    parser.add_argument('--output',   '-o', help='Output MP4 path')
    parser.add_argument('--dry-run',  action='store_true', help='Print rates only, no video')
    parser.add_argument('--mock',     action='store_true', help='Use sample rates (no API call)')
    parser.add_argument('--bg-index', type=int, default=-1,
                        help='Force a specific background video (0-based index). Default: rotate by day.')
    args = parser.parse_args()


    # ── Fetch rates ───────────────────────────────────────────────────────────
    if args.mock:
        rates = SAMPLE_RATES
        print("Using mock rates (--mock flag)")
    else:
        if not config.API_KEY:
            print("ERROR: GOLD_API_KEY not set in .env")
            sys.exit(1)

        # Auto-login if no token stored yet
        if not config.API_TOKEN:
            print("No Bearer token found — running auth.py …")
            auth_script = os.path.join(os.path.dirname(__file__), 'auth.py')
            subprocess.run([sys.executable, auth_script], check=True)
            # Reload config after auth writes the token
            from importlib import reload
            reload(config)

        print(f"Fetching live gold rates …")
        rates = fetch_gold_rates(
            api_url  = config.API_URL,
            api_key  = config.API_KEY,
            token    = config.API_TOKEN,
            email    = config.API_EMAIL,
            password = config.API_PASSWORD,
        )

    # ── Persist rates and compute changes vs previous trading day ────────────
    # --mock runs never touch last_rates.json so test runs can't corrupt real data
    if args.mock:
        prev_rates = None
        print("--mock: skipping rate store (change indicators hidden)")
    else:
        prev_rates = update_and_get_previous(rates, rates.get('timestamp', ''))
    changes = compute_changes(rates, prev_rates)

    # ── Print rates ───────────────────────────────────────────────────────────
    print("\nGold rates (AED/gram):")
    for karat in ['24K', '22K', '21K', '18K', '14K']:
        chg = changes.get(karat)
        chg_str = f"  ({'+' if chg >= 0 else ''}{chg:,.2f})" if chg is not None else "  (no prev)"
        print(f"  {karat} Gold : AED {rates[karat]:,.2f}{chg_str}")
    print(f"  Timestamp  : {rates.get('timestamp', 'n/a')}")

    if args.dry_run:
        print("\n--dry-run: skipping video generation.")
        return

    # ── Generate video ────────────────────────────────────────────────────────
    if args.output:
        output_path = args.output
    else:
        date_tag = datetime.now().strftime('%Y-%m-%d')
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(config.OUTPUT_DIR, f'gold_rates_{date_tag}.mp4')

    print(f"\nGenerating video → {output_path}")
    generate_video(rates, output_path, bg_index=args.bg_index, changes=changes)
    print(f"\nDone: {output_path}")



if __name__ == '__main__':
    main()
