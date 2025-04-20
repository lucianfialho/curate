from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class ContentSource(BaseModel):
    name: str
    link: str
    published_date: Optional[str] = None
    author: Optional[str] = None

class NewsItem(BaseModel):
    title: str
    description: str
    link: str
    read_time: int
    source: Optional[str] = None
    engagement: Optional[str] = None
    additional_info: Optional[Dict] = {}

class EnhancedNewsItem(BaseModel):
    title: str
    description: str
    primary_link: str
    read_time: int
    primary_source: str
    sources: List[ContentSource]
    source_count: int
    relevance_score: float = Field(ge=0.0, le=1.0)
    keywords: Optional[List[str]] = None
    categories: Optional[List[str]] = None

class ResearchPaper(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    publication: str
    link: str
    date: str
    engagement: Optional[str] = None

class EnhancedResearchPaper(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    primary_publication: str
    link: str
    date: str
    cited_by: Optional[List[str]] = None
    citations_count: Optional[int] = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    related_papers: Optional[List[Dict]] = None

class Repo(BaseModel):
    name: str
    link: str
    summary: str
    source: Optional[str] = None
    engagement: Optional[str] = None

class EnhancedRepo(BaseModel):
    name: str
    link: str
    summary: str
    source: str = "GitHub"
    stars: Optional[str] = None
    forks: Optional[str] = None
    contributors: Optional[int] = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    recent_activity: Optional[str] = None
    categories: Optional[List[str]] = None

class Event(BaseModel):
    title: str
    date: str
    location: str
    description: str

class CuratedContent(BaseModel):
    news: Optional[List[EnhancedNewsItem]] = []
    papers: Optional[List[EnhancedResearchPaper]] = []
    repos: Optional[List[EnhancedRepo]] = []
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    metadata: Optional[Dict] = None