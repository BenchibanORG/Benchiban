import requests
import time
from loguru import logger as log

class CurrencyService:
    _cached_rate = None
    _last_update = 0
    _CACHE_TTL = 3600

    @classmethod
    def get_usd_to_brl(cls) -> float:
        current_time = time.time()
        
        # Retorna cache se ainda for válido
        if cls._cached_rate and (current_time - cls._last_update < cls._CACHE_TTL):
            return cls._cached_rate

        # Tenta API Principal (Frankfurter)
        try:
            rate = cls._fetch_frankfurter()
            cls._update_cache(rate)
            return rate
        except Exception as e:
            log.warning(f"Falha na Frankfurter API: {e}. Tentando Fallback...")

        # Tenta Fallback (AwesomeAPI)
        try:
            rate = cls._fetch_awesomeapi()
            cls._update_cache(rate)
            return rate
        except Exception as e:
            log.error(f"Falha em ambas APIs de cotação: {e}")
            # Se tudo falhar, retorna o último cache conhecido ou levanta erro
            if cls._cached_rate:
                return cls._cached_rate
            raise Exception("Não foi possível obter cotação USD/BRL no momento.")

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