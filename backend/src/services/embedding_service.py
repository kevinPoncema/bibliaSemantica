from sentence_transformers import SentenceTransformer
from typing import List, Union

class EmbeddingService:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            print(f"Cargando el modelo de embeddings: '{self.model_name}'...")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def generate_vector(self, text: str) -> List[float]:
        """
        Genera un vector embedding para un solo texto. 
        Ideal para cuando el usuario realiza una búsqueda.
        """
        return self.model.encode(text, show_progress_bar=False).tolist()

    def generate_vectors_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Genera vectores embedding para una lista de textos. 
        Ideal para el proceso de poblar la base de datos (batching).
        """
        return self.model.encode(texts, show_progress_bar=False).tolist()
