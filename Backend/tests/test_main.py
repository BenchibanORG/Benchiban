from fastapi.testclient import TestClient

# Teste para o endpoint raiz ("/")
def test_read_root(client: TestClient):
    """
    Testa se a rota raiz (/) está funcionando e retornando a mensagem correta.
    """
    
    # Act: Faz uma requisição GET para a rota "/"
    response = client.get("/")
    
    # Assert: Verifica se a resposta está correta
    assert response.status_code == 200
    assert response.json() == {"message": "API funcionando!"}

# Teste para o middleware de CORS
def test_cors_headers(client: TestClient):
    """
    Testa se o middleware de CORS está configurado corretamente,
    respondendo a uma requisição de preflight (OPTIONS).
    """
    # Arrange: Define os cabeçalhos de uma requisição de preflight
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    }
    
    # Act: Faz uma requisição OPTIONS para uma rota qualquer
    response = client.options("/auth/register", headers=headers)
    
    # Assert: Verifica se a resposta contém os cabeçalhos CORS corretos
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"