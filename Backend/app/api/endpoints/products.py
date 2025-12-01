from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from app.api.endpoints.auth import get_db
from app.models.product import Product, PriceHistory
from app.services.product_updater import update_all_products
from app.services.currency_service import CurrencyService
from app.schemas.product import ComparisonResponse 
from app.models.product import Product, PriceHistory
from app.schemas.product import PriceHistoryResponse, PriceHistoryPoint

router = APIRouter()

@router.get("/comparison", response_model=ComparisonResponse)
async def get_product_comparison(
    q: str = Query(..., description="O termo de busca para o produto, ex: 'NVIDIA RTX 5090 32GB'"),
    db: Session = Depends(get_db)
):
    print(f"\n--- Usuário buscou: '{q}' ---")

    # 1. OBTER COTAÇÃO ATUAL E TIMESTAMP (CORRIGIDO)
    try:
        # Pega apenas a taxa (float)
        usd_rate = CurrencyService.get_usd_to_brl()
        
        # Pega a data separadamente usando o novo método
        rate_dt = CurrencyService.get_last_update_timestamp()
        
        # Se rate_dt existir, converte para string ISO; senão, fica None
        rate_timestamp = rate_dt.isoformat() if rate_dt else None
        
    except Exception as e:
        print(f"Erro ao obter cotação: {e}")
        usd_rate = 0.0
        rate_timestamp = None

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
            # Janela de tempo de 2 minutos para pegar itens da mesma "batelada" de scraping
            time_window = last_ts - timedelta(minutes=2)

            latest_history = db.query(PriceHistory)\
                .filter(PriceHistory.product_id == product.id)\
                .filter(PriceHistory.timestamp >= time_window)\
                .order_by(desc(PriceHistory.timestamp))\
                .all()

    # 4. FORMATA A RESPOSTA
    results_by_source = {
        "ebay": [],
        "amazon": [],
    }
    
    for h in latest_history:
        # Se h.price_usd não existir no model ainda, usamos lógica de fallback
        price_usd_val = getattr(h, 'price_usd', None)
        
        # Se o preço original for em USD e não tivermos o campo price_usd salvo
        if h.currency == "USD" and price_usd_val is None:
            price_usd_val = h.price

        calculated_brl = 0.0
    
        # Lógica de conversão
        if h.currency == "BRL":
            # Amazon BR / ML: O preço real é o próprio
            calculated_brl = h.price
        elif price_usd_val and usd_rate > 0:
            # eBay USD: Converte usando a cotação DE AGORA
            calculated_brl = math.ceil((price_usd_val * usd_rate) * 100) / 100

        item = {
            "title": h.original_title if h.original_title else product.name,
            "seller": h.seller_name,
            "seller_username": h.seller_name,
            "rating": h.seller_rating,
            "price_original": h.price,
            "currency_original": h.currency,
            "price_usd": price_usd_val,
            "price_brl": calculated_brl,
            "source": h.source,
            "link": getattr(h, "link", "#"), 
            "timestamp": h.timestamp
        }

        source_key = h.source.lower().replace(" ", "")
        if "amazon" in source_key: 
            results_by_source["amazon"].append(item)
        elif "ebay" in source_key:
            results_by_source["ebay"].append(item)
        # Adiciona suporte caso apareçam outros sources
        elif source_key not in results_by_source:
             results_by_source[source_key] = [item]
        else:
             results_by_source[source_key].append(item)

    # --- Ordenação baseada em REAIS (BRL) ---
    def sort_by_price(item):
        return item['price_brl'] if item['price_brl'] else float('inf')

    # Ordena todas as listas
    for source in results_by_source:
        results_by_source[source].sort(key=sort_by_price)

    # 5. MELHOR OFERTA GERAL
    overall_best_deal = None
    all_items = []
    for items in results_by_source.values():
        all_items.extend(items)
        
    if all_items:
        best_item = min(all_items, key=sort_by_price)
        overall_best_deal = best_item

    return {
        "results_by_source": results_by_source,
        "overall_best_deal": overall_best_deal,
        "current_exchange_rate": usd_rate,
        "exchange_rate_timestamp": rate_timestamp 
    }

@router.get("/history", response_model=PriceHistoryResponse)
def get_product_history(
    product_name: str = Query(..., description="Nome exato ou termo de busca do produto"),
    period_days: int = Query(30, description="Quantos dias de histórico buscar"),
    db: Session = Depends(get_db)
):
    # 1. Busca o Produto (Pai)
    product = db.query(Product).filter(Product.name.ilike(f"%{product_name}%")).first()
    if not product:
        product = db.query(Product).filter(Product.search_term.ilike(f"%{product_name}%")).first()
    
    if not product:
        return PriceHistoryResponse(product_name=product_name, history=[])

    # 2. Define Data Limite (Timezone Aware)
    limit_date = datetime.now(timezone.utc) - timedelta(days=period_days)

    # 3. Busca Todos os Dados Brutos (Ordenados)
    raw_data = (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product.id)
        .filter(PriceHistory.timestamp >= limit_date)
        .order_by(PriceHistory.timestamp.asc()) 
        .all()
    )

    # 4. Agrupamento Inteligente (A Mágica acontece aqui)
    # Objetivo: Reduzir 10 anúncios do mesmo minuto em 1 ponto com o MENOR preço.
    grouped_points: Dict[str, Dict[str, Any]] = {}

    for entry in raw_data:
        # Arredonda para o Minuto (remove segundos/microssegundos para agrupar a bateria de scraping)
        # Ex: "2025-11-28 16:04"
        time_key = entry.timestamp.strftime("%Y-%m-%d %H:%M")
        
        # Chave única para o grupo: Data + Loja
        group_key = f"{time_key}_{entry.source}"

        # Valores atuais dessa linha
        val_usd = entry.price_usd
        val_brl = entry.price if entry.currency == 'BRL' else None # Só confia no BRL se a flag for BRL

        if group_key not in grouped_points:
            # Cria novo ponto no grupo
            grouped_points[group_key] = {
                "date": entry.timestamp.isoformat(), # Mantém formato ISO completo para o front
                "source": entry.source if entry.source else "Desconhecido",
                "price_usd": val_usd,
                "price_brl": val_brl
            }
        else:
            # Se já existe, atualiza com o MENOR preço encontrado naquele minuto
            current = grouped_points[group_key]
            
            # Lógica de Mínimo para USD
            if val_usd is not None:
                if current["price_usd"] is None or val_usd < current["price_usd"]:
                    current["price_usd"] = val_usd
            
            # Lógica de Mínimo para BRL
            if val_brl is not None:
                if current["price_brl"] is None or val_brl < current["price_brl"]:
                    current["price_brl"] = val_brl

    # 5. Converte o dicionário agrupado de volta para lista
    final_history = [
        PriceHistoryPoint(**data) for data in grouped_points.values()
    ]

    # Reordena para garantir cronologia
    final_history.sort(key=lambda x: x.date)

    return PriceHistoryResponse(
        product_name=product.name,
        history=final_history
    )