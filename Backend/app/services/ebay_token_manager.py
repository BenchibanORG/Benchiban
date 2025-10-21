import requests
import base64
import json
import os
from datetime import datetime, timedelta, timezone

from app.core.config import settings

# Caminho para o arquivo que irá armazenar o token
TOKEN_FILE_PATH = "ebay_token.json"

def _read_token_from_file() -> dict | None:
    """Lê os dados do token do arquivo JSON."""
    if not os.path.exists(TOKEN_FILE_PATH):
        return None
    try:
        with open(TOKEN_FILE_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def _write_token_to_file(token_data: dict):
    """Escreve os dados do token no arquivo JSON."""
    with open(TOKEN_FILE_PATH, "w") as f:
        json.dump(token_data, f, indent=2)

def _refresh_access_token() -> str:
    """Usa o Refresh Token para obter um novo Access Token da API do eBay."""
    url = "https://api.ebay.com/identity/v1/oauth2/token"

    basic_auth = base64.b64encode(
        f"{settings.EBAY_APP_ID}:{settings.EBAY_CLIENT_SECRET}".encode()
    ).decode()
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic_auth}"
    }
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": settings.EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    print("--- A renovar Access Token do eBay... ---")
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # Lança um erro se a requisição falhar

    new_token_data = response.json()
    access_token = new_token_data["access_token"]
    expires_in = new_token_data["expires_in"]
    
    # Calcula o timestamp exato de expiração
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    # Salva o novo token e o seu tempo de expiração no arquivo
    _write_token_to_file({
        "access_token": access_token,
        "expires_at": expires_at.isoformat()
    })
    
    print("--- Novo Access Token do eBay obtido e salvo com sucesso! ---")
    return access_token

def get_valid_ebay_token() -> str:
    """
    Obtém um Access Token válido, renovando-o se estiver expirado ou ausente.
    Esta é a única função que outros serviços devem chamar.
    """
    token_info = _read_token_from_file()

    if token_info:
        expires_at = datetime.fromisoformat(token_info["expires_at"])
        # Verifica se o token expira nos próximos 5 minutos para renovar com antecedência
        if datetime.now(timezone.utc) < expires_at - timedelta(minutes=5):
            print("--- Usando Access Token do eBay existente (ainda válido). ---")
            return token_info["access_token"]

    # Se não há token, está expirado ou prestes a expirar, renova
    return _refresh_access_token()
