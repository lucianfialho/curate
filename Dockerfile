FROM python:3.11-slim

WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY . .

# Cria diretório para dados
RUN mkdir -p data && chmod 777 data

# Expõe porta da API
EXPOSE 8000

# Comando para execução
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]