import requests
import math
from typing import List, Dict, Any
from loguru import logger as log
from app.services import ebay_token_manager
from app.services.currency_service import CurrencyService

def search_ebay_items(query: str) -> List[Dict[str, Any]]:
    """
    Busca itens NOVOS no eBay.
    Retorna o preço original E o preço padronizado em USD.
    """
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    params = {
        "q": query,
        "limit": 20,
        "filter": "buyingOptions:{FIXED_PRICE},conditionIds:{1000}" # Apenas produtos novos e preço fixo
    }

    try:
        valid_token = ebay_token_manager.get_valid_ebay_token()
    except Exception as e:
        log.error(f"eBay: Erro ao obter token: {e}")
        return []
    
    headers = {
        "Authorization": f"Bearer {valid_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("itemSummaries", [])
        
        # Filtra itens válidos
        valid_items = [
            item for item in items
            if "price" in item and "seller" in item and item["seller"].get("feedbackPercentage")
        ]

        if not valid_items:
            log.warning(f"eBay: Nenhum item válido encontrado para '{query}'")
            return []

        # Ordena por: Maior Reputação Vendedor -> Menor Preço
        sorted_items = sorted(
            valid_items,
            key=lambda x: (-float(x["seller"]["feedbackPercentage"]), float(x["price"]["value"]))
        )
        
        top_3_raw = sorted_items[:3]
        
        # Obtém cotação para calcular estimativa em BRL
        try:
            usd_to_brl_rate = CurrencyService.get_usd_to_brl()
        except Exception:
            usd_to_brl_rate = None

        formatted_results = []
        for item in top_3_raw:
            price_val = float(item["price"]["value"])
            currency = item["price"]["currency"]
            
            # LÓGICA DE PREÇOS
            # Se for USD, o price_usd é o próprio valor. Se for outra moeda, precisaria converter (assumindo USD por enquanto)
            price_usd = price_val if currency == "USD" else None
            # Estimativa em BRL (apenas para retorno da API, não necessariamente para salvar no banco como 'price')
            price_brl_estimated = None
            if price_usd and usd_to_brl_rate:
                price_brl_estimated = math.ceil((price_usd * usd_to_brl_rate) * 100) / 100

            formatted_results.append({
                "title": item.get("title"),
                # Campos para o Banco de Dados
                "price": price_val,         # Valor Original (ex: 1000)
                "currency": currency,       # Moeda Original (ex: USD)
                "price_usd": price_usd,     # Valor em Dólar (ex: 1000)
                # Campos extras para Display
                "price_brl": price_brl_estimated, 
                "seller_rating": float(item["seller"]["feedbackPercentage"]),
                "seller_username": item["seller"]["username"],
                "link": item["itemWebUrl"],
                "source": "eBay"
            })
            
        return formatted_results

    except requests.exceptions.RequestException as e:
        log.error(f"eBay: Erro na requisição da API: {e}")
        return []