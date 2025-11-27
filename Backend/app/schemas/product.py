from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ProductItem(BaseModel):
    """Define a estrutura de um único item de produto encontrado."""
    title: Optional[str] = None
    price_usd: Optional[float] = None
    price_brl: Optional[float] = None
    currency: Optional[str] = None
    seller_rating: Optional[float] = None
    seller_username: Optional[str] = None
    link: Optional[str] = None
    source: str

class ComparisonResponse(BaseModel):
    results_by_source: Dict[str, List[ProductItem]]
    overall_best_deal: Optional[ProductItem] = None
