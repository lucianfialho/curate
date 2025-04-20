# services/sentiment_service.py

import numpy as np
import logging
from typing import Dict, List, Any, Tuple, Optional
from textblob import TextBlob
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)

class SentimentAnalysisService:
    """Serviço para analisar o sentimento de textos."""
    
    SENTIMENT_TYPES = {
        'BASIC': 'basic',      # Análise rápida e simples (TextBlob)
        'VADER': 'vader',      # Análise específica para mídias sociais (VADER)
        'BERT': 'bert'         # Análise avançada baseada em redes neurais (BERT)
    }
    
    def __init__(self, sentiment_type='basic', language='en'):
        """
        Inicializa o serviço de análise de sentimento.
        
        Args:
            sentiment_type: Tipo de análise a ser usada ('basic', 'vader' ou 'bert')
            language: Código de idioma (atualmente suporta 'en' e 'pt')
        """
        self.sentiment_type = sentiment_type
        self.language = language
        
        # Inicializa o analisador apropriado
        if sentiment_type == self.SENTIMENT_TYPES['BASIC']:
            # TextBlob não precisa de inicialização especial
            pass
            
        elif sentiment_type == self.SENTIMENT_TYPES['VADER']:
            try:
                nltk.download('vader_lexicon', quiet=True)
                self.vader = SentimentIntensityAnalyzer()
            except Exception as e:
                logger.error(f"Erro ao inicializar VADER: {e}")
                logger.info("Caindo para análise básica")
                self.sentiment_type = self.SENTIMENT_TYPES['BASIC']
                
        elif sentiment_type == self.SENTIMENT_TYPES['BERT']:
            try:
                model_name = "distilbert-base-uncased-finetuned-sst-2-english"
                if language == 'pt':
                    model_name = "neuralmind/bert-base-portuguese-cased-sentiment"
                    
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.nlp = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer)
            except Exception as e:
                logger.error(f"Erro ao inicializar BERT: {e}")
                logger.info("Caindo para análise VADER")
                try:
                    nltk.download('vader_lexicon', quiet=True)
                    self.vader = SentimentIntensityAnalyzer()
                    self.sentiment_type = self.SENTIMENT_TYPES['VADER']
                except:
                    logger.info("Caindo para análise básica")
                    self.sentiment_type = self.SENTIMENT_TYPES['BASIC']
        else:
            logger.warning(f"Tipo de sentimento '{sentiment_type}' não reconhecido. Usando 'basic'.")
            self.sentiment_type = self.SENTIMENT_TYPES['BASIC']
            
        logger.info(f"Serviço de análise de sentimento inicializado com tipo: {self.sentiment_type}")
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analisa o sentimento de um texto.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Dicionário com pontuações de sentimento e outras métricas
        """
        if not text or len(text.strip()) < 10:
            return {
                'polarity': 0.0,         # Varia de -1 (negativo) a 1 (positivo)
                'subjectivity': 0.0,     # Varia de 0 (objetivo) a 1 (subjetivo)
                'sentiment': 'neutral',  # 'positive', 'negative', ou 'neutral'
                'confidence': 0.0        # Confiança na classificação
            }
            
        try:
            if self.sentiment_type == self.SENTIMENT_TYPES['BASIC']:
                return self._analyze_with_textblob(text)
                
            elif self.sentiment_type == self.SENTIMENT_TYPES['VADER']:
                return self._analyze_with_vader(text)
                
            elif self.sentiment_type == self.SENTIMENT_TYPES['BERT']:
                return self._analyze_with_bert(text)
                
        except Exception as e:
            logger.error(f"Erro na análise de sentimento: {e}")
            # Tentar fallback para TextBlob em caso de erro
            try:
                return self._analyze_with_textblob(text)
            except:
                # Retornar valores neutros em caso de falha total
                return {
                    'polarity': 0.0,
                    'subjectivity': 0.0,
                    'sentiment': 'neutral',
                    'confidence': 0.0
                }
    
    def _analyze_with_textblob(self, text: str) -> Dict[str, Any]:
        """Analisa sentimento usando TextBlob (rápido mas básico)"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determina o sentimento com base na polaridade
        if polarity > 0.1:
            sentiment = 'positive'
            confidence = min(abs(polarity) * 2, 1.0)  # Mapeia para escala 0-1
        elif polarity < -0.1:
            sentiment = 'negative'
            confidence = min(abs(polarity) * 2, 1.0)
        else:
            sentiment = 'neutral'
            confidence = 1.0 - min(abs(polarity) * 10, 0.8)  # Mais próximo de 0, mais confiante no neutro
            
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment': sentiment,
            'confidence': confidence
        }
    
    def _analyze_with_vader(self, text: str) -> Dict[str, Any]:
        """Analisa sentimento usando VADER (bom para conteúdo de mídia social)"""
        scores = self.vader.polarity_scores(text)
        
        # VADER retorna scores compound, neg, neu, pos
        polarity = scores['compound']  # Varia de -1 a 1
        
        # Estima subjetividade baseado em ausência de neutralidade
        subjectivity = 1.0 - scores['neu']
        
        # Determina sentimento baseado no score composto
        if polarity >= 0.05:
            sentiment = 'positive'
            confidence = min((polarity - 0.05) * 2, 1.0)
        elif polarity <= -0.05:
            sentiment = 'negative'
            confidence = min((abs(polarity) - 0.05) * 2, 1.0)
        else:
            sentiment = 'neutral'
            confidence = 1.0 - min(abs(polarity) * 10, 0.8)
            
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment': sentiment,
            'confidence': confidence,
            'detailed_scores': {
                'negative': scores['neg'],
                'neutral': scores['neu'],
                'positive': scores['pos']
            }
        }
        
    def _analyze_with_bert(self, text: str) -> Dict[str, Any]:
        """Analisa sentimento usando modelo BERT (mais preciso mas mais lento)"""
        # Limita tamanho do texto para evitar problemas com sequências muito longas
        max_length = 512
        if len(text) > max_length:
            # Usa os primeiros n caracteres (poderia ser otimizado)
            text = text[:max_length]
            
        # Executa a inferência
        results = self.nlp(text)
        result = results[0]  # Pega o primeiro resultado
        
        # Mapeia o resultado para nosso formato padrão
        label = result['label'].lower()
        score = result['score']
        
        if label in ['positive', 'positive_sentiment']:
            polarity = score
            sentiment = 'positive'
        elif label in ['negative', 'negative_sentiment']:
            polarity = -score
            sentiment = 'negative'
        else:
            polarity = 0.0
            sentiment = 'neutral'
            
        # BERT não fornece subjetividade, então estimamos
        subjectivity = abs(polarity)
        
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment': sentiment,
            'confidence': score
        }
        
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analisa sentimento para uma lista de textos.
        
        Args:
            texts: Lista de textos para análise
            
        Returns:
            Lista de resultados de análise, um para cada texto
        """
        results = []
        for text in texts:
            results.append(self.analyze_text(text))
        return results
        
    def analyze_news_cluster(self, news_cluster: List[Dict]) -> Dict[str, Any]:
        """
        Analisa o sentimento em um cluster de notícias similares.
        
        Args:
            news_cluster: Lista de notícias similares (mesmo tópico de diferentes fontes)
            
        Returns:
            Análise comparativa de sentimento entre as fontes
        """
        if not news_cluster:
            return {
                'overall_sentiment': 'neutral',
                'sentiment_variance': 0.0,
                'sources': []
            }
            
        # Analisa cada fonte
        sources_analysis = []
        polarities = []
        
        for news in news_cluster:
            # Combina título e descrição para análise
            text = f"{news['title']} {news['description']}"
            analysis = self.analyze_text(text)
            
            source_info = {
                'source': news['source'],
                'sentiment': analysis['sentiment'],
                'polarity': analysis['polarity'],
                'subjectivity': analysis['subjectivity'],
                'confidence': analysis['confidence']
            }
            
            sources_analysis.append(source_info)
            polarities.append(analysis['polarity'])
            
        # Calcula métricas globais
        polarities = np.array(polarities)
        mean_polarity = np.mean(polarities)
        variance = np.var(polarities)
        
        # Determina o sentimento geral
        if mean_polarity > 0.1:
            overall_sentiment = 'positive'
        elif mean_polarity < -0.1:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
            
        # Identifica fontes mais positivas e negativas
        sources_analysis.sort(key=lambda x: x['polarity'], reverse=True)
        most_positive = sources_analysis[0] if sources_analysis and sources_analysis[0]['polarity'] > 0 else None
        most_negative = sources_analysis[-1] if sources_analysis and sources_analysis[-1]['polarity'] < 0 else None
        
        # Calcula o grau de consenso/divergência
        if variance < 0.03:
            consensus = 'high'  # Alta concordância de sentimento
        elif variance < 0.1:
            consensus = 'moderate'  # Concordância moderada
        else:
            consensus = 'low'  # Baixa concordância (alta divergência)
            
        return {
            'overall_sentiment': overall_sentiment,
            'mean_polarity': float(mean_polarity),
            'sentiment_variance': float(variance),
            'consensus_level': consensus,
            'most_positive_source': most_positive,
            'most_negative_source': most_negative,
            'sources': sources_analysis
        }