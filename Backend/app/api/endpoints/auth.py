from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import jwt, JWTError

from app.schemas.user import UserCreate, UserRead, Token
from app.schemas.key import ForgotPasswordSchema, ResetPasswordSchema

from app.services.user_services import get_user_by_email, create_user, update_password
from app.services.email_service import send_reset_password_email

from app.core.security import verify_password, create_access_token, create_password_reset_token
from app.core.config import settings

from app.db.session import SessionLocal
from app.schemas.key import ForgotPasswordSchema

router = APIRouter()

# Dependência para obter a sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Chamada da função corrigida (sem prefixo)
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    # Chamada da função corrigida (sem prefixo)
    return create_user(db=db, user=user)

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: UserCreate, db: Session = Depends(get_db)):
    # Chamada da função corrigida (sem prefixo)
    user = get_user_by_email(db, email=form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorreta",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password", summary="Solicitar redefinição de senha")
def request_password_reset(
    payload: ForgotPasswordSchema = Body(...), db: Session = Depends(get_db)
):
    # --- LUZES DE INSPEÇÃO ---
    print("\n--- DEBUG: PONTO 1: Entrou na função request_password_reset ---")
    print(f"--- DEBUG: PONTO 2: E-mail recebido do frontend: '{payload.email}' ---")

    user = get_user_by_email(db, email=payload.email)
    
    print(f"--- DEBUG: PONTO 3: Resultado da busca no DB para o e-mail: {user} ---")
    
    if user:
        print("--- DEBUG: PONTO 4: Usuário encontrado! Entrando no bloco 'if'. ---")
        token = create_password_reset_token(email=user.email)
        print("--- DEBUG: PONTO 5: Chamando a função send_reset_password_email... ---")
        send_reset_password_email(email_to=user.email, token=token)
    else:
        print("--- DEBUG: PONTO 4: Usuário NÃO encontrado. Pulando o envio de e-mail. ---")
        
    print("--- DEBUG: PONTO 6: Fim da função. Retornando resposta de sucesso. ---\n")
    
    return {"message": "Se um usuário com este e-mail estiver registrado, um e-mail de redefinição de senha será enviado."}

@router.post(
    "/reset-password",
    summary="Efetivar redefinição de senha",
    status_code=status.HTTP_200_OK
)
def reset_password(
    payload: ResetPasswordSchema = Body(...),
    db: Session = Depends(get_db)
):
    try:
        # Decodificar o token para obter o email do usuário
        decoded_token = jwt.decode(payload.token, settings.SECRET_KEY, algorithms=["HS256"])
        
        # Verificar se o token é específico para reset de senha
        if decoded_token.get("scope") != "password_reset":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
            
        user_email = decoded_token.get("sub")
        if user_email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido: sem email")

    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido ou expirado")

    user = get_user_by_email(db, email=user_email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    # Atualizar a senha
    update_password(db=db, user=user, new_password=payload.new_password)

    return {"message": "Sua senha foi redefinida com sucesso."}

