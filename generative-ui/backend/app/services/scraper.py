"""
Web scraper service for the Generative UI Browser.

This module provides comprehensive web scraping capabilities that handle both
static and JavaScript-rendered pages using trafilatura and Playwright.

Features:
- Fast static content extraction with trafilatura
- JavaScript rendering fallback with Playwright
- Comprehensive error handling
- Structured data extraction
- Metadata preservation
- Logging and monitoring
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
load_dotenv()
import trafilatura
from playwright.async_api import async_playwright, Browser, Page
import aiohttp
from aiohttp import ClientTimeout, ClientError, ClientResponseError

# Configure logging
logger = logging.getLogger(__name__)


class ContentScraper:
    """
    Advanced web scraper that handles both static and JavaScript-rendered content.
    
    This scraper uses a two-tier approach:
    1. Fast static extraction with trafilatura
    2. JavaScript rendering fallback with Playwright
    """
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the content scraper.

        Args:
            timeout: Maximum time to wait for page load (seconds)
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        self.use_firecrawl = bool(self.firecrawl_api_key)
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=ClientTimeout(total=self.timeout),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def scrape_url(self, url: str) -> Dict[str, Union[str, Dict, List]]:
        """
        Main scraping method that handles both static and JavaScript-rendered pages.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary containing scraped content and metadata
            
        Raises:
            ValueError: If URL is invalid
            ConnectionError: If network connection fails
            TimeoutError: If scraping times out
            Exception: For other scraping errors
        """
        start_time = datetime.now()
        logger.info(f"Starting scrape for URL: {url}")
        
        # Validate URL
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL format: {url}")

        # Try Firecrawl first
        try:
            logger.info("Attempting content extraction with Firecrawl")
            result = await self._scrape_with_firecrawl(url)
            if result and result.get('success', False):
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Successfully scraped with Firecrawl in {processing_time:.2f}s")
                result["extraction_method"] = "firecrawl"
                result["processing_time"] = processing_time
                return result
        except Exception as e:
            logger.warning(f"Firecrawl extraction failed: {str(e)}")

        # Try trafilatura first (fast path for static content)
        try:
            logger.info("Attempting static content extraction with trafilatura")
            result = await self._scrape_with_trafilatura(url)
            if result:
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Successfully scraped with trafilatura in {processing_time:.2f}s")
                result["extraction_method"] = "trafilatura"
                result["processing_time"] = processing_time
                result["success"] = True
                return result
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed: {str(e)}")

        # Fallback to Playwright for JavaScript-heavy sites
        try:
            logger.info("Falling back to Playwright for JavaScript rendering")
            result = await self._scrape_with_playwright(url)
            if result:
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Successfully scraped with Playwright in {processing_time:.2f}s")
                result["extraction_method"] = "playwright+trafilatura"
                result["processing_time"] = processing_time
                result["success"] = True
                return result
        except Exception as e:
            logger.error(f"Playwright extraction failed: {str(e)}")
            return {
                'success': False,
                'error': f'Playwright extraction failed: {str(e)}',
                'url': url,
                'extraction_timestamp': datetime.now().isoformat()
            }
        
        # If we get here, both methods failed
        return {
            'success': False,
            'error': 'All scraping methods failed',
            'url': url,
            'extraction_timestamp': datetime.now().isoformat()
        }

    async def _scrape_with_firecrawl(self, url: str) -> Optional[Dict[str, Union[str, Dict, List]]]:
        """
        Extract content using Firecrawl API.

        Args:
            url: The URL to scrape

        Returns:
            Extracted content dictionary or None if failed
        """
        try:
            if not self.session:
                return None

            payload = {
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                # "includeTags": ["h1", "h2", "h3", "p", "li", "table", "img"],
                # "excludeTags": ["script", "style", "nav", "footer", "aside"],
                "maxAge": 172800000,  # 2 days in milliseconds
                "headers": {},
                "waitFor": 0,
                "mobile": False,
                "skipTlsVerification": False,
                "timeout": self.timeout * 1000,  # Convert to milliseconds
                "removeBase64Images": True,
                "blockAds": True,
                "proxy": "auto",
                "storeInCache": True,
                "zeroDataRetention": False
            }

            headers = {
                'Authorization': f'Bearer {self.firecrawl_api_key}',
                'Content-Type': 'application/json'
            }

            async with self.session.post(
                'https://api.firecrawl.dev/v2/scrape',
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Firecrawl API error {response.status}: {error_text}")
                    return None

                data = await response.json()

                if not data.get('success', False):
                    logger.error(f"Firecrawl scraping failed: {data.get('error', 'Unknown error')}")
                    return None

                # Extract the content from Firecrawl response
                content_data = data.get('data', {})
                markdown_content = content_data.get('markdown', '')

                if not markdown_content:
                    logger.warning("Firecrawl returned empty content")
                    return None

                # Parse markdown to extract structured data
                return self._parse_firecrawl_markdown(markdown_content, url, content_data)

        except Exception as e:
            logger.error(f"Firecrawl extraction error: {str(e)}")
            return None

    def _parse_firecrawl_markdown(self, markdown: str, url: str, metadata: Dict) -> Dict[str, Union[str, Dict, List]]:
        """
        Parse Firecrawl markdown output into our standard format.

        Args:
            markdown: Markdown content from Firecrawl
            url: Original URL
            metadata: Metadata from Firecrawl response

        Returns:
            Formatted content dictionary
        """
        try:
            # Extract title from markdown (usually first h1)
            title = ""
            lines = markdown.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                if line.strip().startswith('# '):
                    title = line.strip()[2:].strip()
                    break

            if not title:
                title = metadata.get('title', 'Unknown Title')

            # Extract headings
            headings = []
            for line in lines:
                line = line.strip()
                if line.startswith('# '):
                    headings.append({'level': 1, 'text': line[2:].strip()})
                elif line.startswith('## '):
                    headings.append({'level': 2, 'text': line[3:].strip()})
                elif line.startswith('### '):
                    headings.append({'level': 3, 'text': line[4:].strip()})

            # Extract links (basic regex for markdown links)
            links = []
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            matches = re.findall(link_pattern, markdown)
            for text, href in matches:
                links.append({'text': text.strip(), 'href': href.strip()})

            # Clean content (remove excessive whitespace)
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown.strip())

            # Extract description from metadata or first paragraph
            description = metadata.get('description', '')
            if not description:
                # Try to get first paragraph
                paragraphs = [line for line in lines if line.strip() and not line.startswith('#')]
                if paragraphs:
                    description = paragraphs[0][:200] + '...' if len(paragraphs[0]) > 200 else paragraphs[0]

            return {
                'url': url,
                'title': title,
                'content': content,
                'metadata': {
                    'description': description,
                    'author': metadata.get('author'),
                    'date': metadata.get('date'),
                    'language': metadata.get('language'),
                    'site_name': metadata.get('siteName'),
                    'canonical_url': url
                },
                'structured_data': {
                    'headings': headings,
                    'links': links,
                    'tables': [],  # Firecrawl doesn't extract tables in markdown format
                    'images': []   # Firecrawl removes base64 images by default
                },
                'raw_html': '',  # Firecrawl doesn't provide raw HTML
                'extraction_timestamp': datetime.now().isoformat(),
                'success': True
            }

        except Exception as e:
            logger.error(f"Failed to parse Firecrawl markdown: {str(e)}")
            return {
                'url': url,
                'title': 'Error parsing content',
                'content': markdown,  # Return raw markdown as fallback
                'metadata': {},
                'structured_data': {},
                'raw_html': '',
                'extraction_timestamp': datetime.now().isoformat(),
                'success': True
            }

    async def _scrape_with_trafilatura(self, url: str) -> Optional[Dict[str, Union[str, Dict, List]]]:
        """
        Extract content using trafilatura (fast path for static content).
        
        Args:
            url: The URL to scrape
            
        Returns:
            Extracted content dictionary or None if failed
        """
        try:
            # Fetch the URL content
            downloaded = trafilatura.fetch_url(
                url,
                no_ssl=True,  # Handle SSL issues
            )
            
            if not downloaded:
                logger.warning("Trafilatura failed to download content")
                return None
            
            # Extract content with comprehensive options
            result = trafilatura.extract(
                downloaded,
                output_format="json",
                with_metadata=True,
                include_comments=False,
                include_tables=True,  # Keep tables for structured data
                include_images=False,
                include_links=True,
                include_formatting=True
            )
            
            if not result:
                logger.warning("Trafilatura failed to extract content")
                return None
            
            # Format the output
            return self._format_trafilatura_output(result)
            
        except Exception as e:
            logger.error(f"Trafilatura extraction error: {str(e)}")
            return None
    
    def _format_trafilatura_output(self, json_output: str) -> Dict[str, Union[str, Dict, List]]:
        """
        Convert trafilatura JSON to our standard format.
        
        Args:
            json_output: JSON string from trafilatura
            
        Returns:
            Formatted content dictionary
        """
        try:
            data = json.loads(json_output)
            
            # Extract basic content
            content = data.get('text', '').strip()
            title = data.get('title', '').strip()
            
            # Extract metadata
            metadata = {
                'author': data.get('author'),
                'date': data.get('date'),
                'description': data.get('description'),
                'categories': self._extract_categories(data),
                'tags': self._extract_tags(data),
                'language': data.get('language'),
                'site_name': data.get('sitename'),
                'canonical_url': data.get('canonical')
            }
            
            # Clean up metadata (remove None values)
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            # Extract additional structured data
            structured_data = {
                'headings': self._extract_headings(data),
                'links': self._extract_links(data),
                'tables': self._extract_tables(data),
                'images': self._extract_images(data)
            }
            
            return {
                'url': data.get('url', ''),
                'title': title,
                'content': content,
                'metadata': metadata,
                'structured_data': structured_data,
                'raw_html': data.get('raw_html', ''),
                'extraction_timestamp': datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse trafilatura JSON: {str(e)}")
            return {
                'url': '',
                'title': '',
                'content': json_output,  # Fallback to raw output
                'metadata': {},
                'structured_data': {},
                'raw_html': '',
                'extraction_timestamp': datetime.now().isoformat()
            }
    
    async def _scrape_with_playwright(self, url: str) -> Optional[Dict[str, Union[str, Dict, List]]]:
        """
        Fallback for JavaScript-rendered pages using Playwright.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Extracted content dictionary or None if failed
        """
        try:
            async with async_playwright() as p:
                # Launch browser with optimized settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                try:
                    # Create new page
                    page = await browser.new_page()
                    
                    # Set viewport and user agent
                    await page.set_viewport_size({"width": 1920, "height": 1080})
                    await page.set_extra_http_headers({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    })
                    
                    # Navigate to URL with timeout
                    await page.goto(url, wait_until='domcontentloaded')
                    
                    # Wait for content to load
                    await page.wait_for_load_state('domcontentloaded')
                    
                    # Get the rendered HTML
                    html_content = await page.content()
                    
                    # Extract content using trafilatura
                    result = trafilatura.extract(
                        filecontent=html_content,
                        output_format="json",
                        with_metadata=True,
                        include_comments=True,
                        include_tables=True,
                        include_images=True,
                        include_links=True,
                        include_formatting=True
                    )
                    
                    if not result:
                        logger.warning("Playwright + trafilatura failed to extract content")
                        return None
                    
                    # Format the output
                    formatted_result = self._format_trafilatura_output(result)
                    formatted_result['raw_html'] = html_content
                    
                    return formatted_result
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"Playwright extraction error: {str(e)}")
            return None
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _extract_categories(self, data: Dict) -> List[str]:
        """Extract categories from trafilatura data."""
        categories = []
        
        # Try different category fields
        for field in ['categories', 'category', 'section', 'sections']:
            if field in data and data[field]:
                if isinstance(data[field], list):
                    categories.extend(data[field])
                elif isinstance(data[field], str):
                    categories.append(data[field])
        
        return list(set(categories))  # Remove duplicates
    
    def _extract_tags(self, data: Dict) -> List[str]:
        """Extract tags from trafilatura data."""
        tags = []
        
        # Try different tag fields
        for field in ['tags', 'tag', 'keywords', 'keyword']:
            if field in data and data[field]:
                if isinstance(data[field], list):
                    tags.extend(data[field])
                elif isinstance(data[field], str):
                    # Split comma-separated tags
                    tags.extend([tag.strip() for tag in data[field].split(',')])
        
        return list(set(tags))  # Remove duplicates
    
    def _extract_headings(self, data: Dict) -> List[Dict[str, str]]:
        """Extract headings from trafilatura data."""
        headings = []
        
        # Look for headings in the content
        content = data.get('text', '')
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        
        for line in content.split('\n'):
            match = re.match(heading_pattern, line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    'level': level,
                    'text': text
                })
        
        return headings
    
    def _extract_links(self, data: Dict) -> List[Dict[str, str]]:
        """Extract links from trafilatura data."""
        links = []
        
        # Extract links from raw HTML if available
        raw_html = data.get('raw_html', '')
        if raw_html:
            link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
            matches = re.findall(link_pattern, raw_html, re.IGNORECASE)
            
            for href, text in matches:
                links.append({
                    'href': href,
                    'text': text.strip()
                })
        
        return links
    
    def _extract_tables(self, data: Dict) -> List[Dict[str, str]]:
        """Extract tables from trafilatura data."""
        tables = []
        
        # Look for table data in structured content
        if 'tables' in data and data['tables']:
            for table in data['tables']:
                tables.append({
                    'html': table,
                    'type': 'html_table'
                })
        
        return tables
    
    def _extract_images(self, data: Dict) -> List[Dict[str, str]]:
        """Extract images from trafilatura data."""
        images = []
        
        # Extract images from raw HTML if available
        raw_html = data.get('raw_html', '')
        if raw_html:
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*>'
            matches = re.findall(img_pattern, raw_html, re.IGNORECASE)
            
            for src, alt in matches:
                images.append({
                    'src': src,
                    'alt': alt.strip()
                })
        
        return images


# Utility functions for external use
async def scrape_url(url: str, timeout: int = 30) -> Dict[str, Union[str, Dict, List]]:
    """
    Convenience function to scrape a single URL.
    
    Args:
        url: The URL to scrape
        timeout: Maximum time to wait for page load (seconds)
        
    Returns:
        Dictionary containing scraped content and metadata
    """
    async with ContentScraper(timeout=timeout) as scraper:
        return await scraper.scrape_url(url)


async def scrape_multiple_urls(urls: List[str], timeout: int = 30) -> List[Dict[str, Union[str, Dict, List]]]:
    """
    Scrape multiple URLs concurrently.
    
    Args:
        urls: List of URLs to scrape
        timeout: Maximum time to wait for each page load (seconds)
        
    Returns:
        List of dictionaries containing scraped content and metadata
    """
    async with ContentScraper(timeout=timeout) as scraper:
        tasks = [scraper.scrape_url(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)