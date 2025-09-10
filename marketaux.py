import requests
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
_ = load_dotenv(find_dotenv())
marketaux_api = os.environ["MARKETAUX_API"]

# Marketaux endpoint
url = "https://api.marketaux.com/v1/news/all"
params = {
    "symbols": "AAPL",
    "filter_entities": "true",
    "language": "en",
    "api_token": marketaux_api
}

resp = requests.get(url, params=params)

if resp.status_code == 200:
    data = resp.json()
    if "data" in data and len(data["data"]) > 0:
        print("Marketaux - News received")
        first = data["data"][0]
        print("Headline:", first["title"])
        print("Published:", first["published_at"])
    else:
        print("Marketaux response but no news:", data)
else:
    print("Marketaux ❌ - Error:", resp.status_code, resp.text)
