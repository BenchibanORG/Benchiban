import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Sendgrid para Envio de Emails
    SENDGRID_API_KEY: str
    EMAILS_FROM_EMAIL: str

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()
