import pytest
from unittest.mock import MagicMock, patch
from app.services.amazon_service import (
    _parse_price_br,
    _parse_search_page,
    search_amazon_items,
)
from scrapfly import ScrapeApiResponse


# ============================================================
# TESTES PARA _parse_price_br
# ============================================================
def test_parse_price_br_valid():
    assert _parse_price_br("R$ 1.234,56") == 1234.56


def test_parse_price_br_invalid():
    assert _parse_price_br("abc") is None
    assert _parse_price_br("") is None
    assert _parse_price_br(None) is None


# ============================================================
# TESTES PARA _parse_search_page
# ============================================================
@patch("app.services.amazon_service.CurrencyService.get_usd_to_brl", return_value=5.00)
def test_parse_search_page_basic(mock_currency):
    mock_result = MagicMock()
    mock_box = MagicMock()

    # .css() é chamado várias vezes → precisamos mockar como um seletor
    mock_box.css.return_value.get.side_effect = [
        # título
        "Placa NVIDIA RTX 5090 32GB Ultra",
        # link
        "/rtx5090-ultra",
        # preço
        "R$ 12.000,00",
    ]

    mock_result.selector.css.return_value = [mock_box]

    results = _parse_search_page(
        mock_result,
        ["placa", "rtx", "5090", "32gb"]
    )

    assert len(results) == 1
    item = results[0]

    assert item["title"] == "Placa NVIDIA RTX 5090 32GB Ultra"
    assert item["price_brl"] == 12000.00
    assert item["currency"] == "BRL"
    assert item["price_usd"] == pytest.approx(2400.00)  # 12000 * 0.20
    assert item["link"] == "https://www.amazon.com.br/rtx5090-ultra"
    assert item["source"] == "Amazon"


# ============================================================
# TESTES PARA search_amazon_items
# ============================================================
@patch("app.services.amazon_service.CurrencyService.get_usd_to_brl", return_value=5.00)
@patch("app.services.amazon_service.SCRAPFLY.scrape")
def test_search_amazon_items_success(mock_scrape, mock_currency):
    mock_result = MagicMock()
    mock_box = MagicMock()

    mock_box.css.return_value.get.side_effect = [
        "Placa NVIDIA RTX 5090 32GB Ultra",
        "/rtx5090-ultra",
        "R$ 12.000,00",
    ]

    mock_result.selector.css.return_value = [mock_box]
    mock_scrape.return_value = mock_result

    results = search_amazon_items("NVIDIA RTX 5090 32GB")

    assert len(results) == 1
    assert results[0]["price_brl"] == 12000.00
    assert "Placa NVIDIA RTX 5090 32GB Ultra" in results[0]["title"]


def test_search_amazon_items_no_config():
    """Query não mapeada deve retornar lista vazia."""
    results = search_amazon_items("Produto inexistente")
    assert results == []


# ============================================================
# TESTE: retorna somente 3 mais baratos
# ============================================================
@patch("app.services.amazon_service.CurrencyService.get_usd_to_brl", return_value=5.00)
@patch("app.services.amazon_service.SCRAPFLY.scrape")
def test_search_amazon_items_returns_only_3_cheapest(mock_scrape, mock_currency):
    mock_result = MagicMock()

    def make_box(title, link, price):
        box = MagicMock()
        full_title = f"Placa {title} 32GB"
        box.css.return_value.get.side_effect = [
            full_title,
            link,
            price
        ]
        return box

    mock_result.selector.css.return_value = [
        make_box("RTX 5090 Modelo 1", "/a", "R$ 15.000,00"),
        make_box("RTX 5090 Modelo 2", "/b", "R$ 12.000,00"),
        make_box("RTX 5090 Modelo 3", "/c", "R$ 10.000,00"),
        make_box("RTX 5090 Modelo 4", "/d", "R$ 9.000,00"),
    ]

    mock_scrape.return_value = mock_result

    results = search_amazon_items("NVIDIA RTX 5090 32GB")

    assert len(results) == 3

    prices = [item["price_brl"] for item in results]

    assert prices == sorted(prices)
    assert 9000.00 in prices
    assert 10000.00 in prices
    assert 12000.00 in prices


# ============================================================
# TESTE: erro na chamada ao scraper
# ============================================================
@patch("app.services.amazon_service.SCRAPFLY.scrape", side_effect=Exception("erro"))
def test_search_amazon_items_scrape_error(mock_scrape):
    results = search_amazon_items("NVIDIA RTX 5090 32GB")
    assert results == []
