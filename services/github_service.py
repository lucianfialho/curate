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

    def _extract_from_html(self, link):
        """Extrai repositórios da página de trending do GitHub"""
        repos = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(link, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            repo_list = soup.find_all('article', class_='Box-row')

            for repo in repo_list:
                name = repo.find('h2', class_='h3').text.strip().replace('\n', '').replace(' ', '')

                description = repo.find('p', class_='col-9 color-fg-muted my-1 pr-4')
                description = description.text.strip() if description else "Sem descrição disponível."

                stars_element = repo.find('a', class_='Link Link--muted d-inline-block mr-3') or \
                               repo.find('a', class_='Link--muted d-inline-block mr-3')
                stars = stars_element.text.strip().replace(',', '') if stars_element else "0"

                fork_elements = repo.find_all('a', class_='Link Link--muted d-inline-block mr-3') or \
                               repo.find_all('a', class_='Link--muted d-inline-block mr-3')
                forks = fork_elements[1].text.strip().replace(',', '') if len(fork_elements) > 1 else "0"

                repos.append({
                    'name': name,
                    'description': description,
                    'stars': stars,
                    'forks': forks
                })

            return repos[:self.top_n]
        except Exception as e:
            logger.error(f"Erro extraindo repositórios do GitHub: {str(e)}")
            return []
            
    def filter_by_keywords(self, repos: List[Dict], keywords: List[str]) -> List[Dict]:
        """Filtra repositórios por palavras-chave"""
        if not keywords:
            return repos
            
        filtered_repos = []
        for repo in repos:
            content = f"{repo['name']} {repo['description']}".lower()
            if any(keyword.lower() in content for keyword in keywords):
                filtered_repos.append(repo)
                
        return filtered_repos

    async def get_trending_repos(self, keywords: List[str] = None) -> List[Repo]:
        """Retorna os repositórios em tendência no GitHub"""
        repositories = self._extract_from_html(self.site_url)
        
        # Filtra por palavras-chave se fornecidas
        if keywords:
            repositories = self.filter_by_keywords(repositories, keywords)
            if not repositories:
                logger.warning(f"Nenhum repositório encontrado com as palavras-chave: {keywords}")
                return []
        
        # Converte para objetos Repo
        trending_repos = []
        for repo in repositories:
            repo_obj = Repo(
                name=repo["name"],
                link=f"https://github.com/{repo['name']}",
                summary=repo["description"],
                source="GitHub",
                engagement=repo["stars"]
            )
            trending_repos.append(repo_obj)
            
        return trending_repos