import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class NewsClusteringService:
    def __init__(self, similarity_threshold=0.6):
        """
        Inicializa o serviço de clustering.
        
        Args:
            similarity_threshold: Valor entre 0 e 1 que define quando duas notícias
                                  são consideradas similares.
        """
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
    def _compute_similarity_matrix(self, news_items: List[Dict]) -> np.ndarray:
        """
        Calcula a matriz de similaridade entre todas as notícias.
        
        Args:
            news_items: Lista de notícias para comparar
            
        Returns:
            Matriz de similaridade (numpy array)
        """
        try:
            if not news_items:
                logger.warning("Lista de notícias vazia, retornando matriz vazia")
                return np.array([[]])
                
            # Extrai texto para vetorização
            text_content = []
            for item in news_items:
                # Usa título e descrição para melhor comparação
                title = item.get('title', '')
                description = item.get('description', '')
                text = f"{title} {description}"
                text_content.append(text)
                
            # Vetoriza o texto usando TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform(text_content)
            
            # Calcula similaridade de cosseno entre todos os pares
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            return similarity_matrix
        except Exception as e:
            logger.error(f"Erro ao calcular matriz de similaridade: {str(e)}")
            # Retorna matriz vazia em caso de erro
            return np.zeros((len(news_items), len(news_items)))
    
    def cluster_news(self, news_items: List[Dict]) -> List[List[Dict]]:
        """
        Agrupa notícias similares.
        
        Args:
            news_items: Lista de notícias para agrupar
            
        Returns:
            Lista de clusters (cada cluster é uma lista de notícias)
        """
        try:
            if not news_items:
                logger.warning("Lista de notícias vazia, retornando lista vazia")
                return []
                
            # Calcula a matriz de similaridade
            similarity_matrix = self._compute_similarity_matrix(news_items)
            
            # Inicializa clusters e notícias não processadas
            clusters = []
            processed = [False] * len(news_items)
            
            # Agrupa notícias
            for i in range(len(news_items)):
                if processed[i]:
                    continue
                    
                # Inicia novo cluster com notícia atual
                cluster = [news_items[i]]
                processed[i] = True
                
                # Adiciona notícias similares ao cluster
                for j in range(len(news_items)):
                    if i != j and not processed[j] and similarity_matrix[i, j] >= self.similarity_threshold:
                        cluster.append(news_items[j])
                        processed[j] = True
                
                clusters.append(cluster)
            
            # Ordena clusters por tamanho (maior primeiro)
            clusters.sort(key=len, reverse=True)
            
            logger.info(f"Agrupadas {len(news_items)} notícias em {len(clusters)} clusters")
            return clusters
        except Exception as e:
            logger.error(f"Erro ao agrupar notícias: {str(e)}")
            # Em caso de erro, retorna cada notícia como seu próprio cluster
            return [[item] for item in news_items]
    
    def format_clustered_news(self, news_clusters: List[List[Dict]]) -> List[Dict]:
        """
        Formata clusters de notícias para API.
        
        Args:
            news_clusters: Lista de clusters de notícias
            
        Returns:
            Lista de notícias formatadas com informações de fontes agrupadas
        """
        try:
            if not news_clusters:
                logger.warning("Lista de clusters vazia, retornando lista vazia")
                return []
                
            formatted_news = []
            
            for cluster in news_clusters:
                if not cluster:
                    continue
                    
                # Encontra o artigo principal do cluster (com maior pontuação de importância)
                primary = max(
                    cluster, 
                    key=lambda x: x.get('additional_info', {}).get('importance_score', 0.0)
                )
                
                # Calcula tempo médio de leitura
                read_times = [item.get('read_time', 5) for item in cluster if 'read_time' in item]
                avg_read_time = int(sum(read_times) / len(read_times)) if read_times else 5
                
                # Extrai informações do artigo principal
                formatted_item = {
                    'title': primary.get('title', ''),
                    'description': primary.get('description', ''),
                    'link': primary.get('link', ''),
                    'source': primary.get('source', 'Unknown Source'),
                    'read_time': avg_read_time,
                    'importance_score': primary.get('additional_info', {}).get('importance_score', 0.5),
                    'sources': []
                }
                
                # Adiciona todas as fontes
                for item in cluster:
                    source_info = {
                        'name': item.get('source', 'Unknown Source'),
                        'link': item.get('link', ''),
                        'published_date': item.get('additional_info', {}).get('published_date', None),
                        'author': item.get('additional_info', {}).get('author', None)
                    }
                    formatted_item['sources'].append(source_info)
                
                formatted_news.append(formatted_item)
            
            # Ordena por pontuação de importância
            formatted_news.sort(key=lambda x: x.get('importance_score', 0.0), reverse=True)
            
            logger.info(f"Formatados {len(formatted_news)} clusters de notícias")
            return formatted_news
        except Exception as e:
            logger.error(f"Erro ao formatar notícias agrupadas: {str(e)}")
            # Em caso de erro, retorna lista vazia
            return []
