import pytest
import math
import requests
from unittest.mock import patch, MagicMock

from app.services.ebay_service import search_ebay_items


# -----------------------------------------------------------
# Testes da função search_ebay_items
# -----------------------------------------------------------

@patch("app.services.ebay_service.CurrencyService.get_usd_to_brl")
@patch("app.services.ebay_service.ebay_token_manager.get_valid_ebay_token")
@patch("app.services.ebay_service.requests.get")
def test_search_ebay_items_success(mock_get, mock_token, mock_rate):
    # Mock do token válido
    mock_token.return_value = "fake_ebay_token"

    # Mock da taxa de conversão USD -> BRL usada dentro da função
    mock_rate.return_value = 5.00

    # Mock da resposta JSON da API eBay
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "itemSummaries": [
            {
                "title": "GPU X",
                "price": {"value": "100.0", "currency": "USD"},
                "seller": {"feedbackPercentage": "99.5", "username": "best_seller"},
                "itemWebUrl": "https://example.com/item1"
            },
            {
                "title": "GPU Y",
                "price": {"value": "90.0", "currency": "USD"},
                "seller": {"feedbackPercentage": "98.0", "username": "good_seller"},
                "itemWebUrl": "https://example.com/item2"
            }
        ]
    }

    mock_get.return_value = mock_response

    results = search_ebay_items("GPU")

    # Deve retornar 2 resultados
    assert len(results) == 2

    # O primeiro deve ser o vendedor com maior feedback
    assert results[0]["title"] == "GPU X"
    assert results[0]["price"] == 100.0
    assert results[0]["currency"] == "USD"
    assert results[0]["price_usd"] == 100.0
    assert results[0]["seller_rating"] == 99.5
    assert results[0]["seller_username"] == "best_seller"

    # Verifica cálculo do preço estimado em BRL
    expected_brl = math.ceil(100.0 * 5.00 * 100) / 100
    assert results[0]["price_brl"] == expected_brl


@patch("app.services.ebay_service.ebay_token_manager.get_valid_ebay_token")
@patch("app.services.ebay_service.requests.get")
def test_search_ebay_items_empty(mock_get, mock_token):
    mock_token.return_value = "fake_ebay_token"

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"itemSummaries": []}

    mock_get.return_value = mock_response

    results = search_ebay_items("GPU")
    assert results == []


@patch("app.services.ebay_service.ebay_token_manager.get_valid_ebay_token")
@patch("app.services.ebay_service.requests.get")
def test_search_ebay_items_api_error(mock_get, mock_token):
    mock_token.return_value = "fake_ebay_token"

    # Simula falha da API eBay
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    
    results = search_ebay_items("GPU")

    assert results == []


@patch("app.services.ebay_service.requests.get")
def test_search_ebay_items_token_error(mock_get):
    # Simula erro ao obter token
    with patch("app.services.ebay_service.ebay_token_manager.get_valid_ebay_token",
               side_effect=Exception("token error")):
        results = search_ebay_items("GPU")

        assert results == []
