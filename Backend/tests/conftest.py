import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from api.endpoints.auth import get_db
from db.session import SessionLocal, engine
from db.base_class import Base

Base.metadata.create_all(bind=engine)

# Fixture principal para a sessão do banco de dados
@pytest.fixture(scope="function")
def db_session() -> Session:
    """
    Cria uma nova sessão de banco de dados para cada teste,
    rodando dentro de uma transação que será desfeita ao final.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session  # O teste executa aqui
    
    session.close()
    transaction.rollback() # Desfaz todas as alterações do teste
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """
    Cria um TestClient que usa a sessão de banco de dados transacional.
    """
    def override_get_db():
        """Sobrescreve a dependência get_db para usar a sessão de teste."""
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    yield TestClient(app)
    
    # Limpa a sobrescrita após o teste
    del app.dependency_overrides[get_db]