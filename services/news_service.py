import asyncio
import logging
import numpy as np
import aiohttp
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import email.utils
import re
from typing import Dict, List, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer

from models.content_models import NewsItem

logger = logging.getLogger(__name__)

class NewsService:
    """Serviço para coleta e processamento de notícias via RSS"""
    
    def __init__(self, rss_urls: List[str]):
        self.rss_urls = rss_urls
        self.tfidf = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.session: Optional[aiohttp.ClientSession] = None
        self.news = []
        self._is_closed = False

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags do texto"""
        if not text:
            return ''
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text().strip()
    def _parse_date(self, date_str: str) -> datetime:
        """Converte string de data para objeto datetime"""
        if not date_str:
            return datetime.now()
            
        try:
            # Try RFC 2822 format (common in RSS)
            return datetime.fromtimestamp(email.utils.mktime_tz(email.utils.parsedate_tz(date_str)))
        except:
            try:
                # Try ISO 8601 format (common in Atom)
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                try:
                    # Try other common formats
                    return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                except:
                    try:
                        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        return datetime.now()
                return datetime.now()
    async def _get_session(self) -> aiohttp.ClientSession:
        """Retorna uma sessão HTTP, criando-a se necessário"""
        if self._is_closed:
            raise RuntimeError("NewsService foi fechado e não pode ser reutilizado")
            
        try:
            if self.session is None or self.session.closed:
                logger.debug("Criando nova sessão HTTP")
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30, connect=10),
                    headers={'User-Agent': 'Mozilla/5.0 AILert News Service'},
                    raise_for_status=True
                )
            return self.session
        except Exception as e:
            logger.error(f"Erro ao criar sessão HTTP: {str(e)}")
            # Fallback to a basic session in case of configuration failure
            return aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        
    async def _fetch_feed_content(self, url: str) -> str:
        """Busca o conteúdo de um feed RSS de forma assíncrona"""
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Erro ao buscar feed {url}: Status {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Erro ao buscar feed {url}: {str(e)}")
            return ""
            
    def _get_feed_type_and_namespaces(self, root: ET.Element) -> Tuple[str, Dict[str, str]]:
        """Determine feed type (RSS or Atom) and extract namespaces"""
        tag = root.tag.lower()
        namespaces = {}
        
        # Extract namespace dictionary from root
        match = re.match(r'\{(.*?)\}(.*)', tag) if '{' in tag else None
        if match:
            ns_url = match.group(1)
            namespaces['default'] = ns_url
        
        # Check for common namespaces in attributes
        for key, value in root.attrib.items():
            if key.startswith('xmlns:'):
                ns_name = key.split(':', 1)[1]
                namespaces[ns_name] = value
        
        # Determine feed type
        if 'rss' in tag or 'rdf' in tag:
            return 'rss', namespaces
        elif 'feed' in tag:
            return 'atom', namespaces
        
        # Try checking child elements if tag is ambiguous
        for child in root:
            if child.tag.lower().endswith('channel'):
                return 'rss', namespaces
        
        # Default to RSS
        return 'rss', namespaces
    
    def _extract_text(self, element: Optional[ET.Element]) -> str:
        """Extract text from an Element, handling None case"""
        if element is None:
            return ""
        return (element.text or "").strip()
    
    def _find_element_content(self, element: ET.Element, tags: List[str]) -> str:
        """Try to find content using various tag names"""
        for tag in tags:
            found = element.find(tag)
            if found is not None and found.text:
                return found.text.strip()
        return ""
    
    async def _parse_feed(self, content: str, source_url: str) -> List[Dict]:
        """Processa um feed RSS/Atom de forma assíncrona usando ElementTree"""
        if not content:
            return []
        
        news_items = []
        try:
            # Parse XML
            root = ET.fromstring(content)
            feed_type, namespaces = self._get_feed_type_and_namespaces(root)
            
            # Extract feed title (different in RSS and Atom)
            feed_title = "Unknown Source"
            
            if feed_type == 'rss':
                # Find channel element (root for RSS 2.0, child for RSS 1.0/RDF)
                channel = root.find('channel') or root
                feed_title_elem = channel.find('title')
                if feed_title_elem is not None and feed_title_elem.text:
                    feed_title = feed_title_elem.text.strip()
                
                # Find items (different path in RSS 2.0 vs RSS 1.0)
                items = channel.findall('item') or root.findall('item')
                
                # Process items
                for item in items:
                    try:
                        # Basic item data
                        title = self._extract_text(item.find('title'))
                        description = self._extract_text(item.find('description'))
                        link = self._extract_text(item.find('link'))
                        
                        # Publication date
                        pub_date = self._extract_text(item.find('pubDate') or item.find('date'))
                        
                        # Author
                        author = self._extract_text(item.find('author') or item.find('creator'))
                        
                        # Categories/tags
                        categories = []
                        for cat in item.findall('category'):
                            if cat.text:
                                categories.append(cat.text.strip())
                        
                        # GUID
                        guid = self._extract_text(item.find('guid'))
                        
                        # Additional info
                        additional_info = {
                            'published_date': self._parse_date(pub_date),
                            'author': author,
                            'categories': categories,
                            'guid': guid,
                            'source_url': source_url
                        }
                        
                        # Clean description
                        clean_description = self._clean_html(description)
                        
                        # Create news item
                        news_item = {
                            'title': title,
                            'description': clean_description,
                            'link': link,
                            'source': feed_title,
                            'engagement': None,
                            'additional_info': additional_info,
                            'full_text': f"{title} {clean_description}"
                        }
                        
                        news_items.append(news_item)
                    except Exception as e:
                        logger.error(f"Erro ao processar item RSS do feed {source_url}: {str(e)}")
            
            elif feed_type == 'atom':
                # Extract feed title
                feed_title_elem = root.find('title')
                if feed_title_elem is not None and feed_title_elem.text:
                    feed_title = feed_title_elem.text.strip()
                
                # Find entries
                entries = root.findall('entry')
                
                # Process entries
                for entry in entries:
                    try:
                        # Basic item data
                        title = self._extract_text(entry.find('title'))
                        
                        # Content could be in content or summary elements
                        description = self._extract_text(entry.find('content') or entry.find('summary'))
                        
                        # Link is typically in href attribute of link element
                        link = ""
                        link_elem = entry.find('link')
                        if link_elem is not None:
                            link = link_elem.get('href', '')
                        
                        # Publication date
                        updated = self._extract_text(entry.find('updated') or entry.find('published'))
                        
                        # Author is in nested author element
                        author = ""
                        author_elem = entry.find('author')
                        if author_elem is not None:
                            name_elem = author_elem.find('name')
                            if name_elem is not None and name_elem.text:
                                author = name_elem.text.strip()
                        
                        # Categories
                        categories = []
                        for cat in entry.findall('category'):
                            term = cat.get('term', '')
                            if term:
                                categories.append(term)
                        
                        # ID
                        entry_id = self._extract_text(entry.find('id'))
                        
                        # Additional info
                        additional_info = {
                            'published_date': self._parse_date(updated),
                            'author': author,
                            'categories': categories,
                            'guid': entry_id,
                            'source_url': source_url
                        }
                        
                        # Clean description
                        clean_description = self._clean_html(description)
                        
                        # Create news item
                        news_item = {
                            'title': title,
                            'description': clean_description,
                            'link': link,
                            'source': feed_title,
                            'engagement': None,
                            'additional_info': additional_info,
                            'full_text': f"{title} {clean_description}"
                        }
                        
                        news_items.append(news_item)
                    except Exception as e:
                        logger.error(f"Erro ao processar item Atom do feed {source_url}: {str(e)}")
            
        except ET.ParseError as e:
            logger.error(f"Erro ao processar XML do feed {source_url}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro não esperado ao processar feed {source_url}: {str(e)}")
            
        return news_items

    async def _fetch_feed(self, url: str) -> List[Dict]:
        """Busca e processa um feed RSS de forma assíncrona"""
        try:
            logger.info(f"Buscando feed: {url}")
            content = await self._fetch_feed_content(url)
            if not content:
                return []
                
            news_items = await self._parse_feed(content, url)
            logger.info(f"Processados {len(news_items)} itens do feed: {url}")
            return news_items
        except Exception as e:
            logger.error(f"Erro ao processar feed {url}: {str(e)}")
            return []

    def _calculate_importance_scores(self, news_items: List[Dict]) -> List[float]:
        """Calcula pontuação de importância usando TF-IDF"""
        if not news_items:
            return []
        try:
            texts = [item['full_text'] for item in news_items]
            x = self.tfidf.fit_transform(texts)
            doc_lengths = x.sum(axis=1).A1
            term_importance = np.sqrt(np.asarray(x.mean(axis=0)).ravel())
            scores = doc_lengths * np.dot(x.toarray(), term_importance)
            if len(scores) > 0:
                scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-8)
            return scores.tolist()
        except Exception as e:
            logger.error(f"Erro ao calcular scores de importância: {str(e)}")
            return [0.5] * len(news_items)  # Valor padrão em caso de erro

    def _calculate_read_time(self, text: str, words_per_minute: int = 200) -> int:
        """Calcula tempo estimado de leitura do texto"""
        words = len(text.strip().split())
        minutes = max(1, int(words / words_per_minute))
        return minutes

    def filter_by_keywords(self, items: List[Dict], keywords: List[str]) -> List[Dict]:
        """Filtra itens por palavras-chave"""
        if not keywords:
            return items
            
        filtered_items = []
        for item in items:
            full_text = item['full_text'].lower()
            if any(keyword.lower() in full_text for keyword in keywords):
                filtered_items.append(item)
        return filtered_items
        
    async def get_top_news(self, max_items: int = 10, keywords: List[str] = None) -> List[NewsItem]:
        """Retorna as notícias mais relevantes de forma assíncrona"""
        try:
            # Coleta todas as notícias de forma concorrente
            logger.info(f"Buscando notícias de {len(self.rss_urls)} feeds")
            feed_results = await asyncio.gather(
                *[self._fetch_feed(url) for url in self.rss_urls],
                return_exceptions=True
            )
            
            # Processa resultados, ignorando exceções
            all_news = []
            for result in feed_results:
                if isinstance(result, Exception):
                    logger.error(f"Erro ao buscar feed: {str(result)}")
                else:
                    all_news.extend(result)
            
            if not all_news:
                logger.warning("Nenhuma notícia encontrada")
                return []
            
            # Filtra por palavras-chave se fornecidas
            if keywords:
                all_news = self.filter_by_keywords(all_news, keywords)
                if not all_news:
                    logger.warning(f"Nenhuma notícia encontrada com as palavras-chave: {keywords}")
                    return []

            # Calcula pontuações e adiciona aos itens
            importance_scores = self._calculate_importance_scores(all_news)
            for item, score in zip(all_news, importance_scores):
                item['additional_info']['importance_score'] = float(score)

            # Ordena por pontuação de importância
            sorted_news = sorted(
                all_news,
                key=lambda x: x['additional_info']['importance_score'],
                reverse=True
            )

            # Converte para objetos NewsItem
            top_news = []
            for item in sorted_news[:max_items]:
                read_time = self._calculate_read_time(item['description'])
                news_item = NewsItem(
                    title=item['title'],
                    description=item['description'],
                    link=item['link'],
                    read_time=read_time,
                    source=item['source'],
                    engagement=item['engagement'],
                    additional_info=item['additional_info']
                )
                top_news.append(news_item)
            
            return top_news
        except Exception as e:
            logger.error(f"Erro ao obter top notícias: {str(e)}")
            return []
        
    async def close(self):
        """Fecha recursos assíncronos"""
        if self._is_closed:
            return
            
        try:
            # Fecha a sessão HTTP
            if self.session and not self.session.closed:
                await self.session.close()
                self.session = None
                
            # Limpa o estado do vetorizador
            if hasattr(self.tfidf, '_tfidf'):
                delattr(self.tfidf, '_tfidf')
            if hasattr(self.tfidf, 'vocabulary_'):
                delattr(self.tfidf, 'vocabulary_')
            
            # Limpa outras referências
            self.news = []
            self._is_closed = True
            
            logger.info("NewsService recursos liberados")
        except Exception as e:
            logger.error(f"Erro ao fechar recursos do NewsService: {str(e)}")
    
    async def __aenter__(self):
        """Suporte para uso com context manager assíncrono"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup ao sair do context manager"""
        await self.close()
