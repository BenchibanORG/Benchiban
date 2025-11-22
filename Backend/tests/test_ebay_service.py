import pytest
import math, requests
from unittest.mock import patch, MagicMock

from app.services.ebay_service import search_ebay_items, get_usd_to_brl_rate


# -----------------------------------------------------------
# Teste da função get_usd_to_brl_rate
# -----------------------------------------------------------
@patch("app.services.ebay_service.requests.get")
def test_get_usd_to_brl_rate_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"rates": {"BRL": 5.25}}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    rate = get_usd_to_brl_rate()

    assert rate == 5.25
    mock_get.assert_called_once()


@patch("app.services.ebay_service.requests.get")
def test_get_usd_to_brl_rate_failure(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("API down")

    rate = get_usd_to_brl_rate()

    assert rate is None


# -----------------------------------------------------------
# Testes da função search_ebay_items
# -----------------------------------------------------------

@patch("app.services.ebay_service.get_usd_to_brl_rate")
@patch("app.services.ebay_service.ebay_token_manager.get_valid_ebay_token")
@patch("app.services.ebay_service.requests.get")
def test_search_ebay_items_success(mock_get, mock_token, mock_rate):
    # Mock do token válido
    mock_token.return_value = "fake_ebay_token"

    # Mock da taxa de conversão USD -> BRL
    mock_rate.return_value = 5.00

    # Mock da resposta da API do eBay
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

    assert len(results) == 2
    assert results[0]["title"] == "GPU X"
    assert results[0]["price_usd"] == 100.0
    assert results[0]["price_brl"] == math.ceil(100.0 * 5.00 * 100) / 100
    assert results[0]["seller_rating"] == 99.5
    assert results[0]["seller_username"] == "best_seller"


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

    # Simula exceção na API
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    
    results = search_ebay_items("GPU")

    assert results == []
