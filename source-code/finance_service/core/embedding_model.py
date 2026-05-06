# finance_service/core/embedding_model.py

import torch
from transformers import AutoTokenizer, AutoModel
from logger import setup_logger

logger = setup_logger("Embedding")


class EmbeddingModel:
    def __init__(self, name="sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(name)
        self.model     = AutoModel.from_pretrained(name)

    def encode(self, text: str):
        logger.info("Encoding query")
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)[0].numpy()
