import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate
from app.services.user_services import create_user, get_user_by_email
from app.core.security import verify_password


class TestRegisterEndpoint:
    """Testes para o endpoint de registro de usuário"""
    
    def test_register_new_user_success(self, client: TestClient, db_session: Session):
        """
        Dado: Um email e senha válidos que não existem no banco
        Quando: Faço POST para /api/auth/register
        Então: Retorna 200, cria o usuário e retorna os dados sem a senha
        """
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "password": "securepass123"
        }
        
        # Act
        response = client.post("/api/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data
        
        # Verifica se foi salvo no banco
        db_user = get_user_by_email(db_session, email=user_data["email"])
        assert db_user is not None
        assert db_user.email == user_data["email"]
    
    def test_register_duplicate_email_fails(self, client: TestClient, db_session: Session):
        """
        Dado: Um email que já existe no banco
        Quando: Tento registrar novamente
        Então: Retorna 400 com mensagem de erro
        """
        # Arrange - Cria usuário primeiro
        existing_user = UserCreate(email="existing@example.com", password="pass123")
        create_user(db=db_session, user=existing_user)
        
        # Act - Tenta criar com mesmo email
        response = client.post(
            "/api/auth/register",
            json={"email": "existing@example.com", "password": "anotherpass"}
        )
        
        # Assert
        assert response.status_code == 400
        assert "já cadastrado" in response.json()["detail"]
    
    def test_register_invalid_email_format(self, client: TestClient):
        """
        Dado: Um email com formato inválido
        Quando: Tento registrar
        Então: Retorna 422 (Validation Error)
        """
        # Arrange
        invalid_data = {
            "email": "not-an-email",
            "password": "pass123"
        }
        
        # Act
        response = client.post("/api/auth/register", json=invalid_data)
        
        # Assert
        assert response.status_code == 422
    
    def test_register_empty_password(self, client: TestClient):
        """
        Dado: Uma senha vazia
        Quando: Tento registrar
        Então: Retorna 422
        """
        # Arrange
        data = {
            "email": "valid@example.com",
            "password": ""
        }
        
        # Act
        response = client.post("/api/auth/register", json=data)
        
        # Assert
        assert response.status_code == 422


class TestLoginEndpoint:
    """Testes para o endpoint de login"""
    
    def test_login_with_valid_credentials(self, client: TestClient, db_session: Session):
        """
        Dado: Credenciais válidas de um usuário existente
        Quando: Faço POST para /api/auth/login
        Então: Retorna 200 com access_token e token_type
        """
        # Arrange - Cria usuário
        user_data = UserCreate(email="logintest@example.com", password="mypassword")
        create_user(db=db_session, user=user_data)
        
        # Act
        response = client.post(
            "/api/auth/login",
            json={"email": "logintest@example.com", "password": "mypassword"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 20  # Token deve ter tamanho razoável
    
    def test_login_with_wrong_password(self, client: TestClient, db_session: Session):
        """
        Dado: Email válido mas senha incorreta
        Quando: Tento fazer login
        Então: Retorna 401 Unauthorized
        """
        # Arrange
        user_data = UserCreate(email="user@example.com", password="correctpass")
        create_user(db=db_session, user=user_data)
        
        # Act
        response = client.post(
            "/api/auth/login",
            json={"email": "user@example.com", "password": "wrongpass"}
        )
        
        # Assert
        assert response.status_code == 401
        assert "incorreta" in response.json()["detail"]
    
    def test_login_with_non_existing_email(self, client: TestClient):
        """
        Dado: Um email que não existe no banco
        Quando: Tento fazer login
        Então: Retorna 401
        """
        # Act
        response = client.post(
            "/api/auth/login",
            json={"email": "notfound@example.com", "password": "anypass"}
        )
        
        # Assert
        assert response.status_code == 401
    
    def test_login_missing_fields(self, client: TestClient):
        """
        Dado: Request sem email ou senha
        Quando: Tento fazer login
        Então: Retorna 422
        """
        # Act - Sem email
        response1 = client.post("/api/auth/login", json={"password": "pass"})
        
        # Act - Sem password
        response2 = client.post("/api/auth/login", json={"email": "test@test.com"})
        
        # Assert
        assert response1.status_code == 422
        assert response2.status_code == 422


class TestTokenExpiration:
    """Testes relacionados à expiração e validade de tokens"""
    
    def test_token_can_be_decoded(self, client: TestClient, db_session: Session):
        """
        Dado: Um token gerado pelo login
        Quando: Tento decodificar o token
        Então: Consigo extrair o email do usuário
        """
        from jose import jwt
        from app.core.config import settings
        
        # Arrange
        user_data = UserCreate(email="tokentest@example.com", password="pass123")
        create_user(db=db_session, user=user_data)
        
        # Act - Faz login
        response = client.post(
            "/api/auth/login",
            json={"email": "tokentest@example.com", "password": "pass123"}
        )
        token = response.json()["access_token"]
        
        # Decodifica o token
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Assert
        assert decoded["sub"] == "tokentest@example.com"
        assert "exp" in decoded  # Token tem data de expiração
