from pydantic import BaseModel, EmailStr, Field

class ForgotPasswordSchema(BaseModel):
   
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    
    token: str
    new_password: str = Field(
        ..., 
        min_length=8, 
        description="A nova senha deve ter no mínimo 8 caracteres."
    )