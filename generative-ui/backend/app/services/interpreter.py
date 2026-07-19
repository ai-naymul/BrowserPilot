"""
Content interpreter service for the Generative UI Browser.

This module provides LLM-powered content interpretation that extracts
structured information from scraped web content and converts it into
TaskDrivenDataModel format for UI generation.

Features:
- Multi-LLM support (Anthropic Claude, OpenAI GPT)
- Structured content extraction
- Entity and relationship identification
- Robust error handling and retry logic
- Content validation and cleaning
"""

import asyncio
import json
import logging
import os
import re
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

import anthropic
from openai import AsyncOpenAI
from pydantic import ValidationError

from app.models.data_model import TaskDrivenDataModel, Entity, Dependency, Attribute

# Configure logging
logger = logging.getLogger(__name__)


class ContentInterpreter:
    """
    LLM-powered content interpreter that extracts structured information
    from scraped web content and converts it to TaskDrivenDataModel format.
    """
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        Initialize the content interpreter.
        
        Args:
            anthropic_api_key: OpenRouter API key for Claude (from env if None)
            openai_api_key: OpenAI API key (from env if None)
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize Anthropic client via OpenRouter
        self.anthropic_client = None
        if anthropic_api_key or os.getenv("OPENROUTER_API_KEY"):
            self.anthropic_client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=anthropic_api_key or os.getenv("OPENROUTER_API_KEY"),
                default_headers={
                    "HTTP-Referer": "https://generative-ui-browser.local",
                    "X-Title": "Generative UI Browser"
                }
            )
            logger.info("Anthropic client initialized via OpenRouter")
        
        # Initialize OpenAI client (fallback)
        self.openai_client = None
        if openai_api_key or os.getenv("OPENAI_API_KEY"):
            self.openai_client = AsyncOpenAI(
                api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
            )
            logger.info("OpenAI client initialized")
        
        if not self.anthropic_client and not self.openai_client:
            logger.warning("No LLM clients initialized - check API keys")
    
    async def interpret_content(self, scraped_data: Dict[str, Any]) -> TaskDrivenDataModel:
        """
        Interpret scraped content and extract structured information.
        
        Args:
            scraped_data: Scraped content from ContentScraper
            
        Returns:
            TaskDrivenDataModel: Structured data model
            
        Raises:
            ValueError: If content cannot be interpreted
            Exception: If all LLM calls fail
        """
        logger.info("Starting content interpretation")
        
        # Extract content and metadata
        content = scraped_data.get('content', '')
        title = scraped_data.get('title', '')
        url = scraped_data.get('url', '')
        
        if not content.strip():
            raise ValueError("No content to interpret")
        
        # Build the interpretation prompt
        prompt = self._build_interpretation_prompt(content, title, url, scraped_data)
        
        # Try different LLM providers with retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Interpretation attempt {attempt + 1}/{self.max_retries}")
                
                # Try Anthropic first (preferred for structured output)
                if self.anthropic_client:
                    result = await self._interpret_with_anthropic(prompt)
                    if result:
                        return self._parse_and_validate_result(result, url)
                
                # Fallback to OpenAI
                if self.openai_client:
                    result = await self._interpret_with_openai(prompt)
                    if result:
                        return self._parse_and_validate_result(result, url)
                
                # If we get here, both failed
                raise Exception("All LLM providers failed")
                
            except Exception as e:
                logger.warning(f"Interpretation attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Content interpretation failed after {self.max_retries} attempts: {str(e)}")
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _build_interpretation_prompt(
        self, 
        content: str, 
        title: str, 
        url: str, 
        scraped_data: Dict[str, Any]
    ) -> str:
        """
        Build a comprehensive prompt for LLM content interpretation.
        
        Args:
            content: Main content text
            title: Page title
            url: Source URL
            scraped_data: Full scraped data
            
        Returns:
            str: Formatted prompt for LLM
        """
        # Extract additional context
        metadata = scraped_data.get('metadata', {})
        structured_data = scraped_data.get('structured_data', {})
        
        # Build context information
        context_info = []
        if title:
            context_info.append(f"Title: {title}")
        if url:
            context_info.append(f"URL: {url}")
        if metadata.get('author'):
            context_info.append(f"Author: {metadata['author']}")
        if metadata.get('date'):
            context_info.append(f"Date: {metadata['date']}")
        if metadata.get('description'):
            context_info.append(f"Description: {metadata['description']}")
        
        # Extract headings for structure
        headings = structured_data.get('headings', [])
        if headings:
            context_info.append(f"Document Structure: {len(headings)} headings")
        
        # Extract links for context
        links = structured_data.get('links', [])
        if links:
            context_info.append(f"External Links: {len(links)} found")
        
        context_str = "\n".join(context_info) if context_info else "No additional context"
        
        prompt = f"""
You are an expert content analyst specializing in extracting structured information from web content. Your task is to analyze the provided content and extract entities, relationships, and key information in a structured format.

CONTENT TO ANALYZE:
{content[:4000]}  # Limit content length for token efficiency

ADDITIONAL CONTEXT:
{context_str}

ANALYSIS REQUIREMENTS:
1. Identify main entities (people, organizations, concepts, products, locations, etc.)
2. Extract relationships between entities
3. Determine key attributes for each entity
4. Identify the primary purpose/task of the content
5. Extract any structured data (lists, tables, categories)

OUTPUT FORMAT:
Return a JSON object matching this exact schema:
{{
  "task_description": "Brief description of what this content is about and its primary purpose",
  "entities": [
    {{
      "id": "unique_entity_id",
      "type": "entity_type (e.g., Person, Organization, Concept, Product, Location)",
      "attributes": [
        {{
          "name": "attribute_name",
          "data_type": "primitive|reference|array|dict",
          "value": "attribute_value",
          "metadata": {{"render_as": "suggested_ui_component"}}
        }}
      ]
    }}
  ],
  "dependencies": [
    {{
      "source_entity_id": "entity_id",
      "target_entity_id": "entity_id", 
      "relationship": "relationship_type (e.g., authored_by, located_in, related_to, part_of)",
      "metadata": {{"strength": 0.8, "type": "relationship_category"}}
    }}
  ]
}}

ENTITY TYPES TO CONSIDER:
- Person: Individuals mentioned
- Organization: Companies, institutions, groups
- Concept: Ideas, topics, themes
- Product: Goods, services, software
- Location: Places, addresses, regions
- Event: Meetings, conferences, dates
- Document: Papers, articles, reports
- Technology: Tools, platforms, systems

RELATIONSHIP TYPES:
- authored_by: Person authored document
- works_for: Person works for organization
- located_in: Entity located in place
- related_to: General association
- part_of: Hierarchical relationship
- mentions: Entity mentioned in content
- collaborates_with: Working relationship

ATTRIBUTE SUGGESTIONS:
- For Person: name, title, affiliation, email, expertise
- For Organization: name, type, industry, size, location
- For Concept: name, description, category, importance
- For Product: name, type, features, price, availability
- For Location: name, type, address, coordinates
- For Event: name, date, location, attendees, purpose

IMPORTANT GUIDELINES:
1. Be thorough but concise - extract the most important information
2. Use clear, descriptive entity types and relationship names
3. Include relevant metadata for UI rendering hints
4. Ensure all entity IDs are unique
5. Focus on information that would be useful for generating a user interface
6. If content is unclear or insufficient, still provide a basic structure
7. For technical content, prioritize key concepts and relationships
8. For news/articles, focus on people, organizations, and main topics
9. For product pages, emphasize product details and features
10. For academic papers, highlight authors, concepts, and citations

Return only the JSON object, no additional text or formatting.
"""
        
        return prompt.strip()
    
    async def _interpret_with_anthropic(self, prompt: str) -> Optional[str]:
        """
        Interpret content using Anthropic Claude via OpenRouter.
        
        Args:
            prompt: Formatted prompt for interpretation
            
        Returns:
            str: LLM response or None if failed
        """
        if not self.anthropic_client:
            return None
        
        try:
            logger.info("Using Anthropic Claude via OpenRouter for interpretation")
            
            response = await self.anthropic_client.chat.completions.create(
                model="anthropic/claude-sonnet-4.5",  # or "anthropic/claude-3.7-sonnet"
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                logger.warning("Empty response from Anthropic")
                return None
                
        except Exception as e:
            logger.error(f"Anthropic interpretation failed: {str(e)}")
            return None
    
    async def _interpret_with_openai(self, prompt: str) -> Optional[str]:
        """
        Interpret content using OpenAI GPT.
        
        Args:
            prompt: Formatted prompt for interpretation
            
        Returns:
            str: LLM response or None if failed
        """
        if not self.openai_client:
            return None
        
        try:
            logger.info("Using OpenAI GPT for interpretation")
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content analyst. Return only valid JSON matching the specified schema."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                logger.warning("Empty response from OpenAI")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI interpretation failed: {str(e)}")
            return None
    
    def _parse_and_validate_result(self, llm_response: str, source_url: str) -> TaskDrivenDataModel:
        """
        Parse LLM response and validate against TaskDrivenDataModel schema.
        
        Args:
            llm_response: Raw response from LLM
            source_url: Source URL for context
            
        Returns:
            TaskDrivenDataModel: Validated data model
            
        Raises:
            ValueError: If response cannot be parsed or validated
        """
        try:
            # Clean the response (remove markdown formatting if present)
            cleaned_response = self._clean_llm_response(llm_response)
            
            # Parse JSON
            data = json.loads(cleaned_response)
            
            # Validate required fields
            if not isinstance(data, dict):
                raise ValueError("Response is not a valid JSON object")
            
            if 'task_description' not in data:
                raise ValueError("Missing required field: task_description")
            
            if 'entities' not in data:
                raise ValueError("Missing required field: entities")
            
            if 'dependencies' not in data:
                raise ValueError("Missing required field: dependencies")
            
            # Convert to TaskDrivenDataModel
            entities = []
            for entity_data in data.get('entities', []):
                entity = self._create_entity_from_data(entity_data)
                entities.append(entity)
            
            dependencies = []
            for dep_data in data.get('dependencies', []):
                dependency = self._create_dependency_from_data(dep_data)
                dependencies.append(dependency)
            
            # Create the data model
            data_model = TaskDrivenDataModel(
                task_description=data.get('task_description', 'Content analysis'),
                entities=entities,
                dependencies=dependencies,
                created_at=datetime.utcnow(),
                metadata={
                    'source_url': source_url,
                    'interpretation_method': 'llm_analysis',
                    'entity_count': len(entities),
                    'dependency_count': len(dependencies)
                }
            )
            
            logger.info(f"Successfully created data model with {len(entities)} entities and {len(dependencies)} dependencies")
            return data_model
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
        except ValidationError as e:
            raise ValueError(f"Data model validation failed: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")
    
    def _clean_llm_response(self, response: str) -> str:
        """
        Clean LLM response to extract valid JSON.
        
        Args:
            response: Raw LLM response
            
        Returns:
            str: Cleaned JSON string
        """
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*$', '', response)
        
        # Remove any leading/trailing whitespace
        response = response.strip()
        
        # Try to find JSON object boundaries
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            response = response[start_idx:end_idx + 1]
        
        return response
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> Entity:
        """
        Create Entity object from parsed data.
        
        Args:
            entity_data: Entity data from LLM response
            
        Returns:
            Entity: Validated entity object
        """
        # Extract attributes
        attributes = []
        for attr_data in entity_data.get('attributes', []):
            attribute = Attribute(
                name=attr_data.get('name', ''),
                data_type=attr_data.get('data_type', 'primitive'),
                value=attr_data.get('value', ''),
                metadata=attr_data.get('metadata', {})
            )
            attributes.append(attribute)
        
        # Create entity
        entity = Entity(
            id=entity_data.get('id', f"entity_{len(attributes)}"),
            type=entity_data.get('type', 'Unknown'),
            attributes=attributes
        )
        
        return entity
    
    def _create_dependency_from_data(self, dep_data: Dict[str, Any]) -> Dependency:
        """
        Create Dependency object from parsed data.
        
        Args:
            dep_data: Dependency data from LLM response
            
        Returns:
            Dependency: Validated dependency object
        """
        dependency = Dependency(
            source_entity_id=dep_data.get('source_entity_id', ''),
            target_entity_id=dep_data.get('target_entity_id', ''),
            relationship=dep_data.get('relationship', 'related_to'),
            metadata=dep_data.get('metadata', {})
        )
        
        return dependency


# Utility functions for external use
async def interpret_content(
    scraped_data: Dict[str, Any],
    anthropic_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None
) -> TaskDrivenDataModel:
    """
    Convenience function to interpret scraped content.
    
    Args:
        scraped_data: Scraped content from ContentScraper
        anthropic_api_key: Anthropic API key (optional)
        openai_api_key: OpenAI API key (optional)
        
    Returns:
        TaskDrivenDataModel: Structured data model
    """
    interpreter = ContentInterpreter(
        anthropic_api_key=anthropic_api_key,
        openai_api_key=openai_api_key
    )
    
    return await interpreter.interpret_content(scraped_data)