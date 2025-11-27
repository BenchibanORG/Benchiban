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
        rate = CurrencyService.get_usd_to_brl()
        
        return {
            "currency_from": "USD",
            "currency_to": "BRL",
            "rate": rate,
            "timestamp": datetime.now(timezone.utc)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Serviço de cotação indisponível: {str(e)}")