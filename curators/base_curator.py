# curators/base_curator.py

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from models.content_models import CuratedContent, NewsItem, ResearchPaper, Repo
from services.news_service import NewsService

logger = logging.getLogger(__name__)

class ContentCurator:
    """
    Classe base para curadores de conteúdo.
    Implementa funcionalidades básicas de curadoria que podem ser estendidas
    por classes derivadas.
    """
    
    def __init__(self, config: Dict = None):
        """
        Inicializa o curador base
        
        Args:
            config: Configuração do curador
        """
        # Inicializa configurações
        config = config or {}
        
        # Configurações de fontes de dados
        self.rss_feeds = config.get('rss_feeds', [])
        self.api_keys = config.get('api_keys', {})
        
        # Inicializa serviços
        self.news_service = NewsService(self.rss_feeds)
        self.research_service = None  # Será inicializado nas classes derivadas se necessário
        self.repo_service = None      # Será inicializado nas classes derivadas se necessário
        
        logger.info("Curador de conteúdo base inicializado")
    
    async def get_curated_content(self, request: Dict) -> CuratedContent:
        """
        Método base para obter conteúdo curado.
        Retorna um objeto CuratedContent com notícias, papers e repos.
        
        Args:
            request: Parâmetros para a curadoria
            
        Returns:
            Objeto CuratedContent com o conteúdo curado
        """
        try:
            # Implementação base simples
            news = await self._get_news(request)
            papers = await self._get_research_papers(request)
            repos = await self._get_repositories(request)
            
            # Cria resposta
            curated_content = CuratedContent(
                news=news,
                papers=papers,
                repos=repos,
                timestamp=datetime.now().isoformat(),
                metadata={"source": "base_curator"}
            )
            
            return curated_content
        except Exception as e:
            logger.error(f"Erro ao obter conteúdo curado: {str(e)}")
            # Retorna objeto vazio em caso de erro
            return CuratedContent(
                news=[],
                papers=[],
                repos=[],
                timestamp=datetime.now().isoformat(),
                metadata={"source": "base_curator", "error": str(e)}
            )
    
    async def _get_news(self, request: Dict) -> List[NewsItem]:
        """
        Método base para obter notícias.
        A ser sobrescrito por classes derivadas.
        
        Args:
            request: Parâmetros para a curadoria
            
        Returns:
            Lista de NewsItem
        """
        # Implementação básica usando o news_service
        try:
            max_news = request.get('max_news', 10)
            keywords = request.get('keywords', None)
            return await self.news_service.get_top_news(max_news, keywords)
        except Exception as e:
            logger.error(f"Erro ao obter notícias: {str(e)}")
            return []
    
    async def _get_research_papers(self, request: Dict) -> List[ResearchPaper]:
        """
        Método base para obter papers de pesquisa.
        A ser sobrescrito por classes derivadas.
        
        Args:
            request: Parâmetros para a curadoria
            
        Returns:
            Lista de ResearchPaper
        """
        # Implementação base (vazia)
        return []
    
    async def _get_repositories(self, request: Dict) -> List[Repo]:
        """
        Método base para obter repositórios.
        A ser sobrescrito por classes derivadas.
        
        Args:
            request: Parâmetros para a curadoria
            
        Returns:
            Lista de Repo
        """
        # Implementação base (vazia)
        return []
