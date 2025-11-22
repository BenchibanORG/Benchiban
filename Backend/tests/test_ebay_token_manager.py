import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timedelta, timezone

import app.services.ebay_token_manager as manager


# ============================================================
# TESTE 1 — TOKEN VÁLIDO DEVE SER RETORNADO SEM RENOVAR
# ============================================================
def test_get_valid_token_returns_existing_token():
    fake_token = "TOKEN_VALIDO"
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

    mock_data = json.dumps({
        "access_token": fake_token,
        "expires_at": future_time
    })

    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_data)), \
         patch("app.services.ebay_token_manager._refresh_access_token") as mock_refresh:

        token = manager.get_valid_ebay_token()

        assert token == fake_token
        mock_refresh.assert_not_called()


# ============================================================
# TESTE 2 — TOKEN PRESTES A EXPIRAR → DEVE RENOVAR
# ============================================================
def test_get_valid_token_refreshes_when_expiring():
    expiring_time = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()

    mock_data = json.dumps({
        "access_token": "OLD_TOKEN",
        "expires_at": expiring_time
    })

    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_data)), \
         patch("app.services.ebay_token_manager._refresh_access_token", return_value="NEW_TOKEN") as mock_refresh:

        token = manager.get_valid_ebay_token()

        assert token == "NEW_TOKEN"
        mock_refresh.assert_called_once()


# ============================================================
# TESTE 3 — AUSÊNCIA DE TOKEN → DEVE RENOVAR
# ============================================================
def test_get_valid_token_refresh_when_no_file():
    with patch("os.path.exists", return_value=False), \
         patch("app.services.ebay_token_manager._refresh_access_token", return_value="TOKEN123") as mock_refresh:

        token = manager.get_valid_ebay_token()

        assert token == "TOKEN123"
        mock_refresh.assert_called_once()


# ============================================================
# TESTE 4 — ERRO AO DECODIFICAR JSON → DEVE RENOVAR
# ============================================================
def test_get_valid_token_refresh_when_invalid_json():
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="INVALID JSON")), \
         patch("app.services.ebay_token_manager._refresh_access_token", return_value="TOKEN_OK") as mock_refresh:

        token = manager.get_valid_ebay_token()

        assert token == "TOKEN_OK"
        mock_refresh.assert_called_once()


# ============================================================
# TESTE 5 — TESTE DA FUNÇÃO _refresh_access_token (SUCESSO)
# ============================================================
def test_refresh_access_token_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "TOKEN_TESTE_123",
        "expires_in": 7200
    }

    with patch(manager.__name__ + ".requests.post", return_value=mock_response) as mock_post, \
         patch(manager.__name__ + "._write_token_to_file") as mock_write, \
         patch(manager.__name__ + ".settings") as mock_settings:

        mock_settings.EBAY_APP_ID = "fake-id"
        mock_settings.EBAY_CLIENT_SECRET = "fake-secret"
        mock_settings.EBAY_REFRESH_TOKEN = "fake-refresh"

        result = manager._refresh_access_token()

    assert result == "TOKEN_TESTE_123"
    assert mock_post.called
    assert mock_write.called