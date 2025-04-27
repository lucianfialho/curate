# models/database.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

# Tabela de associação entre conteúdo e palavras-chave
content_keywords = Table(
    'content_keywords',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('content.id'), primary_key=True),
    Column('keyword_id', Integer, ForeignKey('keywords.id'), primary_key=True)
)

# Tabela base de conteúdo (para herança)
class Content(Base):
    __tablename__ = 'content'
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    link = Column(String(1000))
    source_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    type = Column(String(50))  # Para discriminação de tipo (news, paper, repo)
    
    # Relacionamentos
    keywords = relationship("Keyword", secondary=content_keywords, back_populates="content_items")
    sentiment_analysis = relationship("SentimentAnalysis", back_populates="content", uselist=False)
    
    __mapper_args__ = {
        'polymorphic_identity': 'content',
        'polymorphic_on': type
    }

# Notícias
class News(Content):
    __tablename__ = 'news'
    id = Column(Integer, ForeignKey('content.id'), primary_key=True)
    read_time = Column(Integer)
    published_date = Column(DateTime)
    author = Column(String(255))
    cluster_id = Column(Integer, ForeignKey('news_clusters.id'))
    primary_source = Column(Boolean, default=False)  # Se é a fonte primária no cluster
    
    # Relacionamentos
    cluster = relationship("NewsCluster", back_populates="news_items")
    
    __mapper_args__ = {
        'polymorphic_identity': 'news',
    }

# Clusters de notícias
class NewsCluster(Base):
    __tablename__ = 'news_clusters'
    id = Column(Integer, primary_key=True)
    relevance_score = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relacionamentos
    news_items = relationship("News", back_populates="cluster")

# Papers de pesquisa
class ResearchPaper(Content):
    __tablename__ = 'research_papers'
    id = Column(Integer, ForeignKey('content.id'), primary_key=True)
    authors = Column(JSON)  # Lista de autores
    publication = Column(String(255))
    published_date = Column(DateTime)
    citations_count = Column(Integer)
    
    __mapper_args__ = {
        'polymorphic_identity': 'paper',
    }

# Repositórios
class Repository(Content):
    __tablename__ = 'repositories'
    id = Column(Integer, ForeignKey('content.id'), primary_key=True)
    stars = Column(Integer)
    forks = Column(Integer)
    language = Column(String(100))
    last_update = Column(DateTime)
    
    __mapper_args__ = {
        'polymorphic_identity': 'repo',
    }

# Palavras-chave
class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True)
    word = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamentos
    content_items = relationship("Content", secondary=content_keywords, back_populates="keywords")

# Análise de sentimento
class SentimentAnalysis(Base):
    __tablename__ = 'sentiment_analysis'
    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('content.id'))
    sentiment = Column(String(50))  # positive, negative, neutral
    polarity = Column(Float)
    subjectivity = Column(Float)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamentos
    content = relationship("Content", back_populates="sentiment_analysis")

# Registros de coleta
class CollectionJob(Base):
    __tablename__ = 'collection_jobs'
    id = Column(Integer, primary_key=True)
    job_type = Column(String(50))  # news, papers, repos
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(50))  # running, completed, failed
    items_collected = Column(Integer, default=0)
    error_message = Column(Text)