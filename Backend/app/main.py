from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.base_class import Base
from app.db.session import engine
from app.core.scheduler import start_scheduler
from app.models.product import Product, PriceHistory  # noqa: F401
from app.models.user import User  # noqa: F401
from app.api.endpoints import auth, products, current_exchange

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica de Início
    print("--- Criando Tabelas no Banco de Dados (se não existirem) ---")
    Base.metadata.create_all(bind=engine)
    
    print("--- Inicializando Agendador de Tarefas ---")
    start_scheduler()
    
    yield

# Passamos o lifespan na criação do app
app = FastAPI(title="Benchiban API", lifespan=lifespan)

# Origem do FrontEnd e Backend
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://benchiban.azurewebsites.net", 
    "https://black-mud-07542d60f.3.azurestaticapps.net" 
]

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROTAS ---

# Autenticação
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# Produtos (Scraping e Comparação)
app.include_router(products.router, prefix="/api/products", tags=["products"])

# Câmbio
app.include_router(current_exchange.router, prefix="/api/exchange-rate", tags=["exchange-rate"])

@app.get("/")
def root():
    return {"message": "API funcionando!"}