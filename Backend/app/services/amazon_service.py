import re
import math
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
from loguru import logger as log
from scrapfly import ScrapeApiResponse, ScrapeConfig, ScrapflyClient
from app.core.config import settings # Importa as configurações seguras

# --- CONFIGURAÇÃO DO CLIENTE ---
SCRAPFLY = ScrapflyClient(key=settings.SCRAPFLY_API_KEY)
BASE_CONFIG = {
    "asp": True,
    "country": "BR",
}

# --- MAPA DE CONFIGURAÇÃO DE BUSCA ---
# Aqui centralizamos a lógica de busca para cada produto.
# A chave (ex: "NVIDIA RTX 5090 32GB") DEVE ser idêntica à string
# enviada pelo frontend (do DashboardPage.js)
AMAZON_SEARCH_CONFIG = {
    "NVIDIA RTX 5090 32GB": {
        "search_term": "NVIDIA RTX 5090 32GB",
        "required_keywords": ["placa", "rtx", "5090", "32gb"]
    },
    "NVIDIA RTX A6000 48GB": {
        "search_term": "NVIDIA RTX A6000 48GB",
        "required_keywords": ["placa", "rtx", "a6000", "48gb"]
    },
    "AMD Radeon PRO W7900 48GB": {
        "search_term": "AMD Radeon PRO W7900 48GB",
        "required_keywords": ["w7900", "48gb"]
    }
}

# --- FUNÇÕES HELPER (do seu script Colab) ---
def _parse_preco_para_float(preco_str: str) -> Optional[float]:
    """Converte uma string de preço (ex: 'R$ 1.234,56') para float (1234.56)"""
    if not preco_str:
        return None
    try:
        limpo = preco_str.replace("R$", "").strip()
        limpo = limpo.replace(".", "").replace(",", ".")
        return float(limpo)
    except (ValueError, TypeError):
        log.warning(f"Amazon: Não foi possível converter o preço: {preco_str}")
        return None

def _parse_search_page(result: ScrapeApiResponse, palavras_chave_obrigatorias: List[str]) -> List[Dict[str, Any]]:
    """Extrai Título, Preço e Link da página de busca E FILTRA"""
    previews = []
    product_boxes = result.selector.css("div.s-result-item[data-component-type=s-search-result]")
    
    log.info(f"Amazon: {len(product_boxes)} containers encontrados. Filtrando por {palavras_chave_obrigatorias}...")

    for box in product_boxes:
        titulo = box.css("div>a>h2::attr(aria-label)").get()
        if not titulo:
            titulo = "".join(box.css("h2 a span::text").getall()).strip()
        
        link_relativo = box.css("div>a::attr(href)").get()
        if not link_relativo or "/slredirect/" in link_relativo:
            continue
        
        link_abs = f"https://www.amazon.com.br{link_relativo.split('?')[0]}"
        preco_str = box.css(".a-price .a-offscreen::text").get()
        preco_num = _parse_preco_para_float(preco_str)

        if titulo and preco_num and link_abs:
            titulo_lower = titulo.lower()
            
            # Verifica se TODAS as palavras-chave estão no título
            filtro_passou = True
            for palavra in palavras_chave_obrigatorias:
                if palavra.lower() not in titulo_lower:
                    filtro_passou = False
                    break 
            
            if filtro_passou:
                previews.append({
                    "title": titulo.strip(),
                    "price_usd": None, # Amazon.com.br já está em BRL
                    "price_brl": preco_num,
                    "currency": "BRL",
                    "seller_rating": None, # O scraping da Amazon não pegou o rating
                    "seller_username": "Amazon Seller", # O scraping não pegou o vendedor
                    "link": link_abs,
                    "source": "Amazon"
                })
            else:
                log.debug(f"Amazon: Filtrado (não contém palavras-chave): {titulo.strip()}")
            
    log.info(f"Amazon: Extraídos {len(previews)} produtos válidos APÓS FILTRAGEM.")
    return previews

# --- FUNÇÃO PRINCIPAL DO SERVIÇO ---
def search_amazon_items(query: str) -> List[Dict[str, Any]]:
    log.info(f"--- Amazon: Recebida busca por '{query}' ---")
    
    # 1. Encontra a configuração correta
    config_para_busca = AMAZON_SEARCH_CONFIG.get(query)
    
    if not config_para_busca:
        log.warning(f"--- Amazon: Nenhuma configuração de scraping encontrada para '{query}'. Pulando. ---")
        return []

    # 2. Prepara a URL
    search_term = config_para_busca["search_term"]
    palavras_filtro = config_para_busca["required_keywords"]
    url_busca = f"https://www.amazon.com.br/s?k={quote_plus(search_term)}"
    
    log.info(f"--- Amazon: Buscando URL: {url_busca} ---")

    try:
        # 3. Faz o scraping (SÍNCRONO)
        result = SCRAPFLY.scrape(ScrapeConfig(url_busca, **BASE_CONFIG))
        
        # 4. Faz o parse e filtra
        resultados = _parse_search_page(result, palavras_filtro)
        
        # 5. Ordena pelo preço e retorna os 3 melhores
        resultados_ordenados = sorted(resultados, key=lambda x: x['price_brl'])
        return resultados_ordenados[:3]

    except Exception as e:
        log.error(f"--- Amazon: Falha ao buscar a URL {url_busca}: {e}")
        return []
