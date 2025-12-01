import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.product import Product, PriceHistory
from app.services import ebay_service, amazon_service
from app.services.currency_service import CurrencyService 
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
    db: Session = SessionLocal()
    
    try:
        log.info("--- Iniciando Atualização Massiva de Preços ---")
        
        # 2. Obtemos a cotação ATUAL do Dólar antes de começar o loop
        # Isso garante que todos os produtos salvos agora tenham a mesma base de conversão
        try:
            usd_rate = CurrencyService.get_usd_to_brl()
            log.info(f"Taxa de conversão USD -> BRL obtida: {usd_rate}")
        except Exception as e:
            log.error(f"Erro ao obter cotação: {e}. Usando fallback de segurança 5.4")
            usd_rate = 5.4

        for term in PRODUCTS_TO_MONITOR:
            log.info(f"Buscando: {term}...")
            
            # Garante que o produto pai existe na tabela 'products'
            db_product = db.query(Product).filter(Product.search_term == term).first()
            if not db_product:
                db_product = Product(name=term, search_term=term)
                db.add(db_product)
                db.commit()
                db.refresh(db_product)

            # Busca em paralelo (eBay + Amazon)
            # Nota: amazon_service deve ser async ou executado em executor se for bloqueante
            # Aqui assumindo que suas funções de busca já funcionam como estão
            results_ebay = ebay_service.search_ebay_items(term)
            results_amazon = await amazon_service.search_amazon_items(term) # Assumindo async, se não for, remova o await
            
            # Combina resultados
            all_results = results_ebay + results_amazon
            
            if all_results:
                count_saved = 0
                for item in all_results:
                    raw_price = item.get("price")
                    raw_currency = item.get("currency")
                    
                    if raw_price is not None:
                        
                        # 3. LÓGICA DE CONVERSÃO DE MOEDA
                        final_price_brl = float(raw_price)
                        currency_to_save = "BRL" # Padronizamos o banco como BRL

                        if raw_currency == "USD":
                            # Se veio em Dólar, convertemos para Real antes de salvar no 'price'
                            final_price_brl = float(raw_price) * usd_rate
                        
                        # Se já veio em BRL (Amazon), mantém o valor original
                        
                        history_entry = PriceHistory(
                            product_id=db_product.id,
                            price=final_price_brl, 
                            currency=currency_to_save, 
                            price_usd=item.get("price_usd"), 
                            exchange_rate=usd_rate if raw_currency == "USD" else 1.0,
                            source=item.get("source", "Desconhecido"),
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
                log.warning(f" -> {term}: Nenhum resultado encontrado.")

    except Exception as e:
        log.critical(f"Erro crítico no updater: {e}")
        db.rollback()
    finally:
        db.close()
        log.info("--- Atualização Finalizada ---")

if __name__ == "__main__":
    asyncio.run(update_all_products())