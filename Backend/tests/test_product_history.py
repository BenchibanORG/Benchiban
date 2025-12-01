import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.api.endpoints.auth import get_db
from app.models.product import Product, PriceHistory

@pytest.fixture
def mock_db_session():
    """Cria um mock da sessão do banco de dados para não precisar de banco real."""
    return MagicMock()

@pytest.fixture
def client(mock_db_session):
    """Cria um cliente de teste do FastAPI injetando o mock do banco."""
    # Sobrescreve a dependência get_db para retornar nosso mock
    def override_get_db():
        yield mock_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    # Limpa depois do teste
    app.dependency_overrides = {}

# --- Testes Unitários ---

def test_get_history_success_grouping(client, mock_db_session):
    """
    CENÁRIO: Busca por uma placa existente com histórico.
    EXPECTATIVA: 
    1. Retornar status 200.
    2. Retornar a estrutura correta (product_name, history).
    3. Testar a lógica de agrupamento (deve pegar o MENOR preço do minuto).
    """
    
    # 1. Mock do Produto Pai
    mock_product = Product(id=1, name="NVIDIA RTX 5090 32GB", search_term="rtx 5090")
    
    # Configura o mock para retornar este produto quando buscar por nome
    # O chain é: db.query().filter().first()
    # Usamos side_effect com lista se precisássemos de múltiplos retornos, 
    # mas aqui o primeiro retorno é suficiente.
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_product

    # 2. Mock do Histórico (Simulando dados "sujos" no banco)
    # Vamos criar 3 entradas para o MESMO minuto para testar se o código agrupa
    base_time = datetime(2025, 11, 28, 10, 0, 0, tzinfo=timezone.utc)
    
    history_entries = [
        # Entrada 1: eBay (Preço alto)
        PriceHistory(
            product_id=1, 
            price=15000.00, price_usd=3000.00, currency="BRL", source="eBay", 
            timestamp=base_time
        ),
        # Entrada 2: eBay (Preço menor no mesmo minuto - deve ser escolhido)
        PriceHistory(
            product_id=1, 
            price=14000.00, price_usd=2800.00, currency="BRL", source="eBay", 
            timestamp=base_time
        ),
        # Entrada 3: Amazon (Outra fonte, mesmo minuto)
        PriceHistory(
            product_id=1, 
            price=18000.00, price_usd=None, currency="BRL", source="Amazon", 
            timestamp=base_time
        )
    ]

    # Configura o mock para retornar essa lista quando buscar o histórico
    # O chain é complexo: db.query().filter().filter().order_by().all()
    # Mockamos a cadeia inteira para retornar nossa lista no final
    mock_db_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = history_entries

    # 3. Executa a Requisição
    response = client.get("/api/products/history?product_name=NVIDIA RTX 5090 32GB&period_days=30")

    # 4. Asserções (Validação)
    assert response.status_code == 200
    data = response.json()

    assert data["product_name"] == "NVIDIA RTX 5090 32GB"
    
    # Validação do Agrupamento:
    # Tínhamos 3 entradas, mas 2 eram do eBay no mesmo minuto. 
    # O código deve agrupar, resultando em 2 entradas finais (1 eBay + 1 Amazon).
    assert len(data["history"]) == 2 

    # Verifica se pegou o MENOR preço do eBay (2800 USD ao invés de 3000 USD)
    ebay_point = next(p for p in data["history"] if p["source"] == "eBay")
    assert ebay_point["price_usd"] == 2800.00
    assert ebay_point["price_brl"] == 14000.00
    
    # Verifica Amazon
    amazon_point = next(p for p in data["history"] if p["source"] == "Amazon")
    assert amazon_point["price_brl"] == 18000.00


def test_get_history_product_not_found(client, mock_db_session):
    """
    CENÁRIO: Busca por uma placa que não existe no banco.
    EXPECTATIVA: Retornar lista vazia (não erro 404/500), mas com o nome pesquisado.
    """
    # Configura mock para retornar None (não achou produto no primeiro filter)
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/api/products/history?product_name=PlacaFantasma")

    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "PlacaFantasma"
    assert data["history"] == []


def test_get_history_date_filtering(client, mock_db_session):
    """
    CENÁRIO: Valida se a rota aceita e processa o parâmetro 'period_days'.
    """
    mock_product = Product(id=1, name="Test GPU", search_term="test gpu")
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_product
    
    # Retorna lista vazia só para não quebrar fluxo e focar no status da requisição
    mock_db_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

    # Chama com 7 dias para garantir que o endpoint processa o argumento
    response = client.get("/api/products/history?product_name=Test GPU&period_days=7")

    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "Test GPU"
    # Se chegou aqui sem erro 422 (Unprocessable Entity), o parâmetro foi aceito corretamente.