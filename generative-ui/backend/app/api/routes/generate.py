"""
Main API endpoint for UI generation.

This module provides the primary API endpoint for generating UI specifications
from URLs, with both REST and WebSocket support for progress streaming.

Endpoints:
- POST /api/generate: Generate UI from URL
- WebSocket /api/generate/ws: Stream progress updates
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field

from app.models.data_model import TaskDrivenDataModel
from app.models.ui_spec import UISpecification
from app.services.pipeline import GenerationPipeline

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/generate", tags=["generate"])

# Global pipeline instance
pipeline = GenerationPipeline()


# Pydantic models for request/response
class GenerateRequest(BaseModel):
    """Request model for UI generation."""
    url: HttpUrl = Field(..., description="URL to generate UI for")
    stream_progress: bool = Field(False, description="Whether to stream progress updates")
    additional_context: Optional[str] = Field(None, description="Additional context or follow-up prompt for generation")


class GenerateResponse(BaseModel):
    """Response model for UI generation."""
    success: bool = Field(..., description="Whether generation was successful")
    data_model: Optional[TaskDrivenDataModel] = Field(None, description="Generated data model")
    ui_spec: Optional[UISpecification] = Field(None, description="Generated UI specification")
    error: Optional[str] = Field(None, description="Error message if generation failed")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")


class ProgressUpdate(BaseModel):
    """WebSocket progress update model."""
    step: str = Field(..., description="Current pipeline step")
    message: str = Field(..., description="Progress message")
    progress: float = Field(..., description="Progress percentage (0-100)")
    timestamp: str = Field(..., description="Update timestamp")


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for progress streaming."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")
    
    async def send_progress(self, client_id: str, progress: ProgressUpdate):
        """Send progress update to a specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(progress.json())
            except Exception as e:
                logger.error(f"Failed to send progress to {client_id}: {str(e)}")
                self.disconnect(client_id)
    
    async def send_error(self, client_id: str, error_message: str):
        """Send error message to a specific client."""
        if client_id in self.active_connections:
            try:
                error_update = ProgressUpdate(
                    step="error",
                    message=error_message,
                    progress=0.0,
                    timestamp=json.dumps({"timestamp": "now"})
                )
                await self.active_connections[client_id].send_text(error_update.json())
            except Exception as e:
                logger.error(f"Failed to send error to {client_id}: {str(e)}")
                self.disconnect(client_id)


# Global connection manager
manager = ConnectionManager()


def validate_url(url: str) -> bool:
    """
    Validate URL format and accessibility.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is valid
    """
    try:
        parsed = urlparse(str(url))
        return all([parsed.scheme, parsed.netloc])
    except Exception:
        return False


async def send_progress_update(client_id: str, step: str, message: str, progress: float):
    """Send progress update via WebSocket."""
    if client_id:
        update = ProgressUpdate(
            step=step,
            message=message,
            progress=progress,
            timestamp=json.dumps({"timestamp": "now"})
        )
        await manager.send_progress(client_id, update)


@router.post("/", response_model=GenerateResponse)
async def generate_ui(request: GenerateRequest):
    """
    Generate UI specification from a URL.
    
    Args:
        request: GenerateRequest with URL and options
        
    Returns:
        GenerateResponse: Generated data model and UI specification
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Validate URL
        if not validate_url(str(request.url)):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        logger.info(f"Starting UI generation for URL: {request.url}")
        
        # Generate UI using pipeline
        data_model, ui_spec = await pipeline.generate_ui_from_url(str(request.url), request.additional_context)
        
        # Calculate processing time
        processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        logger.info(f"UI generation completed successfully in {processing_time}ms")
        
        return GenerateResponse(
            success=True,
            data_model=data_model,
            ui_spec=ui_spec,
            error=None,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        error_message = f"UI generation failed: {str(e)}"
        logger.error(error_message)
        
        return GenerateResponse(
            success=False,
            data_model=None,
            ui_spec=None,
            error=error_message,
            processing_time_ms=processing_time
        )


@router.websocket("/ws")
async def websocket_generate(websocket: WebSocket, url: str, client_id: Optional[str] = None):
    """
    WebSocket endpoint for streaming UI generation progress.
    
    Args:
        websocket: WebSocket connection
        url: URL to generate UI for
        client_id: Optional client identifier
    """
    if not client_id:
        client_id = f"client_{len(manager.active_connections)}"
    
    await manager.connect(websocket, client_id)
    
    try:
        # Validate URL
        if not validate_url(url):
            await manager.send_error(client_id, "Invalid URL format")
            return
        
        logger.info(f"Starting WebSocket UI generation for URL: {url} (client: {client_id})")
        
        # Send initial progress
        await send_progress_update(client_id, "starting", "Initializing UI generation...", 0.0)
        
        # Step 1: Scraping
        await send_progress_update(client_id, "scraping", "Scraping content from URL...", 20.0)
        
        try:
            # Initialize scraper
            from app.services.scraper import ContentScraper
            scraper = ContentScraper()
            
            async with scraper as scraper_instance:
                scraped_content = await scraper_instance.scrape_url(url)
                
                if not scraped_content.get('success', False):
                    raise Exception(f"Scraping failed: {scraped_content.get('error', 'Unknown error')}")
                
                await send_progress_update(client_id, "scraping", "Content scraped successfully!", 40.0)
                
        except Exception as e:
            await manager.send_error(client_id, f"Scraping failed: {str(e)}")
            return
        
        # Step 2: Interpretation
        await send_progress_update(client_id, "interpreting", "Interpreting content with AI...", 50.0)
        
        try:
            from app.services.interpreter import ContentInterpreter
            interpreter = ContentInterpreter()
            
            data_model = await interpreter.interpret_content(scraped_content)
            await send_progress_update(client_id, "interpreting", f"Content interpreted! Found {len(data_model.entities)} entities.", 70.0)
            
        except Exception as e:
            await manager.send_error(client_id, f"Content interpretation failed: {str(e)}")
            return
        
        # Step 3: UI Generation
        await send_progress_update(client_id, "generating", "Generating UI specification...", 80.0)
        
        try:
            from app.services.ui_generator import UIGenerator
            ui_generator = UIGenerator()
            
            ui_spec = ui_generator.generate_ui_spec(data_model)
            await send_progress_update(client_id, "generating", f"UI specification generated! Created {len(ui_spec.panels)} panels.", 90.0)
            
        except Exception as e:
            await manager.send_error(client_id, f"UI generation failed: {str(e)}")
            return
        
        # Step 4: Complete
        await send_progress_update(client_id, "complete", "UI generation complete!", 100.0)
        
        # Send final result
        result = {
            "success": True,
            "data_model": data_model.model_dump(),
            "ui_spec": ui_spec.model_dump(),
            "message": "UI generation completed successfully"
        }
        
        await websocket.send_text(json.dumps(result))
        
        logger.info(f"WebSocket UI generation completed for URL: {url} (client: {client_id})")
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        error_message = f"WebSocket UI generation failed: {str(e)}"
        logger.error(error_message)
        await manager.send_error(client_id, error_message)
    finally:
        manager.disconnect(client_id)


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the generation service.
    
    Returns:
        Dict: Health status of all services
    """
    try:
        health_status = await pipeline.health_check()
        return {
            "status": "healthy",
            "services": health_status,
            "cache_stats": pipeline.get_cache_stats()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear the generation pipeline cache.
    
    Returns:
        Dict: Cache clearing confirmation
    """
    try:
        pipeline.clear_cache()
        return {
            "success": True,
            "message": "Cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Cache clearing failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/cache/stats")
async def cache_stats():
    """
    Get cache statistics.
    
    Returns:
        Dict: Cache statistics
    """
    try:
        stats = pipeline.get_cache_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Cache stats failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }