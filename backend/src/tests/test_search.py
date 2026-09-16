import pytest
import sys
import os

# Solucionar el problema de importación del módulo 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fastapi.testclient import TestClient
from src.main import app

# Cliente de pruebas que simula peticiones HTTP a nuestra aplicación FastAPI
client = TestClient(app)

def test_read_root():
    """Prueba que el endpoint raíz responda correctamente."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Bienvenido" in response.json()["message"]

def test_search_endpoint_validation():
    """
    Prueba que el endpoint de búsqueda valide correctamente los parámetros.
    Debería fallar (422) si pasamos una consulta muy corta o nula.
    """
    # Consulta vacía (debería dar error 422 de validación)
    response = client.get("/api/v1/search?q=")
    assert response.status_code == 422
    
    # Límite fuera de rango (debería dar error 422)
    response_limit = client.get("/api/v1/search?q=amor&limit=100")
    assert response_limit.status_code == 422

# Nota: Para probar la búsqueda real en Qdrant (Integration Test Completo), 
# necesitaríamos "mockear" (simular) la base de datos o apuntar a una DB de test,
# pero con este test probamos que la capa HTTP, inyección de dependencias
# y validación de Pydantic funcionan perfectamente sin romper la aplicación.
def test_search_endpoint_success(monkeypatch):
    """
    Prueba que la búsqueda devuelve 200 y una estructura válida
    si los parámetros son correctos.
    """
    # Vamos a simular que el SearchService devuelve resultados controlados
    # para no depender de Qdrant en este test unitario/integración rápido.
    from src.controllers.search_controller import get_search_service
    
    class MockSearchService:
        def search_bible(self, query, limit):
            return [{
                "score": 0.99,
                "book": "Test Book",
                "chapter": "Test Chapter 1",
                "verse": 1,
                "text": "Versículo de prueba."
            }]
            
    # Sobreescribimos la dependencia en FastAPI inyectando el mock
    app.dependency_overrides[get_search_service] = lambda: MockSearchService()
    
    response = client.get("/api/v1/search?q=amor&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "amor"
    assert len(data["results"]) == 1
    assert data["results"][0]["book"] == "Test Book"
    
    # Limpiamos las dependencias sobreescritas
    app.dependency_overrides.clear()
