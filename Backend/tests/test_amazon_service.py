import pytest
from unittest.mock import MagicMock, patch
from app.services.amazon_service import (
    _parse_preco_para_float,
    _parse_search_page,
    search_amazon_items
)
from scrapfly import ScrapeApiResponse


# -------------------------------------------------------------
# TESTES UNITÁRIOS PARA _parse_preco_para_float
# -------------------------------------------------------------
def test_parse_preco_para_float_valid():
    assert _parse_preco_para_float("R$ 1.234,56") == 1234.56


def test_parse_preco_para_float_invalid():
    assert _parse_preco_para_float("abc") is None
    assert _parse_preco_para_float("") is None
    assert _parse_preco_para_float(None) is None


# -------------------------------------------------------------
# TESTES UNITÁRIOS PARA _parse_search_page
# -------------------------------------------------------------
def test_parse_search_page_basic():
    mock_result = MagicMock()
    mock_box = MagicMock()

    # Título compatível com TODAS as palavras obrigatórias
    mock_box.css.return_value.get.side_effect = [
        "Placa NVIDIA RTX 5090 32GB Ultra",
        "/rtx5090-ultra",
        "R$ 12.000,00"
    ]

    mock_result.selector.css.return_value = [mock_box]

    result = _parse_search_page(
        mock_result,
        ["placa", "rtx", "5090", "32gb"]
    )

    assert len(result) == 1
    assert result[0]["title"] == "Placa NVIDIA RTX 5090 32GB Ultra"
    assert result[0]["price_brl"] == 12000.00


# -------------------------------------------------------------
# TESTES PARA search_amazon_items
# -------------------------------------------------------------
@patch("app.services.amazon_service.SCRAPFLY.scrape")
def test_search_amazon_items_success(mock_scrape):
    mock_result = MagicMock()
    mock_box = MagicMock()

    # Agora o título contém TODAS as palavras obrigatórias:
    # placa / rtx / 5090 / 32gb
    mock_box.css.return_value.get.side_effect = [
        "Placa NVIDIA RTX 5090 32GB Ultra",
        "/rtx5090-ultra",
        "R$ 12.000,00"
    ]

    mock_result.selector.css.return_value = [mock_box]
    mock_scrape.return_value = mock_result

    results = search_amazon_items("NVIDIA RTX 5090 32GB")

    assert len(results) == 1
    assert results[0]["price_brl"] == 12000.00
    assert "Placa NVIDIA RTX 5090 32GB Ultra" in results[0]["title"]


@patch("app.services.amazon_service.SCRAPFLY.scrape")
def test_search_amazon_items_no_config(mock_scrape):
    """Se mandar query que não está no AMAZON_SEARCH_CONFIG, deve retornar lista vazia."""
    results = search_amazon_items("Produto Inexistente")
    assert results == []


# -------------------------------------------------------------
# Este é o teste que escolhe apenas 3 mais baratos
# -------------------------------------------------------------
@patch("app.services.amazon_service.SCRAPFLY.scrape")
def test_search_amazon_items_returns_only_3_cheapest(mock_scrape):
    mock_result = MagicMock()

    def mock_box_factory(title, link, price):
        box = MagicMock()
        # Título ajustado para conter TODAS as palavras obrigatórias
        full_title = f"Placa {title} 32GB"
        box.css.return_value.get.side_effect = [
            full_title,
            link,
            price
        ]
        return box

    mock_result.selector.css.return_value = [
        mock_box_factory("RTX 5090 Modelo 1", "/a", "R$ 15.000,00"),
        mock_box_factory("RTX 5090 Modelo 2", "/b", "R$ 12.000,00"),
        mock_box_factory("RTX 5090 Modelo 3", "/c", "R$ 10.000,00"),
        mock_box_factory("RTX 5090 Modelo 4", "/d", "R$ 9.000,00"),
    ]

    mock_scrape.return_value = mock_result

    results = search_amazon_items("NVIDIA RTX 5090 32GB")

    assert len(results) == 3
    prices = [item["price_brl"] for item in results]

    # Verifica que são os 3 mais baratos
    assert prices == sorted(prices)
    assert 9000.00 in prices
    assert 10000.00 in prices
    assert 12000.00 in prices


# -------------------------------------------------------------
# Teste de exceção no scraper
# -------------------------------------------------------------
@patch("app.services.amazon_service.SCRAPFLY.scrape", side_effect=Exception("erro"))
def test_search_amazon_items_scrape_error(mock_scrape):
    results = search_amazon_items("NVIDIA RTX 5090 32GB")
    assert results == []
