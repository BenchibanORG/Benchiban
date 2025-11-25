from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.base_class import Base
from app.api.endpoints import auth, products
from app.db.session import engine
from app.models.product import Product, PriceHistory
from app.models.user import User
from app.core.scheduler import start_scheduler

# Cria todas as tabelas no banco de dados (na primeira inicialização)
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica de Início
    print("--- Criando Tabelas no Banco de Dados ---")
    Base.metadata.create_all(bind=engine)
    
    print("--- Inicializando Agendador de Tarefas ---")
    start_scheduler()
    
    yield

# Passamos o lifespan na criação do app
app = FastAPI(title="Benchiban API", lifespan=lifespan)

# Origem do FrontEnd e Backend
origins = [
    "http://localhost:3000",#frontend local
    "http://localhost:8000",# backend local
    "https://benchiban.azurewebsites.net", #backend em nuvem
    "https://black-mud-07542d60f.3.azurestaticapps.net" #frontend em nuvem
]

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas de autenticação
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

#Rota de Produtos
app.include_router(products.router, prefix="/api/products", tags=["products"])

@app.get("/")
def root():
    return {"message": "API funcionando!"}