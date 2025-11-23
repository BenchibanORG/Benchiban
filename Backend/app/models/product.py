from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base_class import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    search_term = Column(String, unique=True, nullable=False)
    
    # Relacionamento com o histórico
    history = relationship("PriceHistory", back_populates="product")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    price = Column(Float, nullable=False) # Preço
    currency = Column(String, default="BRL") # Moeda
    source = Column(String) # De qual plataforma o preço é buscado
    link = Column(String) # Link do anúncio
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    original_title = Column(String)  # O título real do anúncio
    seller_name = Column(String)     # Nome do vendedor
    seller_rating = Column(Float, nullable=True) # Avaliação
    
    # Relacionamento reverso
    product = relationship("Product", back_populates="history")