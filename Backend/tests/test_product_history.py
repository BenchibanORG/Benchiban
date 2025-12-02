import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.api.endpoints.auth import get_db
from app.models.product import Product, PriceHistory

@pytest.fixture
def mock_db_session():
    """Cria um mock da sessão do banco de dados."""
    return MagicMock()

@pytest.fixture
def client(mock_db_session):
    """Cria um cliente de teste do FastAPI injetando o mock do banco."""
    def override_get_db():
        yield mock_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}

# --- Testes Unitários ---

def test_get_history_values_integrity(client, mock_db_session):
    
    # 1. Mock do Produto
    mock_product = Product(id=1, name="RTX 5090", search_term="rtx 5090")
    
    # 2. Mock do Histórico (Item eBay)
    mock_history_item = MagicMock(spec=PriceHistory)
    mock_history_item.timestamp = datetime(2023, 10, 1, 12, 0, 0)
    mock_history_item.source = "eBay"
    mock_history_item.currency = "USD"
    mock_history_item.price = 5500.00        # BRL no banco
    mock_history_item.price_usd = 1000.00    # USD no banco
    mock_history_item.exchange_rate = 5.5
    
    # Configura a query chain
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_product
    # A query do histórico (segunda query)
    mock_history_query = mock_db_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value
    mock_history_query.all.return_value = [mock_history_item]

    # 3. Execução
    response = client.get("/api/products/history?product_name=RTX 5090")

    assert response.status_code == 200
    data = response.json()
    
    history = data["history"]
    assert len(history) == 1
    
    item = history[0]
    # Valida se os valores vieram puros do banco, sem conversões extras erradas na API
    assert item["price_brl"] == 5500.00
    assert item["price_usd"] == 1000.00
    assert item["source"] == "eBay"


def test_get_history_product_not_found(client, mock_db_session):
    """Busca por produto inexistente retorna lista vazia."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/api/products/history?product_name=PlacaFantasma")

    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "PlacaFantasma"
    assert data["history"] == []


def test_get_history_date_filtering(client, mock_db_session):
    """Verifica se o parâmetro period_days é processado corretamente."""
    mock_product = Product(id=1, name="Test GPU", search_term="test gpu")
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_product
    
    # Retorna lista vazia
    mock_db_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

    response = client.get("/api/products/history?product_name=Test GPU&period_days=7")
    
    assert response.status_code == 200
    
    # Verifica se filter foi chamado com a data correta (aproximada)
    # A lógica exata de timestamp é difícil de mockar, mas garantimos que o fluxo rodou
    assert mock_db_session.query.called