# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os

from config.settings import get_settings

settings = get_settings()

# Pegar a URL do ambiente ou usar o padrão
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@db:5432/ailert"  # Use 'db' como host, não 'localhost'
)

engine = create_engine(DATABASE_URL)

# Criar fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar base para modelos
Base = declarative_base()

@contextmanager
def get_db_session():
    """Gerenciador de contexto para uso da sessão."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()