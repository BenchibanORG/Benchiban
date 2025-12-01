import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session
from app.services.product_updater import update_all_products, PRODUCTS_TO_MONITOR


# Helper para funções async
async def async_return(value):
    return value


@pytest.fixture
def mock_db_session():
    """Mock da SessionLocal usada pelo updater."""
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    return mock_db


@pytest.mark.asyncio
async def test_update_all_products_success(mock_db_session):
    """Fluxo completo funcionando: dólar → ebay → amazon → salvar no banco."""

    fake_product = MagicMock()
    fake_product.id = 1

    # Quando o updater fizer query(...).filter(...).first()
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    fake_results_ebay = [
        {"price": 100, "currency": "USD", "price_usd": 100, "title": "GPU TESTE-A", "source": "eBay"},
    ]

    fake_results_amazon = [
        {"price": 900, "currency": "BRL", "title": "GPU TESTE-B", "source": "Amazon"},
    ]

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db_session), \
         patch("app.services.product_updater.Product", return_value=fake_product), \
         patch("app.services.product_updater.PriceHistory"), \
         patch("app.services.product_updater.CurrencyService.get_usd_to_brl", return_value=4.95), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=fake_results_ebay), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", side_effect=lambda t: async_return(fake_results_amazon)):

        await update_all_products()

        # Verifica se produtos foram criados
        assert mock_db_session.add.call_count >= len(PRODUCTS_TO_MONITOR)

        # Verifica commits sendo chamados
        assert mock_db_session.commit.call_count >= len(PRODUCTS_TO_MONITOR)

        # Deve salvar entradas de histórica (PriceHistory)
        assert mock_db_session.add.call_count > 0


@pytest.mark.asyncio
async def test_update_all_products_no_results(mock_db_session):
    """APIs não retornam nada → nenhum PriceHistory salvo."""

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db_session), \
         patch("app.services.product_updater.CurrencyService.get_usd_to_brl", return_value=5.0), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=[]), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", side_effect=lambda t: async_return([])):

        await update_all_products()

        # Nenhum preço salvo
        assert mock_db_session.add.call_count == len(PRODUCTS_TO_MONITOR)  # Apenas os Product criados
        # Nenhum histórico salvo além dos produtos
        assert mock_db_session.commit.call_count == len(PRODUCTS_TO_MONITOR)


@pytest.mark.asyncio
async def test_update_all_products_api_error(mock_db_session):
    """Se eBay ou Amazon falham, updater não quebra e continua."""

    async def raise_error(*args, **kwargs):
        raise RuntimeError("API OFF")

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db_session), \
         patch("app.services.product_updater.CurrencyService.get_usd_to_brl", return_value=5.0), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", side_effect=raise_error), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", side_effect=raise_error):

        await update_all_products()

        # Mesmo com erro, o updater não salva PriceHistory
        assert mock_db_session.add.call_count <= len(PRODUCTS_TO_MONITOR)  # Só produtos criados
        # O commit ocorre apenas ao criar produtos
        assert mock_db_session.commit.call_count <= len(PRODUCTS_TO_MONITOR)


@pytest.mark.asyncio
async def test_update_all_products_currency_service_fallback(mock_db_session):
    """Se CurrencyService falhar, usa o fallback 5.4."""

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db_session), \
         patch("app.services.product_updater.CurrencyService.get_usd_to_brl", side_effect=Exception("API DEAD")), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=[]), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", side_effect=lambda t: async_return([])), \
         patch("app.services.product_updater.log.error") as mock_log:

        await update_all_products()

        # Confirma que chamada ao fallback ocorreu
        mock_log.assert_called()
