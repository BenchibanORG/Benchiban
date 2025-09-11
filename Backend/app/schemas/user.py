from pydantic import BaseModel, EmailStr

# Schema para receber dados de criação de usuário
class UserCreate(BaseModel):
    email: EmailStr
    password: str

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