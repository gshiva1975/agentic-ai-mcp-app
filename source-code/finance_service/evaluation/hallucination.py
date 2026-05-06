# finance_service/evaluation/hallucination.py

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class HallucinationEvaluator:

    def __init__(self, threshold: float = 0.65):
        self.embedder  = SentenceTransformer("all-MiniLM-L6-v2")
        self.threshold = threshold

    def _split_sentences(self, text: str) -> list:
        return [s.strip() for s in text.split(".") if s.strip()]

    def evaluate(self, answer: str, retrieved_docs: list) -> dict:
        if not retrieved_docs:
            return {
                "hallucination_rate":    1.0,
                "faithfulness_score":    0.0,
                "unsupported_sentences": self._split_sentences(answer),
            }

        answer_sentences = self._split_sentences(answer)
        doc_embeddings   = self.embedder.encode(retrieved_docs)
        unsupported      = []

        for sentence in answer_sentences:
            sent_emb = self.embedder.encode([sentence])
            sims     = cosine_similarity(sent_emb, doc_embeddings)
            if np.max(sims) < self.threshold:
                unsupported.append(sentence)

        hallucination_rate = len(unsupported) / max(1, len(answer_sentences))

        return {
            "hallucination_rate":    hallucination_rate,
            "faithfulness_score":    1 - hallucination_rate,
            "unsupported_sentences": unsupported,
        }
