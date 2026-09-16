from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.controllers import search_controller

app = FastAPI(
    title="Biblia Semántica API",
    description="API REST para buscar versículos de la Biblia mediante similitud semántica (Embeddings).",
    version="1.0.0",
)

# Configurar CORS para permitir peticiones desde el frontend (Vue en el puerto 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción deberías poner ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los controladores (routers)
app.include_router(search_controller.router)

@app.get("/", tags=["Health"])
def read_root():
    return {
        "message": "Bienvenido a la API del buscador semántico.",
        "docs": "Visita /docs para probar la API desde Swagger UI."
    }
