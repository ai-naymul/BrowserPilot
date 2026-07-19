"""
API routes for web scraping functionality.

This module provides RESTful endpoints for scraping web content with
rate limiting, comprehensive error handling, and structured responses.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.services.scraper import ContentScraper
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create router
router = APIRouter()

# Rate limiter will be configured in main.py


class ScrapeRequest(BaseModel):
    """
    Request model for web scraping endpoint.
    
    Validates URL format and provides clear error messages.
    """
    url: HttpUrl = Field(
        ...,
        description="The URL to scrape",
        example="https://www.washingtonpost.com/"
    )
    
    timeout: Optional[int] = Field(
        default=30,
        ge=5,
        le=120,
        description="Timeout in seconds (5-120)",
        example=30
    )
    
    @validator('url')
    def validate_url(cls, v):
        """Additional URL validation."""
        if not v.scheme or v.scheme not in ['http', 'https']:
            raise ValueError('URL must use HTTP or HTTPS protocol')
        return v


class ScrapeResponse(BaseModel):
    """
    Response model for successful scraping operations.
    
    Provides comprehensive information about the scraped content.
    """
    url: str = Field(..., description="The scraped URL")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Main content text")
    metadata: Dict[str, Any] = Field(..., description="Page metadata")
    structured_data: Dict[str, Any] = Field(..., description="Structured data (headings, links, etc.)")
    extraction_method: str = Field(..., description="Method used for extraction")
    success: bool = Field(True, description="Whether scraping was successful")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    timestamp: str = Field(..., description="When the scraping was performed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """
    Error response model for failed scraping operations.
    
    Provides detailed error information for debugging.
    """
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Detailed error message")
    url: str = Field(..., description="The URL that failed")
    timestamp: str = Field(..., description="When the error occurred")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


@router.post(
    "/scrape",
    response_model=ScrapeResponse,
    responses={
        200: {"description": "Scraping successful", "model": ScrapeResponse},
        400: {"description": "Invalid request", "model": ErrorResponse},
        422: {"description": "Scraping failed", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
        504: {"description": "Request timeout", "model": ErrorResponse}
    },
    summary="Scrape web content",
    description="Extract content from a web page using advanced scraping techniques"
)
@limiter.limit("10/minute")
async def scrape_url(
    request: Request,
    scrape_request: ScrapeRequest
) -> ScrapeResponse:
    """
    Scrape content from a web URL.
    
    This endpoint uses a two-tier approach:
    1. Fast static content extraction with trafilatura
    2. JavaScript rendering fallback with Playwright
    
    Rate limited to 10 requests per minute per IP address.
    
    Args:
        request: FastAPI request object (for rate limiting)
        scrape_request: Scraping request with URL and options
        
    Returns:
        ScrapeResponse: Structured response with scraped content
        
    Raises:
        HTTPException: For various error conditions
    """
    start_time = time.time()
    url_str = str(scrape_request.url)
    
    logger.info(f"Starting scrape request for URL: {url_str}")
    
    try:
        # Initialize scraper with timeout
        async with ContentScraper(timeout=scrape_request.timeout) as scraper:
            # Perform scraping
            result = await scraper.scrape_url(url_str)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Log success
            logger.info(f"Successfully scraped {url_str} in {processing_time_ms}ms")
            
            # Return structured response
            return ScrapeResponse(
                url=result.get('url', url_str),
                title=result.get('title', ''),
                content=result.get('content', ''),
                metadata=result.get('metadata', {}),
                structured_data=result.get('structured_data', {}),
                extraction_method=result.get('extraction_method', 'unknown'),
                success=True,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.now().isoformat()
            )
            
    except ValueError as e:
        # Invalid URL or request validation
        logger.warning(f"Invalid request for {url_str}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="Invalid Request",
                detail=str(e),
                url=url_str,
                timestamp=datetime.now().isoformat()
            ).dict()
        )
        
    except TimeoutError as e:
        # Scraping timeout
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Timeout scraping {url_str} after {processing_time_ms}ms: {str(e)}")
        raise HTTPException(
            status_code=504,
            detail=ErrorResponse(
                error="Gateway Timeout",
                detail=f"Scraping timed out after {scrape_request.timeout} seconds",
                url=url_str,
                timestamp=datetime.now().isoformat()
            ).dict()
        )
        
    except ConnectionError as e:
        # Network connection issues
        logger.error(f"Connection error scraping {url_str}: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error="Connection Error",
                detail="Failed to connect to the target URL",
                url=url_str,
                timestamp=datetime.now().isoformat()
            ).dict()
        )
        
    except Exception as e:
        # General scraping errors
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Scraping failed for {url_str} after {processing_time_ms}ms: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error="Scraping Failed",
                detail=str(e),
                url=url_str,
                timestamp=datetime.now().isoformat()
            ).dict()
        )


@router.get(
    "/scrape/health",
    summary="Scraping service health check",
    description="Check if the scraping service is operational"
)
async def health_check():
    """
    Health check endpoint for the scraping service.
    
    Returns:
        dict: Service status information
    """
    return {
        "status": "healthy",
        "service": "scraper",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.get(
    "/scrape/limits",
    summary="Get rate limit information",
    description="Get information about current rate limits"
)
async def get_rate_limits():
    """
    Get information about rate limits.
    
    Returns:
        dict: Rate limit configuration
    """
    return {
        "rate_limit": "10 requests per minute per IP",
        "timeout_range": "5-120 seconds",
        "supported_protocols": ["http", "https"],
        "extraction_methods": ["trafilatura", "playwright+trafilatura"]
    }


# Exception handler will be configured in main.py
