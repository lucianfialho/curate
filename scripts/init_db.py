# scripts/init_db.py
from models.database import Base
from config.database import engine

def init_database():
    """Inicializa o banco de dados, criando todas as tabelas."""
    Base.metadata.create_all(bind=engine)
    print("Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    init_database()