from fastapi.testclient import TestClient

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