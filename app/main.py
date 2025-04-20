import logging
from fastapi import FastAPI, HTTPException
from typing import Dict, Any

from config.settings import get_settings
from curators.sentiment_curator import SentimentEnhancedContentCurator
from api.schemas import CurationRequest
from utils.formatters import convert_to_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="AIlert Sentiment API",
    description="""
    AI content curation API with sentiment analysis.
    
    Features:
    - Curates content from multiple sources (news, papers, repositories)
    - Applies sentiment analysis to content
    - Filters content by keywords
    - Groups similar content together
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

@app.get("/")
async def root():
    """Root endpoint - provides API information and links to documentation"""
    return {
        "name": "AIlert Sentiment API",
        "version": "1.0.0",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }

@app.on_event("startup")
async def startup_event():
    """Initialize curator on startup"""
    try:
        settings = get_settings()
        logger.info(f"Starting with config: {settings.CURATOR_CONFIG}")
        app.state.curator = SentimentEnhancedContentCurator(settings.CURATOR_CONFIG)
        logger.info("API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    try:
        if hasattr(app.state, 'curator'):
            await app.state.curator.close()
        logger.info("API shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

@app.post("/api/curate")
async def curate_content(request: CurationRequest) -> Dict[str, Any]:
    """
    Curate content based on request parameters
    
    Args:
        request: CurationRequest object containing parameters for content curation
            - max_news: Maximum number of news items to return (1-50)
            - max_papers: Maximum number of research papers to return (0-20)
            - max_repos: Maximum number of repositories to return (0-20)
            - keywords: Optional list of keywords to filter content
            - include_sentiment: Whether to include sentiment analysis
            - metadata: Additional request metadata
        
    Returns:
        Dictionary containing:
        - Curated content (news, papers, repositories)
        - Sentiment insights (if requested)
        - Metadata about the curation process
        
    Raises:
        HTTPException(400): If request validation fails
        HTTPException(500): If an error occurs during curation
    """
    try:
        # Log the request details for debugging
        request_dict = request.model_dump()
        logger.info(f"Processing curation request: {request_dict}")
        
        # Get curator from app state
        curator = app.state.curator
        if curator is None:
            logger.error("Curator not initialized in app state")
            raise ValueError("API service not properly initialized")
        
        # Log that we're about to call get_curated_content
        logger.info("Calling curator.get_curated_content")
        content = await curator.get_curated_content(request_dict)
        
        # Log whether content is None and its type
        if content is None:
            logger.error("curator.get_curated_content returned None")
        else:
            logger.info(f"Content returned with type: {type(content)}")
            
        # Add sentiment if requested
        insights = {}
        if request.include_sentiment:
            logger.info("Adding sentiment analysis")
            insights = curator.highlight_sentiment_insights(content)
            logger.info(f"Sentiment insights type: {type(insights)}")
        
        # Convert to JSON
        logger.info("Converting content to JSON")
        result = convert_to_json(content, insights)
        logger.info("Conversion to JSON successful")
        
        return result
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Curation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)