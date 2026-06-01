"""
Persist gold rates with date-aware comparison so change indicators are
always today vs the most-recent PREVIOUS trading day — never same-day vs
same-day, never a stale fake baseline.

File layout (last_rates.json):
{
  "current":  { "date": "2026-06-01", "rates": { "24K": 544.0, ... } },
  "previous": { "date": "2026-05-29", "rates": { "24K": 546.0, ... } }
}

Rules:
  • Run on a NEW day  → promote current → previous, save fresh current.
  • Run AGAIN same day → only refresh current rates; previous unchanged.
  • First run ever    → save current only; no previous; badges hidden.
"""

import json, os
from datetime import datetime
from typing import Optional

_STORE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_rates.json')
_KARATS = ['24K', '22K', '21K', '18K', '14K']


def _today(api_timestamp: str = '') -> str:
    """
    Return today's date string YYYY-MM-DD.
    Prefer the date from the API timestamp (UAE time) so the comparison
    is always based on the trading day, not the server clock.
    """
    if api_timestamp:
        try:
            # API format: "2026-06-01T09:00:23.114+04:00"
            return api_timestamp[:10]
        except Exception:
            pass
    return datetime.now().strftime('%Y-%m-%d')


def _load() -> dict:
    """Load the raw store dict, or empty dict if missing/corrupt."""
    if not os.path.exists(_STORE):
        return {}
    try:
        with open(_STORE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    with open(_STORE, 'w') as f:
        json.dump(data, f, indent=2)


def update_and_get_previous(rates: dict, api_timestamp: str = '') -> Optional[dict]:
    """
    Call this ONCE per run after fetching today's rates.

    • Determines today's trading date from the API timestamp.
    • Promotes current → previous when the date changes.
    • Saves updated store to disk.
    • Returns the previous day's rates dict, or None if this is the first run.

    The returned dict is used to compute change indicators.
    """
    today = _today(api_timestamp)
    clean = {k: rates[k] for k in _KARATS if k in rates}
    store = _load()

    current_in_file  = store.get('current',  {})
    previous_in_file = store.get('previous', {})

    saved_date = current_in_file.get('date', '')

    if saved_date == today:
        # Same trading day — keep previous unchanged, just refresh current rates
        new_store = {
            'current':  {'date': today,      'rates': clean},
            'previous': previous_in_file,    # untouched
        }
        prev_rates = previous_in_file.get('rates') or None
        action = 'refreshed (same day)'

    elif saved_date:
        # New trading day — promote current → previous
        new_store = {
            'current':  {'date': today,                          'rates': clean},
            'previous': {'date': saved_date,
                         'rates': current_in_file.get('rates', {})},
        }
        prev_rates = current_in_file.get('rates') or None
        action = f'promoted {saved_date} → previous'

    else:
        # First run ever — no previous data
        new_store = {
            'current':  {'date': today, 'rates': clean},
        }
        prev_rates = None
        action = 'first run — no previous data'

    _save(new_store)

    print(f"[rates_store] {action}")
    if prev_rates:
        prev_date = new_store.get('previous', {}).get('date', '?')
        print(f"[rates_store] comparing {today} vs {prev_date}")
    else:
        print("[rates_store] no previous rates — change indicators hidden")

    return prev_rates


def compute_changes(current: dict, previous: Optional[dict]) -> dict:
    """
    Returns {karat: float | None}.
    None = no data (badges hidden).  0.0 = flat.  +/- = up/down.
    """
    if not previous:
        return {k: None for k in _KARATS}
    result = {}
    for k in _KARATS:
        if k in current and k in previous:
            result[k] = round(current[k] - previous[k], 2)
        else:
            result[k] = None
    return result
