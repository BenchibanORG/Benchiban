from pydantic import BaseModel
from datetime import datetime

class ExchangeRateResponse(BaseModel):
    """
    Define o formato da resposta da cotação atual.
    """
    currency_from: str
    currency_to: str
    rate: float
    timestamp: datetime