import re
import math
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
from loguru import logger as log
from scrapfly import ScrapeApiResponse, ScrapeConfig, ScrapflyClient
from app.core.config import settings
from app.services.currency_service import CurrencyService 

# --- CONFIGURAÇÃO DO CLIENTE ---
SCRAPFLY = ScrapflyClient(key=settings.SCRAPFLY_API_KEY)
BASE_CONFIG = {
    "asp": True,
    "country": "US",
}

# --- MAPA DE CONFIGURAÇÃO DE BUSCA ---
# Atualizado para termos mais compatíveis com o mercado americano
AMAZON_SEARCH_CONFIG = {
    "NVIDIA RTX 5090 32GB": {
        "search_term": "NVIDIA RTX 5090 32GB",
        "required_keywords": ["rtx", "5090","32GB"]
    },
    "NVIDIA RTX A6000 48GB": {
        "search_term": "NVIDIA RTX A6000 48GB",
        "required_keywords": ["nvidia", "rtx", "a6000","48GB"]
    },
    "AMD Radeon PRO W7900 48GB": {
        "search_term": "AMD Radeon PRO W7900 48GB",
        "required_keywords": ["amd", "radeon", "w7900", "48GB"] 
    }
}

# --- FUNÇÕES HELPER ---

def _parse_price_us(price_str: str) -> Optional[float]:
    """
    Converte preço formato US (ex: '$ 1,234.56') para float (1234.56).
    Diferença: Remove vírgula (milhar) e mantém ponto (decimal).
    """
    if not price_str:
        return None
    try:
        # Remove sifrão, USD e espaços
        clean = price_str.replace("$", "").replace("USD", "").strip()
        # Remove vírgula (separador de milhar nos EUA)
        clean = clean.replace(",", "")
        return float(clean)
    except (ValueError, TypeError):
        log.warning(f"Amazon US: Não foi possível converter o preço: {price_str}")
        return None

def _parse_search_page(result: ScrapeApiResponse, palavras_chave_obrigatorias: List[str]) -> List[Dict[str, Any]]:
    """Extrai Título, Preço e Link da página de busca E FILTRA"""
    previews = []
    # O seletor CSS geralmente é o mesmo globalmente
    product_boxes = result.selector.css("div.s-result-item[data-component-type=s-search-result]")
    
    # Tenta obter a cotação para já retornar uma estimativa em BRL
    try:
        usd_to_brl_rate = CurrencyService.get_usd_to_brl()
    except Exception:
        usd_to_brl_rate = None

    log.info(f"Amazon US: {len(product_boxes)} containers encontrados. Filtrando por {palavras_chave_obrigatorias}...")

    for box in product_boxes:
        titulo = box.css("div>a>h2::attr(aria-label)").get()
        if not titulo:
            titulo = "".join(box.css("h2 a span::text").getall()).strip()
        
        link_relativo = box.css("div>a::attr(href)").get()
        if not link_relativo or "/slredirect/" in link_relativo:
            continue
        
        # URL Base ajustada para .com
        link_abs = f"https://www.amazon.com{link_relativo.split('?')[0]}"
        
        preco_str = box.css(".a-price .a-offscreen::text").get()
        # Usa a nova função de parse americana
        preco_usd = _parse_price_us(preco_str)

        if titulo and preco_usd and link_abs:
            titulo_lower = titulo.lower()
            
            # Verifica se TODAS as palavras-chave estão no título
            filtro_passou = True
            for palavra in palavras_chave_obrigatorias:
                if palavra.lower() not in titulo_lower:
                    filtro_passou = False
                    break 
            
            if filtro_passou:
                # Calcula estimativa em BRL para exibição
                price_brl_estimated = None
                if usd_to_brl_rate:
                    # Multiplica e arredonda para 2 casas
                    price_brl_estimated = math.ceil((preco_usd * usd_to_brl_rate) * 100) / 100

                previews.append({
                    "title": titulo.strip(),
                    "price": preco_usd,        # Valor Original (para salvar no histórico)
                    "currency": "USD",         # Moeda Original
                    "price_usd": preco_usd,    # Valor Padronizado em Dólar
                    "price_brl": price_brl_estimated, # Apenas visualização
                    "seller_rating": None,
                    "seller_username": "Amazon US",
                    "link": link_abs,
                    "source": "Amazon"
                })
            else:
                log.debug(f"Amazon: Filtrado (não contém keywords): {titulo.strip()}")
            
    log.info(f"Amazon US: Extraídos {len(previews)} produtos válidos APÓS FILTRAGEM.")
    return previews

# --- FUNÇÃO PRINCIPAL DO SERVIÇO ---
def search_amazon_items(query: str) -> List[Dict[str, Any]]:
    log.info(f"--- Amazon US: Recebida busca por '{query}' ---")
    
    config_para_busca = AMAZON_SEARCH_CONFIG.get(query)
    
    if not config_para_busca:
        log.warning(f"--- Amazon: Nenhuma configuração para '{query}'. ---")
        return []

    search_term = config_para_busca["search_term"]
    palavras_filtro = config_para_busca["required_keywords"]
    
    # URL da Amazon Americana
    url_busca = f"https://www.amazon.com/s?k={quote_plus(search_term)}"
    
    log.info(f"--- Amazon US: Buscando URL: {url_busca} ---")

    try:
        result = SCRAPFLY.scrape(ScrapeConfig(url_busca, **BASE_CONFIG))
        
        resultados = _parse_search_page(result, palavras_filtro)
        
        # Ordena pelo preço em Dólar (price_usd)
        resultados_ordenados = sorted(resultados, key=lambda x: x['price_usd'])
        return resultados_ordenados[:3]

    except Exception as e:
        log.error(f"--- Amazon US: Falha ao buscar a URL {url_busca}: {e}")
        return []