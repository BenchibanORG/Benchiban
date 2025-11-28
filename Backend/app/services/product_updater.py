import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.product import Product, PriceHistory
from app.services import ebay_service, amazon_service
from loguru import logger as log

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
    db: Session = SessionLocal()
    loop = asyncio.get_event_loop()
    
    try:
        log.info("--- Iniciando Atualização Massiva de Preços ---")
        
        for term in PRODUCTS_TO_MONITOR:
            log.info(f"Buscando preços para: {term}")

            # 1. Garante que o produto exista no banco
            product = db.query(Product).filter(Product.search_term == term).first()
            if not product:
                product = Product(name=term, search_term=term)
                db.add(product)
                db.commit()
                db.refresh(product)

            # 2. Busca simultânea nas duas APIs (eBay + Amazon BR)
            ebay_future = loop.run_in_executor(None, ebay_service.search_ebay_items, term)
            amazon_future = loop.run_in_executor(None, amazon_service.search_amazon_items, term)
            
            # Aguarda ambas finalizarem (em paralelo)
            results = await asyncio.gather(ebay_future, amazon_future, return_exceptions=True)
            
            ebay_results = results[0]
            amazon_results = results[1]

            # Trata possíveis exceções das APIs
            if isinstance(ebay_results, Exception):
                log.error(f"eBay falhou para '{term}': {ebay_results}")
                ebay_results = []
                
            if isinstance(amazon_results, Exception):
                log.error(f"Amazon falhou para '{term}': {amazon_results}")
                amazon_results = []

            all_results = ebay_results + amazon_results

            if all_results:
                count_saved = 0
                for item in all_results:
                    # Validação básica
                    if item.get("price") is not None:
                        history_entry = PriceHistory(
                            product_id=product.id,
                            price=item["price"],
                            currency=item.get("currency", "BRL"),
                            price_usd=item.get("price_usd"),
                            source=item["source"],
                            link=item.get("link"),
                            original_title=item.get("title"),
                            seller_name=item.get("seller_username"),
                            seller_rating=item.get("seller_rating"),
                        )
                        db.add(history_entry)
                        count_saved += 1
                
                db.commit()
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
    asyncio.run(update_all_products())