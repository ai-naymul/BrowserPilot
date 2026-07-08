"""
JSON-based storage service for data models.
In production, replace with proper database.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Storage directory
STORAGE_DIR = Path(__file__).parent.parent.parent / "data" / "models"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class DataModelStorage:
    """Handles saving and loading data models to/from JSON files."""
    
    @staticmethod
    def save(session_id: str, data_model: Dict[Any, Any]) -> bool:
        """
        Save data model to JSON file.
        
        Args:
            session_id: Unique identifier for the session
            data_model: The data model dictionary to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp if not present
            if 'updated_at' not in data_model:
                data_model['updated_at'] = datetime.utcnow().isoformat()
            
            # Save to file
            file_path = STORAGE_DIR / f"{session_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_model, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved data model to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save data model: {str(e)}")
            return False
    
    @staticmethod
    def load(session_id: str) -> Optional[Dict[Any, Any]]:
        """
        Load data model from JSON file.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            Dict or None: The data model if found, None otherwise
        """
        try:
            file_path = STORAGE_DIR / f"{session_id}.json"
            
            if not file_path.exists():
                logger.warning(f"Data model not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data_model = json.load(f)
            
            logger.info(f"✓ Loaded data model from {file_path}")
            return data_model
            
        except Exception as e:
            logger.error(f"Failed to load data model: {str(e)}")
            return None
    
    @staticmethod
    def list_sessions() -> list[str]:
        """
        List all saved session IDs.
        
        Returns:
            list: List of session IDs
        """
        try:
            return [f.stem for f in STORAGE_DIR.glob("*.json")]
        except Exception as e:
            logger.error(f"Failed to list sessions: {str(e)}")
            return []
    
    @staticmethod
    def delete(session_id: str) -> bool:
        """
        Delete a data model file.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = STORAGE_DIR / f"{session_id}.json"
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"✓ Deleted data model: {file_path}")
                return True
            else:
                logger.warning(f"Data model not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete data model: {str(e)}")
            return False


# Singleton instance
storage = DataModelStorage()
