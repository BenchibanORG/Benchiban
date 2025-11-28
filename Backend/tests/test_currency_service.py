import pytest
from unittest.mock import patch, MagicMock
from app.services.currency_service import CurrencyService
from datetime import datetime, timezone

# ---------------------------------------------------------
# FIXTURE: limpa o cache ANTES de cada teste
# ---------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_cache():
    CurrencyService._cached_rate = None
    CurrencyService._last_update = 0
    yield


# ---------------------------------------------------------
# TESTE 1 — Deve buscar a cotação da API Frankfurter
# ---------------------------------------------------------
@patch("app.services.currency_service.requests.get")
@patch("app.services.currency_service.time.time", return_value=1000)
def test_fetch_frankfurter_success(mock_time, mock_get):

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"rates": {"BRL": 5.00}}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    rate = CurrencyService.get_usd_to_brl()

    assert rate == 5.00
    assert CurrencyService._cached_rate == 5.00
    assert CurrencyService._last_update == 1000
    mock_get.assert_called_once()


# ---------------------------------------------------------
# TESTE 2 — Deve usar cache quando TTL ainda válido
# ---------------------------------------------------------
@patch("app.services.currency_service.time.time")
def test_cache_is_used(mock_time):

    CurrencyService._cached_rate = 5.10
    CurrencyService._last_update = 1000
    CurrencyService._CACHE_TTL = 3600

    mock_time.return_value = 1200  # ainda dentro do TTL

    rate = CurrencyService.get_usd_to_brl()

    assert rate == 5.10  # usou cache


# ---------------------------------------------------------
# TESTE 3 — force_refresh deve ignorar o cache
# ---------------------------------------------------------
@patch("app.services.currency_service.requests.get")
@patch("app.services.currency_service.time.time", return_value=2000)
def test_force_refresh_ignores_cache(mock_time, mock_get):

    # cache existente
    CurrencyService._cached_rate = 4.50
    CurrencyService._last_update = 1990

    # resposta nova
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"rates": {"BRL": 5.20}}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    rate = CurrencyService.get_usd_to_brl(force_refresh=True)

    assert rate == 5.20
    assert CurrencyService._cached_rate == 5.20  # cache atualizado


# ---------------------------------------------------------
# TESTE 4 — Frankfurter falha → deve chamar AwesomeAPI
# ---------------------------------------------------------
@patch("app.services.currency_service.requests.get")
@patch("app.services.currency_service.time.time", return_value=3000)
def test_fallback_to_awesomeapi(mock_time, mock_get):

    # Frankfurter falha
    mock_get.side_effect = [
        Exception("Frankfurter down"),
        MagicMock(
            json=lambda: {"USDBRL": {"bid": "5.30"}},
            raise_for_status=lambda: None
        )
    ]

    rate = CurrencyService.get_usd_to_brl()

    assert rate == 5.30
    assert CurrencyService._cached_rate == 5.30
    assert CurrencyService._last_update == 3000
    assert mock_get.call_count == 2  # tentou 2 APIs


# ---------------------------------------------------------
# TESTE 5 — Falha total → deve lançar Exception
# ---------------------------------------------------------
@patch("app.services.currency_service.requests.get", side_effect=Exception("Erro total"))
def test_total_failure_raises_exception(mock_get):
    with pytest.raises(Exception):
        CurrencyService.get_usd_to_brl(force_refresh=True)


# ---------------------------------------------------------
# TESTE 6 — get_last_update_timestamp retorna datetime
# ---------------------------------------------------------
def test_last_update_timestamp():

    CurrencyService._last_update = 4000

    ts = CurrencyService.get_last_update_timestamp()

    assert isinstance(ts, datetime)
    assert ts.tzinfo == timezone.utc
    assert ts.timestamp() == 4000


# ---------------------------------------------------------
# TESTE 7 — Quando sem updates ainda, timestamp deve ser None
# ---------------------------------------------------------
def test_last_update_none():
    CurrencyService._last_update = 0
    assert CurrencyService.get_last_update_timestamp() is None
