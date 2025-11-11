"""Embedding generation utilities"""
from typing import List, Union
from sentence_transformers import SentenceTransformer
from nexus.config import settings


class EmbeddingGenerator:
    """Generate embeddings for text"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        self.model = SentenceTransformer(self.model_name)
    
    def encode(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Encode text to embeddings"""
        embeddings = self.model.encode(text)
        if isinstance(text, str):
            return embeddings.tolist()
        return [emb.tolist() for emb in embeddings]
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encode a batch of texts"""
        embeddings = self.model.encode(texts, batch_size=batch_size)
        return [emb.tolist() for emb in embeddings]
