from fastapi import FastAPI
from app.db.base_class import Base
from app.db.session import engine
from app.api.endpoints import auth

# Cria todas as tabelas no banco de dados (na primeira inicialização)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Inclui as rotas de autenticação
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def root():
    return {"message": "API funcionando!"}