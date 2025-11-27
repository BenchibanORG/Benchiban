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
    "country": "BR", # VOLTAMOS PARA BRASIL (Custo reduzido de créditos)
}

# --- MAPA DE CONFIGURAÇÃO DE BUSCA ---
AMAZON_SEARCH_CONFIG = {
    "NVIDIA RTX 5090 32GB": {
        "search_term": "NVIDIA RTX 5090 32GB",
        "required_keywords": ["rtx", "5090", "32GB"]
    },
    "NVIDIA RTX A6000 48GB": {
        "search_term": "NVIDIA RTX A6000 48GB",
        "required_keywords": ["nvidia", "rtx", "a6000", "48GB"]
    },
    "AMD Radeon PRO W7900 48GB": {
        "search_term": "AMD Radeon PRO W7900 48GB",
        "required_keywords": ["amd", "radeon", "w7900", "48GB"] 
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
    
    # Precisamos da cotação para preencher o price_usd (para ordenação global no banco)
    # Cálculo inverso: Se USD/BRL é 5.00, então 1 Real = 0.20 Dólares
    try:
        usd_to_brl = CurrencyService.get_usd_to_brl()
        brl_to_usd_rate = 1 / usd_to_brl if usd_to_brl else 0
    except Exception:
        brl_to_usd_rate = 0

    log.info(f"Amazon BR: {len(product_boxes)} containers encontrados. Filtrando por {palavras_chave_obrigatorias}...")

    for box in product_boxes:
        titulo = box.css("div>a>h2::attr(aria-label)").get()
        if not titulo:
            titulo = "".join(box.css("h2 a span::text").getall()).strip()
        
        link_relativo = box.css("div>a::attr(href)").get()
        if not link_relativo or "/slredirect/" in link_relativo:
            continue
        
        # URL Base ajustada para .com.br
        link_abs = f"https://www.amazon.com.br{link_relativo.split('?')[0]}"
        
        preco_str = box.css(".a-price .a-offscreen::text").get()
        # Usa o parser Brasileiro
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
                # CÁLCULO INVERSO: Temos Reais, estimamos Dólar para manter compatibilidade no banco
                price_usd_estimated = round(preco_brl * brl_to_usd_rate, 2) if brl_to_usd_rate > 0 else None

                previews.append({
                    "title": titulo.strip(),
                    # Agora o dado nativo é BRL
                    "price": preco_brl,        # Valor Original em Reais (para salvar no histórico)
                    "currency": "BRL",         # Moeda Original
                    "price_usd": price_usd_estimated, # Estimativa em Dólar (importante para ordenar com eBay)
                    
                    # Campos extras
                    "price_brl": preco_brl,    # O próprio valor
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