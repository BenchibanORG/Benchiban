from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class ProductItem(BaseModel):
    """Define a estrutura de um único item de produto encontrado."""
    title: Optional[str] = None
    price_usd: Optional[float] = None
    price_brl: Optional[float] = None
    price_original: Optional[float] = None
    currency_original: Optional[str] = None
    currency: Optional[str] = None
    seller_rating: Optional[float] = None
    seller_username: Optional[str] = None
    seller: Optional[str] = None
    link: Optional[str] = None
    source: str
    timestamp: Optional[Any] = None

class ComparisonResponse(BaseModel):
    """
    Define a estrutura da resposta final da API de comparação.
    """
    results_by_source: Dict[str, List[ProductItem]]
    overall_best_deal: Optional[ProductItem] = None
    current_exchange_rate: Optional[float] = None
    exchange_rate_timestamp: Optional[str] = None 