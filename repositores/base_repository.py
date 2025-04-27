# repositories/base_repository.py
from sqlalchemy.orm import Session
from typing import Generic, TypeVar, Type, List, Optional, Dict, Any

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Repositório base para operações de CRUD."""
    
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Busca entidade pelo ID."""
        return self.session.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self) -> List[T]:
        """Busca todas as entidades."""
        return self.session.query(self.model_class).all()
    
    def create(self, entity: T) -> T:
        """Cria uma nova entidade."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """Atualiza uma entidade existente."""
        entity = self.get_by_id(id)
        if entity:
            for key, value in data.items():
                setattr(entity, key, value)
            self.session.commit()
            self.session.refresh(entity)
        return entity
    
    def delete(self, id: int) -> bool:
        """Remove uma entidade."""
        entity = self.get_by_id(id)
        if entity:
            self.session.delete(entity)
            self.session.commit()
            return True
        return False