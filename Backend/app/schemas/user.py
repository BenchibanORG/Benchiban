from pydantic import BaseModel, EmailStr, Field

# Schema para receber dados de criação de usuário
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, description="Senha não pode ser vazia")

# Schema para retornar dados do usuário (sem a senha)
class UserRead(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

# Schema para a resposta do token de login
class Token(BaseModel):
    access_token: str
    token_type: str