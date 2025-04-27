# services/enhanced_news_service.py
# Exemplo de como adaptar o serviço de notícias para usar armazenamento persistente

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from models.database import News, NewsCluster, SentimentAnalysis
from repositories.news_repository import NewsRepository
from services.news_service import NewsService  # Serviço original
from utils.clustering import NewsClusteringService

logger = logging.getLogger(__name__)

class EnhancedNewsService:
    """Serviço aprimorado que combina buscas em tempo real com armazenamento persistente."""
    
    def __init__(self, db_session, rss_urls: List[str], max_age_hours: int = 24):
        self.db_session = db_session
        self.news_repo = NewsRepository(db_session)
        self.original_service = NewsService(rss_urls)
        self.clustering_service = NewsClusteringService()
        self.max_age_hours = max_age_hours
    
    async def get_top_news(self, max_items: int = 10, keywords: List[str] = None, 
                          include_stored: bool = True, force_fresh: bool = False) -> List[News]:
        """
        Retorna notícias combinando dados armazenados com novas buscas.
        
        Args:
            max_items: Número máximo de notícias
            keywords: Palavras-chave para filtrar
            include_stored: Se deve incluir notícias armazenadas
            force_fresh: Se deve forçar busca de novas notícias
            
        Returns:
            Lista de objetos News
        """
        result_news = []
        
        # 1. Obter notícias armazenadas se solicitado
        if include_stored and not force_fresh:
            stored_news = []
            if keywords:
                stored_news = self.news_repo.get_by_keywords(keywords, max_items)
            else:
                stored_news = self.news_repo.get_latest_news(max_items)
                
            # Se temos notícias suficientes e recentes, usamos apenas o armazenamento
            if len(stored_news) >= max_items and not force_fresh:
                return stored_news[:max_items]
                
            # Caso contrário, incluímos as armazenadas e buscamos o restante
            result_news.extend(stored_news)
        
        # 2. Buscar novas notícias
        # Determinamos quantas notícias ainda precisamos
        needed_news = max(0, max_items - len(result_news))
        
        if needed_news > 0 or force_fresh:
            # Buscamos o dobro para ter margem para filtragem de duplicatas
            fresh_news_items = await self.original_service.get_top_news(
                needed_news * 2, keywords
            )
            
            # Converter para objetos do banco de dados e salvar
            for item in fresh_news_items:
                # Verificar se já existe
                existing = self.news_repo.find_by_title_and_source(item.title, item.source)
                if existing:
                    # Já existe, incluir se ainda não estiver na lista
                    if existing not in result_news:
                        result_news.append(existing)
                else:
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
                    
                    # Extrair palavras-chave do conteúdo ou usar as fornecidas
                    extracted_keywords = keywords or self._extract_keywords(item)
                    
                    # Salvar com keywords
                    saved_news = self.news_repo.save_with_keywords(news_db, extracted_keywords)
                    
                    # Adicionar análise de sentimento se disponível
                    if hasattr(item, 'sentiment_analysis') and item.sentiment_analysis:
                        sentiment = SentimentAnalysis(
                            content_id=saved_news.id,
                            sentiment=item.sentiment_analysis.get('overall_sentiment', 'neutral'),
                            polarity=item.sentiment_analysis.get('mean_polarity', 0.0),
                            subjectivity=item.sentiment_analysis.get('subjectivity', 0.0),
                            confidence=item.sentiment_analysis.get('confidence', 0.0)
                        )
                        self.db_session.add(sentiment)
                        self.db_session.commit()
                    
                    result_news.append(saved_news)
                    
                    # Limitar ao máximo solicitado
                    if len(result_news) >= max_items:
                        break
        
        # Retornar resultado limitado
        return result_news[:max_items]
    
    def _extract_keywords(self, news_item) -> List[str]:
        """Extrai palavras-chave do conteúdo da notícia."""
        # Implementação básica - poderia ser aprimorada com NLP
        # Por enquanto, apenas retorna algumas palavras do título
        if not news_item.title:
            return []
            
        words = news_item.title.lower().split()
        # Filtrar palavras muito curtas e comuns
        words = [w for w in words if len(w) > 3]
        return words[:5]  # Limitar a 5 palavras-chave