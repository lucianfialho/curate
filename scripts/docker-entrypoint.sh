#!/bin/bash
set -e

# Inicializa o banco de dados se necessário
python -m scripts.init_db

# Executa o comando especificado ou o padrão
if [ "$1" ]; then
  exec "$@"
else
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi