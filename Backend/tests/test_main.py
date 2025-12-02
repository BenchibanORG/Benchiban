from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app

client = TestClient(app)

# Teste para o endpoint raiz ("/")
def test_read_root(client: TestClient):
    """
    Testa se a rota raiz (/) está funcionando e retornando a mensagem correta.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API funcionando!"}

# Teste para o middleware de CORS
def test_cors_headers(client: TestClient):
    """
    Testa se o middleware de CORS aceita TODAS as origens permitidas.
    """
    # Lista exata das origens que definimos no main.py
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://benchiban.azurewebsites.net",
        "https://black-mud-07542d60f.3.azurestaticapps.net" 
    ]

    for origin in allowed_origins:
        headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        }
        
        # Faz a requisição OPTIONS (preflight) simulando cada origem
        # Ajustei para /api/auth/register pois seu main.py usa prefixo /api/auth
        response = client.options("/api/auth/register", headers=headers)
        
        # Verifica se o backend aceitou e devolveu a origem correta
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        print(f"CORS validado com sucesso para: {origin}")

def test_force_update_manual_success(mock_update_all_products: MagicMock):
    """
    Testa se a rota /api/admin/force-update:
    - Responde 200
    - Chama a função em background
    - Retorna mensagem correta
    """
    # Simula que a função foi chamada em background
    mock_update_all_products.return_value = None

    response = client.post("/api/admin/force-update")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Atualização forçada iniciada! O processo está rodando em segundo plano."
    assert "details" in data

    # Garante que a função foi chamada exatamente 1 vez em background
    mock_update_all_products.assert_called_once()

# === TESTE: Rota de force-update responde corretamente ===
# --- CORREÇÃO: O patch deve apontar para "app.main.update_all_products" ---
@patch("app.main.update_all_products", new_callable=AsyncMock)
def test_force_update_manual_success(mock_update_all_products):
    """
    Testa se a rota /api/admin/force-update:
    - Responde 200
    - Chama a função em background
    - Retorna mensagem correta
    """
    
    response = client.post("/api/admin/force-update")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Atualização forçada iniciada! O processo está rodando em segundo plano."
    
    # O TestClient do FastAPI roda background tasks sincrornamente após a resposta
    mock_update_all_products.assert_called_once()