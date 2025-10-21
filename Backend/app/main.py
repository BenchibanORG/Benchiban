from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 1. Importe o Middleware
from app.db.base_class import Base
from app.db.session import engine
from app.api.endpoints import auth
from app.api.endpoints import auth, products
from app.db.base_class import Base
from app.db.session import engine

# Cria todas as tabelas no banco de dados (na primeira inicialização)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Benchiban API")

# Origem do FrontEnd
origins = [
    "http://localhost:3000",
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