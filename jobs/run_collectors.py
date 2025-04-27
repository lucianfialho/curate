# jobs/run_collectors.py
import asyncio
import logging
from datetime import datetime
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Implementação temporária para o coletor
async def run_collector():
    """Função principal do coletor de conteúdo"""
    logger.info("Iniciando coletor de conteúdo...")
    
    # Aqui implementaremos a lógica de coleta
    # Por enquanto, apenas log para verificar funcionamento
    logger.info("Coletor em execução.")
    
    try:
        # Manter o processo em execução
        while True:
            logger.info(f"Coletor ativo em {datetime.now().isoformat()}")
            await asyncio.sleep(300)  # Aguarda 5 minutos entre verificações
    except KeyboardInterrupt:
        logger.info("Coletor encerrado pelo usuário.")
    except Exception as e:
        logger.error(f"Erro no coletor: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_collector())
    except KeyboardInterrupt:
        logger.info("Coletor encerrado.")
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        sys.exit(1)