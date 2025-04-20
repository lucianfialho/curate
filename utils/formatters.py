import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def convert_to_json(content, insights: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convert curated content to a simplified JSON format that can be easily consumed by any application.
    
    Args:
        content: CuratedContent object with curated content
        insights: Optional dictionary with sentiment insights
        
    Returns:
        Dictionary ready for JSON serialization
    """
    try:
        # Check if content is None
        if content is None:
            logger.warning("Content is None, returning empty content")
            return {
                "content": {},
                "insights": insights or {},
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "status": "empty"
                }
            }
            
        # Ensure insights is a dict
        insights = insights or {}
        
        # Convert Pydantic model to dict
        content_dict = {}
        
        if hasattr(content, 'model_dump'):
            # For newer Pydantic versions (v2+)
            content_dict = content.model_dump()
        elif hasattr(content, 'dict'):
            # For older Pydantic versions (v1)
            content_dict = content.dict()
        elif isinstance(content, dict):
            # If it's already a dict
            content_dict = content
        else:
            # Safe fallback for non-Pydantic objects
            logger.warning("Content is not a Pydantic model or dict, using safe conversion")
            try:
                # Try to safely convert using __dict__
                content_dict = {k: v for k, v in content.__dict__.items() 
                              if not k.startswith('_')}
            except (AttributeError, TypeError) as e:
                logger.error(f"Failed to convert content to dict: {e}")
                content_dict = {"error": "Could not convert content to dictionary"}
        
        # Construct result
        return {
            "content": content_dict,
            "insights": insights,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
    except Exception as e:
        logger.error(f"Error converting content to JSON: {str(e)}")
        return {
            "error": str(e),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
        }