from fastapi import APIRouter, Query, HTTPException, status
from typing import List
from app.services import ebay_service
from app.schemas.product import ComparisonResponse, ProductItem

router = APIRouter()

@router.get("/comparison", response_model=ComparisonResponse)
def get_product_comparison(
    q: str = Query(..., description="O termo de busca para o produto, ex: 'Nvidia RTX A6000'")
):
    
    print(f"\n--- Iniciando busca comparativa para: '{q}' ---")
    
    
    ebay_results = ebay_service.search_ebay_items(query=q)
    print(f"-> Encontrados {len(ebay_results)} resultados válidos no eBay.")
    
    # PLACEHOLDERS PARA FUTURAS INTEGRAÇÕES
    # mercadolivre_results = mercadolivre_service.search_items(query=q)
    # aliexpress_results = aliexpress_service.search_items(query=q)
    # caseking_results = caseking_service.search_items(query=q)
    
    # --- Etapa 2: Estruturar os resultados por fonte ---
    results_by_source = {
        "ebay": ebay_results,
        "mercado_livre": [], # Placeholder
        "aliexpress": [],    # Placeholder
        "caseking": []       # Placeholder
    }
    
    # --- Etapa 3: Encontrar a melhor oferta geral ---
    
    # Junta todos os resultados de todas as fontes numa única lista
    all_results = []
    all_results.extend(ebay_results)
    # all_results.extend(mercadolivre_results) # Descomente quando implementar
    
    overall_best_deal = None
    if all_results:
        # Filtra apenas os itens que têm preço em BRL para uma comparação justa
        valid_for_sorting = [item for item in all_results if item.get("price_brl") is not None]
        
        if valid_for_sorting:
            # Encontra o item com o menor preço em BRL
            overall_best_deal = min(valid_for_sorting, key=lambda x: x['price_brl'])
            print(f"--- Melhor oferta geral encontrada: {overall_best_deal['title']} por R$ {overall_best_deal['price_brl']:.2f} ---")
        else:
            print("--- Nenhum item com preço em BRL encontrado para determinar a melhor oferta. ---")

    # --- Etapa 4: Retornar a resposta estruturada ---
    return {
        "results_by_source": results_by_source,
        "overall_best_deal": overall_best_deal
    }