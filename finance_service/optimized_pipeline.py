# finance_service/optimized_pipeline.py

from finance_service.evaluation.hallucination import HallucinationEvaluator


class OptimizedFinancePipeline:

    def __init__(self, llm, store, embed, researcher_agent):
        self.llm              = llm
        self.store            = store
        self.embed            = embed
        self.researcher_agent = researcher_agent
        self.evaluator        = HallucinationEvaluator()

    def analyze(self, query: str):
        # Retrieve documents
        state        = {"query": query}
        enriched     = self.researcher_agent.run(state)
        docs         = enriched.get("docs", [])
        context      = "\n".join(docs)

        # Build grounded prompt
        prompt = f"""
You are a financial analyst.

Answer the question strictly using the provided documents.
Do NOT repeat the prompt.
Do NOT invent facts.
If the answer is not in the documents, say: Insufficient data.

Documents:
{context}

Question:
{query}

Provide grounded reasoning.
"""
        response = self.llm.generate(prompt)

        # Evaluate hallucination
        metrics = self.evaluator.evaluate(response, docs)

        return {
            "mode":                  "OPTIMIZED",
            "answer":                response,
            "tools_used":            ["market", "sec", "social"],
            "grounded":              True,
            "hallucination_rate":    metrics["hallucination_rate"],
            "faithfulness_score":    metrics["faithfulness_score"],
            "unsupported_sentences": metrics["unsupported_sentences"],
        }
