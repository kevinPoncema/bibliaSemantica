import sys
import os
import json
from typing import Iterator, Dict, Any, Tuple, List

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.repositories.qdrant_repository import QdrantRepository
from src.services.embedding_service import EmbeddingService

DEFAULT_JSON_PATH = os.environ.get(
    "BIBLE_JSON_PATH", 
    os.path.join(os.path.dirname(__file__), '..', 'data', 'RVC_vid_146.json')
)
DEFAULT_BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 200))
DEFAULT_QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")

def load_bible_data(filepath: str) -> dict:
    """Lee y parsea el archivo JSON de la Biblia desde el disco."""
    print(f"Cargando datos de la Biblia desde {filepath}...")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"El archivo {filepath} no existe.")
        
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def extract_verses_from_data(bible_data: dict) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """
    Generador que extrae versículos, manteniendo en memoria el contexto 
    de subtítulos (heading1) y etiquetas (label).
    """
    for book in bible_data.get("books", []):
        book_name = book.get("name")
        
        for chapter in book.get("chapters", []):
            chapter_name = chapter.get("current", {}).get("human", "")
            
            # Inicializamos la memoria de estado para este capítulo
            pericopa_actual = ""
            label_actual = ""
            
            for item in chapter.get("items", []):
                item_type = item.get("type")
                
                # Extraemos el texto crudo del item actual
                lineas = " ".join(item.get("lines", []))
                
                # Lógica de máquina de estados
                if item_type == "heading1":
                    pericopa_actual = lineas
                elif item_type == "label":
                    label_actual = lineas
                elif item_type == "verse":
                    verse_nums = item.get("verse_numbers", [])
                    verse_number = verse_nums[0] if verse_nums else 0
                    
                    texto_versiculo = lineas
                    if not texto_versiculo.strip():
                        continue
                    
                    metadata = {
                        "book": book_name,
                        "chapter": chapter_name,
                        "verse": verse_number,
                        "heading": pericopa_actual,
                        "label": label_actual,
                        "text": texto_versiculo
                    }
                    
                    contexto_ia = f"Libro: {book_name}."
                    if pericopa_actual:
                        contexto_ia += f" Tema: {pericopa_actual}."
                    if label_actual:
                        contexto_ia += f" Contexto: {label_actual}."
                        
                    # El prefijo 'passage: ' es OBLIGATORIO para el modelo E5
                    texto_para_vectorizar = f"passage: {contexto_ia} Texto: {texto_versiculo}"
                    
                    yield texto_para_vectorizar, metadata

def process_and_insert_batches(
    verses_iterator: Iterator[Tuple[str, Dict[str, Any]]], 
    embedding_service: EmbeddingService, 
    repository: QdrantRepository, 
    batch_size: int
):
    """Agrupa los versículos en lotes, genera sus embeddings y los inserta en la base de datos."""
    print(f"Iniciando el procesamiento en lotes (batch_size={batch_size})...")
    texts_batch = []
    meta_batch = []
    total_inserted = 0
    
    for text, metadata in verses_iterator:
        texts_batch.append(text)
        meta_batch.append(metadata)
        
        if len(texts_batch) >= batch_size:
            _insert_batch(texts_batch, meta_batch, embedding_service, repository)
            total_inserted += len(texts_batch)
            print(f"--> Insertados {total_inserted} versículos en Qdrant...")
            
            texts_batch.clear()
            meta_batch.clear()
            
    if texts_batch:
        _insert_batch(texts_batch, meta_batch, embedding_service, repository)
        total_inserted += len(texts_batch)
        print(f"--> Insertados {total_inserted} versículos en Qdrant...")

def _insert_batch(
    texts: List[str], 
    metadata: List[dict], 
    embedding_service: EmbeddingService, 
    repository: QdrantRepository
):
    """Método auxiliar interno para vectorizar un conjunto de textos y guardarlos."""
    dense_embeddings = embedding_service.generate_vectors_batch(texts)
    sparse_embeddings = embedding_service.generate_sparse_vectors_batch(texts)
    
    repository.upsert_batch(texts, dense_embeddings, sparse_embeddings, metadata)

def main():
    try:
        embedding_service = EmbeddingService()
        qdrant_repo = QdrantRepository(url=DEFAULT_QDRANT_URL)
        
        bible_data = load_bible_data(DEFAULT_JSON_PATH)
        verses_iterator = extract_verses_from_data(bible_data)
        
        process_and_insert_batches(
            verses_iterator=verses_iterator,
            embedding_service=embedding_service,
            repository=qdrant_repo,
            batch_size=DEFAULT_BATCH_SIZE
        )
        
        print("¡Proceso finalizado! La base de datos ha sido poblada con éxito.")
        
    except Exception as error:
        print(f"Error crítico durante la ejecución: {error}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
