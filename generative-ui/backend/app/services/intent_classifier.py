"""
Intent Classification Service for Jelly-inspired UI Browser.

Determines what type of user request this is:
- NEW_TASK: Create a fresh data model from scratch
- ADD_INFORMATION: Extend existing model with new entities
- MODIFY_DATA: Update or delete existing entities
- CHANGE_VIEW: Transform visualization without changing data
- REFINE_ANALYSIS: Re-prioritize or re-analyze existing data
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

from openai import AsyncOpenAI
import os

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Types of user intents"""
    NEW_TASK = "new_task"              # "I'm moving to SF" - create new task
    ADD_INFORMATION = "add_information"  # "tell me about areas" - add entities
    MODIFY_DATA = "modify_data"        # "remove Pacific Heights" - edit/delete
    CHANGE_VIEW = "change_view"        # "switch to table view" - change visualization
    REFINE_ANALYSIS = "refine_analysis"  # "focus on safety" - re-analyze
    URL_ANALYSIS = "url_analysis"      # "analyze https://..." - scrape URL


class IntentClassifier:
    """
    Classifies user intents to determine processing pipeline.
    """
    
    def __init__(self):
        """Initialize the intent classifier with LLM client."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://generative-ui-browser.local",
                "X-Title": "Generative UI Browser - Intent Classifier"
            }
        )
        
        logger.info("Intent classifier initialized")
    
    async def classify_intent(
        self, 
        user_input: str,
        has_existing_model: bool = False,
        existing_task: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[IntentType, Dict[str, any]]:
        """
        Classify user intent and extract relevant parameters.
        
        Args:
            user_input: The user's input text
            has_existing_model: Whether there's an existing data model in context
            existing_task: Description of existing task if any
            conversation_history: Previous conversation turns
            
        Returns:
            Tuple of (IntentType, parameters dict)
        """
        
        # Quick pattern matching for obvious cases
        input_lower = user_input.lower().strip()
        
        # Check for URL
        if input_lower.startswith(('http://', 'https://', 'www.')):
            return IntentType.URL_ANALYSIS, {"url": user_input.strip()}
        
        # If no existing model, likely NEW_TASK
        if not has_existing_model:
            # Check if it's a task-oriented statement
            task_keywords = ['i\'m', 'i am', 'i need to', 'i want to', 'help me', 
                           'planning', 'organizing', 'moving', 'creating']
            
            if any(keyword in input_lower for keyword in task_keywords):
                return IntentType.NEW_TASK, {"task_description": user_input}
            else:
                # Might be asking for URL analysis without providing URL
                return IntentType.NEW_TASK, {"task_description": user_input}
        
        # Has existing model - check for common patterns first
        if has_existing_model:
            # Generic expansion requests should be ADD_INFORMATION
            expansion_keywords = ['tell me more', 'show more', 'additional details',
                                'what else', 'more information', 'show additional',
                                'tell me about', 'what about', 'add', 'include',
                                'show me', 'create', 'make', 'timeline', 'breakdown',
                                'break down', 'details about', 'information on']

            if any(keyword in input_lower for keyword in expansion_keywords):
                return IntentType.ADD_INFORMATION, {"expansion_request": user_input}
            
            # View change requests
            view_keywords = ['show as', 'view as', 'display as', 'switch to', 'change view']
            if any(keyword in input_lower for keyword in view_keywords):
                view_type = self.extract_view_type(user_input)
                if view_type:
                    return IntentType.CHANGE_VIEW, {"view_type": view_type}
            
            # Deletion/removal requests
            delete_keywords = ['remove', 'delete', 'get rid of', 'take out']
            if any(keyword in input_lower for keyword in delete_keywords):
                return IntentType.MODIFY_DATA, {"action": "delete", "target": user_input}
        
        # Use LLM to classify
        return await self._llm_classify(
            user_input, 
            has_existing_model, 
            existing_task,
            conversation_history
        )
    
    async def _llm_classify(
        self,
        user_input: str,
        has_existing_model: bool,
        existing_task: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> Tuple[IntentType, Dict[str, any]]:
        """Use LLM to classify intent with context."""
        
        # Build context
        context_parts = []
        
        if existing_task:
            context_parts.append(f"CURRENT TASK: {existing_task}")
        
        if conversation_history and len(conversation_history) > 0:
            recent_history = conversation_history[-4:]  # Last 2 turns
            history_text = "\n".join([
                f"{turn['role'].upper()}: {turn['content']}" 
                for turn in recent_history
            ])
            context_parts.append(f"CONVERSATION HISTORY:\n{history_text}")
        
        context = "\n\n".join(context_parts) if context_parts else "No prior context."
        
        # Build classification prompt
        prompt = f"""You are an intent classifier for a dynamic UI generation system.

CONTEXT:
{context}

USER INPUT: "{user_input}"

Classify the user's intent into ONE of these categories:

1. ADD_INFORMATION - User wants to add new entities, breakdowns, or detailed data to existing model
   Examples: "tell me about different neighborhoods", "show me nearby restaurants", "add budget tracking"
   IMPORTANT: Queries asking for "breakdown", "break down", "detailed costs", "daily expenses" are ADD_INFORMATION

2. MODIFY_DATA - User wants to edit or delete existing entities
   Examples: "remove Pacific Heights", "change the budget to $5000", "delete that item"

3. CHANGE_VIEW - User wants to change how EXISTING data is visualized (same data, different layout/chart type)
   Examples: "switch to table view", "show as a map", "change to list layout", "display as bar chart"
   NOTE: If user is asking for NEW data or breakdowns, it's ADD_INFORMATION, NOT CHANGE_VIEW

4. REFINE_ANALYSIS - User wants to re-analyze or re-prioritize existing data WITHOUT adding new data
   Examples: "focus on safety", "prioritize cost", "emphasize walkability", "compare these metrics"

5. NEW_TASK - User wants to start a completely new task (rare when context exists)
   Examples: "actually, let's plan a party instead", "new task: job search"

Respond with ONLY a JSON object:
{{
    "intent": "ADD_INFORMATION" | "MODIFY_DATA" | "CHANGE_VIEW" | "REFINE_ANALYSIS" | "NEW_TASK",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "extracted_params": {{
        // Relevant parameters based on intent
        // For ADD_INFORMATION: {{"entities_to_add": ["neighborhood", "restaurant"]}}
        // For MODIFY_DATA: {{"action": "delete", "target": "Pacific Heights"}}
        // For CHANGE_VIEW: {{"view_type": "table", "entity_type": "neighborhoods"}}
        // For REFINE_ANALYSIS: {{"focus_attribute": "safety", "priority": "high"}}
    }}
}}"""
        
        try:
            response = await self.client.chat.completions.create(
                model="anthropic/claude-sonnet-4.5",
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            import json
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            result = json.loads(response_text.strip())
            
            intent_str = result.get("intent", "ADD_INFORMATION")
            intent = IntentType(intent_str.lower())
            params = result.get("extracted_params", {})
            
            logger.info(f"Classified intent: {intent.value} (confidence: {result.get('confidence', 0)})")
            logger.debug(f"Reasoning: {result.get('reasoning', 'N/A')}")
            
            return intent, params
            
        except Exception as e:
            logger.error(f"Intent classification failed: {str(e)}")
            # Fallback to ADD_INFORMATION as safest default
            return IntentType.ADD_INFORMATION, {}
    
    def extract_target_entity(self, user_input: str, entity_types: List[str]) -> Optional[str]:
        """
        Extract which entity the user is referring to.
        
        Args:
            user_input: User's input
            entity_types: Available entity types
            
        Returns:
            Entity type name or None
        """
        input_lower = user_input.lower()
        
        for entity_type in entity_types:
            if entity_type.lower() in input_lower:
                return entity_type
        
        return None
    
    def extract_view_type(self, user_input: str) -> Optional[str]:
        """
        Extract desired view type from user input.
        
        Args:
            user_input: User's input
            
        Returns:
            View type name (table, map, list, cards) or None
        """
        input_lower = user_input.lower()
        
        view_mappings = {
            'table': ['table', 'spreadsheet', 'grid'],
            'map': ['map', 'geographic', 'location'],
            'list': ['list', 'vertical'],
            'cards': ['cards', 'card grid', 'tiles'],
            'graph': ['graph', 'network', 'relationships'],
            'chart': ['chart', 'visualization', 'graph']
        }
        
        for view_type, keywords in view_mappings.items():
            if any(keyword in input_lower for keyword in keywords):
                return view_type
        
        return None
