import requests
import math
from typing import List, Dict, Any

from app.services import ebay_token_manager

def get_usd_to_brl_rate() -> float | None:
    """Obtém a taxa de conversão mais recente de USD para BRL."""
    try:
        url = "https://api.frankfurter.app/latest?from=USD&to=BRL"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data["rates"]["BRL"]
    except requests.exceptions.RequestException as e:
        print(f"Aviso: Não foi possível obter a taxa de conversão. Erro: {e}")
        return None

def search_ebay_items(query: str) -> List[Dict[str, Any]]:
    """
    Busca itens NOVOS no eBay, filtra, ordena e retorna os 3 melhores resultados formatados.
    """
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    params = {
        "q": query,
        "limit": 20,
        "filter": "buyingOptions:{FIXED_PRICE},conditionIds:{1000}"
    }

    valid_token = ebay_token_manager.get_valid_ebay_token()
    
    headers = {
        "Authorization": f"Bearer {valid_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("itemSummaries", [])
        
        valid_items = [
            item for item in items
            if "price" in item and "seller" in item and item["seller"].get("feedbackPercentage")
        ]

        if not valid_items:
            return []

        sorted_items = sorted(
            valid_items,
            key=lambda x: (-float(x["seller"]["feedbackPercentage"]), float(x["price"]["value"]))
        )
        
        top_3_raw = sorted_items[:3]
        
        usd_to_brl_rate = get_usd_to_brl_rate()
        formatted_results = []
        for item in top_3_raw:
            price_usd = float(item["price"]["value"])
            price_brl = None
            if usd_to_brl_rate and item["price"]["currency"] == "USD":
                raw_brl = price_usd * usd_to_brl_rate
                price_brl = math.ceil(raw_brl * 100) / 100

            formatted_results.append({
                "title": item.get("title"),
                "price_usd": price_usd,
                "price_brl": price_brl,
                "currency": item["price"]["currency"],
                "seller_rating": float(item["seller"]["feedbackPercentage"]),
                "seller_username": item["seller"]["username"],
                "link": item["itemWebUrl"],
                "source": "eBay"
            })
            
        return formatted_results

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API do eBay: {e}")
        return []