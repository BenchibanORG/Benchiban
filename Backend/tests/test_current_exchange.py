import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Importa sua aplicação principal
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_timestamp():
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


# --------------------------
#  TESTE DE SUCESSO
# --------------------------
def test_get_current_exchange_rate_success(mock_timestamp):

    with patch("app.services.currency_service.CurrencyService.get_usd_to_brl") as mock_rate, \
         patch("app.services.currency_service.CurrencyService.get_last_update_timestamp") as mock_time:

        mock_rate.return_value = 4.95
        mock_time.return_value = mock_timestamp

        response = client.get("/api/exchange-rate/")

        assert response.status_code == 200

        data = response.json()

        assert data["currency_from"] == "USD"
        assert data["currency_to"] == "BRL"
        assert data["rate"] == 4.95
        assert datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")) == mock_timestamp

# --------------------------
#  TESTE Fallback do timestamp
# --------------------------
def test_get_current_exchange_rate_timestamp_fallback():

    with patch("app.services.currency_service.CurrencyService.get_usd_to_brl") as mock_rate, \
         patch("app.services.currency_service.CurrencyService.get_last_update_timestamp") as mock_time:

        mock_rate.return_value = 5.02
        mock_time.return_value = None  # Força fallback

        response = client.get("/api/exchange-rate/")

        assert response.status_code == 200

        data = response.json()

        assert data["currency_from"] == "USD"
        assert data["currency_to"] == "BRL"
        assert data["rate"] == 5.02

        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)  # ISO string


# --------------------------
#  TESTE DE ERRO
# --------------------------
def test_get_current_exchange_rate_error():

    with patch("app.services.currency_service.CurrencyService.get_usd_to_brl") as mock_rate:
        mock_rate.side_effect = Exception("API offline")

        response = client.get("/api/exchange-rate/")

        assert response.status_code == 503

        data = response.json()
        assert "Serviço de cotação indisponível" in data["detail"]