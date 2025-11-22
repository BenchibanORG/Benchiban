import pytest
import os
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from dotenv import load_dotenv
load_dotenv('.env.test')

from app.db.session import SessionLocal, engine
from app.db.base_class import Base
from app.main import app
from app.api.endpoints.auth import get_db

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Cria um banco de dados e uma sessão limpos para cada função de teste.
    Garante que as tabelas sejam criadas no início e removidas no final.
    """
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Cria um TestClient que usa a sessão de banco de dados de teste,
    sobrescrevendo a dependência 'get_db'.
    """
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    yield TestClient(app)
    
    del app.dependency_overrides[get_db]