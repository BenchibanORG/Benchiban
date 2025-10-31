from fastapi import APIRouter, Query, HTTPException, status
from typing import List
# --- 1. ADICIONE AS IMPORTAÇÕES DOS NOVOS SERVIÇOS ---
from app.services import ebay_service, aliexpress_service, amazon_service
from app.schemas.product import ComparisonResponse, ProductItem

router = APIRouter()

@router.get("/comparison", response_model=ComparisonResponse)
def get_product_comparison(
    q: str = Query(..., description="O termo de busca para o produto, ex: 'NVIDIA RTX A6000 48GB'")
):
    
    print(f"\n--- Iniciando busca comparativa para: '{q}' ---")
    
    # --- Etapa 1: Coletar dados de todas as fontes ---
    
    print(f"-> Buscando no eBay por: '{q}'...")
    ebay_results = ebay_service.search_ebay_items(query=q)
    print(f"<- Encontrados {len(ebay_results)} resultados válidos no eBay.")

    # --- 2. ATIVE A CHAMADA AO SERVIÇO DO ALIEXPRESS ---
    print(f"-> Buscando no AliExpress por: '{q}'...")
    aliexpress_results = aliexpress_service.search_aliexpress_items(query=q)
    print(f"<- Encontrados {len(aliexpress_results)} resultados válidos no AliExpress.")
    
    # --- 3. ATIVE A CHAMADA AO SERVIÇO DA AMAZON ---
    print(f"-> Buscando na Amazon por: '{q}'...")
    amazon_results = amazon_service.search_amazon_items(query=q)
    print(f"<- Encontrados {len(amazon_results)} resultados válidos na Amazon.")
    
    # --- Etapa 2: Estruturar os resultados por fonte ---
    results_by_source = {
        "ebay": ebay_results,
        #"mercado_livre": [], # Placeholder
        "aliexpress": aliexpress_results,
        "amazon": amazon_results,
    }
    
    # --- Etapa 3: Encontrar a melhor oferta geral ---
    
    # Junta todos os resultados de todas as fontes numa única lista
    all_results = []
    all_results.extend(ebay_results)
    # --- 6. INCLUA OS RESULTADOS DO ALIEXPRESS E AMAZON NA COMPARAÇÃO ---
    all_results.extend(aliexpress_results)
    all_results.extend(amazon_results)
    
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