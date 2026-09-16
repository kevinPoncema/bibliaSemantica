# Biblia Semántica

Un buscador semántico minimalista para la Biblia. Permite buscar versículos usando lenguaje natural (embeddings) mediante inteligencia artificial local, sin depender de APIs de terceros.

## Arquitectura

- **Backend:** FastAPI (Python)
- **Base de Datos Vectorial:** Qdrant
- **Modelo de NLP (Embeddings):** `paraphrase-multilingual-MiniLM-L12-v2` (Sentence-Transformers)
- **Frontend:** Vue 3 + Tailwind CSS
- **Infraestructura:** Docker & Docker Compose

## Requisitos

- Docker y Docker Compose
- (Opcional) Python 3.11 para ejecución local sin Docker

## Instalación y Ejecución

1. Clona este repositorio.
2. Levanta la infraestructura usando Docker Compose:
   ```bash
   docker compose up -d --build
   ```
3. La primera vez, necesitas poblar la base de datos con los versículos:
   ```bash
   docker compose exec backend python scripts/populate_db.py
   ```
   *(Este proceso descargará el modelo de lenguaje y procesará el texto por lotes. Puede tardar un par de minutos).*

4. Accede a los servicios:
   - **Frontend (UI de Búsqueda):** [http://localhost:5173](http://localhost:5173)
   - **Backend (API & Documentación Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Qdrant (Panel de control DB):** [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

## Modo Desarrollo (Frontend)

El frontend está configurado para leer la variable de entorno `VITE_DEV_MODE`. Si está en `true`, se mostrará el *score* de similitud (de 0 a 1) en cada resultado devuelto, útil para afinar las búsquedas. En producción, puedes ponerlo en `false` para ocultarlo y tener una interfaz más limpia.

## Endpoints Principales

- `GET /api/v1/search?q={consulta}&limit={n}`: Busca versículos similares al texto proporcionado.
