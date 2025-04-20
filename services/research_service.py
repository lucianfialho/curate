import time
import random
import logging
import urllib.request
import feedparser
import numpy as np
import asyncio
from sklearn import svm
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer

from models.content_models import ResearchPaper

logger = logging.getLogger(__name__)

class ArxivScanner:
    """Serviço para coleta e análise de artigos do arXiv"""
    
    def __init__(self, base_url: str, top_n: int = 5):
        self.base_url = base_url
        self.top_n = top_n
        self.default_query = 'cat:cs.CV+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.AI+OR+cat:cs.NE+OR+cat:cs.RO'

    def _get_response(self, search_query: str, start_index: int = 0) -> bytes:
        """Busca artigos na API do arXiv"""
        query_url = f'{self.base_url}search_query={search_query}&sortBy=lastUpdatedDate&start={start_index}&max_results=100'

        with urllib.request.urlopen(query_url) as url:
            response = url.read()
            if url.status != 200:
                raise Exception(f"ArXiv API returned status {url.status}")
        return response

    def _parse_arxiv_url(self, url: str) -> tuple:
        """Extrai informação de URL do arXiv"""
        idv = url[url.rfind('/') + 1:]
        parts = idv.split('v')
        return idv, parts[0], int(parts[1])

    def _parse_response(self, response: bytes) -> List[Dict[str, Any]]:
        """Processa resposta da API do arXiv"""
        def encode_feedparser_dict(d):
            if isinstance(d, feedparser.FeedParserDict) or isinstance(d, dict):
                return {k: encode_feedparser_dict(d[k]) for k in d.keys()}
            elif isinstance(d, list):
                return [encode_feedparser_dict(k) for k in d]
            return d

        papers = []
        parse = feedparser.parse(response)

        for entry in parse.entries:
            paper = encode_feedparser_dict(entry)
            idv, raw_id, version = self._parse_arxiv_url(paper['id'])

            paper['_idv'] = idv
            paper['_id'] = raw_id
            paper['_version'] = version
            paper['_time'] = time.mktime(paper['updated_parsed'])
            paper['_time_str'] = time.strftime('%b %d %Y', paper['updated_parsed'])

            papers.append(paper)

        return papers

    def rank_papers(self, papers: List[Dict], method: str = 'svm',
                    query: str = None) -> List[Tuple[Dict, float]]:
        """Ranqueia artigos por relevância usando diversos métodos"""
        # Implementação como mostrado anteriormente
        
    def filter_by_keywords(self, papers: List[Dict], keywords: List[str]) -> List[Dict]:
        """Filtra artigos por palavras-chave"""
        if not keywords:
            return papers
            
        filtered_papers = []
        for paper in papers:
            content = f"{paper['title']} {paper['summary']} {' '.join(a['name'] for a in paper['authors'])}".lower()
            if any(keyword.lower() in content for keyword in keywords):
                filtered_papers.append(paper)
                
        return filtered_papers

    def get_top_n_papers(self, search_query: Optional[str] = None,
                        rank_method: str = 'svm',
                        keywords: List[str] = None) -> List[ResearchPaper]:
        """Retorna os N artigos mais relevantes"""
        query = search_query or self.default_query
        papers = []
        start_index = 0

        while len(papers) < max(100, self.top_n):
            try:
                response = self._get_response(query, start_index)
                batch = self._parse_response(response)
                if not batch:
                    break
                papers.extend(batch)
                start_index += len(batch)
                time.sleep(1 + random.uniform(0, 3))
            except Exception as e:
                logger.error(f"Erro buscando artigos: {e}")
                break
                
        # Filtra por palavras-chave se fornecidas
        if keywords:
            papers = self.filter_by_keywords(papers, keywords)
            if not papers:
                logger.warning(f"Nenhum artigo encontrado com as palavras-chave: {keywords}")
                return []
        
        ranked_papers = self.rank_papers(papers, method=rank_method, query=search_query)
        
        # Converte para objetos ResearchPaper
        top_papers = []
        for p, score in ranked_papers[:self.top_n]:
            research_paper = ResearchPaper(
                title=p['title'],
                authors=[a['name'] for a in p['authors']],
                abstract=p['summary'],
                publication="arXiv",
                link=f"https://arxiv.org/abs/{p['_id']}",
                date=p['_time_str'],
                engagement=f"{score:.2f}"
            )
            top_papers.append(research_paper)
            
        return top_papers

class ResearchService:
    """Serviço de agregação de artigos de pesquisa de várias fontes"""
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.arxiv_url = config.get('arxiv_url', "http://export.arxiv.org/api/query?")
        self.max_papers = config.get('max_papers', 5)
        self.arxiv_scanner = ArxivScanner(self.arxiv_url, self.max_papers)
        
    async def get_research_papers(self, keywords: List[str] = None) -> List[ResearchPaper]:
        """Obtém artigos de pesquisa de todas as fontes configuradas"""
        # Por enquanto temos apenas arXiv
        # Este método está preparado para futuras expansões
        
        # arXiv não é assíncrono, então usamos asyncio.to_thread
        papers = await asyncio.to_thread(
            self.arxiv_scanner.get_top_n_papers, 
            None, 'svm', 
            keywords
        )
        
        return papers