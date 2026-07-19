"""
Firecrawl Search Service for enriching LLM responses with real-world data.
"""

import logging
import os
from typing import Dict, List, Optional, Any
import aiohttp

logger = logging.getLogger(__name__)


class FirecrawlService:
    """Service for searching and scraping web content using Firecrawl API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Firecrawl service."""
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.base_url = "https://api.firecrawl.dev/v2"
        
        if not self.api_key:
            logger.warning("No Firecrawl API key found. Web enrichment will be disabled.")
    
    async def search(
        self,
        query: str,
        limit: int = 20,
        location: Optional[str] = None,
        scrape: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search the web for relevant information.
        
        Args:
            query: Search query
            limit: Maximum number of results (default: 20)
            location: Geographic location for search results
            scrape: Whether to scrape the search results
            
        Returns:
            List of search results with optional scraped content
        """
        if not self.api_key:
            logger.warning("Firecrawl API key not configured. Returning empty results.")
            return []
        
        try:
            url = f"{self.base_url}/search"
            
            payload = {
                "query": query,
                "limit": limit,
                "sources": [
                    {
                        "type": "web",
                        "tbs": "qdr:w"  # Last week - fresh data only
                    }
                ],
                "tbs": "qdr:w",  # Time-based search: last week
                "timeout": 30000,
                "ignoreInvalidURLs": True,
            }
            
            if location:
                payload["location"] = location
                payload["country"] = "US"  # Default to US
            
            if scrape:
                payload["scrapeOptions"] = {
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                    "maxAge": 172800000,  # 2 days cache
                    "timeout": 15000,
                    "removeBase64Images": True,
                    "blockAds": True,
                    "proxy": "auto"
                }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=35) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("data", [])
                        logger.info(f"Firecrawl search returned {len(results)} results for query: {query}")
                        return results
                    else:
                        error_text = await response.text()
                        logger.error(f"Firecrawl API error {response.status}: {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error searching with Firecrawl: {e}")
            return []
    
    async def enrich_moving_query(self, location: str) -> Dict[str, Any]:
        """
        Enrich a moving query with real-world neighborhood data.
        
        Args:
            location: City/location (e.g., "San Francisco")
            
        Returns:
            Dictionary with neighborhoods, housing, and cost of living data
        """
        try:
            # Search for neighborhoods
            neighborhoods_query = f"best neighborhoods to live in {location} with prices and characteristics"
            neighborhoods_results = await self.search(neighborhoods_query, limit=15, location=location)
            
            # Search for housing market
            housing_query = f"{location} housing market average rent prices 2024"
            housing_results = await self.search(housing_query, limit=10, location=location)
            
            # Search for cost of living
            cost_query = f"{location} cost of living expenses 2024"
            cost_results = await self.search(cost_query, limit=10, location=location)
            
            return {
                "neighborhoods": neighborhoods_results,
                "housing": housing_results,
                "cost_of_living": cost_results
            }
            
        except Exception as e:
            logger.error(f"Error enriching moving query: {e}")
            return {}
    
    def format_search_context(self, results: List[Dict[str, Any]], max_chars: int = 8000) -> str:
        """
        Format search results into a context string for the LLM.
        
        Args:
            results: List of search results
            max_chars: Maximum characters to include
            
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        context_parts = ["# Real-World Search Results:\n"]
        current_length = len(context_parts[0])
        
        # Ensure results is a list and limit to top 15
        if not isinstance(results, list):
            return ""
        
        limited_results = results[:15] if len(results) > 15 else results
        
        for i, result in enumerate(limited_results, 1):
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            description = result.get("description", "")
            
            # Get scraped markdown content if available
            markdown = ""
            if "markdown" in result:
                markdown = result["markdown"][:500]  # Limit markdown length
            
            result_text = f"\n## Result {i}: {title}\n"
            result_text += f"URL: {url}\n"
            
            if description:
                result_text += f"Description: {description}\n"
            
            if markdown:
                result_text += f"Content Preview:\n{markdown}\n"
            
            # Check if adding this result exceeds max_chars
            if current_length + len(result_text) > max_chars:
                break
            
            context_parts.append(result_text)
            current_length += len(result_text)
        
        return "".join(context_parts)


# Global instance
_firecrawl_service = None


def get_firecrawl_service() -> FirecrawlService:
    """Get or create the global Firecrawl service instance."""
    global _firecrawl_service
    if _firecrawl_service is None:
        _firecrawl_service = FirecrawlService()
    return _firecrawl_service
