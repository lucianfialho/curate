from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from models.content_models import EnhancedNewsItem, EnhancedResearchPaper, EnhancedRepo

class SourceSentimentInfo(BaseModel):
    source_name: str
    sentiment: str  # 'positive', 'negative', 'neutral'
    polarity: float  # Valor entre -1 (negativo) e 1 (positivo)
    subjectivity: float  # Valor entre 0 (objetivo) e 1 (subjetivo)
    confidence: float  # Confiança na classificação de sentimento

class ContentSentimentAnalysis(BaseModel):
    overall_sentiment: str  # 'positive', 'negative', 'neutral'
    mean_polarity: float
    sentiment_variance: float
    consensus_level: str  # 'high', 'moderate', 'low'
    has_divergent_views: bool  # Indica se há opiniões divergentes significativas
    most_positive_source: Optional[str] = None
    most_negative_source: Optional[str] = None
    sources_sentiment: List[SourceSentimentInfo]

class SentimentEnhancedNewsItem(EnhancedNewsItem):
    sentiment_analysis: Optional[ContentSentimentAnalysis] = None
    
class SentimentEnhancedResearchPaper(EnhancedResearchPaper):
    sentiment_analysis: Optional[Dict[str, Any]] = None
    
class SentimentEnhancedCuratedContent(BaseModel):
    news: Optional[List[SentimentEnhancedNewsItem]] = Field(default_factory=list)
    papers: Optional[List[SentimentEnhancedResearchPaper]] = Field(default_factory=list)
    repos: Optional[List[EnhancedRepo]] = Field(default_factory=list)
    sentiment_summary: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict] = None