import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from app.main import app
from app.models.product import Product, PriceHistory
from app.api.endpoints.auth import get_db

client = TestClient(app)

# ===============================
# HELPERS PARA MOCKS DE QUERY
# ===============================

def make_single_timestamp_query_mock(ts):
    """Mock da query que faz:
       db.query(PriceHistory.timestamp).order_by(desc()).first()
    """
    mock_query = MagicMock()
    mock_order = MagicMock()
    mock_query.filter.return_value = mock_query   # compatibilidade
    mock_query.order_by.return_value = mock_order
    mock_order.first.return_value = (ts,)
    return mock_query

def make_history_batch_query_mock(history_items):
    """Mock da query que pega o lote do mesmo timestamp."""
    mock_query = MagicMock()
    mock_filter_1 = MagicMock()
    mock_filter_2 = MagicMock()

    mock_query.filter.return_value = mock_filter_1
    mock_filter_1.filter.return_value = mock_filter_2
    mock_filter_2.order_by.return_value = mock_filter_2
    mock_filter_2.all.return_value = history_items

    return mock_query


# ============================================================
# TESTE 1: Produto existe E possui histórico → NÃO deve atualizar
# ============================================================
@pytest.mark.asyncio
async def test_comparison_returns_cached_results():

    mock_db = MagicMock()

    # Produto existente
    ts_now = datetime.now(timezone.utc)
    product = Product(id=1, name="RTX 5090", search_term="RTX 5090")

    history_ebay = PriceHistory(
        id=1, product_id=1, price=10000, currency="BRL",
        source="ebay", link="http://e.com", timestamp=ts_now
    )
    history_amazon = PriceHistory(
        id=2, product_id=1, price=12000, currency="BRL",
        source="amazon", link="http://a.com", timestamp=ts_now
    )

    product.history = [history_ebay, history_amazon]

    # Query #1 — buscar produto
    mock_product_query = MagicMock()
    mock_product_query.filter.return_value.first.return_value = product

    # Query #2 — buscar último timestamp
    mock_timestamp_query = make_single_timestamp_query_mock(ts_now)

    # Query #3 — buscar lote de histórico
    mock_batch_query = make_history_batch_query_mock([history_ebay, history_amazon])

    def query_side_effect(model):
        if model is Product:
            return mock_product_query
        if model is PriceHistory.timestamp:
            return mock_timestamp_query
        if model is PriceHistory:
            return mock_batch_query
        raise RuntimeError(f"Query inesperada para {model}")

    mock_db.query.side_effect = query_side_effect

    # Override de DB
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with patch("app.api.endpoints.products.update_all_products", new=AsyncMock()) as mock_update, \
             patch("app.services.currency_service.CurrencyService.get_usd_to_brl", return_value=5.0), \
             patch("app.services.currency_service.CurrencyService.get_last_update_timestamp", return_value=ts_now):

            response = client.get("/api/products/comparison?q=RTX 5090")
            data = response.json()

            assert response.status_code == 200
            mock_update.assert_not_called()  # não deve atualizar

            assert data["overall_best_deal"]["price_brl"] == 10000.0
            assert len(data["results_by_source"]["ebay"]) == 1

    finally:
        app.dependency_overrides = {}


# ============================================================
# TESTE 2: Produto não existe → DEVE atualizar
# ============================================================
@pytest.mark.asyncio
async def test_comparison_triggers_update_for_missing_product():

    mock_db = MagicMock()

    # 1ª query retorna None → produto não existe
    # 2ª query retorna produto pós-update
    product_after = Product(id=2, name="RTX A6000", search_term="RTX A6000")
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        None,
        product_after
    ]

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with patch("app.api.endpoints.products.update_all_products", new=AsyncMock()) as mock_update, \
             patch("app.services.currency_service.CurrencyService.get_usd_to_brl", return_value=5.0), \
             patch("app.services.currency_service.CurrencyService.get_last_update_timestamp", return_value=None):

            response = client.get("/api/products/comparison?q=RTX A6000")
            assert response.status_code == 200

            mock_update.assert_awaited()

    finally:
        app.dependency_overrides = {}


# ============================================================
# TESTE 3: Produto existe MAS sem histórico → DEVE atualizar
# ============================================================
@pytest.mark.asyncio
async def test_comparison_triggers_update_when_no_history():

    mock_db = MagicMock()

    product = Product(id=3, name="RTX 9000", search_term="RTX 9000")
    product.history = []  # História vazia

    mock_product_query = MagicMock()
    mock_product_query.filter.return_value.first.return_value = product

    mock_db.query.side_effect = lambda model: mock_product_query if model is Product else MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with patch("app.api.endpoints.products.update_all_products", new=AsyncMock()) as mock_update, \
             patch("app.services.currency_service.CurrencyService.get_usd_to_brl", return_value=5.0), \
             patch("app.services.currency_service.CurrencyService.get_last_update_timestamp", return_value=None):

            response = client.get("/api/products/comparison?q=RTX 9000")
            data = response.json()

            assert response.status_code == 200
            mock_update.assert_awaited()

            assert data["results_by_source"]["ebay"] == []

    finally:
        app.dependency_overrides = {}
