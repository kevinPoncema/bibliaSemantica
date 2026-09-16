# Biblia Semántica

Un buscador avanzado para la Biblia que implementa **Búsqueda Híbrida** (Vectores Densos + BM25), permitiendo búsquedas por significado (Inteligencia Artificial) y por palabras clave exactas simultáneamente. Todo de forma local y *open-source*.

## Características Principales
- **Búsqueda Híbrida (RRF):** Fusión de resultados densos (ideas) y dispersos (léxico) delegados nativamente en Qdrant.
- **Enriquecimiento Semántico:** Los versículos se indexan junto a sus subtítulos (`heading1`) y contexto (`label`) para que la IA comprenda la escena completa y no pierda sentido.
- **Modelos Asimétricos (E5):** Uso de `intfloat/multilingual-e5-small`, diferenciando matemáticamente las "consultas" de los "pasajes".
- **Inserción Idempotente:** Hashes UUID v5 deterministas que evitan la duplicación de versículos en la base de datos en caso de reinicios.
- **Interfaz Moderna:** Vue 3 + Tailwind CSS v4.

Para los detalles técnicos y el porqué de cada decisión, consulta la carpeta `/docs`.

## Arquitectura Básica
- **Backend:** FastAPI (Python)
- **Base de Datos Vectorial:** Qdrant
- **Modelos de IA:** `intfloat/multilingual-e5-small` (Denso) y `Qdrant/bm25` (Disperso/Sparse) a través de `fastembed`.
- **Frontend:** Vue 3 + Vite

## Instalación y Ejecución

1. Clona este repositorio y levanta la infraestructura:
   ```bash
   docker compose up -d --build
   ```
2. La primera vez, necesitas poblar la base de datos (se descargarán los modelos y se procesará el texto por lotes):
   ```bash
   docker compose exec backend python scripts/populate_db.py
   ```
3. Accede a los servicios:
   - **Frontend UI:** [http://localhost:5173](http://localhost:5173)
   - **Backend API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Qdrant DB (Dashboard):** [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

## Documentación
Lee la documentación detallada para entender la lógica interna:
- [Arquitectura del Sistema](docs/arquitectura.md)
- [Proceso de Embeddings y Búsqueda](docs/embeddings_y_busqueda.md)
