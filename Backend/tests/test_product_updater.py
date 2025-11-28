import pytest
from unittest.mock import patch, MagicMock
from app.services.product_updater import update_all_products, PRODUCTS_TO_MONITOR


@pytest.mark.asyncio
async def test_update_all_products_creates_product_and_saves_history():
    """Testa fluxo normal: produto não existe, APIs retornam resultados, histórico salvo."""

    mock_db = MagicMock()

    # Produto ainda não existe
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Resultados FAKES contendo "price" (obrigatório)
    fake_ebay_results = [
        {"price": 10000, "currency": "USD", "source": "ebay", "link": "http://e1"}
    ]
    fake_amazon_results = [
        {"price": 9500, "currency": "BRL", "source": "amazon", "link": "http://a1"}
    ]

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=fake_ebay_results), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", return_value=fake_amazon_results), \
         patch("app.services.product_updater.Product") as MockProduct, \
         patch("app.services.product_updater.PriceHistory") as MockPrice:

        # Mock de product
        mock_product = MagicMock()
        mock_product.id = 1
        MockProduct.return_value = mock_product

        await update_all_products()

        # Produto deve ser criado para cada termo da lista
        assert MockProduct.call_count == len(PRODUCTS_TO_MONITOR)

        # PriceHistory deve ser criado para ebay + amazon
        expected_history_count = len(PRODUCTS_TO_MONITOR) * (len(fake_ebay_results) + len(fake_amazon_results))
        assert MockPrice.call_count == expected_history_count

        # Commit deve ser chamado várias vezes
        assert mock_db.commit.call_count >= len(PRODUCTS_TO_MONITOR)


@pytest.mark.asyncio
async def test_update_all_products_when_product_exists():
    """Testa quando o produto já existe no banco."""

    mock_db = MagicMock()

    mock_product = MagicMock()
    mock_product.id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = mock_product

    # Cada API retorna 1 resultado com price
    fake_results = [{"price": 5000, "source": "ebay", "link": "x"}]

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=fake_results), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", return_value=fake_results), \
         patch("app.services.product_updater.PriceHistory") as MockPrice:

        await update_all_products()

        # Product não deve ser criado, apenas history
        assert MockPrice.call_count == len(PRODUCTS_TO_MONITOR) * 2


@pytest.mark.asyncio
async def test_update_all_products_no_results():
    """Nenhuma API retorna resultados → nenhum histórico salvo."""

    mock_db = MagicMock()

    mock_product = MagicMock()
    mock_product.id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = mock_product

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=[]), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", return_value=[]):

        await update_all_products()

        # Nenhum history salvo
        mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_update_all_products_exception_handling():
    """Se ocorre erro, rollback deve ser chamado e sessão fechada."""

    mock_db = MagicMock()

    # Força erro
    mock_db.query.side_effect = Exception("DB error")

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db):

        await update_all_products()

        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()
