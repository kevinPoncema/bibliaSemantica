from fastapi import FastAPI

app = FastAPI(title="Biblia Semántica API")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API del buscador semántico"}
