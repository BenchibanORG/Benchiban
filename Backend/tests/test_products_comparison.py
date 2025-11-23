import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from app.main import app
from app.models.product import Product, PriceHistory
from app.api.endpoints.auth import get_db  # <--- Import necessário para o override

client = TestClient(app)

# ===========================
# HELPERS PARA CONFIGURAÇÃO DE MOCKS
# ===========================

def make_product_query_mock(product):
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = product
    return mock_query

def make_price_history_query_mock(history_list):
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_order = MagicMock()
    mock_limit = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.order_by.return_value = mock_order
    mock_order.limit.return_value = mock_limit
    mock_limit.all.return_value = history_list
    return mock_query

# ============================================================
# TESTE 1: Produto existe E tem histórico → NÃO deve atualizar
# ============================================================
@pytest.mark.asyncio
async def test_comparison_returns_cached_results():
    
    mock_db = MagicMock()

    # 1. Cria os objetos simulados
    product = Product(id=1, name="NVIDIA RTX 5090 32GB", search_term="NVIDIA RTX 5090 32GB")
    
    history_ebay = PriceHistory(
        id=1, product_id=1, price=10000.0, currency="BRL",
        source="ebay", link="http://example.com/ebay",
        timestamp=datetime.now(timezone.utc)
    )
    history_amazon = PriceHistory(
        id=2, product_id=1, price=12000.0, currency="BRL",
        source="amazon", link="http://example.com/amazon",
        timestamp=datetime.now(timezone.utc)
    )

    # 2. Popula o relacionamento manualmente
    product.history = [history_ebay, history_amazon]

    # 3. Configura os mocks de query
    mock_product_query = make_product_query_mock(product)
    mock_history_query = make_price_history_query_mock([history_ebay, history_amazon])

    def query_side_effect(model):
        if model is Product:
            return mock_product_query
        if model is PriceHistory:
            return mock_history_query
        raise RuntimeError(f"Modelo inesperado na query: {model}")

    mock_db.query.side_effect = query_side_effect

    # --- CORREÇÃO: Usar dependency_overrides em vez de patch para o DB ---
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        # Patch apenas na função de update, pois ela é chamada dentro da lógica
        with patch("app.api.endpoints.products.update_all_products", new=AsyncMock()) as mock_update:

            response = client.get("/api/products/comparison?q=NVIDIA RTX 5090 32GB")
            data = response.json()

            assert response.status_code == 200

            # Verificação principal: O update NÃO deve ter sido chamado
            mock_update.assert_not_called()

            assert data["overall_best_deal"]["price_brl"] == 10000.0
            assert len(data["results_by_source"]["ebay"]) == 1
    
    finally:
        # Limpa o override para não afetar outros testes
        app.dependency_overrides = {}


# ============================================================
# TESTE 2: Produto não existe (ou novo) → DEVE atualizar
# ============================================================
@pytest.mark.asyncio
async def test_comparison_triggers_update_for_missing_product():

    mock_db = MagicMock()
    
    product_after_update = Product(id=1, name="RTX A6000", search_term="RTX A6000")
    
    # Simula: 1ª chamada retorna None, 2ª chamada retorna produto
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        None, product_after_update
    ]

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with patch("app.api.endpoints.products.update_all_products", new=AsyncMock()) as mock_update:

            response = client.get("/api/products/comparison?q=RTX A6000")
            assert response.status_code == 200

            # Verificação principal: O update DEVE ter sido chamado
            mock_update.assert_awaited()
    finally:
        app.dependency_overrides = {}


# ============================================================
# TESTE 3: Produto existe mas sem histórico → DEVE atualizar
# ============================================================
@pytest.mark.asyncio
async def test_comparison_returns_empty_when_no_history():

    mock_db = MagicMock()

    product = Product(id=1, name="RTX 9000", search_term="RTX 9000")
    product.history = []  # Histórico vazio

    mock_product_query = make_product_query_mock(product)
    mock_history_query = make_price_history_query_mock([])

    def query_side_effect(model):
        if model is Product:
            return mock_product_query
        if model is PriceHistory:
            return mock_history_query
        raise RuntimeError("Modelo inesperado")

    mock_db.query.side_effect = query_side_effect

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with patch("app.api.endpoints.products.update_all_products", new=AsyncMock()) as mock_update:

            response = client.get("/api/products/comparison?q=RTX 9000")
            data = response.json()

            assert response.status_code == 200
            
            # Deve atualizar pois histórico está vazio
            mock_update.assert_awaited()

            assert data["results_by_source"]["ebay"] == []
    finally:
        app.dependency_overrides = {}