from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.product import Product, PriceHistory
from app.services import ebay_service, amazon_service
import asyncio

# Lista fixa dos produtos do seu TCC
PRODUCTS_TO_MONITOR = [
    "NVIDIA RTX 5090 32GB",
    "NVIDIA RTX A6000 48GB",
    "AMD Radeon PRO W7900 48GB"
]

async def update_all_products():
    """Percorre a lista de produtos, busca nas APIs e salva no banco."""
    db = SessionLocal()
    try:
        for term in PRODUCTS_TO_MONITOR:
            print(f"Atualizando: {term}...")
            
            # 1. Garante que o produto existe no banco
            product = db.query(Product).filter(Product.search_term == term).first()
            if not product:
                product = Product(name=term, search_term=term)
                db.add(product)
                db.commit()
                db.refresh(product)

            # 2. Busca nas APIs (Amazon US e eBay)
            # Como agora ambos buscam fora, a chance de timeout é maior, ideal tratar exceções internamente nos services
            ebay_results = ebay_service.search_ebay_items(term)
            amazon_results = amazon_service.search_amazon_items(term)
            
            all_results = ebay_results + amazon_results

            if all_results:
                count_saved = 0
                for item in all_results:
                    # Verifica se temos o preço original (price) para salvar
                    if item.get("price") is not None:
                        history_entry = PriceHistory(
                            product_id=product.id,
                            
                            # Novos campos padronizados
                            price=item["price"],             # Valor Original (ex: 1500.00)
                            currency=item["currency"],       # Moeda (ex: "USD")
                            price_usd=item.get("price_usd"), # Valor Padronizado em Dólar
                            
                            # Metadados
                            source=item["source"],
                            link=item.get("link"),
                            original_title=item.get("title"),
                            seller_name=item.get("seller_username"),
                            seller_rating=item.get("seller_rating"),
                        )
                        db.add(history_entry)
                        count_saved += 1
                
                db.commit()
                print(f" {term}: {count_saved} preços salvos.")
            else:
                print(f" {term}: Nenhum resultado encontrado nas APIs.")
                
    except Exception as e:
        print(f"Erro crítico no updater: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(update_all_products())