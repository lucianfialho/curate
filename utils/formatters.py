import logging
from datetime import datetime
from typing import Dict, Any, Optional
from models.content_models import CuratedContent

logger = logging.getLogger(__name__)

def convert_to_json(content: CuratedContent, insights: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convert curated content to a simplified JSON format that can be easily consumed by any application.
    
    Args:
        content: CuratedContent object with curated content
        insights: Optional dictionary with sentiment insights
        
    Returns:
        Dictionary ready for JSON serialization
    """
    try:
        # Ensure insights is a dict
        insights = insights or {}
            
        # Convert Pydantic model to dict
        if hasattr(content, 'model_dump'):
            content_dict = content.model_dump()
        elif hasattr(content, 'dict'):
            # For older Pydantic versions
            content_dict = content.dict()
        else:
            # Fallback for non-Pydantic objects
            logger.warning("Content is not a Pydantic model, using __dict__ conversion")
            content_dict = {k: v for k, v in content.__dict__.items() 
                          if not k.startswith('_')}
        
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
