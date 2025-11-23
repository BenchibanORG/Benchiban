from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.api.endpoints.auth import get_db
from app.models.product import Product, PriceHistory
from app.services.product_updater import update_all_products

router = APIRouter()

@router.get("/comparison")
async def get_product_comparison(
    q: str = Query(..., description="O termo de busca para o produto, ex: 'NVIDIA RTX A6000 48GB'"),
    db: Session = Depends(get_db)
):
    print(f"\n--- Usuário buscou: '{q}' ---")

    # 1. TENTA BUSCAR NO BANCO (CACHE)
    product = db.query(Product).filter(Product.search_term == q).first()
    
    # Se o produto não existe ou não tem histórico, força uma atualização imediata para não retornar vazio.
    if not product or not product.history:
        print("--- Produto sem dados ou novo. Forçando atualização inicial... ---")
        await update_all_products()
        product = db.query(Product).filter(Product.search_term == q).first()

    # 2. RECUPERA OS DADOS DO BANCO
    latest_history = []
    if product:
        # Pega os últimos 20 registros ordenados pela data (mais recente primeiro)
        latest_history = db.query(PriceHistory)\
            .filter(PriceHistory.product_id == product.id)\
            .order_by(desc(PriceHistory.timestamp))\
            .limit(20)\
            .all()

    # 3. FORMATA A RESPOSTA (Separando eBay e Amazon)
    results_by_source = {
        "ebay": [],
        "amazon": []
    }
    
    for h in latest_history:
        # Monta o objeto de resposta baseado no histórico salvo
        item = {
            "title": h.original_title if h.original_title else product.name,
            "seller": h.seller_name,
            "rating": h.seller_rating,
            "price_brl": h.price,
            "source": h.source,
            "link": getattr(h, "link", "#"), 
            "timestamp": h.timestamp
        }

        source_key = h.source.lower()
        if source_key in results_by_source:
            results_by_source[source_key].append(item)

    # 4. CALCULA A MELHOR OFERTA GERAL
    overall_best_deal = None
    all_items = []
    
    # Junta tudo numa lista só para achar o mínimo
    for source in results_by_source:
        all_items.extend(results_by_source[source])
        
    if all_items:
        # Encontra o item com o menor preço em BRL
        best_item = min(all_items, key=lambda x: x['price_brl'])
        overall_best_deal = best_item
        print(f"--- Melhor oferta (Cache): {overall_best_deal['title']} por R$ {overall_best_deal['price_brl']:.2f} ---")
    else:
        print("--- Nenhum dado no histórico para exibir. ---")

    return {
        "results_by_source": results_by_source,
        "overall_best_deal": overall_best_deal
    }