import requests
import time
from datetime import datetime, timezone # <--- Import adicionado
from loguru import logger as log

class CurrencyService:
    _cached_rate = None
    _last_update = 0
    _CACHE_TTL = 3600

    @classmethod
    def get_usd_to_brl(cls, force_refresh: bool = False) -> float:
        
        #Força a busca na API de câmbio
        current_time = time.time()
        
        # Se NÃO for forçado e o cache for válido, usa o cache
        if not force_refresh and cls._cached_rate and (current_time - cls._last_update < cls._CACHE_TTL):
            return cls._cached_rate

        # Se for forçado ou cache expirou, busca novo
        log.info(f"Buscando nova cotação... (Force Refresh: {force_refresh})")

        # 1. Tenta API Principal (Frankfurter)
        try:
            rate = cls._fetch_frankfurter()
            cls._update_cache(rate)
            return rate
        except Exception as e:
            log.warning(f"Falha na Frankfurter API: {e}. Tentando Fallback...")

        # 2. Tenta Fallback (AwesomeAPI - BR)
        try:
            rate = cls._fetch_awesomeapi()
            cls._update_cache(rate)
            return rate
        except Exception as e:
            log.error(f"Falha Crítica nas APIs de cotação: {e}")
            if cls._cached_rate:
                return cls._cached_rate
            raise Exception("Serviço de cotação indisponível.")

    @classmethod
    def get_last_update_timestamp(cls):
        """Retorna o datetime da última atualização do cache."""
        if cls._last_update == 0:
            return None
        # Converte timestamp UNIX para objeto datetime com timezone UTC
        return datetime.fromtimestamp(cls._last_update, tz=timezone.utc)

    @classmethod
    def _fetch_frankfurter(cls) -> float:
        url = "https://api.frankfurter.app/latest?from=USD&to=BRL"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return float(resp.json()["rates"]["BRL"])

    @classmethod
    def _fetch_awesomeapi(cls) -> float:
        url = "https://economia.awesomeapi.com.br/last/USD-BRL"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return float(resp.json()["USDBRL"]["bid"])

    @classmethod
    def _update_cache(cls, rate: float):
        cls._cached_rate = rate
        cls._last_update = time.time()
        log.info(f"Cotação USD/BRL atualizada: {rate}")