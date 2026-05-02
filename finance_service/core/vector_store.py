# finance_service/core/vector_store.py

import faiss
import numpy as np
from logger import setup_logger

logger = setup_logger("VectorStore")


class VectorStore:
    def __init__(self, dim: int = 384):
        self.index = faiss.IndexFlatL2(dim)
        self.docs  = []

    def add(self, vectors: list, docs: list):
        logger.info(f"Adding {len(docs)} docs to FAISS")
        self.index.add(np.array(vectors).astype("float32"))
        self.docs.extend(docs)

    def search(self, query_vec, k: int = 3) -> list:
        logger.info("Running RAG retrieval")

        if not self.docs:
            logger.warning("VectorStore empty — no docs to retrieve")
            return []

        D, I = self.index.search(np.array([query_vec]).astype("float32"), k)
        return [self.docs[i] for i in I[0] if 0 <= i < len(self.docs)]
