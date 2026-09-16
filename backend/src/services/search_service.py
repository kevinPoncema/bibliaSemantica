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

    def _perform_core_search(self, query: str, limit: int, offset: int):
        # 1. Vectores
        query_e5 = f"query: {query}"
        dense_vector = self.embedding_service.generate_vector(query_e5)
        
        query_limpia = self._limpiar_stopwords(query)
        sparse_vector = self.embedding_service.generate_sparse_vector(query_limpia)
        
        # 2. Búsqueda híbrida (pedimos 25 por defecto para rerankear)
        fetch_limit = max(25, limit + 15)
        ganadores_crudos = self.qdrant_repository.search_hybrid(
            dense_vector=dense_vector, 
            sparse_vector=sparse_vector, 
            limit=fetch_limit,
            offset=offset
        )
        
        if not ganadores_crudos:
            return []
            
        # 3. Preparar los pares y calcular score real
        pares = [[query, res.payload.get("text", "")] for res in ganadores_crudos]
        scores = self.embedding_service.reranker.predict(pares)
        
        # 4. Asignar nuevo score y reordenar
        for res, score in zip(ganadores_crudos, scores):
            res.score = float(score)
            
        ganadores_ordenados = sorted(ganadores_crudos, key=lambda x: x.score, reverse=True)
        
        # 5. Cortar al límite original
        return ganadores_ordenados[:limit]

    def search_bible(self, query: str, limit: int = 10, offset: int = 0):
        ganadores = self._perform_core_search(query, limit, offset)
        return self.formatear_resultado(ganadores)

    def search_bible_context(self, query: str, limit: int = 10, offset: int = 0):
        ganadores = self._perform_core_search(query, limit, offset)
        
        titulos_procesados = set()
        resultados_agrupados = []
        
        for res in ganadores:
            payload = res.payload
            book = payload.get("book")
            chapter = payload.get("chapter")
            heading = payload.get("heading", "")
            
            context_key = f"{book}_{chapter}_{heading}"
            
            # Evitar devolver la misma ventana si caen dos resultados en la misma historia
            if context_key not in titulos_procesados:
                titulos_procesados.add(context_key)
                
                # Buscar a todos los hermanos
                hermanos = self.qdrant_repository.get_verses_by_context(book, chapter, heading)
                if not hermanos:
                    continue
                    
                # Buscar el índice del versículo ganador
                ganador_verse_num = payload.get("verse")
                indice = 0
                for i, h in enumerate(hermanos):
                    if h.payload.get("verse") == ganador_verse_num:
                        indice = i
                        break
                        
                # 6. Ventana Inteligente (Smart Window): 2 antes, 2 después (máximo 5 versos)
                inicio = max(0, indice - 2)
                fin = min(len(hermanos), indice + 3)
                
                hermanos_ventana = hermanos[inicio:fin]
                
                # 7. Formatear
                textos = [h.payload.get("text", "") for h in hermanos_ventana]
                texto_completo = " ".join(textos)
                
                versiculos_nums = [h.payload.get("verse", 0) for h in hermanos_ventana]
                rango_verse = f"{min(versiculos_nums)}-{max(versiculos_nums)}" if len(versiculos_nums) > 1 else str(versiculos_nums[0])
                
                resultados_agrupados.append({
                    "score": res.score,
                    "book": book,
                    "chapter": chapter,
                    "verse": str(rango_verse),
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
                "verse": str(res.payload.get("verse")),
                "text": res.payload.get("text"),
                "heading": res.payload.get("heading", ""),
                "label": res.payload.get("label", "")
            })
        return formatted_results
            
