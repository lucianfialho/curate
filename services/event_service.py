import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime

from models.content_models import Event

logger = logging.getLogger(__name__)

class EventsService:
    """Serviço para coleta de eventos relacionados a IA"""
    
    def __init__(self, events_url=None, rss_feed_url=None, top_n=3):
        self.events_url = events_url or "https://example.com/ai-events"
        self.rss_feed_url = rss_feed_url or "https://aiml.events/feed/rss/"
        self.top_n = top_n
        self.events = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
    def _fetch_events(self) -> List[Dict]:
        """Implementação base de coleta de eventos"""
        # Este método seria implementado para buscar de fontes reais
        # Por enquanto, retornamos eventos de exemplo
        
        events = [
            {
                "title": "AI Conference 2025",
                "date": "June 15-18, 2025",
                "location": "San Francisco, CA",
                "description": "Annual conference focusing on the latest AI research and applications."
            },
            {
                "title": "Deep Learning Workshop",
                "date": "May 10, 2025",
                "location": "Online",
                "description": "Intensive workshop on deep learning techniques with hands-on sessions."
            },
            {
                "title": "AI Ethics Summit",
                "date": "July 22-23, 2025",
                "location": "London, UK",
                "description": "Discussion on ethical considerations in AI development and deployment."
            }
        ]
        return events
        
    def filter_by_keywords(self, events: List[Dict], keywords: List[str]) -> List[Dict]:
        """Filtra eventos por palavras-chave"""
        if not keywords:
            return events
            
        filtered_events = []
        for event in events:
            content = f"{event['title']} {event['description']}".lower()
            if any(keyword.lower() in content for keyword in keywords):
                filtered_events.append(event)
                
        return filtered_events
        
    async def get_upcoming_events(self, keywords: List[str] = None) -> List[Event]:
        """Retorna os próximos eventos"""
        events = self._fetch_events()
        
        # Filtra por palavras-chave se fornecidas
        if keywords:
            events = self.filter_by_keywords(events, keywords)
            if not events:
                logger.warning(f"Nenhum evento encontrado com as palavras-chave: {keywords}")
                return []
        
        # Converte para objetos Event
        event_objects = []
        for event in events[:self.top_n]:
            event_obj = Event(
                title=event["title"],
                date=event["date"],
                location=event["location"],
                description=event["description"]
            )
            event_objects.append(event_obj)
            
        return event_objects