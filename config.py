import os
from dotenv import load_dotenv

load_dotenv()

API_URL      = os.getenv('GOLD_API_URL', 'https://api-dcog.sortd.pro/v1/rates')
API_KEY      = os.getenv('GOLD_API_KEY', '')
API_TOKEN    = os.getenv('GOLD_BEARER_TOKEN', '')
API_EMAIL    = os.getenv('GOLD_API_EMAIL', '')
API_PASSWORD = os.getenv('GOLD_API_PASSWORD', '')
OUTPUT_DIR   = os.getenv('OUTPUT_DIR') or os.path.join(os.path.dirname(__file__), 'output')
