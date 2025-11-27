from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ProductItem(BaseModel):
    """Define a estrutura de um único item de produto encontrado."""
    title: Optional[str] = None
    price_original: Optional[float] = None # Valor bruto (ex: 15000.00)
    currency_original: Optional[str] = None # Moeda original ("BRL" ou "USD")
    price_usd: Optional[float] = None    # Referência em Dólar
    price_brl: Optional[float] = None    # Referência em Real (calculado)
    seller_rating: Optional[float] = None
    seller_username: Optional[str] = None
    link: Optional[str] = None
    source: str
    timestamp: Optional[datetime] = None

class ComparisonResponse(BaseModel):
    """
    Define a estrutura da resposta final da API de comparação.
    """
    results_by_source: Dict[str, List[ProductItem]]
    overall_best_deal: Optional[ProductItem] = None
    current_exchange_rate: Optional[float] = None