from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings # Vamos criar este arquivo a seguir

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)