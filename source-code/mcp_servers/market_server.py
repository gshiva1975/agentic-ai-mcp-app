# mcp_servers/market_server.py

import os
import requests
from mcp_servers.base_mcp import BaseMCP

mcp = BaseMCP()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


def fetch_market_data(ticker: str) -> list:
    if not ALPHA_VANTAGE_API_KEY:
        return ["API key not configured"]

    url = (
        "https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_DAILY"
        f"&symbol={ticker}"
        f"&apikey={ALPHA_VANTAGE_API_KEY}"
    )

    response = requests.get(url)
    if response.status_code != 200:
        return [f"Failed to fetch market data for {ticker}"]

    data = response.json()

    if "Time Series (Daily)" not in data:
        return ["Market data unavailable (rate limit or API issue)"]

    latest_date = sorted(data["Time Series (Daily)"].keys(), reverse=True)[0]
    latest      = data["Time Series (Daily)"][latest_date]

    summary = (
        f"{ticker} ({latest_date}) — "
        f"Open: ${latest['1. open']}, "
        f"High: ${latest['2. high']}, "
        f"Low: ${latest['3. low']}, "
        f"Close: ${latest['4. close']}, "
        f"Volume: {latest['5. volume']}"
    )
    return [summary]


mcp.register("fetch_market_data", fetch_market_data)

app = mcp.app
