from sentence_transformers import SentenceTransformer
from typing import List, Union
from fastembed import SparseTextEmbedding

class EmbeddingService:
    def __init__(self, dense_model_name: str = "intfloat/multilingual-e5-small"):
        self.dense_model_name = dense_model_name
        self._dense_model = None
        self._sparse_model = None

    @property
    def dense_model(self) -> SentenceTransformer:
        if self._dense_model is None:
            print(f"Cargando el modelo DENSE: '{self.dense_model_name}'...")
            self._dense_model = SentenceTransformer(self.dense_model_name)
        return self._dense_model

    @property
    def sparse_model(self) -> SparseTextEmbedding:
        if self._sparse_model is None:
            print(f"Cargando el modelo SPARSE (BM25): 'Qdrant/bm25'...")
            self._sparse_model = SparseTextEmbedding("Qdrant/bm25")
        return self._sparse_model

    def generate_vector(self, text: str) -> List[float]:
        return self.dense_model.encode(text, show_progress_bar=False).tolist()

    def generate_sparse_vector(self, text: str):
        # Devuelve el vector sparse de fastembed para una consulta
        return list(self.sparse_model.embed([text]))[0]

    def generate_vectors_batch(self, texts: List[str]) -> List[List[float]]:
        return self.dense_model.encode(texts, show_progress_bar=False).tolist()
        
    def generate_sparse_vectors_batch(self, texts: List[str]):
        # Retorna una lista de SparseEmbedding de fastembed
        return list(self.sparse_model.embed(texts))
