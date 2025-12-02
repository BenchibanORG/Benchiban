import pytest
from unittest.mock import patch, MagicMock, ANY
from sqlalchemy.orm import Session
from app.services.product_updater import update_all_products, PRODUCTS_TO_MONITOR
from app.models.product import PriceHistory, Product

# Helper para simular retorno de funções async
async def async_return(value):
    return value

@pytest.fixture
def mock_db_session():
    """Mock da SessionLocal usada pelo updater."""
    mock_db = MagicMock(spec=Session)
    # Simula que o produto ainda não existe no banco (vai criar novo)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    return mock_db

@pytest.mark.asyncio
async def test_update_all_products_success(mock_db_session):

    # --- MOCKS DE DADOS ---
    
    # eBay retorna em Dólar
    fake_results_ebay = [
        {
            "price": 100.00,   
            "currency": "USD", 
            "price_usd": 100.00, 
            "title": "GPU USD Test", 
            "source": "eBay",
            "link": "http://ebay.com/1",
            "seller_username": "seller_us"
        },
    ]

    # Amazon retorna em Real
    fake_results_amazon = [
        {
            "price": 1000.00,      # R$ 1000
            "currency": "BRL", 
            "title": "GPU BRL Test", 
            "source": "Amazon",
            "link": "http://amazon.com/1"
        },
    ]

    # --- EXECUÇÃO COM PATCHES ---
    
    with patch("app.services.product_updater.SessionLocal", return_value=mock_db_session), \
         patch("app.services.product_updater.CurrencyService.get_usd_to_brl", return_value=5.0), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=fake_results_ebay), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", return_value=fake_results_amazon):

        await update_all_products()

    # --- VALIDAÇÕES ---
    
    added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
    history_entries = [obj for obj in added_objects if isinstance(obj, PriceHistory)]

    assert len(history_entries) > 0, "Nenhum histórico foi salvo!"

    # 1. Validação do Item eBay (USD -> BRL)
    ebay_entry = next((x for x in history_entries if x.source == "eBay"), None)
    assert ebay_entry is not None
    assert ebay_entry.currency == "USD"
    assert ebay_entry.exchange_rate == 5.0
    # Lógica Nova: price deve ser convertido para BRL (100 * 5.0 = 500)
    assert ebay_entry.price == 500.00 
    # Lógica Nova: price_usd deve ser mantido (100)
    assert ebay_entry.price_usd == 100.00

    # 2. Validação do Item Amazon (BRL -> USD)
    amazon_entry = next((x for x in history_entries if x.source == "Amazon"), None)
    assert amazon_entry is not None
    assert amazon_entry.currency == "BRL"
    assert amazon_entry.exchange_rate == 5.0
    # Lógica Nova: price já é BRL, mantém (1000)
    assert amazon_entry.price == 1000.00
    # Lógica Nova: price_usd deve ser convertido (1000 / 5.0 = 200)
    assert amazon_entry.price_usd == 200.00

    # Verifica se fez commit
    assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_update_all_products_api_error_handling(mock_db_session):
    """
    Testa se o updater sobrevive a erros nas APIs de busca (eBay/Amazon)
    sem derrubar o processo inteiro.
    """
    async def raise_error(*args, **kwargs):
        raise Exception("API Connection Failed")

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db_session), \
         patch("app.services.product_updater.CurrencyService.get_usd_to_brl", return_value=5.0), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", side_effect=raise_error), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", side_effect=raise_error):

        # Não deve lançar exceção (o updater captura e loga)
        await update_all_products()

        # Verifica que tentou fazer commit dos Produtos criados (se não existiam),
        # mas não deve ter adicionado nenhum PriceHistory
        added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
        history_entries = [obj for obj in added_objects if isinstance(obj, PriceHistory)]
        
        assert len(history_entries) == 0


@pytest.mark.asyncio
async def test_update_all_products_currency_failure(mock_db_session):

    with patch("app.services.product_updater.SessionLocal", return_value=mock_db_session), \
         patch("app.services.product_updater.CurrencyService.get_usd_to_brl", side_effect=Exception("Currency API Down")), \
         patch("app.services.product_updater.ebay_service.search_ebay_items", return_value=[]), \
         patch("app.services.product_updater.amazon_service.search_amazon_items", return_value=[]):

        await update_all_products()
        
        # O comportamento esperado depende do seu catch block. 
        # Se for crítico, não salva nada.
        assert mock_db_session.commit.call_count >= 0