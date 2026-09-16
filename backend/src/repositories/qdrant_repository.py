from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
import uuid

class QdrantRepository:
    def __init__(self, url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=url)
        self.collection_name = "bible_verses"
        self._ensure_collection()

    def _ensure_collection(self):
        """Verifica si la colección existe, y si no, la crea con las dimensiones correctas"""
        collections_response = self.client.get_collections()
        exists = any(c.name == self.collection_name for c in collections_response.collections)
        
        if not exists:
            print(f"Creando la colección '{self.collection_name}' en Qdrant...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def upsert_batch(self, texts: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]]):
        """Inserta un lote (batch) de versículos con sus embeddings a Qdrant"""
        points = []
        for text, emb, meta in zip(texts, embeddings, metadata):
            point_id = str(uuid.uuid4())
            meta_copy = meta.copy()
            meta_copy["text"] = text
            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=meta_copy
                )
            )
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search(self, query_vector: List[float], limit: int = 10):
        """Busca los vectores más similares a la consulta en Qdrant"""
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
