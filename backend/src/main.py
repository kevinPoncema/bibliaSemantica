from fastapi import FastAPI
from src.controllers import search_controller

app = FastAPI(
    title="Biblia Semántica API",
    description="API REST para buscar versículos de la Biblia mediante similitud semántica (Embeddings).",
    version="1.0.0",
    # OpenAPI Swagger UI estará disponible por defecto en /docs
)

# Incluir los controladores (routers)
app.include_router(search_controller.router)

@app.get("/", tags=["Health"])
def read_root():
    return {
        "message": "Bienvenido a la API del buscador semántico.",
        "docs": "Visita /docs para probar la API desde Swagger UI."
    }
