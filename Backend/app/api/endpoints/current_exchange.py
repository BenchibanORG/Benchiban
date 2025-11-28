from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.services.currency_service import CurrencyService
from app.schemas.exchange_rate import ExchangeRateResponse

router = APIRouter()

@router.get("/", response_model=ExchangeRateResponse, description="Retorna a cotação atual do Dólar (USD) para Real (BRL)")
async def get_current_exchange_rate():
    """
    Endpoint dedicado para obter a cotação atual.
    """
    try:
        # 1. Obtém o valor da cotação
        rate = CurrencyService.get_usd_to_brl()
        
        # 2. Obtém a hora real da última atualização do cache
        last_update = CurrencyService.get_last_update_timestamp()

        # Se por algum motivo o cache estiver vazio (primeira chamada), usamos o agora como fallback
        final_timestamp = last_update if last_update else datetime.now(timezone.utc)
        
        return {
            "currency_from": "USD",
            "currency_to": "BRL",
            "rate": rate,
            "timestamp": final_timestamp 
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Serviço de cotação indisponível: {str(e)}")