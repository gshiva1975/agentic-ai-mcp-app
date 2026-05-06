# finance_service/agents/analyst.py

from logger import setup_logger

logger = setup_logger("Analyst")


class AnalystAgent:
    def __init__(self, model=None):
        if model is None:
            from transformers import pipeline
            model = pipeline("text-classification", model="ProsusAI/finbert")
        self.model = model

    def run(self, state: dict) -> dict:
        result = self.model(state["query"])[0]
        state["sentiment"] = {
            "label":      result["label"],
            "confidence": float(result["score"]),
        }
        return state
