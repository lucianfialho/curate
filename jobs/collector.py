# jobs/collector.py
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from models.database import CollectionJob, News
from repositories.news_repository import NewsRepository
from services.news_service import NewsService
from config.database import get_db_session

logger = logging.getLogger(__name__)

class NewsCollectorJob:
    """Job para coleta periódica de notícias."""
    
    def __init__(self, rss_urls: List[str]):
        self.rss_urls = rss_urls
        self.news_service = NewsService(rss_urls)
    
    async def run(self):
        """Executa o job de coleta."""
        job = None
        
        with get_db_session() as session:
            # Registrar início do job
            job = CollectionJob(
                job_type="news",
                status="running"
            )
            session.add(job)
            session.commit()
            
            try:
                # Obter notícias
                news_repo = NewsRepository(session)
                news_items = await self.news_service.get_top_news(100)  # Coletamos mais para ter variedade
                
                # Processar e salvar
                saved_count = 0
                for item in news_items:
                    # Verificar se já existe
                    existing = news_repo.find_by_title_and_source(item.title, item.source)
                    if not existing:
                        # Nova notícia, criar objeto e salvar
                        news_db = News(
                            title=item.title,
                            description=item.description,
                            link=item.link,
                            source_name=item.source,
                            read_time=item.read_time,
                            published_date=item.additional_info.get('published_date') if item.additional_info else None,
                            author=item.additional_info.get('author') if item.additional_info else None
                        )
                        
                        # Extrair palavras-chave
                        extracted_keywords = self._extract_keywords(item)
                        
                        # Salvar
                        news_repo.save_with_keywords(news_db, extracted_keywords)
                        saved_count += 1
                
                # Atualizar status do job
                job.status = "completed"
                job.end_time = datetime.utcnow()
                job.items_collected = saved_count
                session.commit()
                
                logger.info(f"Coleta de notícias concluída. Salvas {saved_count} novas notícias.")
                
            except Exception as e:
                # Registrar erro
                if job:
                    job.status = "failed"
                    job.end_time = datetime.utcnow()
                    job.error_message = str(e)
                    session.commit()
                
                logger.error(f"Erro na coleta de notícias: {str(e)}", exc_info=True)
                
    def _extract_keywords(self, news_item) -> List[str]:
        """Extrai palavras-chave do conteúdo da notícia."""
        # Implementação básica - poderia ser aprimorada com NLP
        if not news_item.title:
            return []
            
        words = news_item.title.lower().split()
        # Filtrar palavras muito curtas e comuns
        words = [w for w in words if len(w) > 3]
        return words[:5]  # Limitar a 5 palavras-chave