import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.product import Product, PriceHistory
from app.services import ebay_service, amazon_service
from loguru import logger as log

# Lista atualizada com 10 GPUs
PRODUCTS_TO_MONITOR = [
    # Profissionais / High-end
    "NVIDIA RTX 5090 32GB",
    "NVIDIA RTX A6000 48GB",
    "AMD Radeon PRO W7900 48GB",
    "NVIDIA RTX 6000 Ada 48GB",

    # Intermediárias / Enthusiast
    "AMD Radeon RX 7900 XTX 24GB",
    "NVIDIA RTX 4070 Ti SUPER 16GB",
    "NVIDIA RTX 4080 Super 16GB",

    # Iniciantes / Custo-benefício
    "AMD Radeon RX 7600 XT 16GB",
    "AMD Radeon RX 7900 XT 20GB",
    "Intel Arc A770 16GB",
]

async def update_all_products():
    """Percorre a lista completa de GPUs, busca no eBay + Amazon e salva no banco."""
    # Cria uma sessão síncrona para usar dentro da thread
    db: Session = SessionLocal()
    loop = asyncio.get_event_loop()
    
    try:
        log.info("--- Iniciando Atualização Massiva de Preços ---")
        
        for term in PRODUCTS_TO_MONITOR:
            log.info(f"Buscando preços para: {term}")

            # 1. Garante que o produto exista no banco (Upsert)
            product = db.query(Product).filter(Product.search_term == term).first()
            if not product:
                product = Product(name=term, search_term=term)
                db.add(product)
                db.commit()
                db.refresh(product)

            # 2. Busca simultânea nas duas APIs (eBay + Amazon BR)
            # O run_in_executor evita que as chamadas HTTP bloqueiem o loop assíncrono
            ebay_future = loop.run_in_executor(None, ebay_service.search_ebay_items, term)
            amazon_future = loop.run_in_executor(None, amazon_service.search_amazon_items, term)
            
            # Aguarda ambas finalizarem (em paralelo)
            results = await asyncio.gather(ebay_future, amazon_future, return_exceptions=True)
            
            ebay_results = results[0]
            amazon_results = results[1]

            # Trata possíveis exceções das APIs (para não parar o loop se uma cair)
            if isinstance(ebay_results, Exception):
                log.error(f"eBay falhou para '{term}': {ebay_results}")
                ebay_results = []
                
            if isinstance(amazon_results, Exception):
                log.error(f"Amazon falhou para '{term}': {amazon_results}")
                amazon_results = []

            # Junta os resultados
            all_results = (ebay_results or []) + (amazon_results or [])

            count_saved = 0
            if all_results:
                for item in all_results:
                    # CORREÇÃO DEFINITIVA:
                    # Se for Amazon, tem 'price'. Se for eBay, tem 'price_usd'.
                    # Pegamos o que estiver disponível.
                    final_price = item.get("price") or item.get("price_usd")

                    if final_price is not None:
                        history_entry = PriceHistory(
                            product_id=product.id,
                            price=float(final_price), # Garante float para o banco
                            currency=item.get("currency", "BRL"), # eBay virá 'USD', Amazon virá 'BRL'
                            
                            # Campos adicionais novos
                            price_usd=item.get("price_usd"), 
                            source=item.get("source", "Desconhecido"),
                            link=item.get("link"),
                            original_title=item.get("title"),
                            seller_name=item.get("seller_username"),
                            seller_rating=item.get("seller_rating"),
                        )
                        db.add(history_entry)
                        count_saved += 1
                
                db.commit() # Salva o lote deste produto de uma vez
                log.info(f" -> {term}: {count_saved} novos preços salvos!")
            else:
                log.warning(f" -> {term}: Nenhum resultado encontrado (eBay ou Amazon).")

    except Exception as e:
        log.critical(f"Erro crítico no updater: {e}")
        db.rollback()
    finally:
        db.close()
        log.info("--- Atualização Finalizada ---")

if __name__ == "__main__":
    # Permite rodar este arquivo diretamente para teste manual
    asyncio.run(update_all_products())