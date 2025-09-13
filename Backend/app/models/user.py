from sqlalchemy import Column, Integer, String
from db.base_class import Base # Vamos criar este arquivo no próximo passo

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)