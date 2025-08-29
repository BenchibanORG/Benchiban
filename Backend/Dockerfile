# Estágio 1: Define a imagem base do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências primeiro para aproveitar o cache do Docker
# Crie um arquivo chamado "requirements.txt" com a lista de bibliotecas (ex: fastapi, uvicorn, scrapy, beautifulsoup4, requests, mysql-connector-python)
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para o diretório de trabalho
COPY . .

# Expõe a porta que a API vai rodar (Uvicorn usa 8000 por padrão)
EXPOSE 8000

# Comando para iniciar a aplicação quando o contêiner for executado
# Este comando assume que você tem um arquivo chamado "main.py" e dentro dele uma instância do FastAPI chamada "app"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]