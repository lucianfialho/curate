import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

from models.content_models import Repo

logger = logging.getLogger(__name__)

class GitHubScanner:
    """Serviço para coleta de repositórios em tendência no GitHub"""
    
    def __init__(self, site_url, top_n=5):
        self.site_url = site_url
        self.top_n = top_n
        self.response = []
        logger.info(f"GitHubScanner initialized with URL: {site_url}, top_n: {top_n}")

    def _extract_from_html(self, link):
        """Extrai repositórios da página de trending do GitHub"""
        repos = []
        try:
            logger.debug(f"Iniciando extração de repositórios do URL: {link}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Requisição HTTP
            logger.debug("Fazendo requisição HTTP...")
            response = requests.get(link, headers=headers)
            logger.debug(f"Status Code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Erro na requisição HTTP. Status code: {response.status_code}")
                logger.error(f"Response content: {response.text[:500]}...")  # Primeiros 500 caracteres
                return []
            
            response.raise_for_status()
            
            # Parsing HTML
            logger.debug("Fazendo parsing do HTML...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscando repositórios
            logger.debug("Buscando articles com class 'Box-row'...")
            repo_list = soup.find_all('article', class_='Box-row')
            logger.debug(f"Encontrados {len(repo_list)} articles com class 'Box-row'")
            
            # Se não encontrar Box-row, verifica se há outro formato
            if not repo_list:
                logger.debug("Não encontrou articles com class 'Box-row'. Tentando selector alternativo...")
                repo_list = soup.find_all('div', class_='repository')
                logger.debug(f"Encontrados {len(repo_list)} divs com class 'repository'")
            
            # Log da estrutura HTML para debug
            if not repo_list:
                logger.error("Não encontrou repositórios na página. Estrutura HTML (primeiros 1000 caracteres):")
                logger.error(str(soup)[:1000])
            
            for idx, repo in enumerate(repo_list):
                try:
                    logger.debug(f"Processando repositório {idx + 1} de {len(repo_list)}...")
                    
                    # Nome do repositório
                    name_elem = repo.find('h2', class_='h3')
                    if not name_elem:
                        logger.warning(f"Não encontrou elemento h2 com class 'h3' no repositório {idx + 1}")
                        name_elem = repo.find('h1', class_='h3')  # Tentativa alternativa
                    
                    name = name_elem.text.strip().replace('\n', '').replace(' ', '') if name_elem else "Unknown Repo"
                    logger.debug(f"Nome do repositório: {name}")

                    # Descrição
                    description_elem = repo.find('p', class_='col-9 color-fg-muted my-1 pr-4')
                    if not description_elem:
                        logger.warning(f"Não encontrou descrição no repositório {idx + 1}")
                        description_elem = repo.find('p')  # Tentativa alternativa
                    
                    description = description_elem.text.strip() if description_elem else "Sem descrição disponível."
                    logger.debug(f"Descrição: {description[:50]}...")  # Primeiros 50 caracteres

                    # Stars
                    stars_element = repo.find('a', class_='Link Link--muted d-inline-block mr-3') or \
                                   repo.find('a', class_='Link--muted d-inline-block mr-3')
                    stars = stars_element.text.strip().replace(',', '') if stars_element else "0"
                    logger.debug(f"Stars: {stars}")

                    # Forks
                    fork_elements = repo.find_all('a', class_='Link Link--muted d-inline-block mr-3') or \
                                   repo.find_all('a', class_='Link--muted d-inline-block mr-3')
                    
                    forks = fork_elements[1].text.strip().replace(',', '') if len(fork_elements) > 1 else "0"
                    logger.debug(f"Forks: {forks}")

                    repos.append({
                        'name': name,
                        'description': description,
                        'stars': stars,
                        'forks': forks
                    })
                    
                    logger.info(f"Repositório extraído com sucesso: {name} (stars: {stars}, forks: {forks})")
                    
                except Exception as e:
                    logger.error(f"Erro extraindo dados do repositório {idx + 1}: {str(e)}", exc_info=True)
                    continue

            logger.info(f"Extração finalizada. Total de {len(repos)} repositórios extraídos de {len(repo_list)} encontrados")
            return repos[:self.top_n]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de requisição ao acessar o GitHub: {str(e)}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Erro não esperado ao extrair repositórios do GitHub: {str(e)}", exc_info=True)
            return []
            
    def filter_by_keywords(self, repos: List[Dict], keywords: List[str]) -> List[Dict]:
        """Filtra repositórios por palavras-chave"""
        if not keywords:
            logger.debug("Nenhuma palavra-chave fornecida para filtro. Retornando todos os repositórios.")
            return repos
        
        logger.debug(f"Filtrando repositórios com as palavras-chave: {keywords}")
        filtered_repos = []
        for repo in repos:
            content = f"{repo['name']} {repo['description']}".lower()
            if any(keyword.lower() in content for keyword in keywords):
                filtered_repos.append(repo)
                logger.debug(f"Repositório '{repo['name']}' corresponde ao filtro")
        
        logger.info(f"Filtro resultou em {len(filtered_repos)} repositórios de {len(repos)} originais")
        return filtered_repos

    async def get_trending_repos(self, keywords: List[str] = None) -> List[Repo]:
        """Retorna os repositórios em tendência no GitHub"""
        logger.info("Iniciando busca por repositórios em tendência...")
        
        try:
            # Extraindo repositórios
            repositories = self._extract_from_html(self.site_url)
            logger.debug(f"Repositories extracted: {len(repositories)}")
            
            # Se a extração falhou, log e retorno
            if not repositories:
                logger.warning("Nenhum repositório extraído. Verifique se a estrutura do GitHub mudou.")
                return []
            
            # Filtra por palavras-chave se fornecidas
            if keywords:
                repositories = self.filter_by_keywords(repositories, keywords)
                if not repositories:
                    logger.warning(f"Nenhum repositório encontrado com as palavras-chave: {keywords}")
                    return []
            
            # Converte para objetos Repo
            trending_repos = []
            for repo in repositories:
                try:
                    repo_obj = Repo(
                        name=repo["name"],
                        link=f"https://github.com/{repo['name']}",
                        summary=repo["description"],
                        source="GitHub",
                        engagement=repo["stars"]
                    )
                    trending_repos.append(repo_obj)
                    logger.debug(f"Objeto Repo criado com sucesso: {repo['name']}")
                except Exception as e:
                    logger.error(f"Erro ao criar objeto Repo para {repo['name']}: {str(e)}", exc_info=True)
            
            logger.info(f"Busca finalizada. Retornando {len(trending_repos)} repositórios em tendência")
            return trending_repos
        
        except Exception as e:
            logger.error(f"Erro na função get_trending_repos: {str(e)}", exc_info=True)
            return []