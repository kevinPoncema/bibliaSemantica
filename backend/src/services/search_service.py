from src.services.embedding_service import EmbeddingService
from src.repositories.qdrant_repository import QdrantRepository

class SearchService:
    def __init__(self, embedding_service: EmbeddingService, qdrant_repository: QdrantRepository):
        self.embedding_service = embedding_service
        self.qdrant_repository = qdrant_repository

    def search_bible(self, query: str, limit: int = 10):
        # El modelo E5 requiere el prefijo 'query: ' para textos de búsqueda denso
        query_e5 = f"query: {query}"
        dense_vector = self.embedding_service.generate_vector(query_e5)
        sparse_vector = self.embedding_service.generate_sparse_vector(query)
        
        results = self.qdrant_repository.search_hybrid(
            dense_vector=dense_vector, 
            sparse_vector=sparse_vector, 
            limit=limit
        )
        return self.formatear_resultado(results)

    def formatear_resultado(self, results) -> dict:
        formatted_results = []
        for res in results:
            formatted_results.append({
                "score": res.score,
                "book": res.payload.get("book"),
                "chapter": res.payload.get("chapter"),
                "verse": res.payload.get("verse"),
                "text": res.payload.get("text"),
                "heading": res.payload.get("heading", ""),
                "label": res.payload.get("label", "")
            })
        return formatted_results
            
