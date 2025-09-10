import requests
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
_ = load_dotenv(find_dotenv())
alpha_vintage_api = os.environ["ALPHA_VINTAGE_API"]

# Alpha Vantage endpoint
url = "https://www.alphavantage.co/query"
params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "MSFT",
    "apikey": alpha_vintage_api
}

resp = requests.get(url, params=params)

if resp.status_code == 200:
    data = resp.json()
    if "Time Series (Daily)" in data:
        print("Alpha Vantage  - Data received")
        # Show latest date and closing price
        latest = next(iter(data["Time Series (Daily)"]))
        print("Latest date:", latest)
        print("Close:", data["Time Series (Daily)"][latest]["4. close"])
    else:
        print("Alpha Vantage response but no data:", data)
else:
    print("Alpha Vantage - Error:", resp.status_code, resp.text)
