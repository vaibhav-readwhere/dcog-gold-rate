"""
Persist and retrieve gold rates so daily changes can be computed.
Saves to last_rates.json alongside this file (or a custom path).
"""
import json, os
from datetime import datetime
from typing import Optional

_STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_rates.json')
_KARATS = ['24K', '22K', '21K', '18K', '14K']


def load_previous_rates(path: str = _STORE) -> Optional[dict]:
    """Return the previously saved rates dict, or None if no history."""
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def save_rates(rates: dict, path: str = _STORE) -> None:
    """Save rates to JSON for use in the next run."""
    data = {k: rates[k] for k in _KARATS if k in rates}
    data['_saved_at'] = datetime.now().isoformat()
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[rates_store] saved → {os.path.basename(path)}")


def compute_changes(current: dict, previous: Optional[dict]) -> dict:
    """
    Returns {karat: float | None} for each karat.
    None means no previous data (first run).
    Positive = price went up, negative = went down, 0.0 = flat.
    """
    if previous is None:
        return {k: None for k in _KARATS}
    result = {}
    for k in _KARATS:
        if k in current and k in previous:
            result[k] = round(current[k] - previous[k], 2)
        else:
            result[k] = None
    return result
