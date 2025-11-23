import pytest
from unittest.mock import patch, MagicMock, call
from app.services.product_updater import update_all_products, PRODUCTS_TO_MONITOR


@pytest.mark.asyncio
async def test_update_all_products_creates_product_and_saves_history():
    """Testa fluxo normal: produto não existe, APIs retornam resultados, histórico salvo."""

    # --- Mock Session, Query, Product ---
    mock_db = MagicMock()

    # mock da query(Product).filter().first()
    mock_db.query.return_value.filter.return_value.first.return_value = None  # Não existe ainda

    # Mock dos serviços externos
    fake_ebay_results = [
        {"price_brl": 10000, "source": "ebay", "link": "http://e1"}
    ]
    fake_amazon_results = [
        {"price_brl": 9500, "source": "amazon", "link": "http://a1"}
    ]

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=fake_ebay_results), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", return_value=fake_amazon_results), \
         patch("app.services.product_updater.Product") as MockProduct, \
         patch("app.services.product_updater.PriceHistory") as MockPrice:

        # Mock do Product() criado
        mock_product_instance = MagicMock()
        mock_product_instance.id = 1
        MockProduct.return_value = mock_product_instance

        await update_all_products()

        #  Produto deve ser criado para cada item da lista
        assert MockProduct.call_count == len(PRODUCTS_TO_MONITOR)

        #  Commit chamado após inserir produto e após inserir histórico
        assert mock_db.commit.call_count >= len(PRODUCTS_TO_MONITOR)

        # Histórico de preço deve ser salvo
        assert MockPrice.call_count == len(PRODUCTS_TO_MONITOR) * (
            len(fake_ebay_results) + len(fake_amazon_results)
        )


@pytest.mark.asyncio
async def test_update_all_products_when_product_exists():
    """Testa quando o produto já existe no banco."""
    
    mock_db = MagicMock()

    # mocka como se o produto já existisse
    mock_product_instance = MagicMock()
    mock_product_instance.id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = mock_product_instance

    fake_results = [{"price_brl": 5000, "source": "ebay", "link": "x"}]

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=fake_results), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", return_value=fake_results), \
         patch("app.services.product_updater.PriceHistory") as MockPrice:

        await update_all_products()

        # Nenhum Product criado (já existe)
        mock_db.add.assert_any_call(MockPrice.return_value)
        # PriceHistory deve ser criado
        assert MockPrice.call_count == len(PRODUCTS_TO_MONITOR) * 2


@pytest.mark.asyncio
async def test_update_all_products_no_results():
    """Testa o caso de nenhuma API retornar resultados."""
    
    mock_db = MagicMock()

    mock_existing = MagicMock()
    mock_existing.id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=[]), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", return_value=[]):

        await update_all_products()

        # Nenhum history salvo
        mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_update_all_products_exception_handling():
    """Testa se rollback é chamado quando ocorre erro."""
    
    mock_db = MagicMock()

    # Força erro ao consultar
    mock_db.query.side_effect = Exception("DB error")

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db):

        await update_all_products()

        # Deve chamar rollback
        mock_db.rollback.assert_called_once()

        # Sessão deve ser fechada mesmo com erro
        mock_db.close.assert_called_once()
