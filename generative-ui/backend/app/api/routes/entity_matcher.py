"""
AI-Powered Entity Matching Endpoint

Uses LLM to intelligently match component keys, locations, and references to actual entities.
Replaces brittle hardcoded string matching with semantic understanding.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
from openai import AsyncOpenAI
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM client (same pattern as refine.py)
llm_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://generative-ui-browser.local",
        "X-Title": "Generative UI Browser - Entity Matcher"
    }
)

# In-memory cache for entity matches (cleared on server restart)
# Format: {cache_key: entity_id}
_match_cache: Dict[str, Optional[str]] = {}


class EntityMatchRequest(BaseModel):
    """Request to match a component/location/key to an entity"""

    reference: str = Field(..., description="The reference to match (e.g., component key, location name)")
    reference_type: str = Field(..., description="Type of reference: 'component_key', 'location_name', 'label'")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context (props, location data)")
    entities: List[Dict[str, Any]] = Field(..., description="Available entities to match against")


class EntityMatchResponse(BaseModel):
    """Response with matched entity ID"""

    success: bool
    entity_id: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score (0-1)")
    reasoning: str = Field("", description="Why this entity was matched")
    is_aggregate: bool = Field(False, description="True if this is an aggregate/comparison component (no single entity)")


def _generate_cache_key(reference: str, entities: List[Dict[str, Any]]) -> str:
    """Generate cache key from reference and entity IDs"""
    entity_ids = sorted([e.get('id', '') for e in entities])
    return f"{reference}::{','.join(entity_ids)}"


async def match_entity_with_ai(
    reference: str,
    reference_type: str,
    context: Dict[str, Any],
    entities: List[Dict[str, Any]]
) -> EntityMatchResponse:
    """
    Use LLM to semantically match a reference to an entity.

    This replaces hardcoded string matching with intelligent semantic understanding.
    """

    # Check cache first
    cache_key = _generate_cache_key(reference, entities)
    if cache_key in _match_cache:
        cached_id = _match_cache[cache_key]
        logger.info(f"[EntityMatcher] Cache hit for '{reference}' → '{cached_id}'")
        return EntityMatchResponse(
            success=True,
            entity_id=cached_id,
            confidence=1.0,
            reasoning="Cached result",
            is_aggregate=cached_id is None
        )

    # Format entities for LLM
    entity_summaries = []
    for e in entities:
        summary = {
            "id": e.get("id", ""),
            "type": e.get("type", ""),
            "public_identifier": e.get("public_identifier", ""),
            "attributes_summary": []
        }

        # Extract key attributes
        if "attributes" in e:
            for attr in e["attributes"][:5]:  # First 5 attributes only
                summary["attributes_summary"].append({
                    "name": attr.get("name", ""),
                    "value": str(attr.get("value", ""))[:100]  # Truncate long values
                })

        entity_summaries.append(summary)

    # Build prompt
    prompt = f"""You are an entity matching expert. Your task is to match a reference to the correct entity from a list.

REFERENCE TO MATCH:
Type: {reference_type}
Value: "{reference}"

ADDITIONAL CONTEXT:
{json.dumps(context, indent=2) if context else "No additional context"}

AVAILABLE ENTITIES:
{json.dumps(entity_summaries, indent=2)}

TASK:
Determine which entity (if any) this reference is referring to. Consider:
- Component keys like "winner-transport" or "transport-comparison-table" are AGGREGATE components comparing multiple entities (return null)
- Location names like "Paris" should match entities with matching public_identifier or location attributes
- Partial matches are OK (e.g., "paris" can match "destination_paris")
- If reference is clearly about multiple entities or a comparison, it's an aggregate (return null)

OUTPUT FORMAT (JSON):
{{
    "entity_id": "entity_id_here" OR null if aggregate/no match,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this entity was matched or why it's aggregate",
    "is_aggregate": true/false
}}

IMPORTANT:
- Return null for entity_id if this is a comparison/aggregate component
- Return null if no clear match exists
- Be confident - if the reference clearly relates to an entity, match it"""

    try:
        logger.info(f"[EntityMatcher] Calling LLM to match '{reference}' against {len(entities)} entities")

        response = await llm_client.chat.completions.create(
            model="anthropic/claude-sonnet-4.5",
            temperature=0.3,  # Low temperature for consistent matching
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.choices[0].message.content.strip()

        # Parse JSON response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        result = json.loads(response_text.strip())

        entity_id = result.get("entity_id")
        confidence = float(result.get("confidence", 0.5))
        reasoning = result.get("reasoning", "LLM matched entity")
        is_aggregate = result.get("is_aggregate", False)

        # Cache the result
        _match_cache[cache_key] = entity_id

        logger.info(f"[EntityMatcher] ✓ Matched '{reference}' → '{entity_id}' (confidence: {confidence}, aggregate: {is_aggregate})")

        return EntityMatchResponse(
            success=True,
            entity_id=entity_id,
            confidence=confidence,
            reasoning=reasoning,
            is_aggregate=is_aggregate
        )

    except Exception as e:
        logger.error(f"[EntityMatcher] ✗ Failed to match '{reference}': {e}")

        # Cache negative result to avoid repeated failures
        _match_cache[cache_key] = None

        return EntityMatchResponse(
            success=False,
            entity_id=None,
            confidence=0.0,
            reasoning=f"Matching failed: {str(e)}",
            is_aggregate=False
        )


@router.post("/match-entity", response_model=EntityMatchResponse)
async def match_entity_endpoint(request: EntityMatchRequest):
    """
    Match a reference (component key, location name, etc.) to an entity using AI.

    This endpoint uses LLM to semantically understand which entity a reference refers to,
    replacing brittle hardcoded string matching.
    """

    if not request.entities:
        raise HTTPException(status_code=400, detail="No entities provided")

    if not request.reference:
        raise HTTPException(status_code=400, detail="No reference provided")

    return await match_entity_with_ai(
        reference=request.reference,
        reference_type=request.reference_type,
        context=request.context,
        entities=request.entities
    )


@router.post("/match-entities-batch", response_model=List[EntityMatchResponse])
async def match_entities_batch_endpoint(requests: List[EntityMatchRequest]):
    """
    Batch match multiple references to entities.
    More efficient than individual calls when matching many items at once.
    """

    results = []

    for req in requests:
        result = await match_entity_with_ai(
            reference=req.reference,
            reference_type=req.reference_type,
            context=req.context,
            entities=req.entities
        )
        results.append(result)

    return results


@router.delete("/clear-match-cache")
async def clear_match_cache():
    """Clear the entity match cache. Useful when entities are updated."""
    global _match_cache
    cache_size = len(_match_cache)
    _match_cache.clear()
    logger.info(f"[EntityMatcher] Cleared match cache ({cache_size} entries)")
    return {"success": True, "cleared_entries": cache_size}
