from typing import Dict, List, Any
from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class SentimentConfig(BaseModel):
    """Configuration for sentiment analysis."""
    type: str = 'vader'  # 'basic', 'vader', ou 'bert'
    language: str = 'en'  # 'en' ou 'pt'

class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""
    
    # RSS feed settings
    rss_feeds: List[str] = Field(
        default=[
            "https://www.technologyreview.com/topic/artificial-intelligence/feed",
            "https://deepmind.com/blog/feed/basic/",
            # Adicione mais feeds conforme necessário
        ]
    )
    
    # API endpoints
    arxiv_url: str = Field(default="http://export.arxiv.org/api/query?")
    github_url: str = Field(
        default="https://github.com/trending/python?since=daily&spoken_language_code=en"
    )
    
    # Content processing settings
    similarity_threshold: float = Field(default=0.6)
    
    # Sentiment analysis settings
    sentiment: SentimentConfig = Field(default_factory=SentimentConfig)
    
    @property
    def CURATOR_CONFIG(self) -> Dict[str, Any]:
        """
        Returns the configuration in the format expected by the curator.
        This maintains backward compatibility with the original dict structure.
        """
        return {
            'rss_feeds': self.rss_feeds,
            'arxiv_url': self.arxiv_url,
            'github_url': self.github_url,
            'similarity_threshold': self.similarity_threshold,
            'sentiment': {
                'type': self.sentiment.type,
                'language': self.sentiment.language
            }
        }
    
    class Config:
        env_prefix = "APP_"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings class.
    Using lru_cache for creating a singleton instance.
    """
    return Settings()

# For backward compatibility
CURATOR_CONFIG = get_settings().CURATOR_CONFIG
