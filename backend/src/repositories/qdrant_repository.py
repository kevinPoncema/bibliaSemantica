from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any
import uuid

class QdrantRepository:
    def __init__(self, url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=url)
        self.collection_name = "bible_verses_hybrid"
        self._ensure_collection()

    def _ensure_collection(self):
        """Verifica si la colección existe, y si no, la crea con vectores densos y dispersos"""
        collections_response = self.client.get_collections()
        exists = any(c.name == self.collection_name for c in collections_response.collections)
        
        if not exists:
            print(f"Creando la colección híbrida '{self.collection_name}' en Qdrant...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": models.VectorParams(size=384, distance=models.Distance.COSINE)
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams()
                }
            )

    def upsert_batch(self, texts: List[str], dense_embeddings: List[List[float]], sparse_embeddings: List[Any], metadata: List[Dict[str, Any]]):
        """Inserta un lote (batch) de versículos con sus embeddings densos y dispersos a Qdrant"""
        points = []
        for text, dense, sparse, meta in zip(texts, dense_embeddings, sparse_embeddings, metadata):
            unique_string = f"{meta.get('book')}_{meta.get('chapter')}_{meta.get('verse')}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
            
            meta_copy = meta.copy()
            
            # Convertimos el objeto SparseEmbedding de fastembed a models.SparseVector
            sparse_vector = models.SparseVector(
                indices=sparse.indices.tolist(),
                values=sparse.values.tolist()
            )
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector={
                        "dense": dense,
                        "sparse": sparse_vector
                    },
                    payload=meta_copy
                )
            )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search_hybrid(self, dense_vector: List[float], sparse_vector: Any, limit: int = 10, offset: int = 0):
        """Ejecuta una búsqueda híbrida utilizando Prefetch y Reciprocal Rank Fusion (RRF)"""
        qdrant_sparse = models.SparseVector(
            indices=sparse_vector.indices.tolist(),
            values=sparse_vector.values.tolist()
        )
        
        # Límites asimétricos para priorizar fuertemente la IA semántica sobre las palabras clave
        dense_prefetch_limit = limit + offset + 60
        sparse_prefetch_limit = limit + offset + 10
        
        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(
                    query=dense_vector,
                    using="dense",
                    limit=dense_prefetch_limit
                ),
                models.Prefetch(
                    query=models.SparseVector(indices=qdrant_sparse.indices, values=qdrant_sparse.values),
                    using="sparse",
                    limit=sparse_prefetch_limit
                )
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            offset=offset,
            with_payload=True
        )
        return response.points

    def get_verses_by_context(self, book: str, chapter: str, heading: str):
        """Recupera la perícopa entera filtrando por contexto."""
        conditions = [
            models.FieldCondition(key="book", match=models.MatchValue(value=book)),
            models.FieldCondition(key="chapter", match=models.MatchValue(value=chapter))
        ]
        
        if heading:
            conditions.append(models.FieldCondition(key="heading", match=models.MatchValue(value=heading)))
        else:
            conditions.append(models.FieldCondition(key="heading", match=models.MatchValue(value="")))

        filter_obj = models.Filter(must=conditions)
        
        response = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filter_obj,
            limit=100,
            with_payload=True
        )
        
        points = response[0]
        points.sort(key=lambda p: p.payload.get("verse", 0))
        return points

    def search(self, query_vector: List[float], limit: int = 10):
        """Busca los vectores más similares a la consulta en Qdrant"""
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit
        )
        return response.points
