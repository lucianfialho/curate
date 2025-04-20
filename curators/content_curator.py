# curators/content_curator.py

import logging
from typing import Dict, List, Any, Optional

from models.content_models import ContentSource, EnhancedNewsItem, EnhancedResearchPaper, EnhancedRepo, CuratedContent
from curators.base_curator import ContentCurator
from utils.clustering import NewsClusteringService

logger = logging.getLogger(__name__)

class EnhancedContentCurator(ContentCurator):
    """
    Curador de conteúdo aprimorado com agrupamento de notícias similares
    e fontes unificadas para o mesmo tópico.
    """
    
    def __init__(self, config: Dict = None):
        """
        Inicializa o curador aprimorado
        
        Args:
            config: Configuração do curador
        """
        # Inicializa a classe base
        super().__init__(config)
        
        # Configurações adicionais
        config = config or {}
        self.similarity_threshold = config.get('similarity_threshold', 0.6)
        
        # Inicializa serviço de clustering
        self.news_clustering = NewsClusteringService(self.similarity_threshold)
        logger.info(f"Curador de conteúdo aprimorado inicializado (threshold: {self.similarity_threshold})")
    
    async def close(self):
        """Fecha recursos e conexões assíncronas"""
        try:
            if hasattr(self, 'news_service') and self.news_service:
                await self.news_service.close()
            logger.info("Recursos do curador de conteúdo aprimorado fechados")
        except Exception as e:
            logger.error(f"Erro ao fechar recursos do curador: {str(e)}")
    
    async def __aenter__(self):
        """Suporte para uso com context manager"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup ao sair do context manager"""
        await self.close()
        
    async def get_curated_content(self, request: Dict) -> CuratedContent:
        """
        Retorna conteúdo curado com agrupamento de fontes similares
        
        Args:
            request: Parâmetros para a curadoria
            
        Returns:
            Objeto CuratedContent com o conteúdo curado
        """
        enhanced_news = []
        try:
            # Obtém parâmetros de busca
            max_news = request.get('max_news', 10)
            keywords = request.get('keywords', None)
            
            # Coleta notícias usando a API pública do serviço de notícias
            logger.info(f"Obtendo top notícias com keywords: {keywords}")
            news_items = await self.news_service.get_top_news(max_news * 3, keywords)  # Pegamos mais para agrupar depois
            
            # Converte objetos NewsItem para dicionários para processamento
            all_news = []
            for item in news_items:
                news_dict = {
                    'title': item.title,
                    'description': item.description,
                    'link': item.link,
                    'source': item.source or 'Unknown Source',
                    'read_time': item.read_time,
                    'additional_info': item.additional_info or {},
                    'full_text': f"{item.title} {item.description}"
                }
                all_news.append(news_dict)
            
            if not all_news:
                logger.warning("Nenhuma notícia encontrada")
            else:
                logger.info(f"Processando {len(all_news)} notícias para agrupamento")
                # Agrupa notícias similares
                news_clusters = self.news_clustering.cluster_news(all_news)
                formatted_news = self.news_clustering.format_clustered_news(news_clusters)
                
                # Limita ao número máximo solicitado
                formatted_news = formatted_news[:max_news]
                
                # Converte para objetos EnhancedNewsItem
                for item in formatted_news:
                    # Converte fontes para o modelo ContentSource
                    sources = []
                    for source in item['sources']:
                        content_source = ContentSource(
                            name=source['name'],
                            link=source['link'],
                            published_date=str(source['published_date']) if 'published_date' in source else None,
                            author=source.get('author')
                        )
                        sources.append(content_source)
                    
                    # Cria objeto EnhancedNewsItem
                    news_item = EnhancedNewsItem(
                        title=item['title'],
                        description=item['description'],
                        primary_link=item['link'],
                        read_time=item['read_time'],
                        primary_source=item['source'],
                        sources=sources,
                        source_count=len(sources),
                        relevance_score=item['importance_score'],
                        keywords=request.get('keywords'),
                        categories=None  # Poderia ser implementado em uma versão futura
                    )
                    enhanced_news.append(news_item)
                
                logger.info(f"Criados {len(enhanced_news)} itens aprimorados de notícias")
        except Exception as e:
            logger.error(f"Erro ao processar notícias: {str(e)}")
            # Em caso de erro, continuamos com enhanced_news vazio
        
        # Coleta informações de outras fontes (processamento paralelo)
        max_papers = request.get('max_papers', 5)
        max_repos = request.get('max_repos', 5)
        
        # Usa métodos da classe base para coletar repos, papers e eventos
        base_content = await super().get_curated_content(request)
        
        # Converte repos para EnhancedRepo
        enhanced_repos = []
        for repo in base_content.repos[:max_repos]:
            enhanced_repo = EnhancedRepo(
                name=repo.name,
                link=repo.link,
                summary=repo.summary,
                source=repo.source or "GitHub",
                stars=repo.engagement,
                forks=None,
                contributors=None,
                relevance_score=min(float(repo.engagement or 0) / 1000, 1.0) if repo.engagement and repo.engagement.isdigit() else 0.5,
                recent_activity=None,
                categories=None
            )
            enhanced_repos.append(enhanced_repo)
            
        # Converte papers para EnhancedResearchPaper
        enhanced_papers = []
        for paper in base_content.papers[:max_papers]:
            enhanced_paper = EnhancedResearchPaper(
                title=paper.title,
                authors=paper.authors,
                abstract=paper.abstract,
                primary_publication=paper.publication,
                link=paper.link,
                date=paper.date,
                cited_by=None,
                citations_count=None,
                relevance_score=float(paper.engagement) if paper.engagement and paper.engagement.replace('.', '', 1).isdigit() else 0.5,
                related_papers=None
            )
            enhanced_papers.append(enhanced_paper)
        
        # Cria resposta final
        curated_content = CuratedContent(
            news=enhanced_news,
            papers=enhanced_papers,
            repos=enhanced_repos,
            timestamp=base_content.timestamp,
            metadata=base_content.metadata
        )
        
        return curated_content