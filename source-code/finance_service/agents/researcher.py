# finance_service/agents/researcher.py

import re
from logger import setup_logger
from finance_service.ingestion.mcp_client import MCPClient
from finance_service.config import settings

logger = setup_logger("Researcher")


class ResearcherAgent:

    def __init__(self, store, embed):
        self.store  = store
        self.embed  = embed
        self.sec    = MCPClient(settings.MCP_SEC_URL)    if settings.MCP_SEC_URL    else None
        self.market = MCPClient(settings.MCP_MARKET_URL) if settings.MCP_MARKET_URL else None
        self.social = MCPClient(settings.MCP_SOCIAL_URL) if settings.MCP_SOCIAL_URL else None

    def extract_ticker(self, query: str):
        match = re.search(r"\b[A-Z]{2,5}\b", query)
        return match.group(0) if match else None

    def run(self, state: dict) -> dict:
        logger.info("Researcher retrieving documents")

        ticker = self.extract_ticker(state["query"])
        docs   = []

        if ticker:
            logger.info(f"Fetching MCP data for {ticker}")

            if self.sec:
                try:
                    docs += self.sec.call_tool("fetch_sec_filings", {"ticker": ticker})
                except Exception as e:
                    logger.warning(f"SEC MCP failed: {e}")

            if self.market:
                try:
                    docs += self.market.call_tool("fetch_market_data", {"ticker": ticker})
                except Exception as e:
                    logger.warning(f"Market MCP failed: {e}")

            if self.social:
                try:
                    docs += self.social.call_tool("fetch_social_sentiment", {"ticker": ticker})
                except Exception as e:
                    logger.warning(f"Social MCP failed: {e}")

            if docs:
                vectors = [self.embed.encode(d) for d in docs]
                self.store.add(vectors, docs)

        vec           = self.embed.encode(state["query"])
        retrieved_docs = self.store.search(vec)

        return {**state, "docs": retrieved_docs}
