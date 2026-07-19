"""
Generation Pipeline service for the Generative UI Browser.

This module orchestrates the complete UI generation pipeline from URL
to final UI specification, coordinating all services and providing
caching and error handling.

Features:
- Complete pipeline orchestration
- In-memory caching for performance
- Comprehensive logging and debugging
- Error handling and recovery
- Service coordination
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from app.models.data_model import TaskDrivenDataModel
from app.models.ui_spec import UISpecification
from app.services.scraper import ContentScraper
from app.services.interpreter import ContentInterpreter
from app.services.ui_generator import UIGenerator

# Configure logging
logger = logging.getLogger(__name__)


class GenerationPipeline:
    """
    Orchestrates the complete UI generation pipeline from URL to UI specification.
    
    Pipeline Steps:
    1. URL Scraping (ContentScraper)
    2. Content Interpretation (ContentInterpreter) 
    3. UI Specification Generation (UIGenerator)
    """
    
    def __init__(
        self,
        cache_ttl_hours: int = 24,
        max_cache_size: int = 100,
        enable_caching: bool = True
    ):
        """
        Initialize the generation pipeline.
        
        Args:
            cache_ttl_hours: Cache time-to-live in hours
            max_cache_size: Maximum number of cached entries
            enable_caching: Whether to enable caching
        """
        self.cache_ttl_hours = cache_ttl_hours
        self.max_cache_size = max_cache_size
        self.enable_caching = enable_caching
        
        # Initialize services
        self.scraper = None  # Will be initialized when needed
        self.interpreter = None  # Will be initialized when needed
        self.ui_generator = UIGenerator()
        
        # In-memory cache
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        logger.info(f"GenerationPipeline initialized with caching={'enabled' if enable_caching else 'disabled'}")
    
    async def generate_ui_from_url(self, url: str, additional_context: Optional[str] = None) -> Tuple[TaskDrivenDataModel, UISpecification]:
        """
        Generate UI specification from a URL through the complete pipeline.
        
        Args:
            url: URL to scrape and generate UI for
            additional_context: Optional additional context or follow-up prompt for generation
            
        Returns:
            Tuple[TaskDrivenDataModel, UISpecification]: Generated data model and UI spec
            
        Raises:
            ValueError: If URL is invalid or pipeline fails
            Exception: If any step in the pipeline fails
        """
        start_time = time.perf_counter()
        logger.info(f"Starting UI generation pipeline for URL: {url}")
        if additional_context:
            logger.info(f"Additional context provided: {additional_context}")
        
        # Create cache key including additional context
        cache_key = f"{url}:{additional_context or 'default'}"
        
        # Check cache first
        if self.enable_caching:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Cache hit for URL: {url} with context: {additional_context or 'default'}")
                return cached_result['data_model'], cached_result['ui_spec']
        
        try:
            # Step 1: Scrape content from URL
            logger.info(f"Step 1: Scraping content from {url}")
            scraped_content = await self._scrape_url(url)
            logger.info(f"Scraping completed. Content length: {len(scraped_content.get('content', ''))}")
            
            # Step 2: Interpret content with LLM
            logger.info("Step 2: Interpreting content with LLM")
            data_model = await self._interpret_content(scraped_content, additional_context)
            logger.info(f"Content interpretation completed. Entities: {len(data_model.entities)}, Dependencies: {len(data_model.dependencies)}")
            
            # Step 3: Generate UI specification
            logger.info("Step 3: Generating UI specification")
            ui_spec = await self._generate_ui_spec(data_model)
            logger.info(f"UI specification generated. Panels: {len(ui_spec.panels)}")
            
            # Cache the result
            if self.enable_caching:
                self._store_in_cache(cache_key, data_model, ui_spec)
            
            # Calculate total time
            total_time = time.perf_counter() - start_time
            logger.info(f"Pipeline completed successfully in {total_time:.2f} seconds")
            
            return data_model, ui_spec
            
        except Exception as e:
            logger.error(f"Pipeline failed for URL {url}: {str(e)}")
            raise Exception(f"UI generation pipeline failed: {str(e)}")
    
    async def _scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from URL using ContentScraper.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict: Scraped content data
            
        Raises:
            Exception: If scraping fails
        """
        try:
            # Initialize scraper if not already done
            if self.scraper is None:
                self.scraper = ContentScraper()
            
            # Use async context manager for scraper
            async with self.scraper as scraper:
                scraped_data = await scraper.scrape_url(url)
                
                if not scraped_data.get('success', False):
                    raise Exception(f"Scraping failed: {scraped_data.get('error', 'Unknown error')}")
                
                logger.debug(f"Scraped content: {scraped_data.get('title', 'No title')}")
                return scraped_data
                
        except Exception as e:
            logger.error(f"Scraping failed for URL {url}: {str(e)}")
            raise Exception(f"Content scraping failed: {str(e)}")
    
    async def _interpret_content(self, scraped_data: Dict[str, Any], additional_context: Optional[str] = None) -> TaskDrivenDataModel:
        """
        Interpret scraped content using ContentInterpreter.
        
        Args:
            scraped_data: Scraped content from scraper
            additional_context: Optional additional context for interpretation
            
        Returns:
            TaskDrivenDataModel: Interpreted data model
            
        Raises:
            Exception: If interpretation fails
        """
        try:
            # Initialize interpreter if not already done
            if self.interpreter is None:
                self.interpreter = ContentInterpreter()
            
            # Add additional context to scraped data if provided
            if additional_context:
                scraped_data = scraped_data.copy()
                scraped_data['additional_context'] = additional_context
                logger.info(f"Added additional context to interpretation: {additional_context}")
            
            # Interpret the content
            data_model = await self.interpreter.interpret_content(scraped_data)
            
            logger.debug(f"Interpreted {len(data_model.entities)} entities and {len(data_model.dependencies)} dependencies")
            return data_model
            
        except Exception as e:
            logger.error(f"Content interpretation failed: {str(e)}")
            raise Exception(f"Content interpretation failed: {str(e)}")
    
    async def _generate_ui_spec(self, data_model: TaskDrivenDataModel) -> UISpecification:
        """
        Generate UI specification using UIGenerator.
        
        Args:
            data_model: TaskDrivenDataModel to generate UI for
            
        Returns:
            UISpecification: Generated UI specification
            
        Raises:
            Exception: If UI generation fails
        """
        try:
            # Generate UI specification
            ui_spec = self.ui_generator.generate_ui_spec(data_model)
            
            logger.debug(f"Generated UI spec with {len(ui_spec.panels)} panels")
            return ui_spec
            
        except Exception as e:
            logger.error(f"UI generation failed: {str(e)}")
            raise Exception(f"UI specification generation failed: {str(e)}")
    
    def _get_from_cache(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result for URL if available and not expired.
        
        Args:
            url: URL to look up in cache
            
        Returns:
            Dict: Cached result or None if not found/expired
        """
        if url not in self.cache:
            return None
        
        # Check if cache entry is expired
        cache_time = self.cache_timestamps.get(url)
        if cache_time and datetime.utcnow() - cache_time > timedelta(hours=self.cache_ttl_hours):
            logger.debug(f"Cache entry expired for URL: {url}")
            self._remove_from_cache(url)
            return None
        
        logger.debug(f"Cache hit for URL: {url}")
        return self.cache[url]
    
    def _store_in_cache(self, url: str, data_model: TaskDrivenDataModel, ui_spec: UISpecification):
        """
        Store result in cache.
        
        Args:
            url: URL to cache result for
            data_model: TaskDrivenDataModel to cache
            ui_spec: UISpecification to cache
        """
        # Check cache size limit
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest_cache_entry()
        
        # Store in cache
        self.cache[url] = {
            'data_model': data_model,
            'ui_spec': ui_spec,
            'cached_at': datetime.utcnow()
        }
        self.cache_timestamps[url] = datetime.utcnow()
        
        logger.debug(f"Cached result for URL: {url}")
    
    def _remove_from_cache(self, url: str):
        """
        Remove entry from cache.
        
        Args:
            url: URL to remove from cache
        """
        if url in self.cache:
            del self.cache[url]
        if url in self.cache_timestamps:
            del self.cache_timestamps[url]
    
    def _evict_oldest_cache_entry(self):
        """Remove the oldest cache entry."""
        if not self.cache_timestamps:
            return
        
        oldest_url = min(self.cache_timestamps.keys(), key=lambda k: self.cache_timestamps[k])
        logger.debug(f"Evicting oldest cache entry: {oldest_url}")
        self._remove_from_cache(oldest_url)
    
    def clear_cache(self):
        """Clear all cached entries."""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics
        """
        return {
            'cache_size': len(self.cache),
            'max_cache_size': self.max_cache_size,
            'cache_ttl_hours': self.cache_ttl_hours,
            'cached_urls': list(self.cache.keys()),
            'oldest_entry': min(self.cache_timestamps.values()) if self.cache_timestamps else None,
            'newest_entry': max(self.cache_timestamps.values()) if self.cache_timestamps else None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all services.
        
        Returns:
            Dict: Health status of all services
        """
        health_status = {
            'pipeline': 'healthy',
            'scraper': 'unknown',
            'interpreter': 'unknown',
            'ui_generator': 'healthy',
            'cache': 'healthy' if self.enable_caching else 'disabled'
        }
        
        # Test scraper
        try:
            if self.scraper is None:
                self.scraper = ContentScraper()
            health_status['scraper'] = 'healthy'
        except Exception as e:
            health_status['scraper'] = f'unhealthy: {str(e)}'
        
        # Test interpreter
        try:
            if self.interpreter is None:
                self.interpreter = ContentInterpreter()
            health_status['interpreter'] = 'healthy'
        except Exception as e:
            health_status['interpreter'] = f'unhealthy: {str(e)}'
        
        return health_status


# Utility functions for external use
async def generate_ui_from_url(url: str, additional_context: Optional[str] = None) -> Tuple[TaskDrivenDataModel, UISpecification]:
    """
    Convenience function to generate UI from URL.
    
    Args:
        url: URL to generate UI for
        additional_context: Optional additional context for generation
        
    Returns:
        Tuple[TaskDrivenDataModel, UISpecification]: Generated data model and UI spec
    """
    pipeline = GenerationPipeline()
    return await pipeline.generate_ui_from_url(url, additional_context)
