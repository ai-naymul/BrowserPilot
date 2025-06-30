import json
import asyncio
import functools
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from backend.browser_controller import BrowserController
import base64
from bs4 import BeautifulSoup
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path
import re

MODEL = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

UNIVERSAL_EXTRACTION_PROMPT = """
You are a universal data extraction specialist. Your task is to analyze any webpage and extract the most relevant information based on the user's specific goal.

USER'S GOAL: {goal}
CURRENT URL: {url}
PAGE TITLE: {title}
WEBSITE TYPE: {website_type}

EXTRACTION GUIDELINES:

**For PERSON/PROFILE information:**
- Full name and professional title
- Current position and company
- Professional background and experience
- Education and credentials
- Skills and expertise areas
- Contact information (if publicly available)
- Notable achievements or projects
- Social media profiles and professional links

**For COMPANY/ORGANIZATION information:**
- Company name and industry
- Mission, vision, and description
- Products or services offered
- Leadership team and key personnel
- Company size and locations
- Contact information and headquarters
- Recent news, funding, or updates
- Key statistics or metrics

**For PRODUCT/SERVICE information:**
- Product/service name and category
- Key features and specifications
- Pricing information
- User reviews and ratings
- Availability and purchasing options
- Technical requirements
- Comparison with alternatives

**For NEWS/CONTENT information:**
- Article headline and summary
- Publication date and source
- Key facts and main points
- Author information
- Related topics or tags
- Important quotes or statistics

**For DATA/RESEARCH information:**
- Main findings or conclusions
- Statistical data and metrics
- Methodology or sources
- Publication details
- Key insights and implications

**For GENERAL INFORMATION:**
- Extract the main facts relevant to the user's goal
- Include supporting details and context
- Provide sources and references when available
- Focus on actionable or useful information

IMPORTANT:
- Only extract information that is VISIBLE and RELEVANT to the user's goal
- Organize information in a clear, structured format
- Include metadata about the source and extraction context
- Be comprehensive but avoid irrelevant details
- If the page doesn't contain the requested information, clearly state what was found instead

WEBPAGE CONTENT:
{content}

Return a well-structured JSON object with the extracted information:
"""

class UniversalExtractor:
    def __init__(self):
        self.extraction_cache = {}
    
    async def extract_intelligent_content(self, browser: BrowserController, goal: str, fmt: str = "json") -> str:
        """Extract content intelligently from any website based on user's goal"""
        try:
            # Get comprehensive page information
            url = browser.page.url
            title = await browser.page.title()
            
            # Detect website type
            website_type = self._detect_website_type(url, title)
            
            # Get clean, structured content
            content = await self._get_structured_content(browser)
            
            # Use AI to extract relevant information
            extracted_data = await self._ai_extract(goal, url, title, website_type, content)
            
            # Format the output based on requested format
            return await self._format_output(extracted_data, fmt, goal)
                
        except Exception as e:
            print(f"❌ Universal extraction failed: {e}")
            return await self._fallback_extraction(browser, fmt, goal)
    
    def _detect_website_type(self, url: str, title: str) -> str:
        """Detect website type for better extraction strategy"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Professional networks
        if "linkedin.com" in url_lower:
            return "linkedin_profile"
        if "github.com" in url_lower:
            return "github_profile"
        
        # Social media
        if any(domain in url_lower for domain in ["twitter.com", "facebook.com", "instagram.com"]):
            return "social_media"
        
        # E-commerce
        if any(domain in url_lower for domain in ["amazon", "ebay", "shopify", "etsy"]):
            return "ecommerce"
        
        # News and content
        if any(word in title_lower for word in ["news", "article", "blog", "post"]):
            return "news_content"
        
        # Company websites
        if any(word in title_lower for word in ["company", "corp", "about", "careers"]):
            return "company_website"
        
        # Search results
        if "/search" in url_lower or "google.com" in url_lower:
            return "search_results"
        
        return "general_website"
    
    async def _get_structured_content(self, browser: BrowserController) -> str:
        """Get clean, structured content from the page"""
        try:
            # Get HTML content
            html = await browser.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script, style, and other non-content elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'advertisement']):
                tag.decompose()
            
            # Extract main content areas
            main_content = []
            
            # Look for main content containers
            main_containers = soup.find_all(['main', 'article', 'section']) or [soup.find('body')]
            
            for container in main_containers[:3]:  # Limit to avoid too much content
                if container:
                    # Extract headings
                    headings = container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    for heading in headings:
                        if heading.get_text(strip=True):
                            main_content.append(f"HEADING: {heading.get_text(strip=True)}")
                    
                    # Extract paragraphs
                    paragraphs = container.find_all('p')
                    for p in paragraphs[:20]:  # Limit paragraphs
                        text = p.get_text(strip=True)
                        if len(text) > 20:  # Only meaningful paragraphs
                            main_content.append(f"TEXT: {text}")
                    
                    # Extract lists
                    lists = container.find_all(['ul', 'ol'])
                    for list_elem in lists[:5]:  # Limit lists
                        items = list_elem.find_all('li')
                        if items:
                            main_content.append("LIST:")
                            for item in items[:10]:  # Limit list items
                                text = item.get_text(strip=True)
                                if text:
                                    main_content.append(f"  - {text}")
                    
                    # Extract table data
                    tables = container.find_all('table')
                    for table in tables[:3]:  # Limit tables
                        rows = table.find_all('tr')
                        if rows:
                            main_content.append("TABLE:")
                            for row in rows[:10]:  # Limit rows
                                cells = row.find_all(['td', 'th'])
                                if cells:
                                    row_text = " | ".join([cell.get_text(strip=True) for cell in cells])
                                    if row_text.strip():
                                        main_content.append(f"  {row_text}")
            
            # Join and limit content
            content = "\n".join(main_content)
            return content[:12000]  # Limit total content to avoid token limits
            
        except Exception as e:
            print(f"❌ Error getting structured content: {e}")
            # Fallback to simple text extraction
            try:
                return await browser.page.inner_text("body")[:8000]
            except:
                return "Content extraction failed"
    
    async def _ai_extract(self, goal: str, url: str, title: str, website_type: str, content: str) -> Dict[str, Any]:
        """Use AI to extract relevant information based on context"""
        try:
            prompt = UNIVERSAL_EXTRACTION_PROMPT.format(
                goal=goal,
                url=url,
                title=title,
                website_type=website_type,
                content=content
            )
            
            response = await asyncio.to_thread(
                functools.partial(MODEL.generate_content, prompt)
            )
            
            # Parse AI response
            raw_text = response.text
            
            # Extract JSON from response
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = raw_text[start:end]
                extracted_data = json.loads(json_str)
                
                # Add metadata
                extracted_data["_metadata"] = {
                    "source_url": url,
                    "page_title": title,
                    "website_type": website_type,
                    "extraction_goal": goal,
                    "extraction_timestamp": asyncio.get_event_loop().time(),
                    "extraction_method": "ai_powered"
                }
                
                return extracted_data
            else:
                # Fallback: structure the raw text
                return {
                    "extracted_content": raw_text,
                    "content_type": "unstructured_text",
                    "_metadata": {
                        "source_url": url,
                        "page_title": title,
                        "website_type": website_type,
                        "extraction_goal": goal,
                        "extraction_timestamp": asyncio.get_event_loop().time(),
                        "extraction_method": "text_fallback"
                    }
                }
                
        except Exception as e:
            print(f"❌ AI extraction failed: {e}")
            return self._create_fallback_structure(content, url, title, website_type, goal)
    
    def _create_fallback_structure(self, content: str, url: str, title: str, website_type: str, goal: str) -> Dict[str, Any]:
        """Create structured fallback when AI extraction fails"""
        return {
            "extraction_status": "fallback_mode",
            "raw_content": content[:2000],  # Truncated content
            "content_summary": self._create_simple_summary(content),
            "_metadata": {
                "source_url": url,
                "page_title": title,
                "website_type": website_type,
                "extraction_goal": goal,
                "extraction_method": "fallback_structure",
                "note": "AI extraction failed, using fallback method"
            }
        }
    
    def _create_simple_summary(self, content: str) -> Dict[str, Any]:
        """Create a simple summary of content without AI"""
        lines = content.split('\n')
        
        summary = {
            "headings": [],
            "key_text": [],
            "lists": [],
            "total_lines": len(lines)
        }
        
        current_list = []
        
        for line in lines[:50]:  # Limit processing
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("HEADING:"):
                summary["headings"].append(line[8:].strip())
            elif line.startswith("TEXT:"):
                text = line[5:].strip()
                if len(text) > 30:  # Only substantial text
                    summary["key_text"].append(text[:200])
            elif line.startswith("LIST:"):
                if current_list:
                    summary["lists"].append(current_list)
                current_list = []
            elif line.startswith("  -"):
                current_list.append(line[4:].strip())
        
        if current_list:
            summary["lists"].append(current_list)
        
        return summary
    
    async def _format_output(self, data: Dict[str, Any], fmt: str, goal: str) -> str:
        """Format extracted data in the requested format"""
        if fmt == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif fmt == "txt":
            return self._format_as_text(data)
        elif fmt == "md":
            return self._format_as_markdown(data)
        elif fmt == "html":
            return self._format_as_html(data)
        elif fmt == "csv":
            return self._format_as_csv(data)
        elif fmt == "pdf":
            return await self._format_as_pdf(data, goal)
        else:
            return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _format_as_text(self, data: Dict[str, Any]) -> str:
        """Format as clean text"""
        lines = []
        metadata = data.get("_metadata", {})
        
        if metadata:
            lines.append(f"EXTRACTED INFORMATION")
            lines.append(f"Source: {metadata.get('source_url', 'Unknown')}")
            lines.append(f"Goal: {metadata.get('extraction_goal', 'Unknown')}")
            lines.append(f"Website Type: {metadata.get('website_type', 'Unknown')}")
            lines.append("-" * 60)
            lines.append("")
        
        def format_item(key: str, value, indent: int = 0):
            spaces = "  " * indent
            if isinstance(value, dict):
                if key != "_metadata":
                    lines.append(f"{spaces}{key.replace('_', ' ').title()}:")
                    for k, v in value.items():
                        format_item(k, v, indent + 1)
            elif isinstance(value, list):
                lines.append(f"{spaces}{key.replace('_', ' ').title()}:")
                for item in value:
                    if isinstance(item, str):
                        lines.append(f"{spaces}  • {item}")
                    else:
                        lines.append(f"{spaces}  • {str(item)}")
            else:
                lines.append(f"{spaces}{key.replace('_', ' ').title()}: {value}")
        
        for key, value in data.items():
            format_item(key, value)
        
        return "\n".join(lines)
    
    def _format_as_markdown(self, data: Dict[str, Any]) -> str:
        """Format as Markdown"""
        lines = []
        metadata = data.get("_metadata", {})
        
        if metadata:
            lines.append("# Extracted Information")
            lines.append("")
            lines.append(f"**Source:** {metadata.get('source_url', 'Unknown')}")
            lines.append(f"**Goal:** {metadata.get('extraction_goal', 'Unknown')}")
            lines.append(f"**Website Type:** {metadata.get('website_type', 'Unknown')}")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        def format_item(key: str, value, level: int = 2):
            if isinstance(value, dict):
                if key != "_metadata":
                    lines.append(f"{'#' * level} {key.replace('_', ' ').title()}")
                    lines.append("")
                    for k, v in value.items():
                        format_item(k, v, level + 1)
            elif isinstance(value, list):
                lines.append(f"{'#' * level} {key.replace('_', ' ').title()}")
                lines.append("")
                for item in value:
                    lines.append(f"- {item}")
                lines.append("")
            else:
                lines.append(f"**{key.replace('_', ' ').title()}:** {value}")
                lines.append("")
        
        for key, value in data.items():
            format_item(key, value)
        
        return "\n".join(lines)
    
    def _format_as_html(self, data: Dict[str, Any]) -> str:
        """Format as HTML"""
        html_parts = ["<!DOCTYPE html><html><head><title>Extracted Information</title>"]
        html_parts.append("<style>body{font-family:Arial,sans-serif;margin:40px;} h1,h2,h3{color:#333;} .metadata{background:#f5f5f5;padding:15px;border-radius:5px;margin-bottom:20px;}</style>")
        html_parts.append("</head><body>")
        
        metadata = data.get("_metadata", {})
        if metadata:
            html_parts.append("<h1>Extracted Information</h1>")
            html_parts.append("<div class='metadata'>")
            html_parts.append(f"<p><strong>Source:</strong> <a href='{metadata.get('source_url', '#')}'>{metadata.get('source_url', 'Unknown')}</a></p>")
            html_parts.append(f"<p><strong>Goal:</strong> {metadata.get('extraction_goal', 'Unknown')}</p>")
            html_parts.append(f"<p><strong>Website Type:</strong> {metadata.get('website_type', 'Unknown')}</p>")
            html_parts.append("</div>")
        
        def format_item(key: str, value, level: int = 2):
            if isinstance(value, dict):
                if key != "_metadata":
                    html_parts.append(f"<h{level}>{key.replace('_', ' ').title()}</h{level}>")
                    for k, v in value.items():
                        format_item(k, v, min(level + 1, 6))
            elif isinstance(value, list):
                html_parts.append(f"<h{level}>{key.replace('_', ' ').title()}</h{level}>")
                html_parts.append("<ul>")
                for item in value:
                    html_parts.append(f"<li>{item}</li>")
                html_parts.append("</ul>")
            else:
                html_parts.append(f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>")
        
        for key, value in data.items():
            format_item(key, value)
        
        html_parts.append("</body></html>")
        return "\n".join(html_parts)
    
    def _format_as_csv(self, data: Dict[str, Any]) -> str:
        """Format as CSV"""
        try:
            # Flatten the nested structure
            flattened = self._flatten_dict(data)
            
            # Create DataFrame
            df = pd.DataFrame([flattened])
            
            return df.to_csv(index=False)
            
        except Exception as e:
            print(f"❌ CSV formatting failed: {e}")
            # Simple fallback
            csv_lines = ["Field,Value"]
            for key, value in data.items():
                if key != "_metadata":
                    clean_value = str(value).replace('"', '""').replace('\n', ' ')
                    csv_lines.append(f'"{key}","{clean_value}"')
            return "\n".join(csv_lines)
    
    async def _format_as_pdf(self, data: Dict[str, Any], goal: str) -> str:
        """Format as PDF and return file path"""
        try:
            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)
            
            filename = f"extracted_data_{int(asyncio.get_event_loop().time())}.pdf"
            filepath = output_dir / filename
            
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            story.append(Paragraph("Extracted Information", styles['Title']))
            story.append(Spacer(1, 12))
            
            # Metadata
            metadata = data.get("_metadata", {})
            if metadata:
                story.append(Paragraph(f"<b>Source:</b> {metadata.get('source_url', 'Unknown')}", styles['Normal']))
                story.append(Paragraph(f"<b>Goal:</b> {metadata.get('extraction_goal', 'Unknown')}", styles['Normal']))
                story.append(Paragraph(f"<b>Website Type:</b> {metadata.get('website_type', 'Unknown')}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Content
            def add_content(key: str, value, level: int = 0):
                if isinstance(value, dict):
                    if key != "_metadata":
                        style = styles['Heading1'] if level == 0 else styles['Heading2']
                        story.append(Paragraph(key.replace('_', ' ').title(), style))
                        story.append(Spacer(1, 6))
                        for k, v in value.items():
                            add_content(k, v, level + 1)
                elif isinstance(value, list):
                    story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b>", styles['Normal']))
                    for item in value:
                        story.append(Paragraph(f"• {item}", styles['Normal']))
                    story.append(Spacer(1, 6))
                else:
                    story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", styles['Normal']))
                    story.append(Spacer(1, 6))
            
            for key, value in data.items():
                add_content(key, value)
            
            doc.build(story)
            return f"PDF saved to: {filepath}"
            
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            return f"PDF generation failed: {str(e)}"
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, '; '.join(map(str, v))))
            else:
                items.append((new_key, v))
        return dict(items)
    
    async def _fallback_extraction(self, browser: BrowserController, fmt: str, goal: str) -> str:
        """Fallback extraction when AI fails"""
        try:
            content = await browser.page.inner_text("body")
            url = browser.page.url
            title = await browser.page.title()
            
            fallback_data = {
                "content": content[:3000],  # Truncated
                "source": url,
                "title": title,
                "extraction_method": "fallback",
                "note": "AI extraction failed, using basic text extraction"
            }
            
            if fmt == "json":
                return json.dumps(fallback_data, indent=2)
            elif fmt == "txt":
                return f"Title: {title}\nSource: {url}\n\nContent:\n{content}"
            else:
                return content
                
        except Exception as e:
            return f"Extraction completely failed: {str(e)}"
