#!/usr/bin/env python3
"""
One-time setup (or daily refresh): exchange credentials for a Bearer token.
Token is written back into .env as GOLD_BEARER_TOKEN.

Run: python3 auth.py
"""
import json, os, re, subprocess, sys
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv('GOLD_API_KEY', '').strip()
EMAIL    = os.getenv('GOLD_API_EMAIL', '').strip()
PASSWORD = os.getenv('GOLD_API_PASSWORD', '').strip()

if not all([API_KEY, EMAIL, PASSWORD]):
    print("ERROR: GOLD_API_KEY, GOLD_API_EMAIL and GOLD_API_PASSWORD must all be set in .env")
    sys.exit(1)

print(f"Logging in as {EMAIL} …")

result = subprocess.run(
    ['curl', '-s',
     '-X', 'POST', 'https://api-dcog.sortd.pro/v1/login',
     '-H', f'x-api-key: {API_KEY}',
     '-H', 'Content-Type: application/json',
     '-d', json.dumps({'email': EMAIL, 'password': PASSWORD})],
    capture_output=True, text=True, timeout=30,
)

try:
    body = json.loads(result.stdout)
except Exception:
    print(f"ERROR: non-JSON response: {result.stdout[:200]}")
    sys.exit(1)

if not body.get('success'):
    print(f"ERROR: login failed: {body}")
    sys.exit(1)

token = body['data']['token']
print(f"Token received: {token[:24]}…")

# Write token back into .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
with open(env_path, 'r') as f:
    content = f.read()

if 'GOLD_BEARER_TOKEN=' in content:
    content = re.sub(r'GOLD_BEARER_TOKEN=.*', f'GOLD_BEARER_TOKEN={token}', content)
else:
    content += f'\nGOLD_BEARER_TOKEN={token}\n'

with open(env_path, 'w') as f:
    f.write(content)

print("✓ Token saved to .env")
print("You can now run:  python3 main.py")
