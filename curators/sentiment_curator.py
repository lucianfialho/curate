from typing import Dict, List, Any, Optional
import asyncio
import logging
import os
from datetime import datetime

from models.content_models import ContentSource, EnhancedNewsItem
from models.sentiment_models import (
    SentimentEnhancedNewsItem, SentimentEnhancedResearchPaper, 
    SentimentEnhancedCuratedContent, ContentSentimentAnalysis,
    SourceSentimentInfo
)
from curators.content_curator import EnhancedContentCurator
from services.sentiment_service import SentimentAnalysisService

logger = logging.getLogger(__name__)

class SentimentEnhancedContentCurator(EnhancedContentCurator):
    """ContentCurator aprimorado com análise de sentimento"""
    
    def __init__(self, config: Dict = None):
        """
        Inicializa o curador com capacidades de análise de sentimento
        """
        # Inicializa a classe base
        super().__init__(config)
        
        # Configurações adicionais
        config = config or {}
        sentiment_config = config.get('sentiment', {})
        
        # Inicializa serviço de análise de sentimento
        sentiment_type = sentiment_config.get('type', 'basic')
        language = sentiment_config.get('language', 'en')
        
        try:
            self.sentiment_service = SentimentAnalysisService(sentiment_type, language)
            logger.info(f"Serviço de análise de sentimento inicializado com tipo: {sentiment_type}")
        except Exception as e:
            logger.error(f"Erro ao inicializar serviço de sentimento: {str(e)}")
            self.sentiment_service = SentimentAnalysisService('basic', 'en')  # Fallback para básico
            
        logger.info("Curador com capacidades de sentimento inicializado")
    
    def _convert_to_sentiment_news_item(self, news_item: EnhancedNewsItem) -> SentimentEnhancedNewsItem:
        """
        Converte um EnhancedNewsItem para SentimentEnhancedNewsItem
        
        Args:
            news_item: Item de notícia a ser convertido
            
        Returns:
            Item de notícia com campos de sentimento (sem análise de sentimento)
        """
        # Cria um dicionário com os atributos
        news_dict = {
            "title": news_item.title,
            "description": news_item.description,
            "primary_link": news_item.primary_link,
            "read_time": news_item.read_time,
            "primary_source": news_item.primary_source,
            "sources": news_item.sources,
            "source_count": news_item.source_count,
            "relevance_score": news_item.relevance_score,
            "keywords": news_item.keywords,
            "categories": news_item.categories,
            "sentiment_analysis": None  # Inicialmente sem análise
        }
        
        # Cria o objeto a partir do dicionário
        return SentimentEnhancedNewsItem(**news_dict)
    
    async def get_curated_content(self, curation_request) -> SentimentEnhancedCuratedContent:
        """
        Retorna conteúdo curado com análise de sentimento adicional
        
        Args:
            curation_request: Requisição de curadoria com parâmetros
            
        Returns:
            Conteúdo curado com análise de sentimento
        """
        try:
            logger.info(f"Iniciando curadoria de conteúdo com sentimento: {curation_request}")
            
            # Obtém conteúdo da classe base
            logger.info("Obtendo conteúdo base...")
            base_content = await super().get_curated_content(curation_request)
            
            if base_content is None:
                logger.error("Conteúdo base retornou None")
                # Retorna um objeto vazio mas válido em vez de None
                return SentimentEnhancedCuratedContent(
                    news=[],
                    papers=[],
                    repos=[],
                    sentiment_summary={},
                    timestamp=datetime.now().isoformat(),
                    metadata={"error": "Não foi possível obter conteúdo base"}
                )
            
            # Verifica se deve incluir análise de sentimento
            include_sentiment = curation_request.get('include_sentiment', True)
            
            logger.info(f"Base content obtido: {len(base_content.news)} notícias, {len(base_content.papers)} papers, {len(base_content.repos)} repos")
            
            # Converte notícias para o tipo correto (SentimentEnhancedNewsItem)
            enhanced_news = [self._convert_to_sentiment_news_item(news) for news in base_content.news]
            
            # Se não precisar de sentimento, retorna diretamente
            if not include_sentiment:
                logger.info("Análise de sentimento não solicitada, retornando conteúdo base")
                # Retorna com os objetos já convertidos para o tipo correto
                return SentimentEnhancedCuratedContent(
                    news=enhanced_news,
                    papers=[],  # Sem papers por enquanto
                    repos=base_content.repos,
                    timestamp=base_content.timestamp,
                    metadata=base_content.metadata or {}
                )
                
            # Adiciona análise de sentimento
            logger.info("Adicionando análise de sentimento ao conteúdo")
            
            # Analisa notícias
            for item in enhanced_news:
                # Analisa o conteúdo da notícia
                text_to_analyze = f"{item.title} {item.description}"
                analysis = self.sentiment_service.analyze_text(text_to_analyze)
                
                # Se tivermos múltiplas fontes, analisa cada uma
                sources_sentiment = []
                for source in item.sources:
                    source_analysis = self.sentiment_service.analyze_text(source.name)
                    source_sentiment = SourceSentimentInfo(
                        source_name=source.name,
                        sentiment=source_analysis['sentiment'],
                        polarity=source_analysis['polarity'],
                        subjectivity=source_analysis['subjectivity'],
                        confidence=source_analysis['confidence']
                    )
                    sources_sentiment.append(source_sentiment)
                
                # Cria análise de sentimento completa
                content_analysis = ContentSentimentAnalysis(
                    overall_sentiment=analysis['sentiment'],
                    mean_polarity=analysis['polarity'],
                    sentiment_variance=0.0,  # Calculado se houver múltiplas fontes
                    consensus_level='high',  # Padrão se houver apenas uma fonte
                    has_divergent_views=False,
                    most_positive_source=max(sources_sentiment, key=lambda x: x.polarity).source_name if sources_sentiment else None,
                    most_negative_source=min(sources_sentiment, key=lambda x: x.polarity).source_name if sources_sentiment else None,
                    sources_sentiment=sources_sentiment
                )
                
                # Atualiza o item com a análise
                item.sentiment_analysis = content_analysis
                
            # Cria resumo de sentimento
            sentiment_summary = self._create_sentiment_summary(enhanced_news, [])
            
            # Cria conteúdo final
            enhanced_content = SentimentEnhancedCuratedContent(
                news=enhanced_news,
                papers=[],  # Sem papers por enquanto
                repos=base_content.repos,
                sentiment_summary=sentiment_summary,
                timestamp=base_content.timestamp,
                metadata=base_content.metadata
            )
            
            logger.info("Conteúdo aprimorado com sentimento criado com sucesso")
            return enhanced_content
            
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo com sentimento: {str(e)}", exc_info=True)
            # Retorna um objeto vazio mas válido em vez de None
            return SentimentEnhancedCuratedContent(
                news=[],
                papers=[],
                repos=[],
                sentiment_summary={},
                timestamp=datetime.now().isoformat(),
                metadata={"error": str(e)}
            )
    
    def _create_sentiment_summary(self, news_items, papers) -> Dict[str, Any]:
        """
        Cria um resumo global da análise de sentimento
        
        Args:
            news_items: Lista de notícias analisadas
            papers: Lista de papers analisados
            
        Returns:
            Resumo da análise de sentimento
        """
        try:
            # Se não temos conteúdo, retorna resumo vazio
            if not news_items and not papers:
                return {
                    "overall_sentiment": "neutral",
                    "content_count": 0,
                    "sentiment_distribution": {
                        "positive": 0,
                        "neutral": 0,
                        "negative": 0
                    }
                }
                
            # Conta ocorrências de cada sentimento
            sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
            
            # Analisa notícias
            for item in news_items:
                if item.sentiment_analysis:
                    sentiment = item.sentiment_analysis.overall_sentiment
                    sentiment_counts[sentiment] += 1
            
            # Analisa papers
            for paper in papers:
                if paper.sentiment_analysis:
                    sentiment = paper.sentiment_analysis.get('sentiment', 'neutral')
                    sentiment_counts[sentiment] += 1
            
            # Calcula sentimento geral
            total_items = sum(sentiment_counts.values())
            if total_items == 0:
                overall_sentiment = "neutral"
            else:
                # Determina o sentimento mais comum
                max_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])
                overall_sentiment = max_sentiment[0]
                
                # Se há um empate, considera neutral
                if list(sentiment_counts.values()).count(max_sentiment[1]) > 1:
                    overall_sentiment = "neutral"
            
            # Cria resumo
            summary = {
                "overall_sentiment": overall_sentiment,
                "content_count": total_items,
                "sentiment_distribution": sentiment_counts,
                
                # Adiciona percentuais
                "sentiment_percentages": {
                    sentiment: (count / total_items * 100 if total_items > 0 else 0)
                    for sentiment, count in sentiment_counts.items()
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao criar resumo de sentimento: {str(e)}")
            return {
                "overall_sentiment": "neutral",
                "error": str(e)
            }
            
    def highlight_sentiment_insights(self, content: SentimentEnhancedCuratedContent) -> Dict[str, Any]:
        """
        Extrai insights de sentimento úteis
        
        Args:
            content: Conteúdo curado com análise de sentimento
            
        Returns:
            Insights sobre o sentimento do conteúdo
        """
        try:
            # Se não há conteúdo ou não incluiu sentimento, retorna vazio
            if content is None:
                logger.warning("Conteúdo nulo ao extrair insights de sentimento")
                return {}
                
            # Se não há resumo de sentimento, retorna vazio
            if not hasattr(content, 'sentiment_summary') or not content.sentiment_summary:
                logger.warning("Conteúdo sem resumo de sentimento ao extrair insights")
                return {}
            
            # Extrai informações do resumo
            insights = {
                "overall_sentiment": content.sentiment_summary.get("overall_sentiment", "neutral"),
                "sentiment_distribution": content.sentiment_summary.get("sentiment_distribution", {}),
            }
            
            # Adiciona insights por tópico
            topic_insights = {}
            
            # Agrupa notícias por palavras-chave
            if content.news:
                for item in content.news:
                    if not hasattr(item, 'keywords') or not item.keywords:
                        continue
                        
                    for keyword in item.keywords:
                        if keyword not in topic_insights:
                            topic_insights[keyword] = {
                                "count": 0,
                                "sentiment_counts": {"positive": 0, "neutral": 0, "negative": 0},
                                "total_polarity": 0.0
                            }
                            
                        # Atualiza contadores
                        topic_insights[keyword]["count"] += 1
                        
                        # Adiciona sentimento se disponível
                        if hasattr(item, 'sentiment_analysis') and item.sentiment_analysis:
                            sentiment = item.sentiment_analysis.overall_sentiment
                            topic_insights[keyword]["sentiment_counts"][sentiment] += 1
                            topic_insights[keyword]["total_polarity"] += item.sentiment_analysis.mean_polarity
            
            # Calcula sentimento predominante para cada tópico
            for topic, data in topic_insights.items():
                if data["count"] > 0:
                    # Sentimento predominante
                    max_sentiment = max(data["sentiment_counts"].items(), key=lambda x: x[1])
                    data["sentiment"] = max_sentiment[0]
                    
                    # Polaridade média
                    data["avg_polarity"] = data["total_polarity"] / data["count"]
                    
                    # Remove campos temporários
                    data.pop("total_polarity", None)
            
            # Adiciona insights por tópico
            if topic_insights:
                insights["topic_insights"] = topic_insights
            
            # Adiciona fontes mais positivas e negativas
            most_positive_items = sorted(
                [n for n in content.news if hasattr(n, 'sentiment_analysis') and n.sentiment_analysis],
                key=lambda x: x.sentiment_analysis.mean_polarity,
                reverse=True
            )
            
            most_negative_items = sorted(
                [n for n in content.news if hasattr(n, 'sentiment_analysis') and n.sentiment_analysis],
                key=lambda x: x.sentiment_analysis.mean_polarity
            )
            
            if most_positive_items:
                insights["most_positive_item"] = {
                    "title": most_positive_items[0].title,
                    "polarity": most_positive_items[0].sentiment_analysis.mean_polarity
                }
                
            if most_negative_items:
                insights["most_negative_item"] = {
                    "title": most_negative_items[0].title,
                    "polarity": most_negative_items[0].sentiment_analysis.mean_polarity
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"Erro ao extrair insights de sentimento: {str(e)}")
            return {"error": str(e)}