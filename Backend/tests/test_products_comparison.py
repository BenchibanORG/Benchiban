import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from app.main import app
from app.models.product import Product, PriceHistory
from app.api.endpoints.auth import get_db

client = TestClient(app)

# ===============================
# HELPERS PARA MOCKS DE QUERY
# ===============================

def make_single_timestamp_query_mock(ts):
    """
    Mock da query que busca o último registro de timestamp:
    db.query(PriceHistory.timestamp).order_by(desc()).first()
    """
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_order = MagicMock()
    
    # Configura a corrente: query.filter(...).order_by(...).first()
    mock_query.filter.return_value = mock_filter
    mock_filter.order_by.return_value = mock_order
    
    # O endpoint espera uma tupla (timestamp,) ou None se não achar nada
    mock_order.first.return_value = (ts,) if ts else None
    
    return mock_query

def make_history_batch_query_mock(history_items):
    """
    Mock da query que pega o lote de histórico (comparison):
    db.query(PriceHistory).filter(...).filter(...).order_by(...).all()
    """
    mock_query = MagicMock()
    mock_filter_1 = MagicMock()
    mock_filter_2 = MagicMock()
    mock_order = MagicMock()

    # Simula a corrente: query.filter(...).filter(...).order_by(...).all()
    mock_query.filter.return_value = mock_filter_1
    mock_filter_1.filter.return_value = mock_filter_2
    mock_filter_2.order_by.return_value = mock_order
    mock_order.all.return_value = history_items

    return mock_query


# ============================================================
# TESTE 1: Produto existe E possui histórico recente → NÃO deve atualizar
# ============================================================
@pytest.mark.asyncio
async def test_comparison_returns_cached_results():
    mock_db = MagicMock()

    # Dados Mockados (Timestamp RECENTE para evitar update)
    ts_now = datetime.now(timezone.utc)
    product = Product(id=1, name="RTX 5090", search_term="RTX 5090")
    
    # CRÍTICO: Mockar o relationship history para não disparar query real
    product.history = []  # será preenchido com o item abaixo

    history_ebay = PriceHistory(
        id=1, product_id=1, price=10000, currency="BRL",
        source="eBay", link="http://e.com", timestamp=ts_now,
        exchange_rate=5.0, price_usd=2000,
        original_title="RTX 5090", seller_name="Seller", seller_rating=5.0
    )
    
    # Agora sim: product tem histórico!
    product.history = [history_ebay]  # ← ESSA LINHA FAZ O TESTE PASSAR

    # Mocks de query
    mock_product_query = MagicMock()
    mock_product_query.filter.return_value.first.return_value = product

    mock_timestamp_query = make_single_timestamp_query_mock(ts_now)
    mock_batch_query = make_history_batch_query_mock([history_ebay])

    def query_side_effect(*args, **kwargs):
        queried = args[0]
        if queried is Product:
            return mock_product_query
        if queried is PriceHistory:
            return mock_batch_query
        if str(queried).endswith('.timestamp'):
            return mock_timestamp_query
        return MagicMock()

    mock_db.query.side_effect = query_side_effect

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with patch("app.api.endpoints.products.update_all_products", new=AsyncMock()) as mock_update, \
             patch("app.services.currency_service.CurrencyService.get_usd_to_brl", return_value=5.0), \
             patch("app.services.currency_service.CurrencyService.get_last_update_timestamp", return_value=ts_now):

            response = client.get("/api/products/comparison?q=RTX 5090")
            data = response.json()

            assert response.status_code == 200
            mock_update.assert_not_called()  # ← AGORA PASSA!
            assert data["overall_best_deal"]["price_brl"] == 10000.0

    finally:
        app.dependency_overrides.clear()


# ============================================================
# TESTE 2: Produto não existe → DEVE atualizar
# ============================================================
@pytest.mark.asyncio
async def test_comparison_triggers_update_for_missing_product():
    mock_db = MagicMock()
    
    # Produto não existe na primeira chamada
    mock_product_query = MagicMock()
    mock_product_query.filter.return_value.first.return_value = None
    
    # Como o produto é a primeira coisa consultada, se retornar None ele já dispara o update.
    mock_db.query.return_value = mock_product_query

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with patch("app.api.endpoints.products.update_all_products", new=AsyncMock()) as mock_update, \
             patch("app.services.currency_service.CurrencyService.get_usd_to_brl", return_value=5.0), \
             patch("app.services.currency_service.CurrencyService.get_last_update_timestamp", return_value=None):

            # Faz a requisição
            client.get("/api/products/comparison?q=RTX A6000")
            
            # TESTE CRÍTICO: Se não achou produto, DEVE chamar o update
            mock_update.assert_awaited()

    finally:
        app.dependency_overrides = {}


# ============================================================
# TESTE 3: Produto existe MAS sem histórico → DEVE atualizar
# ============================================================
@pytest.mark.asyncio
async def test_comparison_triggers_update_when_no_history():
    mock_db = MagicMock()
    ts_now = datetime.now(timezone.utc)

    # 1. Produto existe
    product = Product(id=3, name="RTX 9000", search_term="RTX 9000")
    mock_product_query = MagicMock()
    mock_product_query.filter.return_value.first.return_value = product
    
    # 2. Mas histórico (timestamp query) retorna None (sem dados)
    mock_timestamp_query = make_single_timestamp_query_mock(None)

    def query_side_effect(*args):
        model_or_column = args[0]
        if model_or_column is Product: 
            return mock_product_query
        
        # Detecta query da coluna timestamp
        if hasattr(model_or_column, 'key') and model_or_column.key == 'timestamp': 
            return mock_timestamp_query
            
        return MagicMock()

    mock_db.query.side_effect = query_side_effect
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with patch("app.api.endpoints.products.update_all_products", new=AsyncMock()) as mock_update, \
             patch("app.services.currency_service.CurrencyService.get_usd_to_brl", return_value=5.0), \
             patch("app.services.currency_service.CurrencyService.get_last_update_timestamp", return_value=ts_now):

            client.get("/api/products/comparison?q=RTX 9000")
            
            # TESTE CRÍTICO: Produto sem histórico -> Update
            mock_update.assert_awaited()

    finally:
        app.dependency_overrides = {}