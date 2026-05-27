"""
Fetches live gold rates from api-dcog.sortd.pro.
Uses system curl to avoid macOS LibreSSL compatibility issues.
Auto-refreshes the Bearer token if it has expired (401).
"""
import json, os, re, subprocess
from typing import Optional


def _curl_get(url: str, api_key: str, token: str) -> dict:
    """GET request via curl, returns parsed JSON."""
    result = subprocess.run(
        ['curl', '-s',
         '-H', f'Authorization: Bearer {token}',
         '-H', f'x-api-key: {api_key}',
         url],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl error: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except Exception:
        raise ValueError(f"Non-JSON response: {result.stdout[:200]}")


def _refresh_token(api_key: str, email: str, password: str) -> str:
    """Login and return a fresh Bearer token, also saves it to .env."""
    result = subprocess.run(
        ['curl', '-s',
         '-X', 'POST', 'https://api-dcog.sortd.pro/v1/login',
         '-H', f'x-api-key: {api_key}',
         '-H', 'Content-Type: application/json',
         '-d', json.dumps({'email': email, 'password': password})],
        capture_output=True, text=True, timeout=30,
    )
    body = json.loads(result.stdout)
    if not body.get('success'):
        raise ValueError(f"Login failed: {body}")

    token = body['data']['token']

    # Persist updated token to .env
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        if 'GOLD_BEARER_TOKEN=' in content:
            content = re.sub(r'GOLD_BEARER_TOKEN=.*', f'GOLD_BEARER_TOKEN={token}', content)
        else:
            content += f'\nGOLD_BEARER_TOKEN={token}\n'
        with open(env_path, 'w') as f:
            f.write(content)

    return token


def fetch_gold_rates(api_url: str,
                     api_key: str,
                     token: str,
                     email: Optional[str] = None,
                     password: Optional[str] = None) -> dict:
    """
    Fetch current gold rates. Automatically re-logs in if token is expired.
    Returns dict with keys: 24K, 22K, 21K, 18K, 14K, timestamp
    """
    body = _curl_get(api_url, api_key, token)

    # Token expired → refresh and retry once
    if not body.get('success') and email and password:
        print("Token expired — refreshing …")
        token = _refresh_token(api_key, email, password)
        # Update env in current process so config picks it up next time
        os.environ['GOLD_BEARER_TOKEN'] = token
        body = _curl_get(api_url, api_key, token)

    if not body.get('success'):
        raise ValueError(f"API error: {body.get('message', body)}")

    d = body['data']
    return {
        '24K': float(d['Rate24Karat']),
        '22K': float(d['Rate22Karat']),
        '21K': float(d['Rate21Karat']),
        '18K': float(d['Rate18Karat']),
        '14K': float(d.get('Rate14Karat', 0)),   # graceful fallback if missing
        'timestamp': d.get('Timestamp', ''),
    }
