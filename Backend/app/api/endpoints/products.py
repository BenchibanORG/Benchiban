from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
import math
from datetime import timedelta
from app.api.endpoints.auth import get_db
from app.models.product import Product, PriceHistory
from app.services.product_updater import update_all_products
from app.services.currency_service import CurrencyService
from app.schemas.product import ComparisonResponse 

router = APIRouter()

# Adicionado response_model=ComparisonResponse
@router.get("/comparison", response_model=ComparisonResponse)
async def get_product_comparison(
    q: str = Query(..., description="O termo de busca para o produto, ex: 'NVIDIA RTX 5090 32GB'"),
    db: Session = Depends(get_db)
):
    print(f"\n--- Usuário buscou: '{q}' ---")

    # 1. OBTER COTAÇÃO ATUAL
    try:
        usd_rate = CurrencyService.get_usd_to_brl()
    except Exception as e:
        print(f"Erro ao obter cotação: {e}")
        usd_rate = 0.0

    # 2. TENTA BUSCAR NO BANCO
    product = db.query(Product).filter(Product.search_term == q).first()
    
    if not product or not product.history:
        print("--- Produto novo ou sem dados. Atualizando... ---")
        await update_all_products()
        product = db.query(Product).filter(Product.search_term == q).first()

    # 3. RECUPERA APENAS O ÚLTIMO LOTE DE DADOS
    latest_history = []
    if product:
        last_entry = db.query(PriceHistory.timestamp)\
            .filter(PriceHistory.product_id == product.id)\
            .order_by(desc(PriceHistory.timestamp))\
            .first()

        if last_entry:
            last_ts = last_entry[0]
            time_window = last_ts - timedelta(minutes=2)

            latest_history = db.query(PriceHistory)\
                .filter(PriceHistory.product_id == product.id)\
                .filter(PriceHistory.timestamp >= time_window)\
                .order_by(desc(PriceHistory.timestamp))\
                .all()

    # 4. FORMATA A RESPOSTA
    results_by_source = {
        "ebay": [],
        "amazon": []
    }
    
    for h in latest_history:
        price_usd = h.price_usd
        calculated_brl = 0.0
    
        # Lógica de conversão inicial
        if h.currency == "BRL":
            # Amazon BR: O preço real é o próprio
            calculated_brl = h.price
        elif price_usd and usd_rate > 0:
            # eBay USD: Converte usando a cotação DE AGORA
            calculated_brl = math.ceil((price_usd * usd_rate) * 100) / 100

        item = {
            "title": h.original_title if h.original_title else product.name,
            "seller": h.seller_name,
            "seller_username": h.seller_name,
            "rating": h.seller_rating,
            "price_original": h.price,
            "currency_original": h.currency,
            "price_usd": price_usd,
            "price_brl": calculated_brl, # Valor base para comparação
            "source": h.source,
            "link": getattr(h, "link", "#"), 
            "timestamp": h.timestamp
        }

        source_key = h.source.lower()
        if "amazon" in source_key: 
            results_by_source["amazon"].append(item)
        elif "ebay" in source_key:
            results_by_source["ebay"].append(item)

    # --- Ordenação baseada em REAIS (BRL) ---
    def sort_by_price(item):
 
        # Comparamos Amazon (fixo) vs eBay (convertido agora).
        return item['price_brl'] if item['price_brl'] else float('inf')

    results_by_source["amazon"].sort(key=sort_by_price)
    results_by_source["ebay"].sort(key=sort_by_price)

    # 5. MELHOR OFERTA GERAL
    overall_best_deal = None
    all_items = results_by_source["amazon"] + results_by_source["ebay"]
        
    if all_items:
        best_item = min(all_items, key=sort_by_price)
        overall_best_deal = best_item

    return {
        "results_by_source": results_by_source,
        "overall_best_deal": overall_best_deal,
        "current_exchange_rate": usd_rate
    }