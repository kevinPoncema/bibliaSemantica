from src.services.embedding_service import EmbeddingService
from src.repositories.qdrant_repository import QdrantRepository

class SearchService:
    def __init__(self, embedding_service: EmbeddingService, qdrant_repository: QdrantRepository):
        self.embedding_service = embedding_service
        self.qdrant_repository = qdrant_repository

    def _limpiar_stopwords(self, texto: str) -> str:
        stopwords = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "a", "al", "en", "para", "por", "con", "su", "sus", "y", "o", "que", "se", "lo", "te", "me", "le", "nos", "os", "mi", "mis", "tu", "tus", "es", "son"}
        palabras = texto.split()
        palabras_limpias = [p for p in palabras if p.lower() not in stopwords]
        return " ".join(palabras_limpias) if palabras_limpias else texto

    def search_bible(self, query: str, limit: int = 10, offset: int = 0):
        query_e5 = f"query: {query}"
        dense_vector = self.embedding_service.generate_vector(query_e5)
        
        query_limpia = self._limpiar_stopwords(query)
        sparse_vector = self.embedding_service.generate_sparse_vector(query_limpia)
        
        results = self.qdrant_repository.search_hybrid(
            dense_vector=dense_vector, 
            sparse_vector=sparse_vector, 
            limit=limit,
            offset=offset
        )
        return self.formatear_resultado(results)

    def search_bible_context(self, query: str, limit: int = 10, offset: int = 0):
        query_e5 = f"query: {query}"
        dense_vector = self.embedding_service.generate_vector(query_e5)
        
        query_limpia = self._limpiar_stopwords(query)
        sparse_vector = self.embedding_service.generate_sparse_vector(query_limpia)
        
        ganadores = self.qdrant_repository.search_hybrid(
            dense_vector=dense_vector, 
            sparse_vector=sparse_vector, 
            limit=limit,
            offset=offset
        )
        
        contextos_vistos = set()
        resultados_agrupados = []
        
        for res in ganadores:
            payload = res.payload
            book = payload.get("book")
            chapter = payload.get("chapter")
            heading = payload.get("heading", "")
            
            context_key = f"{book}_{chapter}_{heading}"
            
            if context_key not in contextos_vistos:
                contextos_vistos.add(context_key)
                
                hermanos = self.qdrant_repository.get_verses_by_context(book, chapter, heading)
                
                if not hermanos:
                    continue
                    
                textos = [h.payload.get("text", "") for h in hermanos]
                texto_completo = " ".join(textos)
                
                versiculos_nums = [h.payload.get("verse", 0) for h in hermanos]
                rango_verse = f"{min(versiculos_nums)}-{max(versiculos_nums)}" if len(versiculos_nums) > 1 else str(versiculos_nums[0])
                
                resultados_agrupados.append({
                    "score": res.score,
                    "book": book,
                    "chapter": chapter,
                    "verse": rango_verse,
                    "text": texto_completo,
                    "heading": heading,
                    "label": payload.get("label", "")
                })
                
        return resultados_agrupados

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
            
