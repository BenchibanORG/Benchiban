import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


# -----------------------------------------------------------
# TESTE: Cenário normal com resultados e melhor oferta válida
# -----------------------------------------------------------
def test_product_comparison_success():
    mock_ebay = [
        {"title": "Produto A", "price_brl": 1000.00, "source": "ebay"},
        {"title": "Produto B", "price_brl": 1500.00, "source": "ebay"},
    ]

    mock_amazon = [
        {"title": "Produto C", "price_brl": 900.00, "source": "amazon"},  # melhor oferta
        {"title": "Produto D", "price_brl": 2000.00, "source": "amazon"},
    ]

    with patch("app.api.endpoints.products.ebay_service.search_ebay_items", return_value=mock_ebay), \
         patch("app.api.endpoints.products.amazon_service.search_amazon_items", return_value=mock_amazon):

        response = client.get("/api/products/comparison?q=RTX+A6000")

        assert response.status_code == 200
        data = response.json()

        # Verifica se retornou tudo organizadinho
        assert "results_by_source" in data
        assert "overall_best_deal" in data

        best = data["overall_best_deal"]
        assert best["title"] == "Produto C"
        assert best["price_brl"] == 900.00
        assert best["source"] == "amazon"


# -----------------------------------------------------------------
# TESTE: Nenhum dos itens tem price_brl válido para comparação
# -----------------------------------------------------------------
def test_product_comparison_no_valid_prices():
    mock_ebay = [
        {"title": "A", "price_brl": None, "source": "ebay"},
    ]

    mock_amazon = [
        {"title": "B", "price_brl": None, "source": "amazon"},
    ]

    with patch("app.api.endpoints.products.ebay_service.search_ebay_items", return_value=mock_ebay), \
         patch("app.api.endpoints.products.amazon_service.search_amazon_items", return_value=mock_amazon):

        response = client.get("/api/products/comparison?q=test")

        assert response.status_code == 200
        data = response.json()

        # Mesmo sem preços válidos, a API deve responder normalmente
        assert data["overall_best_deal"] is None


# -----------------------------------------------------
# TESTE: Nenhum resultado retornado por nenhum serviço
# -----------------------------------------------------
def test_product_comparison_no_results():
    with patch("app.api.endpoints.products.ebay_service.search_ebay_items", return_value=[]), \
         patch("app.api.endpoints.products.amazon_service.search_amazon_items", return_value=[]):

        response = client.get("/api/products/comparison?q=qualquercoisa")

        assert response.status_code == 200
        data = response.json()

        assert data["results_by_source"]["ebay"] == []
        assert data["results_by_source"]["amazon"] == []
        assert data["overall_best_deal"] is None
