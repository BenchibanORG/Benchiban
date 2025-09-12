import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Apenas as variáveis que sua aplicação realmente usa precisam ser definidas aqui
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # A linha abaixo diz ao Pydantic para ignorar as variáveis extras
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()
