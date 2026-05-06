# finance_service/agents/scribe.py

from logger import setup_logger

logger = setup_logger("Scribe")


class ScribeAgent:
    def run(self, state: dict) -> dict:
        logger.info("Generating final report")
        report = (
            f"\nFinancial Report:\n\n"
            f"Sentiment: {state['sentiment']['label']}\n"
            f"Confidence: {state['sentiment']['confidence']}\n"
        )
        return {**state, "report": report}
