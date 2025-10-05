from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_password_reset_token
from app.services.user_services import create_user
from app.schemas.user import UserCreate

def test_request_password_reset_for_existing_user(client: TestClient, db_session: Session):
    user_in = UserCreate(email="test@example.com", password="password123")
    create_user(db=db_session, user=user_in)

    with patch("app.api.endpoints.auth.send_reset_password_email") as mock_send_email:
        response = client.post("/api/auth/forgot-password", json={"email": "test@example.com"})
        
        assert response.status_code == 200
        assert "message" in response.json()
        mock_send_email.assert_called_once()

def test_request_password_reset_for_non_existing_user(client: TestClient):
    with patch("app.api.endpoints.auth.send_reset_password_email") as mock_send_email:
        response = client.post("/api/auth/forgot-password", json={"email": "nonexistent@example.com"})
        
        assert response.status_code == 200
        assert "message" in response.json()
        mock_send_email.assert_not_called()

def test_reset_password_with_valid_token(client: TestClient, db_session: Session):
    user_in = UserCreate(email="reset@example.com", password="oldpassword")
    user = create_user(db=db_session, user=user_in)
    token = create_password_reset_token(email=user.email)

    response = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "newpassword123"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Sua senha foi redefinida com sucesso."}

def test_reset_password_with_invalid_token(client: TestClient):
    response = client.post(
        "/api/auth/reset-password",
        json={"token": "invalidtoken", "new_password": "somepassword"}
    )
    assert response.status_code == 400
    assert "Token inválido ou expirado" in response.json()["detail"]

