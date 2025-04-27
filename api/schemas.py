from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class CurationRequest(BaseModel):
    """Schema for content curation request parameters."""
    
    max_news: int = Field(
        default=10, 
        ge=1, 
        le=50, 
        description="Maximum number of news items to return (1-50)"
    )
    
    max_papers: int = Field(
        default=5, 
        ge=0, 
        le=20, 
        description="Maximum number of research papers to return (0-20)"
    )
    
    max_repos: int = Field(
        default=5,
        ge=0,
        le=20,
        description="Maximum number of repositories to return (0-20)"
    )
    
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords to filter content"
    )
    
    include_sentiment: bool = Field(
        default=True,
        description="Whether to include sentiment analysis in the response"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata for the request"
    )

    @validator('keywords', allow_reuse=True)
    def validate_keywords(cls, keywords):
        """Validate that keywords are not empty strings"""
        if keywords:
            # Filter out empty strings and ensure uniqueness
            keywords = list(set(k.strip() for k in keywords if k and k.strip()))
            if len(keywords) > 10:
                raise ValueError("Maximum of 10 keywords allowed")
        return keywords

    model_config = {
        "json_schema_extra": {
            "example": {
                "max_news": 15,
                "max_papers": 3,
                "max_repos": 3,
                "keywords": ["AI", "machine learning", "data science"],
                "include_sentiment": True,
                "metadata": {
                    "source": "user_request",
                    "priority": "normal"
                }
            }
        }
    }