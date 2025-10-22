from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Carrega e valida as variáveis de ambiente da aplicação usando a sintaxe da Pydantic V2.
    """
    # Define a configuração para ler o arquivo .env
    # Esta linha substitui a necessidade da classe interna 'Config'
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra='ignore')

    # Define todas as suas variáveis de ambiente aqui
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Credenciais de Serviços Externos
    SENDGRID_API_KEY: str
    EMAILS_FROM_EMAIL: str
    EBAY_APP_ID: str
    EBAY_CLIENT_SECRET: str
    EBAY_REFRESH_TOKEN: str

# Cria a instância única das configurações para ser usada em toda a aplicação
settings = Settings()