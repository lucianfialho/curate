# repositories/news_repository.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta

from models.database import News, NewsCluster, Keyword, SentimentAnalysis
from repositories.base_repository import BaseRepository

class NewsRepository(BaseRepository[News]):
    """Repositório para operações com notícias."""
    
    def __init__(self, session: Session):
        super().__init__(session, News)
    
    def find_by_title_and_source(self, title: str, source: str) -> Optional[News]:
        """Busca notícia por título e fonte para verificar duplicatas."""
        return self.session.query(News).filter(
            News.title == title,
            News.source_name == source
        ).first()
    
    def find_similar_for_clustering(self, title: str, time_window_hours: int = 48) -> List[News]:
        """Busca notícias potencialmente similares para clustering."""
        time_threshold = datetime.utcnow() - timedelta(hours=time_window_hours)
        return self.session.query(News).filter(
            News.created_at >= time_threshold
        ).all()
    
    def get_latest_news(self, limit: int = 10, offset: int = 0) -> List[News]:
        """Busca as notícias mais recentes."""
        return self.session.query(News).order_by(
            desc(News.created_at)
        ).offset(offset).limit(limit).all()
    
    def get_by_keywords(self, keywords: List[str], limit: int = 10) -> List[News]:
        """Busca notícias relacionadas às palavras-chave."""
        return self.session.query(News).join(
            News.keywords
        ).filter(
            Keyword.word.in_(keywords)
        ).order_by(
            desc(News.created_at)
        ).limit(limit).all()
    
    def get_by_sentiment(self, sentiment: str, limit: int = 10) -> List[News]:
        """Busca notícias com um sentimento específico."""
        return self.session.query(News).join(
            News.sentiment_analysis
        ).filter(
            SentimentAnalysis.sentiment == sentiment
        ).order_by(
            desc(News.created_at)
        ).limit(limit).all()
    
    def save_with_keywords(self, news: News, keywords: List[str]) -> News:
        """Salva notícia com suas palavras-chave."""
        for keyword_text in keywords:
            # Busca ou cria palavra-chave
            keyword = self.session.query(Keyword).filter(Keyword.word == keyword_text).first()
            if not keyword:
                keyword = Keyword(word=keyword_text)
                self.session.add(keyword)
            
            # Adiciona relação
            news.keywords.append(keyword)
        
        self.session.add(news)
        self.session.commit()
        self.session.refresh(news)
        return news