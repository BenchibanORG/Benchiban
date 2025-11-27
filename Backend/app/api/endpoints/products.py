from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
import math
from app.api.endpoints.auth import get_db
from app.models.product import Product, PriceHistory
from app.services.product_updater import update_all_products
from app.services.currency_service import CurrencyService  # Importar o serviço de cotação

router = APIRouter()

@router.get("/comparison")
async def get_product_comparison(
    q: str = Query(..., description="O termo de busca para o produto, ex: 'NVIDIA RTX 5090 32GB'"),
    db: Session = Depends(get_db)
):
    print(f"\n--- Usuário buscou: '{q}' ---")

    # 1. OBTER COTAÇÃO ATUAL (USD -> BRL)
    try:
        usd_rate = CurrencyService.get_usd_to_brl()
    except Exception as e:
        print(f"Erro ao obter cotação: {e}")
        usd_rate = 0.0

    # 2. TENTA BUSCAR NO BANCO (CACHE)
    product = db.query(Product).filter(Product.search_term == q).first()
    
    # Se o produto não existe ou não tem histórico, força uma atualização imediata
    if not product or not product.history:
        print("--- Produto sem dados ou novo. Forçando atualização inicial... ---")
        await update_all_products()
        product = db.query(Product).filter(Product.search_term == q).first()

    # 3. RECUPERA OS DADOS DO BANCO
    latest_history = []
    if product:
        # Pega os últimos 20 registros ordenados pela data
        latest_history = db.query(PriceHistory)\
            .filter(PriceHistory.product_id == product.id)\
            .order_by(desc(PriceHistory.timestamp))\
            .limit(20)\
            .all()

    # 4. FORMATA A RESPOSTA
    results_by_source = {
        "ebay": [],
        "amazon": []
    }
    
    for h in latest_history:
        price_usd = h.price_usd
        calculated_brl = 0.0
    
        if price_usd and usd_rate > 0:
            calculated_brl = math.ceil((price_usd * usd_rate) * 100) / 100
        elif h.currency == "BRL":
            calculated_brl = h.price

        item = {
            "title": h.original_title if h.original_title else product.name,
            "seller": h.seller_name,
            "seller_username": h.seller_name,
            "rating": h.seller_rating,
            "price_usd": price_usd,
            "price_brl": calculated_brl,
            "source": h.source,
            "link": getattr(h, "link", "#"), 
            "timestamp": h.timestamp
        }

        source_key = h.source.lower()
        if "amazon" in source_key: 
            results_by_source["amazon"].append(item)
        elif "ebay" in source_key:
            results_by_source["ebay"].append(item)

    # --- NOVO: ORDENAÇÃO EXPLÍCITA ---
    # Garante que, na tela, o item #1 da lista seja visualmente o mais barato
    def sort_by_price(item):
        # Prioriza price_usd, fallback para price_brl
        return item['price_usd'] if item['price_usd'] else item['price_brl']

    # Ordena a lista da Amazon (Melhor preço primeiro)
    results_by_source["amazon"].sort(key=sort_by_price)
    
    # Ordena a lista do eBay (Melhor preço primeiro)
    results_by_source["ebay"].sort(key=sort_by_price)

    # 5. CALCULA A MELHOR OFERTA GERAL (Comparando os 6 itens já ordenados)
    overall_best_deal = None
    all_items = results_by_source["amazon"] + results_by_source["ebay"]
        
    if all_items:
        # Pega o menor de todos
        best_item = min(all_items, key=sort_by_price)
        overall_best_deal = best_item

    return {
        "results_by_source": results_by_source, # Listas agora ordenadas
        "overall_best_deal": overall_best_deal,
        "current_exchange_rate": usd_rate # Mostra a taxa usada na conversão das 18h
    }