from fastapi import APIRouter, Query, Depends, HTTPException
import logging

logger = logging.getLogger(__name__)
from typing import List
from pydantic import BaseModel
from typing import List, Optional, Union
from pydantic import BaseModel, Field
import os

from src.services.search_service import SearchService
from src.services.embedding_service import EmbeddingService
from src.repositories.qdrant_repository import QdrantRepository

router = APIRouter(prefix="/api/v1", tags=["Search"])

class SearchResult(BaseModel):
    score: float
    book: str
    chapter: str
    verse: Union[int, str]
    text: str
    heading: str = ""
    label: str = ""

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]

def get_embedding_service():
    return EmbeddingService()

def get_qdrant_repository():
    qdrant_url = os.environ.get("QDRANT_URL", "http://qdrant:6333")
    return QdrantRepository(url=qdrant_url)

def get_search_service(
    emb_service: EmbeddingService = Depends(get_embedding_service),
    repo: QdrantRepository = Depends(get_qdrant_repository)
):
    return SearchService(embedding_service=emb_service, qdrant_repository=repo)

@router.get("/search", response_model=SearchResponse, summary="Busca versículos por similitud semántica")
def search_verses(
    q: str = Query(..., min_length=2, description="Texto de la consulta (ej. 'amor al prójimo')"),
    limit: int = Query(10, ge=1, le=50, description="Cantidad máxima de resultados a retornar"),
    offset: int = Query(0, ge=0, description="Cantidad de resultados a omitir (Paginación)"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Recibe una consulta en lenguaje natural, la convierte en un embedding vectorial,
    y busca los versículos de la Biblia más similares semánticamente en Qdrant.
    """
    try:
        results = search_service.search_bible(query=q, limit=limit, offset=offset)
        return SearchResponse(query=q, results=results)
    except Exception as error:
        logger.error(f"Error crítico en la búsqueda vectorial: {error}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al procesar la búsqueda vectorial."
        )

@router.get("/search/context", response_model=SearchResponse)
async def search_verses_context(
    q: str = Query(..., min_length=2, description="Texto de búsqueda semántica (ej. 'amor al prójimo')"),
    limit: int = Query(10, ge=1, le=50, description="Cantidad máxima de resultados a retornar"),
    offset: int = Query(0, ge=0, description="Cantidad de resultados a omitir (Paginación)"),
    search_service: SearchService = Depends(get_search_service)
):
    try:
        results = search_service.search_bible_context(query=q, limit=limit, offset=offset)
        return SearchResponse(query=q, results=results)
    except Exception as error:
        logger.error(f"Error crítico en la búsqueda de contexto: {error}")
        raise HTTPException(
            status_code=500,
            detail="Error interno al consultar la base de datos vectorial."
        )
