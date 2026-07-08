"""
Refine API endpoint for iterative UI generation.

Handles:
- Follow-up questions
- Adding new entities
- Modifying existing data
- Changing views
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.models.data_model import (
    TaskDrivenDataModel, 
    Entity, 
    Dependency,
    ComponentSpec,
    LayoutSpec,
    UIResponse
)
from app.services.intent_classifier import IntentClassifier, IntentType
from app.services.firecrawl_service import get_firecrawl_service
from app.services.storage import storage
from app.services.prompts import (
    get_task_creation_prompt,
    get_information_addition_prompt,
    get_refinement_prompt
)
from app.services.schema_merger import SchemaMerger
from app.services.geocoding import geocoding_service
from openai import AsyncOpenAI
import os

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI router
router = APIRouter(prefix="/refine", tags=["refine"])

# Initialize services
intent_classifier = IntentClassifier()
firecrawl_service = get_firecrawl_service()
schema_merger = SchemaMerger()

# Initialize LLM client
llm_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://generative-ui-browser.local",
        "X-Title": "Generative UI Browser - Refine"
    }
)


class RefineRequest(BaseModel):
    """Request model for UI refinement."""
    user_input: str = Field(..., description="User's follow-up input")
    current_data_model: Dict[str, Any] = Field(..., description="Current data model state")
    current_ui_spec: Optional[Dict[str, Any]] = Field(None, description="Current UI specification")


class RefineResponse(BaseModel):
    """Response model for UI refinement."""
    success: bool = Field(..., description="Whether refinement was successful")
    intent: str = Field(..., description="Detected intent type")
    updated_data_model: Optional[Dict[str, Any]] = Field(None, description="Updated data model")
    incremental_entities: Optional[list] = Field(None, description="Only new/changed entities")
    incremental_ui_spec: Optional[Dict[str, Any]] = Field(None, description="Only new/changed panels")
    components: Optional[list[Dict[str, Any]]] = Field(None, description="Component specifications for dynamic UI")
    layout: Optional[Dict[str, Any]] = Field(None, description="Layout specification")
    suggested_questions: Optional[list[str]] = Field(None, description="Updated context-aware suggested questions")
    message: Optional[str] = Field(None, description="Human-readable message")
    error: Optional[str] = Field(None, description="Error message if failed")


class TaskCreateRequest(BaseModel):
    """Request model for creating a new task from natural language."""
    user_input: str = Field(..., description="User's task description")


class TaskCreateResponse(BaseModel):
    """Response model for task creation with component support."""
    success: bool = Field(..., description="Whether task creation was successful")
    data_model: Optional[Dict[str, Any]] = Field(None, description="Generated data model (entities/attributes)")
    ui_spec: Optional[Dict[str, Any]] = Field(None, description="Generated UI specification (panels)")
    components: Optional[list[Dict[str, Any]]] = Field(None, description="Component specifications for dynamic UI")
    layout: Optional[Dict[str, Any]] = Field(None, description="Layout specification")
    suggested_questions: Optional[list[str]] = Field(None, description="Context-aware suggested questions")
    error: Optional[str] = Field(None, description="Error message if failed")


class SuggestionRequest(BaseModel):
    """Request model for generating chat suggestions."""
    data_model: Optional[Dict[str, Any]] = Field(None, description="Current data model with entities")
    messages: Optional[list[Dict[str, str]]] = Field(None, description="Conversation history")
    current_query: Optional[str] = Field(None, description="Current/last user query")


async def generate_suggested_questions(
    task_description: str,
    entities: list[Entity],
    user_input: str
) -> list[str]:
    """
    Generate contextual follow-up questions based on current task and entities
    Uses LLM to create relevant, actionable suggestions
    """
    try:
        # Build entity summary - safely access attributes
        entity_summaries = []
        for e in entities[:5]:  # Top 5 entities
            identifier = getattr(e, 'public_identifier', None) or getattr(e, 'id', 'Entity')
            entity_type = getattr(e, 'type', 'Unknown')
            entity_summaries.append(f"- {entity_type}: {identifier}")
        
        entity_summary = "\n".join(entity_summaries)
        
        # Count key attribute types - safely access attributes
        has_costs = any(
            any(getattr(attr, 'widget', None) == 'currency' for attr in getattr(e, 'attributes', []))
            for e in entities
        )
        has_ratings = any(
            any(getattr(attr, 'widget', None) == 'rating' for attr in getattr(e, 'attributes', []))
            for e in entities
        )
        has_locations = any(
            any('location' in getattr(attr, 'name', '').lower() for attr in getattr(e, 'attributes', []))
            for e in entities
        )
        
        prompt = f"""Based on this user's task, generate 4 specific, relevant follow-up questions.

USER REQUEST: "{user_input}"

TASK DESCRIPTION: {task_description}

CURRENT ENTITIES:
{entity_summary}

CONTEXT:
- Has financial data: {has_costs}
- Has ratings/scores: {has_ratings}
- Has location data: {has_locations}

Generate 4 questions that would help the user:
1. Explore specific details (e.g., "Tell me more about [specific entity]")
2. Add missing information (e.g., "Can you add [relevant data]?")
3. Make comparisons (e.g., "How does [X] compare to [Y]?")
4. Take action (e.g., "Help me decide between..." or "Create a [plan/schedule]")

Make questions SPECIFIC to this task. Use actual entity names. Don't be generic.

Return ONLY a JSON array of 4 strings, nothing else:
["Question 1?", "Question 2?", "Question 3?", "Question 4?"]"""

        response = await llm_client.chat.completions.create(
            model="anthropic/claude-sonnet-4.5",
            temperature=0.7,
            # max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean JSON markers
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        questions = json.loads(response_text.strip())
        
        if isinstance(questions, list) and len(questions) > 0:
            logger.info(f"Generated {len(questions)} suggested questions")
            return questions[:4]  # Max 4
        else:
            logger.warning("No questions generated, using fallback")
            return []
            
    except Exception as e:
        logger.error(f"Failed to generate suggested questions: {e}", exc_info=True)
        return []  # Return empty on error, don't block main response


async def generate_components_from_entities(entities: list[Entity]) -> list[Dict[str, Any]]:
    """
    Generate component specifications from entities.
    Reuses the template system from task creation.
    """
    try:
        from app.services.component_templates import generate_components_from_list
        
        # For now, return empty and let frontend handle it
        # TODO: Implement backend component generation based on entity structure
        logger.info(f"[Components] Generating components for {len(entities)} entities")
        
        # Return empty - frontend's componentMapper will handle it
        return []
        
    except Exception as e:
        logger.error(f"[Components] Failed to generate components: {e}")
        return []


async def enrich_entities_with_geocoding(entities: list[Entity]) -> list[Entity]:
    """
    Enrich entities with coordinates using geocoding API
    Only geocodes if location exists but coordinates don't
    """
    logger.info(f"[Geocoding] Checking {len(entities)} entities for geocoding needs")
    
    for entity in entities:
        # Find location and coordinates attributes
        location_attr = None
        coordinates_attr = None
        
        for attr in entity.attributes:
            if attr.widget == 'location' or 'location' in attr.name.lower():
                location_attr = attr
            if attr.name == 'coordinates':
                coordinates_attr = attr
        
        # If has location but no coordinates, geocode it
        if location_attr and not coordinates_attr:
            location_str = str(location_attr.value)
            
            if location_str and location_str.strip():
                entity_name = getattr(entity, 'public_identifier', None) or getattr(entity, 'id', 'Unknown')
                logger.info(f"[Geocoding] Entity '{entity_name}' needs geocoding for: {location_str}")
                
                # Call geocoding service
                coords = await geocoding_service.geocode(location_str)
                
                if coords:
                    logger.info(f"[Geocoding] ✓ Added coordinates to '{entity_name}': ({coords['lat']}, {coords['lng']})")
                    
                    # Add coordinates attribute
                    from app.models.data_model import Attribute
                    entity.attributes.append(Attribute(
                        name="coordinates",
                        value={"lat": coords["lat"], "lng": coords["lng"]},
                        widget="object",
                        data_type="object",
                        editable=False,
                        function="display"
                    ))
                    
                    # Optionally update location with full display name
                    if coords.get("display_name"):
                        location_attr.value = coords["display_name"]
                else:
                    logger.warning(f"[Geocoding] ✗ Failed to geocode: {location_str}")
    
    return entities



@router.get("/sessions")
async def list_sessions():
    """
    List all saved sessions.
    """
    try:
        sessions = storage.list_sessions()
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/load/{session_id}")
async def load_session(session_id: str):
    """
    Load a saved session by ID.
    """
    try:
        data_model = storage.load(session_id)
        
        if data_model:
            logger.info(f"✓ Loaded session: {session_id}")
            return {
                "success": True,
                "data_model": data_model,
                "session_id": session_id
            }
        else:
            return {
                "success": False,
                "error": f"Session not found: {session_id}"
            }
            
    except Exception as e:
        logger.error(f"Failed to load session: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/update")
async def update_data_model(request: dict):
    """
    Update data model without full refinement.
    Used for real-time syncing of user edits.
    Saves to JSON file for persistence.
    """
    try:
        data_model = request.get('data_model')
        if not data_model:
            return {"success": False, "error": "No data model provided"}
        
        # Generate or use existing session ID
        session_id = request.get('session_id', data_model.get('task_description', 'default').lower().replace(' ', '_')[:50])
        
        # Save to JSON storage
        success = storage.save(session_id, data_model)
        
        if success:
            logger.info(f"✓ Persisted {len(data_model.get('entities', []))} entities to {session_id}.json")
            return {
                "success": True,
                "message": "Data model saved",
                "session_id": session_id,
                "timestamp": data_model.get('updated_at'),
                "entities_count": len(data_model.get('entities', []))
            }
        else:
            return {
                "success": False,
                "error": "Failed to save data model"
            }
            
    except Exception as e:
        logger.error(f"Update failed: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/", response_model=RefineResponse)
async def refine_ui(request: RefineRequest):
    """
    Refine existing UI based on user follow-up.
    
    This endpoint handles:
    - Adding new information/entities
    - Modifying existing data
    - Changing views
    - Re-analyzing with different focus
    """
    try:
        logger.info(f"Refine request: {request.user_input}")
        
        # Parse current data model
        current_model = TaskDrivenDataModel(**request.current_data_model)
        
        # Classify intent
        intent, params = await intent_classifier.classify_intent(
            user_input=request.user_input,
            has_existing_model=True,
            existing_task=current_model.task_description,
            conversation_history=current_model.conversation_history
        )
        
        logger.info(f"Detected intent: {intent.value}")
        
        # Handle based on intent
        if intent == IntentType.ADD_INFORMATION:
            return await handle_add_information(request, current_model, params)
        
        elif intent == IntentType.MODIFY_DATA:
            return await handle_modify_data(request, current_model, params)
        
        elif intent == IntentType.CHANGE_VIEW:
            return await handle_change_view(request, current_model, params)
        
        elif intent == IntentType.REFINE_ANALYSIS:
            return await handle_refine_analysis(request, current_model, params)
        
        else:
            # Default to ADD_INFORMATION
            return await handle_add_information(request, current_model, params)
    
    except Exception as e:
        logger.error(f"Refine failed: {str(e)}")
        return RefineResponse(
            success=False,
            intent="unknown",
            error=str(e)
        )


async def handle_add_information(
    request: RefineRequest,
    current_model: TaskDrivenDataModel,
    params: Dict[str, Any]
) -> RefineResponse:
    """Handle adding new entities to the model."""
    
    logger.info("Handling ADD_INFORMATION intent")
    
    # Build prompt for LLM
    # CRITICAL: Use to_render_spec() not to_dict() to include full attribute structure
    prompt = get_information_addition_prompt(
        user_input=request.user_input,
        existing_model=current_model.to_render_spec(),  # ← FIXED: includes full attributes
        conversation_history=current_model.conversation_history
    )
    
    # Call LLM
    logger.info(f"Calling LLM with prompt length: {len(prompt)} chars")
    
    # Debug: Save prompt to file for inspection
    try:
        with open("/tmp/llm_prompt_debug.txt", "w") as f:
            f.write(prompt)
        logger.info("Prompt saved to /tmp/llm_prompt_debug.txt")
    except Exception as e:
        logger.warning(f"Could not save prompt to file: {e}")
    
    response = await llm_client.chat.completions.create(
        model="anthropic/claude-sonnet-4.5",
        temperature=0.75,
        max_tokens=60000,  # High limit for complex entities with many attributes
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = response.choices[0].message.content.strip()
    logger.info(f"LLM response length: {len(response_text)} chars")
    logger.debug(f"LLM response preview: {response_text[:500]}...")
    
    # Debug: Save response to file for inspection
    try:
        with open("/tmp/llm_response_debug.txt", "w") as f:
            f.write(response_text)
        logger.info("Response saved to /tmp/llm_response_debug.txt")
    except Exception as e:
        logger.warning(f"Could not save response to file: {e}")
    
    # Parse JSON response
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    try:
        result = json.loads(response_text.strip())
        logger.info(f"✓ Parsed JSON successfully")
        logger.info(f"  - new_entities count: {len(result.get('new_entities', []))}")
        logger.info(f"  - new_dependencies count: {len(result.get('new_dependencies', []))}")
    except json.JSONDecodeError as e:
        logger.error(f"✗ Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response text (first 1000 chars): {response_text[:1000]}")
        raise ValueError(f"LLM returned invalid JSON: {e}")
    
    # Log what we got from LLM
    logger.info("=" * 80)
    logger.info("LLM RESPONSE ANALYSIS:")
    for idx, entity_data in enumerate(result.get("new_entities", [])):
        entity_id = entity_data.get('id', 'unknown')
        entity_type = entity_data.get('type', 'unknown')
        attributes = entity_data.get("attributes", [])
        attr_count = len(attributes) if isinstance(attributes, list) else 0
        
        logger.info(f"  Entity #{idx + 1}:")
        logger.info(f"    - ID: {entity_id}")
        logger.info(f"    - Type: {entity_type}")
        logger.info(f"    - Icon: {entity_data.get('icon', 'N/A')}")
        logger.info(f"    - Color: {entity_data.get('color', 'N/A')}")
        logger.info(f"    - Attributes: {attr_count}")
        
        if attr_count == 0:
            logger.error(f"    ✗ PROBLEM: Entity {entity_id} has ZERO attributes!")
            logger.error(f"    ✗ Raw entity data keys: {list(entity_data.keys())}")
            logger.error(f"    ✗ Attributes field type: {type(attributes)}")
            logger.error(f"    ✗ Attributes field value: {attributes}")
        else:
            logger.info(f"    ✓ Entity has {attr_count} attributes - OK")
            # Log first 3 attribute names
            attr_names = [attr.get('name', '?') for attr in attributes[:3]]
            logger.info(f"    ✓ First 3 attributes: {', '.join(attr_names)}")
    logger.info("=" * 80)
    
    # Create new entities with validation
    new_entities = []
    for entity_data in result.get("new_entities", []):
        # Validate entity has attributes
        if not entity_data.get("attributes"):
            logger.warning(f"⚠ SKIPPING entity {entity_data.get('id')} - no attributes")
            continue
        
        attr_count = len(entity_data.get("attributes", []))
        logger.info(f"✓ Creating entity {entity_data.get('id')} with {attr_count} attributes")
        
        entity = Entity(**entity_data)
        new_entities.append(entity)
    
    if not new_entities:
        logger.error("=" * 80)
        logger.error("FATAL: LLM generated no valid entities with attributes!")
        logger.error(f"Total entities in response: {len(result.get('new_entities', []))}")
        logger.error(f"Valid entities after filtering: {len(new_entities)}")
        logger.error("Check /tmp/llm_prompt_debug.txt and /tmp/llm_response_debug.txt")
        logger.error("=" * 80)
        raise ValueError("No valid entities were generated. Please try again.")
    
    # Create new dependencies
    new_dependencies = []
    for dep_data in result.get("new_dependencies", []):
        dep = Dependency(**dep_data)
        new_dependencies.append(dep)
    
    # Merge with existing model
    new_model = TaskDrivenDataModel(
        version=1,
        task_description=current_model.task_description,
        entities=new_entities,
        dependencies=new_dependencies,
        conversation_history=[]
    )
    
    merged_model = schema_merger.merge_models(
        existing_model=current_model,
        new_model=new_model,
        merge_strategy="add"
    )
    
    # Add conversation turn
    merged_model.add_conversation_turn(request.user_input)
    
    # Generate UI spec for new entities
    from app.services.ui_generator import UIGenerator
    ui_generator = UIGenerator()
    
    # Generate spec only for new entities
    incremental_ui_spec = ui_generator.generate_incremental_ui(
        new_entities=new_entities,
        new_dependencies=new_dependencies,
        suggested_views=result.get("suggested_views", {})
    )
    
    logger.info(f"Added {len(new_entities)} new entities")
    
    # Generate components from ALL entities (not just new ones)
    component_specs = await generate_components_from_entities(merged_model.entities)
    
    # Generate NEW suggested questions based on updated model
    logger.info("[Questions] Generating updated suggested questions after adding entities...")
    suggested_questions = await generate_suggested_questions(
        task_description=merged_model.task_description,
        entities=merged_model.entities,  # ALL entities (old + new)
        user_input=request.user_input
    )
    logger.info(f"[Questions] Generated {len(suggested_questions)} new suggestions")
    
    return RefineResponse(
        success=True,
        intent="add_information",
        updated_data_model=merged_model.to_render_spec(),
        incremental_entities=[e.to_render_spec() for e in new_entities],
        incremental_ui_spec=incremental_ui_spec,
        components=component_specs,
        suggested_questions=suggested_questions,  # ← NEW: Updated suggestions
        message=f"Added {len(new_entities)} new entities to your task"
    )


async def extract_entity_from_query(
    user_query: str,
    available_entities: list[Entity]
) -> Optional[str]:
    """
    Use LLM to dynamically extract the entity name/identifier from a natural language query.

    This is a dynamic, AI-driven approach that works for any use case without hardcoding.

    Args:
        user_query: User's natural language query (e.g., "Remove Barcelona from the list")
        available_entities: List of entities in the current model

    Returns:
        Entity identifier (public_identifier or id) if found, None otherwise
    """
    if not available_entities:
        logger.warning("No entities available for extraction")
        return None

    # Build list of entity identifiers for the LLM
    entity_list = []
    for entity in available_entities:
        identifier = entity.get_public_identifier()
        entity_type = entity.type or "Unknown"
        entity_list.append(f"- {identifier} ({entity_type})")
        logger.debug(f"Available entity: {identifier} (ID: {entity.id}, Type: {entity_type})")

    entity_list_str = "\n".join(entity_list)
    logger.info(f"Entity extraction - Query: '{user_query}' | Available: {len(available_entities)} entities")

    prompt = f"""You are an entity name extractor. Your ONLY job is to identify which entity the user is referring to.

USER'S QUERY:
"{user_query}"

AVAILABLE ENTITIES (these are the ONLY valid options):
{entity_list_str}

CRITICAL RULES:
1. Read the user's query carefully - they are asking about a SPECIFIC entity
2. Find the entity name mentioned in their query (e.g., "Barcelona", "Paris", "Rome")
3. Return EXACTLY that entity name - nothing more, nothing less
4. The entity name is the text BEFORE the parentheses in the available entities list
5. If you cannot find a match, return "NONE"

EXAMPLES:
Query: "Remove Barcelona from the list"
Available: Paris (Destination), Rome (Destination), Barcelona (Destination)
Correct Answer: Barcelona

Query: "Delete Madrid"
Available: Paris (Destination), Rome (Destination), Barcelona (Destination)
Correct Answer: NONE

Query: "Get rid of Paris"
Available: Paris (Destination), Rome (Destination)
Correct Answer: Paris

YOUR RESPONSE (just the entity name, nothing else):"""

    try:
        response = await llm_client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=50
        )

        extracted = response.choices[0].message.content.strip()
        logger.info(f"LLM extracted: '{extracted}' from query: '{user_query}'")

        # Validate the extracted name exists
        if extracted and extracted.upper() != "NONE":
            # Try exact match first (case-insensitive)
            for entity in available_entities:
                entity_name = entity.get_public_identifier()
                if entity_name.lower() == extracted.lower():
                    logger.info(f"✓ Exact match found: '{entity_name}' (ID: {entity.id})")
                    return entity_name

            # Try partial match (case-insensitive)
            logger.warning(f"No exact match for '{extracted}', trying partial match...")
            for entity in available_entities:
                entity_name = entity.get_public_identifier()
                if extracted.lower() in entity_name.lower():
                    logger.info(f"✓ Partial match found: '{entity_name}' (ID: {entity.id})")
                    return entity_name

            logger.error(f"✗ No match found for extracted name: '{extracted}'")
        else:
            logger.info(f"LLM returned NONE - no entity identified in query")

        return None

    except Exception as e:
        logger.error(f"Error extracting entity from query: {e}")
        return None


async def handle_modify_data(
    request: RefineRequest,
    current_model: TaskDrivenDataModel,
    params: Dict[str, Any]
) -> RefineResponse:
    """Handle modifying or deleting existing entities."""

    logger.info("Handling MODIFY_DATA intent")

    action = params.get("action", "delete")
    target_query = params.get("target", "")

    if action == "delete":
        # Use LLM to dynamically extract entity name from natural language query
        logger.info(f"Extracting entity from query: '{target_query}'")
        entity_name = await extract_entity_from_query(
            user_query=target_query,
            available_entities=current_model.entities
        )
        logger.info(f"Extracted entity name: '{entity_name}'")

        if not entity_name:
            return RefineResponse(
                success=False,
                intent="modify_data",
                error=f"Could not identify which entity to remove from: '{target_query}'"
            )

        # Find entity to delete using the extracted name
        entity_to_remove = schema_merger.find_entity_by_name(
            model=current_model,
            name=entity_name
        )

        if entity_to_remove:
            schema_merger.remove_entity_by_criteria(
                model=current_model,
                entity_id=entity_to_remove.id
            )
            
            current_model.add_conversation_turn(request.user_input)
            
            # Generate components from remaining entities
            component_specs = await generate_components_from_entities(current_model.entities)
            
            # Generate updated suggestions
            suggested_questions = await generate_suggested_questions(
                task_description=current_model.task_description,
                entities=current_model.entities,
                user_input=request.user_input
            )
            
            return RefineResponse(
                success=True,
                intent="modify_data",
                updated_data_model=current_model.to_render_spec(),
                components=component_specs,
                suggested_questions=suggested_questions,
                message=f"Removed {entity_to_remove.get_public_identifier()}"
            )
        else:
            return RefineResponse(
                success=False,
                intent="modify_data",
                error=f"Entity '{entity_name}' was identified but could not be found in the data model"
            )
    
    else:
        # For other modifications, use LLM
        return RefineResponse(
            success=False,
            intent="modify_data",
            error="Modification type not yet supported"
        )


async def handle_change_view(
    request: RefineRequest,
    current_model: TaskDrivenDataModel,
    params: Dict[str, Any]
) -> RefineResponse:
    """Handle changing view type for existing data."""
    
    logger.info("Handling CHANGE_VIEW intent")
    
    view_type = intent_classifier.extract_view_type(request.user_input)
    entity_type = params.get("entity_type")
    
    if not view_type:
        return RefineResponse(
            success=False,
            intent="change_view",
            error="Could not determine desired view type"
        )
    
    # Generate new UI spec with requested view
    from app.services.ui_generator import UIGenerator
    ui_generator = UIGenerator()
    
    # Get entities of the target type
    target_entities = current_model.entities
    if entity_type:
        target_entities = current_model.get_entities_by_type(entity_type)
    
    # Generate panel with new view type
    incremental_ui_spec = ui_generator.generate_view_change_spec(
        entities=target_entities,
        view_type=view_type
    )
    
    current_model.add_conversation_turn(request.user_input)
    
    # Generate components from entities
    component_specs = await generate_components_from_entities(current_model.entities)
    
    # Generate updated suggestions
    suggested_questions = await generate_suggested_questions(
        task_description=current_model.task_description,
        entities=current_model.entities,
        user_input=request.user_input
    )
    
    return RefineResponse(
        success=True,
        intent="change_view",
        updated_data_model=current_model.to_render_spec(),
        incremental_ui_spec=incremental_ui_spec,
        components=component_specs,
        suggested_questions=suggested_questions,
        message=f"Changed view to {view_type}"
    )


async def handle_refine_analysis(
    request: RefineRequest,
    current_model: TaskDrivenDataModel,
    params: Dict[str, Any]
) -> RefineResponse:
    """Handle refining/re-prioritizing existing analysis by generating NEW components."""

    logger.info("Handling REFINE_ANALYSIS intent")

    # Build enhanced prompt that instructs LLM to generate NEW components
    # CRITICAL: Use to_render_spec() not to_dict() to include full attribute structure
    prompt = get_refinement_prompt(
        user_input=request.user_input,
        existing_model=current_model.to_render_spec(),  # ← FIXED: includes full attributes
        conversation_history=current_model.conversation_history
    )

    # Call LLM with higher token limit for complex components
    logger.info(f"[Refine] Calling LLM with prompt length: {len(prompt)} chars")
    response = await llm_client.chat.completions.create(
        model="anthropic/claude-sonnet-4.5",
        temperature=0.75,
        max_tokens=60000,  # High limit for complex component generation
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.choices[0].message.content.strip()
    logger.info(f"[Refine] LLM response length: {len(response_text)} chars")

    # Parse response
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]

    try:
        result = json.loads(response_text.strip())
        logger.info(f"[Refine] ✓ Parsed JSON successfully")
    except json.JSONDecodeError as e:
        logger.error(f"[Refine] ✗ Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response preview (first 500 chars): {response_text[:500]}")
        raise ValueError(f"LLM returned invalid JSON: {e}")

    # Extract and validate components from LLM response
    component_specs = []
    components_data = result.get("components", [])

    if components_data and len(components_data) > 0:
        logger.info(f"[Refine] LLM generated {len(components_data)} components")

        # Use component template system for validation
        try:
            from app.services.component_templates import generate_components_from_list
            component_specs = generate_components_from_list(components_data)
            logger.info(f"[Refine] ✓ Validated {len(component_specs)} component specs")
        except Exception as e:
            logger.error(f"[Refine] Component validation failed: {e}")
            # Still return the raw components if validation fails
            component_specs = components_data
    else:
        logger.warning("[Refine] ⚠️ LLM returned NO components - using empty array")
        logger.warning("[Refine] This shouldn't happen with the new prompt!")

    # Parse layout specification
    layout_spec = None
    if "layout" in result:
        try:
            layout_spec = LayoutSpec(**result["layout"])
            logger.info(f"[Refine] Parsed layout: {layout_spec.type}")
        except Exception as e:
            logger.warning(f"[Refine] Failed to parse layout: {e}")

    # Add conversation turn
    current_model.add_conversation_turn(request.user_input)

    # Use suggested_questions from LLM response, or fallback to generated ones
    suggested_questions = result.get("suggested_questions", [])
    if not suggested_questions:
        logger.info("[Refine] No suggested questions from LLM, generating...")
        suggested_questions = await generate_suggested_questions(
            task_description=current_model.task_description,
            entities=current_model.entities,
            user_input=request.user_input
        )
    else:
        logger.info(f"[Refine] Using {len(suggested_questions)} suggested questions from LLM")

    # Convert component specs to dicts for JSON response
    components_dict = [comp.model_dump() if hasattr(comp, 'model_dump') else comp for comp in component_specs]
    layout_dict = layout_spec.model_dump() if layout_spec else None

    logger.info(f"[Refine] Returning {len(components_dict)} components to frontend")

    return RefineResponse(
        success=True,
        intent="refine_analysis",
        updated_data_model=current_model.to_render_spec(),
        components=components_dict,  # NEW components from LLM!
        layout=layout_dict,
        suggested_questions=suggested_questions,
        message=result.get("message", "Analysis complete with new visualizations")
    )


@router.post("/create-task", response_model=TaskCreateResponse)
async def create_task_from_input(request: TaskCreateRequest):
    """
    Create a new task-driven UI from natural language input.
    
    Example: "I'm moving to San Francisco"
    """
    logger.info(f"CREATE-TASK REQUEST RECEIVED: {request.user_input}")
    try:
        logger.info(f"Creating task from: {request.user_input}")
        
        # Detect if this is a location-based query (moving, trip, etc.)
        web_context = ""
        input_lower = request.user_input.lower()
        
        if any(keyword in input_lower for keyword in ['moving to', 'relocating to', 'trip to', 'travel to', 'visiting']):
            try:
                from app.services.firecrawl_service import get_firecrawl_service
                firecrawl = get_firecrawl_service()
                
                # Extract location
                import re
                location_match = re.search(r'(?:moving to|relocating to|trip to|travel to|visiting)\s+([A-Z][a-zA-Z\s]+)', request.user_input, re.IGNORECASE)
                if location_match:
                    location = location_match.group(1).strip()
                    logger.info(f"Enriching with web data for location: {location}")
                    
                    # Get real-world data
                    if 'moving' in input_lower or 'relocating' in input_lower:
                        enrichment = await firecrawl.enrich_moving_query(location)
                        
                        # Format as context
                        neighborhoods_context = firecrawl.format_search_context(enrichment.get('neighborhoods', []), max_chars=6000)
                        housing_context = firecrawl.format_search_context(enrichment.get('housing', []), max_chars=2000)
                        
                        web_context = f"\n\n# REAL-WORLD DATA FROM WEB:\n{neighborhoods_context}\n{housing_context}\n"
                        logger.info(f"Added {len(web_context)} chars of web context")
            except Exception as e:
                logger.warning(f"Could not enrich with web data: {e}")
        
        # Build prompt with web context
        prompt = get_task_creation_prompt(request.user_input)
        if web_context:
            prompt += web_context
            prompt += "\n\nIMPORTANT: Use the real-world data above to create accurate, specific entities with actual neighborhood names, prices, and details. DO NOT create placeholder or generic data."
        
        # Call LLM with higher temperature for creativity
        response = await llm_client.chat.completions.create(
            model="anthropic/claude-sonnet-4.5",
            temperature=0.75,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        
        # Create entities (for backward compatibility)
        entities = []
        for entity_data in result.get("entities", []):
            entity = Entity(**entity_data)
            entities.append(entity)
        
        # Create dependencies
        dependencies = []
        for dep_data in result.get("dependencies", []):
            dep = Dependency(**dep_data)
            dependencies.append(dep)
        
        # NEW: Parse component specifications with template fallback
        component_specs = []
        try:
            from app.services.component_templates import (
                generate_components_from_list,
                validate_component_spec,
                create_fallback_component
            )
            
            components_data = result.get("components", [])
            if components_data:
                # Use template system for validation and fallback
                component_specs = generate_components_from_list(components_data)
                logger.info(f"[Components] Generated {len(component_specs)} component specs")
            else:
                logger.info("[Components] No components in LLM response")
                
        except Exception as e:
            logger.error(f"[Components] Failed to parse components: {e}. Continuing with entities only.")
            component_specs = []
        
        # NEW: Parse layout specification
        layout_spec = None
        if "layout" in result:
            try:
                layout_spec = LayoutSpec(**result["layout"])
                logger.info(f"[Layout] Parsed layout: {layout_spec.type}")
            except Exception as e:
                logger.warning(f"[Layout] Failed to parse layout: {e}")
                layout_spec = None
        
        # ENRICH: Add coordinates via geocoding if missing
        logger.info("[Geocoding] Starting geocoding enrichment...")
        entities = await enrich_entities_with_geocoding(entities)
        logger.info("[Geocoding] Geocoding enrichment complete")
        
        # Create data model
        data_model = TaskDrivenDataModel(
            version=1,
            task_description=result.get("task_description", request.user_input),
            entities=entities,
            dependencies=dependencies,
            conversation_history=[{
                "role": "user",
                "content": request.user_input,
                "timestamp": datetime.utcnow().isoformat()
            }]
        )
        
        # Generate UI spec
        from app.services.ui_generator import UIGenerator
        ui_generator = UIGenerator()
        
        ui_spec = ui_generator.generate_task_ui(
            data_model=data_model,
            suggested_views=result.get("suggested_views", {})
        )
        
        # Generate context-aware suggested questions
        logger.info("[Questions] Generating suggested follow-up questions...")
        suggested_questions = await generate_suggested_questions(
            task_description=data_model.task_description,
            entities=entities,
            user_input=request.user_input
        )
        logger.info(f"[Questions] Generated {len(suggested_questions)} questions")
        
        logger.info(f"Created task with {len(entities)} entities and {len(component_specs)} components")
        
        # Convert component specs to dicts for JSON response
        components_dict = [comp.model_dump() for comp in component_specs] if component_specs else None
        layout_dict = layout_spec.model_dump() if layout_spec else None
        
        return TaskCreateResponse(
            success=True,
            data_model=data_model.to_render_spec(),
            ui_spec=ui_spec,
            components=components_dict,  # NEW: Component specs for dynamic UI
            layout=layout_dict,           # NEW: Layout specification
            suggested_questions=suggested_questions
        )
    
    except Exception as e:
        logger.error(f"Task creation failed: {str(e)}")
        return TaskCreateResponse(
            success=False,
            error=str(e)
        )


@router.get("/health")
async def health_check():
    """Health check for refine service."""
    return {
        "status": "healthy",
        "service": "refine",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/suggestions")
async def generate_chat_suggestions(request: SuggestionRequest):
    """
    Generate contextual chat suggestions based on current data model and conversation.
    
    Returns 3-5 short, actionable follow-up prompts that help users:
    - Explore specific details
    - Add missing information
    - Make comparisons
    - Take action
    """
    try:
        logger.info("[Suggestions] Generating chat suggestions...")
        
        # Extract context from data model
        entities = []
        context = ""
        
        if request.data_model and "entities" in request.data_model:
            entities_data = request.data_model["entities"]
            
            # Build context string
            entity_names = [e.get("public_identifier", e.get("id", "")) for e in entities_data[:5]]
            entity_types = list(set([e.get("type", "").split("_")[0] for e in entities_data]))
            
            context = f"Current view shows {len(entities_data)} entities: {', '.join(entity_names[:3])}"
            if len(entity_names) > 3:
                context += f" and {len(entity_names) - 3} more"
            
            logger.info(f"[Suggestions] Context: {context}")
        
        # Get last user message
        last_message = ""
        if request.messages and len(request.messages) > 0:
            last_message = request.messages[-1].get("content", "")
        elif request.current_query:
            last_message = request.current_query
        
        # Generate suggestions using LLM
        prompt = f"""Generate 5 short, actionable follow-up suggestions for a chat interface.

CURRENT CONTEXT: {context if context else "No entities yet"}
LAST USER INPUT: {last_message if last_message else "Initial view"}

Generate 5 suggestions (max 8 words each) that would help the user:
1. Add more information (e.g., "Add another destination")
2. Explore details (e.g., "Show weather patterns")
3. Make comparisons (e.g., "Compare costs")
4. Modify data (e.g., "Remove one city")
5. Take action (e.g., "Book flights")

Make suggestions SPECIFIC and ACTIONABLE. Use actual names if available.

Return ONLY a JSON array of 5 strings:
["Suggestion 1", "Suggestion 2", "Suggestion 3", "Suggestion 4", "Suggestion 5"]"""

        response = await llm_client.chat.completions.create(
            model="anthropic/claude-sonnet-4.5",
            temperature=0.7,
            # max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean JSON markers
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        suggestions = json.loads(response_text.strip())
        
        if isinstance(suggestions, list) and len(suggestions) > 0:
            logger.info(f"[Suggestions] Generated {len(suggestions)} suggestions")
            return {
                "success": True,
                "suggestions": suggestions[:5]  # Return max 5
            }
        else:
            logger.warning("[Suggestions] No suggestions generated, using fallback")
            return {
                "success": True,
                "suggestions": [
                    "Tell me more",
                    "Add another item",
                    "Show more details",
                    "Compare options",
                    "What else should I know?"
                ]
            }
    
    except Exception as e:
        logger.error(f"[Suggestions] Failed to generate: {e}", exc_info=True)
        # Return fallback suggestions on error
        return {
            "success": True,
            "suggestions": [
                "Tell me more",
                "Add another item",
                "Show additional details",
                "What else should I know?"
            ]
        }


@router.post("/stream")
async def create_task_stream(request: TaskCreateRequest):
    """
    Create a new task with STREAMING response (Server-Sent Events).
    
    Components are yielded as they're generated, allowing for real-time UI updates.
    This is an optional optimization for better perceived performance.
    
    Response format: Server-Sent Events (SSE)
    - event: component
      data: {ComponentSpec JSON}
    - event: layout
      data: {LayoutSpec JSON}
    - event: complete
      data: {success: true}
    """
    logger.info(f"[Stream] Starting streaming task creation: {request.user_input[:50]}...")
    
    async def event_generator():
        try:
            # Classify intent
            intent_classifier = IntentClassifier()
            intent = await intent_classifier.classify(request.user_input)
            logger.info(f"[Stream] Intent classified: {intent.type.value}")
            
            # Get prompt based on intent
            if intent.type == IntentType.TASK_CREATE:
                system_prompt = get_task_creation_prompt()
            else:
                system_prompt = get_information_addition_prompt()
            
            # Prepare client
            client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
            
            # Start LLM streaming
            stream = await client.chat.completions.create(
                model="anthropic/claude-3.5-sonnet",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.user_input}
                ],
                # max_tokens=4000,
                temperature=0.7,
                stream=True  # Enable streaming
            )
            
            # Collect response
            full_response = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    
                    # Yield progress event
                    yield f"event: progress\ndata: {json.dumps({'bytes': len(full_response)})}\n\n"
            
            logger.info(f"[Stream] LLM response complete: {len(full_response)} bytes")
            
            # Parse JSON response
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in full_response:
                    start = full_response.index("```json") + 7
                    end = full_response.index("```", start)
                    json_str = full_response[start:end].strip()
                elif "```" in full_response:
                    start = full_response.index("```") + 3
                    end = full_response.index("```", start)
                    json_str = full_response[start:end].strip()
                else:
                    json_str = full_response.strip()
                
                result = json.loads(json_str)
                
            except json.JSONDecodeError as e:
                logger.error(f"[Stream] JSON parse error: {e}")
                yield f"event: error\ndata: {json.dumps({'error': 'Invalid JSON from LLM'})}\n\n"
                return
            
            # Stream components one by one
            from app.services.component_templates import generate_components_from_list
            
            components_data = result.get("components", [])
            if components_data:
                component_specs = generate_components_from_list(components_data)
                
                for idx, comp in enumerate(component_specs):
                    comp_dict = comp.dict()
                    yield f"event: component\ndata: {json.dumps(comp_dict)}\n\n"
                    logger.info(f"[Stream] Sent component {idx + 1}/{len(component_specs)}: {comp.type}")
                    
                    # Small delay for smoother streaming
                    await asyncio.sleep(0.1)
            
            # Send layout
            if "layout" in result:
                try:
                    layout_spec = LayoutSpec(**result["layout"])
                    layout_dict = layout_spec.dict()
                    yield f"event: layout\ndata: {json.dumps(layout_dict)}\n\n"
                    logger.info(f"[Stream] Sent layout: {layout_spec.type}")
                except Exception as e:
                    logger.warning(f"[Stream] Layout parse error: {e}")
            
            # Send entities (for backward compatibility)
            entities = []
            for entity_data in result.get("entities", []):
                try:
                    entity = Entity(**entity_data)
                    entities.append(entity)
                except Exception as e:
                    logger.warning(f"[Stream] Entity parse error: {e}")
            
            if entities:
                # Enrich with geocoding
                entities = await enrich_entities_with_geocoding(entities)
                
                # Send data model
                data_model = TaskDrivenDataModel(
                    version=1,
                    task_description=result.get("task_description", request.user_input),
                    entities=entities,
                    dependencies=[],
                    conversation_history=[]
                )
                
                yield f"event: data_model\ndata: {json.dumps(data_model.dict())}\n\n"
                logger.info(f"[Stream] Sent data model with {len(entities)} entities")
            
            # Send completion
            yield f"event: complete\ndata: {json.dumps({'success': True, 'message': 'Task created successfully'})}\n\n"
            logger.info("[Stream] Task creation complete")
            
        except Exception as e:
            logger.error(f"[Stream] Error: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
