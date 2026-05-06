# mcp_servers/sec_server.py

import requests
from mcp_servers.base_mcp import BaseMCP

mcp = BaseMCP()

SEC_HEADERS     = {"User-Agent": "FinanceIntelligenceService/1.0 your_email@example.com"}
CIK_LOOKUP_URL  = "https://www.sec.gov/files/company_tickers.json"


def _get_cik(ticker: str) -> str | None:
    try:
        response = requests.get(CIK_LOOKUP_URL, headers=SEC_HEADERS)
        if response.status_code != 200:
            return None
        ticker = ticker.upper()
        for entry in response.json().values():
            if entry["ticker"].upper() == ticker:
                return str(entry["cik_str"]).zfill(10)
        return None
    except Exception:
        return None


def fetch_sec_filings(ticker: str) -> list:
    cik = _get_cik(ticker)
    if not cik:
        return []

    response = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=SEC_HEADERS)
    if response.status_code != 200:
        return []

    data   = response.json()
    recent = data.get("filings", {}).get("recent", {})
    forms  = recent.get("form", [])
    dates  = recent.get("filingDate", [])

    filings = [
        f"{ticker} filed {form} on {date}. This filing may contain updated financial disclosures."
        for form, date in zip(forms, dates)
        if form in ("10-K", "10-Q")
    ]
    return filings[:5]


mcp.register("fetch_sec_filings", fetch_sec_filings)

app = mcp.app
