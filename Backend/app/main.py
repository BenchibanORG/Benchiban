from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 1. Importe o Middleware

from db.base_class import Base
from db.session import engine
from api.endpoints import auth

# Cria todas as tabelas no banco de dados (na primeira inicialização)
Base.metadata.create_all(bind=engine)

app = FastAPI()

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
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def root():
    return {"message": "API funcionando!"}