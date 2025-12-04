import math
import re
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
    "country": "BR",
}

# --- MAPA DE CONFIGURAÇÃO DE BUSCA ---
AMAZON_SEARCH_CONFIG = {
    # ------------------------------------------------------
    # PROFISSIONAIS / HIGH-END
    # ------------------------------------------------------

    "NVIDIA RTX 5090 32GB": {
        "search_term": "NVIDIA RTX 5090 32GB",
        "required_keywords": ["rtx", "5090", "32gb"]
    },

    "NVIDIA RTX A6000 48GB": {
        "search_term": "NVIDIA RTX A6000 48GB",
        "required_keywords": ["rtx", "a6000"]
    },

    "AMD Radeon PRO W7900 48GB": {
        "search_term": "AMD Radeon PRO W7900 48GB",
        "required_keywords": ["radeon", "w7900", "48gb"]
    },

    "NVIDIA RTX 6000 Ada 48GB": {
        "search_term": "NVIDIA RTX 6000 Ada 48GB",
        "required_keywords": ["rtx", "6000", "ada"]
    },

    # ------------------------------------------------------
    # INTERMEDIÁRIAS / ENTHUSIAST
    # ------------------------------------------------------
    
    "AMD Radeon RX 7900 XTX 24GB": {
        "search_term": "AMD Radeon RX 7900 XTX 24GB",
        "required_keywords": ["radeon","rx","7900", "xtx"]
    },

    "NVIDIA RTX 4070 Ti SUPER 16GB": {
        "search_term": "NVIDIA RTX 4070 Ti SUPER 16GB",
        "required_keywords": ["rtx", "4070", "ti", "16gb"]
    },

    "NVIDIA RTX 4080 Super 16GB": {
        "search_term": "NVIDIA RTX 4080 Super 16GB",
        "required_keywords": ["rtx", "4080", "super"]
    },

    # ------------------------------------------------------
    # INICIANTES / CUSTO BENEFÍCIO
    # ------------------------------------------------------

    "AMD Radeon RX 7600 XT 16GB": {
        "search_term": "AMD Radeon RX 7600 XT 16GB",
        "required_keywords": ["rx", "7600", "xt", "16gb"]
    },

    "AMD Radeon RX 7900 XT 20GB": {
        "search_term": "AMD Radeon RX 7900 XT 20GB",
        "required_keywords": ["rx", "7900", "xt"]
    },

    "Intel Arc A770 16GB": {
        "search_term": "Intel Arc A770 16GB",
        "required_keywords": ["intel", "arc", "a770"]
    }
}


# --- FUNÇÕES HELPER ---

def _parse_price_br(price_str: str) -> Optional[float]:
    """
    Converte preço formato BR (ex: 'R$ 1.234,56') para float (1234.56).
    """
    if not price_str:
        return None
    try:
        # Remove R$, espaços e pontos de milhar
        limpo = price_str.replace("R$", "").replace(".", "").strip()
        # Troca vírgula decimal por ponto
        limpo = limpo.replace(",", ".")
        return float(limpo)
    except (ValueError, TypeError):
        log.warning(f"Amazon BR: Não foi possível converter o preço: {price_str}")
        return None

def _parse_search_page(result: ScrapeApiResponse, palavras_chave_obrigatorias: List[str]) -> List[Dict[str, Any]]:
    """Extrai Título, Preço e Link da página de busca E FILTRA"""
    previews = []
    product_boxes = result.selector.css("div.s-result-item[data-component-type=s-search-result]")

    try:
        usd_to_brl = CurrencyService.get_usd_to_brl()
        brl_to_usd_rate = 1 / usd_to_brl if usd_to_brl else 0
    except Exception:
        brl_to_usd_rate = 0

    log.info(f"Amazon BR: {len(product_boxes)} containers encontrados. Filtrando por {palavras_chave_obrigatorias}...")

    for box in product_boxes:
        # Primeiro tenta aria-label (pode estar vazio!)
        titulo = box.css("div>a>h2::attr(aria-label)").get()
        if not titulo:
            # Fallback robusto: pega todos os spans dentro do h2
            titulo = "".join(box.css("h2 a span::text").getall()).strip()
        # Limpa espaços extras
        if titulo:
            titulo = re.sub(r'\s+', ' ', titulo).strip()
        
        link_relativo = box.css("div>a::attr(href)").get()
        if not link_relativo or "/slredirect/" in link_relativo:
            continue
        
        link_abs = f"https://www.amazon.com.br{link_relativo.split('?')[0]}"
        
        preco_str = box.css(".a-price .a-offscreen::text").get()
        preco_brl = _parse_price_br(preco_str)

        if titulo and preco_brl and link_abs:
            titulo_lower = titulo.lower()
            
            # Verifica se TODAS as palavras-chave estão no título
            filtro_passou = True
            for palavra in palavras_chave_obrigatorias:
                if palavra.lower() not in titulo_lower:
                    filtro_passou = False
                    break 
            
            if filtro_passou:
                price_usd_estimated = round(preco_brl * brl_to_usd_rate, 2) if brl_to_usd_rate > 0 else None

                previews.append({
                    "title": titulo.strip(),
                    # Agora o dado nativo é BRL
                    "price": preco_brl,        # Valor Original em Reais
                    "currency": "BRL",         # Moeda Original
                    "price_usd": price_usd_estimated, # Estimativa em Dólar
                    
                    # Campos extras
                    "price_brl": preco_brl,
                    "seller_rating": None,
                    "seller_username": "Amazon BR",
                    "link": link_abs,
                    "source": "Amazon"
                })
            else:
                log.debug(f"Amazon: Filtrado (não contém keywords): {titulo.strip()}")
            
    log.info(f"Amazon BR: Extraídos {len(previews)} produtos válidos APÓS FILTRAGEM.")
    return previews

# --- FUNÇÃO PRINCIPAL DO SERVIÇO ---
def search_amazon_items(query: str) -> List[Dict[str, Any]]:
    log.info(f"--- Amazon BR: Recebida busca por '{query}' ---")
    
    config_para_busca = AMAZON_SEARCH_CONFIG.get(query)
    
    if not config_para_busca:
        log.warning(f"--- Amazon: Nenhuma configuração para '{query}'. ---")
        return []

    search_term = config_para_busca["search_term"]
    palavras_filtro = config_para_busca["required_keywords"]
    
    # URL da Amazon Brasileira
    url_busca = f"https://www.amazon.com.br/s?k={quote_plus(search_term)}"
    
    log.info(f"--- Amazon BR: Buscando URL: {url_busca} ---")

    try:
        result = SCRAPFLY.scrape(ScrapeConfig(url_busca, **BASE_CONFIG))
        
        resultados = _parse_search_page(result, palavras_filtro)
        
        # Ordena pelo preço em Reais (já que estamos no BR)
        resultados_ordenados = sorted(resultados, key=lambda x: x['price'])
        return resultados_ordenados[:3]

    except Exception as e:
        log.error(f"--- Amazon BR: Falha ao buscar a URL {url_busca}: {e}")
        return []