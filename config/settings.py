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
            "https://deepmind.com/blog/feed/basic/",
            "https://www.oreilly.com/radar/topics/ai-ml/feed/index.xml",
            "https://www.oreilly.com/radar/topics/next-architecture/feed/index.xml",
            "https://blogs.microsoft.com/ai/feed/",
            "https://www.theguardian.com/technology/artificialintelligenceai/rss",
            "https://www.wired.com/feed/tag/ai/latest/rss",
            "https://www.wired.com/feed/category/business/latest/rss",
            "https://www.databricks.com/feed",
            "https://gizmodo.com/tech/feed",
            "https://huggingface.co/blog/feed.xml",
            "https://www.microsoft.com/en-us/research/feed/",
            "https://www.technologyreview.com/feed/",
            "https://stackoverflow.blog/feed/",
            "https://techcrunch.com/feed/",
            "https://blogs.windows.com/feed",
        ]
    )
    
    # API endpoints
    arxiv_url: str = Field(default="http://export.arxiv.org/api/query?")
    github_python_url: str = Field(
        default="https://github.com/trending/python?since=daily&spoken_language_code=en"
    )
    
    github_javascript_url: str = Field(
        default="https://github.com/trending/javascript?since=daily&spoken_language_code=en"
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
            'github_python_url': self.github_python_url,
            'github_javascript_url': self.github_javascript_url,
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
