# jobs/run_collectors.py
import asyncio
import logging
from datetime import datetime, timedelta
import sys
import os

# Importações de serviços
from services.news_service import NewsService
from services.github_service import GitHubScanner
from services.research_service import ResearchService
from services.event_service import EventsService

# Importações de configuração
from config.settings import get_settings
from config.database import get_db_session

# Importações de modelos
from models.database import CollectionJob, News, Repository, Keyword

# Importações de repositórios
from repositories.news_repository import NewsRepository
from repositories.base_repository import BaseRepository

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentCollector:
    """Classe principal para coleta de conteúdo de diferentes fontes"""
    
    def __init__(self, config=None):
        """
        Inicializa os coletores com configurações
        
        Args:
            config: Configurações personalizadas (opcional)
        """
        # Carrega configurações
        self.settings = config or get_settings()
        
        # Inicializa serviços
        self.news_service = NewsService(self.settings.rss_feeds)
        self.github_python_scanner = GitHubScanner(
            self.settings.github_python_url, 
            top_n=10
        )
        self.github_js_scanner = GitHubScanner(
            self.settings.github_javascript_url, 
            top_n=10
        )
        self.research_service = ResearchService(
            {'arxiv_url': self.settings.arxiv_url}
        )
        self.events_service = EventsService()
        
        # Configurações de coleta
        self.collection_interval = timedelta(hours=4)  # Coleta a cada 4 horas
        self.max_retries = 3
    
    async def collect_news(self, session):
        """
        Coleta notícias de fontes RSS configuradas
        
        Args:
            session: Sessão do banco de dados
        """
        try:
            logger.info("Iniciando coleta de notícias")
            
            # Criar job de coleta
            job = CollectionJob(
                job_type="news",
                status="running"
            )
            session.add(job)
            session.commit()
            
            # Busca notícias
            news_items = await self.news_service.get_top_news(max_items=50)
            
            # Inicializa repositório de notícias
            news_repo = NewsRepository(session)
            saved_count = 0
            
            for item in news_items:
                # Verifica se a notícia já existe
                existing_news = news_repo.find_by_title_and_source(item.title, item.source)
                
                if not existing_news:
                    # Cria objeto de notícia para salvar
                    news = News(
                        title=item.title,
                        description=item.description,
                        link=item.link,
                        source_name=item.source,
                        read_time=item.read_time,
                        published_date=item.additional_info.get('published_date') if item.additional_info else None,
                        author=item.additional_info.get('author') if item.additional_info else None
                    )
                    
                    # Extrai palavras-chave
                    keywords = []
                    if item.additional_info and 'categories' in item.additional_info:
                        keywords = item.additional_info['categories']
                    
                    # Se não tiver categorias, gera palavras-chave simples
                    if not keywords:
                        # Método simples de extração de palavras-chave
                        keywords = [word.lower() for word in item.title.split() if len(word) > 3][:5]
                    
                    # Salva notícia com palavras-chave usando o método do repositório
                    news_repo.save_with_keywords(news, keywords)
                    saved_count += 1
            
            # Atualiza status do job
            job.status = "completed"
            job.end_time = datetime.utcnow()
            job.items_collected = saved_count
            session.commit()
            
            logger.info(f"Coleta de notícias concluída. Total: {saved_count} notícias salvas")
        
        except Exception as e:
            logger.error(f"Erro na coleta de notícias: {str(e)}", exc_info=True)
            # Em caso de erro, atualiza status do job
            job.status = "failed"
            job.end_time = datetime.utcnow()
            job.error_message = str(e)
            session.commit()
    
    async def collect_repositories(self, session):
        """
        Coleta repositórios em tendência do GitHub
        
        Args:
            session: Sessão do banco de dados
        """
        try:
            logger.info("Iniciando coleta de repositórios")
            
            # Criar job de coleta
            job = CollectionJob(
                job_type="repos",
                status="running"
            )
            session.add(job)
            session.commit()
            
            # Coleta repositórios Python e JavaScript
            python_repos = await self.github_python_scanner.get_trending_repos()
            js_repos = await self.github_js_scanner.get_trending_repos()
            
            # Combina repositórios
            all_repos = python_repos + js_repos
            
            # Repositório base para salvar
            repo_repo = BaseRepository(session, Repository)
            saved_count = 0
            
            for repo in all_repos:
                # Verifica se o repositório já existe
                existing_repo = session.query(Repository).filter_by(
                    title=repo.name, 
                    link=repo.link
                ).first()
                
                if not existing_repo:
                    # Cria novo repositório
                    repository = Repository(
                        title=repo.name,
                        description=repo.summary,
                        link=repo.link,
                        source_name=repo.source or "GitHub",
                        type='repo'
                    )
                    
                    # Salva repositório
                    repo_repo.create(repository)
                    saved_count += 1
            
            # Atualiza status do job
            job.status = "completed"
            job.end_time = datetime.utcnow()
            job.items_collected = saved_count
            session.commit()
            
            logger.info(f"Coleta de repositórios concluída. Total: {saved_count} repositórios")
        
        except Exception as e:
            logger.error(f"Erro na coleta de repositórios: {str(e)}", exc_info=True)
            # Em caso de erro, atualiza status do job
            job.status = "failed"
            job.end_time = datetime.utcnow()
            job.error_message = str(e)
            session.commit()
    
    async def collect_research_papers(self, session):
        """
        Coleta papers de pesquisa do arXiv
        
        Args:
            session: Sessão do banco de dados
        """
        try:
            logger.info("Iniciando coleta de papers de pesquisa")
            
            # Criar job de coleta
            job = CollectionJob(
                job_type="papers",
                status="running"
            )
            session.add(job)
            session.commit()
            
            # Coleta papers de pesquisa
            research_papers = await self.research_service.get_research_papers()
            
            # Repositório base para salvar
            paper_repo = BaseRepository(session, Repository)
            saved_count = 0
            
            for paper in research_papers:
                # Verifica se o paper já existe
                existing_paper = session.query(Repository).filter_by(
                    title=paper.title, 
                    link=paper.link
                ).first()
                
                if not existing_paper:
                    # Cria novo paper
                    repository = Repository(
                        title=paper.title,
                        description=paper.abstract,
                        link=paper.link,
                        source_name=paper.publication,
                        type='paper'
                    )
                    
                    # Salva paper
                    paper_repo.create(repository)
                    saved_count += 1
            
            # Atualiza status do job
            job.status = "completed"
            job.end_time = datetime.utcnow()
            job.items_collected = saved_count
            session.commit()
            
            logger.info(f"Coleta de papers concluída. Total: {saved_count} papers")
        
        except Exception as e:
            logger.error(f"Erro na coleta de papers: {str(e)}", exc_info=True)
            # Em caso de erro, atualiza status do job
            job.status = "failed"
            job.end_time = datetime.utcnow()
            job.error_message = str(e)
            session.commit()
    
    async def collect_events(self, session):
        """
        Coleta eventos relacionados a AI
        
        Args:
            session: Sessão do banco de dados
        """
        try:
            logger.info("Iniciando coleta de eventos")
            
            # Criar job de coleta
            job = CollectionJob(
                job_type="events",
                status="running"
            )
            session.add(job)
            session.commit()
            
            # Coleta eventos
            events = await self.events_service.get_upcoming_events()
            
            # Repositório base para salvar
            event_repo = BaseRepository(session, Repository)
            saved_count = 0
            
            for event in events:
                # Verifica se o evento já existe
                existing_event = session.query(Repository).filter_by(
                    title=event.title, 
                    link=event.location
                ).first()
                
                if not existing_event:
                    # Cria novo evento
                    repository = Repository(
                        title=event.title,
                        description=event.description,
                        link=event.location,
                        source_name="AIEvents",
                        type='event'
                    )
                    
                    # Salva evento
                    event_repo.create(repository)
                    saved_count += 1
            
            # Atualiza status do job
            job.status = "completed"
            job.end_time = datetime.utcnow()
            job.items_collected = saved_count
            session.commit()
            
            logger.info(f"Coleta de eventos concluída. Total: {saved_count} eventos")
        
        except Exception as e:
            logger.error(f"Erro na coleta de eventos: {str(e)}", exc_info=True)
            # Em caso de erro, atualiza status do job
            job.status = "failed"
            job.end_time = datetime.utcnow()
            job.error_message = str(e)
            session.commit()
    
    async def run_collectors(self):
        """
        Executa todos os coletores periodicamente
        """
        logger.info("Iniciando processo de coleta de conteúdo")
        
        try:
            while True:
                # Usa session manager para garantir fechamento correto
                with get_db_session() as session:
                    try:
                        # Executa coletas em paralelo
                        await asyncio.gather(
                            self.collect_news(session),
                            self.collect_repositories(session),
                            self.collect_research_papers(session),
                            self.collect_events(session)
                        )
                    except Exception as parallel_error:
                        logger.error(f"Erro em coletas paralelas: {str(parallel_error)}", exc_info=True)
                
                # Aguarda até o próximo ciclo de coleta
                logger.info(f"Próxima coleta em {self.collection_interval}")
                await asyncio.sleep(self.collection_interval.total_seconds())
        
        except KeyboardInterrupt:
            logger.info("Coleta de conteúdo interrompida pelo usuário.")
        except Exception as e:
            logger.error(f"Erro crítico no processo de coleta: {str(e)}", exc_info=True)
            sys.exit(1)

async def main():
    """Função principal para iniciar o coletor"""
    collector = ContentCollector()
    await collector.run_collectors()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Coletor encerrado.")
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        sys.exit(1)