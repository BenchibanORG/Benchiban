import re
import math
from typing import List, Dict, Any, Callable, Optional
from urllib.parse import quote_plus, urljoin
from scrapfly import ScrapflyClient, ScrapeConfig
from bs4 import BeautifulSoup
from app.core.config import settings

# --- Lógica de Limpeza de Preço (Refatorada) ---
def _parse_price_to_float(price_str: str) -> float | None:
    if not price_str:
        return None
    price_cleaned = re.sub(r"[R$\s]", "", price_str).replace('.', '').replace(',', '.')
    try:
        return float(price_cleaned)
    except ValueError:
        print(f"Erro ao converter preço: {price_str}")
        return None

# --- NOVAS FUNÇÕES DE FILTRAGEM ---

def _check_keywords_simple(title_low: str, required: List[str], excluded: List[str]) -> bool:
    """Filtro simples: verifica se todas as keywords requeridas estão no título."""
    if any(kw in title_low for kw in excluded):
        return False
    if not all(kw in title_low for kw in required):
        return False
    return True

def _check_keywords_rtx_a6000(title_low: str, required: List[str], excluded: List[str]) -> bool:
    """Filtro avançado (com Regex) para a RTX A6000, baseado no seu script do Colab."""
    if any(kw in title_low for kw in excluded):
        return False
        
    title_cleaned = re.sub(r'[^a-z0-9\s]', ' ', title_low)
    
    for kw in required:
        if kw == "48g":
            # Caso especial para 48g, 48gb, 48 gb
            if not (re.search(r'\b48g\b', title_cleaned) or 
                    re.search(r'\b48gb\b', title_cleaned) or 
                    re.search(r'\b48 gb\b', title_cleaned)):
                return False
        else:
            if not re.search(r'\b' + re.escape(kw) + r'\b', title_cleaned):
                return False
    return True

ALIEXPRESS_SEARCH_CONFIG = {
    "NVIDIA RTX 5090 32GB": {
        "search_term_url": "NVIDIA RTX 5090 32GB",
        "min_price": 8000,
        "max_price": 20000,
        "required_keywords": ["placa", "rtx", "5090", "32gb"],
        "excluded_keywords": ["suporte", "cooler", "ventilador", "bloco", "cabo", "fan", "waterblock", "dissipador"],
        "filter_function": _check_keywords_simple
    },
    "NVIDIA RTX A6000 48GB": {
        "search_term_url": "NVIDIA RTX A6000 48 GB",
        "min_price": 15000,
        "max_price": None, 
        "required_keywords": ["rtx", "a6000", "48g"],
        "excluded_keywords": ["suporte", "cooler", "ventilador", "bloco", "cabo", "fan", "waterblock", "dissipador"],
        "filter_function": _check_keywords_rtx_a6000 
    }
}

# --- FUNÇÃO DE BUSCA GENÉRICA ---
def search_aliexpress_items(query: str) -> List[Dict[str, Any]]:
  
    print(f"--- AliExpress: Recebida busca por '{query}' ---")
    
    config = ALIEXPRESS_SEARCH_CONFIG.get(query)
    
    if not config:
        print(f"--- AliExpress: Nenhuma configuração de scraping encontrada para '{query}'. Pulando. ---")
        return []

    print(f"--- AliExpress: Configuração encontrada. Buscando por '{config['search_term_url']}'... ---")
    client = ScrapflyClient(key=settings.SCRAPFLY_API_KEY)
    
    base_url = "https://pt.aliexpress.com/"
    
    # Constrói o search_path dinamicamente
    search_params = {
        "SearchText": quote_plus(config['search_term_url']),
        "SortType": "total_tranpro_desc",
        "minPrice": config['min_price']
    }
    if config['max_price']:
        search_params["maxPrice"] = config['max_price']
        
    search_path = f"/wholesale?{'&'.join([f'{k}={v}' for k, v in search_params.items()])}"
    search_url = urljoin(base_url, search_path)
    print(f"--- AliExpress: URL Alvo: {search_url} ---")

    try:
        scrape_config = ScrapeConfig(
            url=search_url,
            country="BR",
            asp=True,
            render_js=True
        )
        result = client.scrape(scrape_config)
        
        soup = BeautifulSoup(result.content, 'html.parser')
        all_product_containers = soup.select("div.gl_e0 a.search-card-item")

        if not all_product_containers:
            print("--- AliExpress: Nenhum container de produto encontrado no HTML. ---")
            return []

        print(f"--- AliExpress: {len(all_product_containers)} containers encontrados. Filtrando... ---")
        formatted_results = []
        
        # Obtém os parâmetros de filtro da configuração
        required_keywords = config['required_keywords']
        excluded_keywords = config['excluded_keywords']
        filter_function = config['filter_function'] # Obtém a função de filtro correta

        count = 0
        for container in all_product_containers:
            if count >= 3:
                break

            title_element = container.select_one('h3.k7_j2')
            title = title_element.get_text(strip=True) if title_element else ''
            title_lower = title.lower()

            price_element = container.select_one('div.k7_k3')
            price_text = price_element.get_text(strip=True) if price_element else ''

            link = container.get('href', '')
            if link and not link.startswith(('http:', 'https:')):
                 link = urljoin(base_url, link)

            # --- Filtro dinâmico ---
            is_relevant_title = filter_function(title_lower, required_keywords, excluded_keywords)
            
            if title and link and is_relevant_title:
                price_float = _parse_price_to_float(price_text)
                
                if price_float:
                    formatted_results.append({
                        "title": title,
                        "price_usd": None,
                        "price_brl": price_float,
                        "currency": "BRL",
                        "seller_rating": None,
                        "seller_username": "AliExpress Seller",
                        "link": link,
                        "source": "AliExpress"
                    })
                    count += 1
        
        print(f"--- AliExpress: {len(formatted_results)} resultados válidos encontrados para '{query}'. ---")
        return formatted_results

    except Exception as e:
        print(f"--- Erro ao fazer scraping do AliExpress para '{query}': {e} ---")
        return []