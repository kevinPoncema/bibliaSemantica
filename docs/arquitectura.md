# Arquitectura del Sistema

La aplicación "Biblia Semántica" está diseñada como una arquitectura moderna utilizando contenedores Docker para aislar dependencias, evitar conflictos y garantizar la portabilidad total entre entornos.

## Componentes

### 1. Base de Datos Vectorial (Qdrant)
- **Por qué Qdrant:** A diferencia de las bases de datos relacionales tradicionales (como PostgreSQL), Qdrant está optimizada específicamente para almacenar "Embeddings" (vectores matemáticos de alta dimensionalidad) y realizar cálculos de distancia (ej. similitud del coseno) a velocidades ultrarrápidas, soportando aceleración de hardware si estuviese disponible.
- **Vectores Nombrados (Named Vectors):** La colección principal (`bible_verses_hybrid`) no utiliza un solo vector por documento. Configura dos representaciones matemáticas distintas:
  - `dense`: Un vector de 384 dimensiones.
  - `sparse`: Un vector de dimensiones variables (basado en el vocabulario léxico del BM25).
- **Idempotencia:** En lugar de usar IDs aleatorios (`uuid4`), Qdrant utiliza `uuid5` basados en un hash de `{Libro}_{Capitulo}_{Versiculo}`. Esto garantiza que si el script de poblamiento se ejecuta de nuevo, los versículos se sobrescriban en lugar de duplicarse.

### 2. Backend (FastAPI)
- **Por qué FastAPI:** Es un framework moderno, extremadamente rápido, maneja asincronía nativa (crucial para I/O de red con Qdrant) y autogenera documentación OpenAPI (Swagger). Es el estándar actual para proyectos de Inteligencia Artificial en Python.
- **Patrón de Diseño (N-Capas):**
  - `Controllers/`: Manejan el enrutamiento HTTP y la validación de entrada/salida estricta usando Pydantic.
  - `Services/`: Contienen toda la lógica de negocio (procesamiento de embeddings, orquestación de la búsqueda híbrida).
  - `Repositories/`: Aíslan la lógica de acceso a datos (comunicación directa con el cliente de Qdrant).
  - `Scripts/`: Tareas asíncronas de mantenimiento, como el motor ETL de poblamiento (`populate_db.py`).

### 3. Frontend (Vue 3 + Vite + Tailwind CSS v4)
- **Por qué Vue 3:** Ofrece una reactividad altísima y una curva de aprendizaje suave, ideal para construir una Single Page Application (SPA) minimalista.
- **Tailwind CSS v4:** La nueva versión del motor CSS elimina la necesidad de pesados archivos de configuración estáticos (`tailwind.config.js`), operando completamente JIT (Just-In-Time) e inyectando las capas de utilidades directamente a través del motor de Vite usando la simple directiva `@import "tailwindcss";`.
- **Feedback UI:** Utiliza rendering condicional para mostrar u ocultar la metadata avanzada de los resultados (`scores`, `headings`, `labels`) dependiendo de si la aplicación está en modo de desarrollo (`VITE_DEV_MODE=true`).
