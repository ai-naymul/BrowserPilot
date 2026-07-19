/**
 * AI-Powered Entity Matching Utility
 *
 * Replaces brittle hardcoded string matching with AI-based semantic understanding.
 * Uses LLM to intelligently match component keys, locations, and references to entities.
 */

import { Entity } from '@/types/entity';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface EntityMatchRequest {
  reference: string;
  reference_type: 'component_key' | 'location_name' | 'label' | 'generic';
  context?: Record<string, any>;
  entities: Entity[];
}

export interface EntityMatchResponse {
  success: boolean;
  entity_id: string | null;
  confidence: number;
  reasoning: string;
  is_aggregate: boolean;
}

// In-memory cache to avoid repeated API calls
const matchCache = new Map<string, EntityMatchResponse>();

/**
 * Generate cache key from reference and entity IDs
 */
function generateCacheKey(reference: string, entities: Entity[]): string {
  const entityIds = entities.map(e => e.id).sort().join(',');
  return `${reference}::${entityIds}`;
}

/**
 * Match a reference (component key, location name, etc.) to an entity using AI.
 *
 * This replaces hardcoded string matching with intelligent semantic understanding.
 *
 * @param request - The matching request with reference and entities
 * @returns The matched entity ID, or null if no match/aggregate component
 */
export async function matchEntityWithAI(
  request: EntityMatchRequest
): Promise<EntityMatchResponse> {
  // Check cache first
  const cacheKey = generateCacheKey(request.reference, request.entities);

  if (matchCache.has(cacheKey)) {
    console.log(`[AI EntityMatcher] Cache hit for "${request.reference}"`);
    return matchCache.get(cacheKey)!;
  }

  try {
    console.log(`[AI EntityMatcher] Calling API to match "${request.reference}" against ${request.entities.length} entities`);

    const response = await fetch(`${API_BASE_URL}/api/match-entity`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}: ${response.statusText}`);
    }

    const result: EntityMatchResponse = await response.json();

    // Cache the result
    matchCache.set(cacheKey, result);

    console.log(
      `[AI EntityMatcher] ✓ Matched "${request.reference}" → "${result.entity_id}" ` +
      `(confidence: ${result.confidence}, aggregate: ${result.is_aggregate})`
    );

    return result;
  } catch (error) {
    console.error(`[AI EntityMatcher] ✗ Failed to match "${request.reference}":`, error);

    // Return failure response (don't cache failures)
    return {
      success: false,
      entity_id: null,
      confidence: 0,
      reasoning: `Matching failed: ${error}`,
      is_aggregate: false,
    };
  }
}

/**
 * Batch match multiple references to entities.
 * More efficient than individual calls when matching many items.
 *
 * @param requests - Array of matching requests
 * @returns Array of matched results
 */
export async function matchEntitiesBatch(
  requests: EntityMatchRequest[]
): Promise<EntityMatchResponse[]> {
  // Check cache for each request
  const results: (EntityMatchResponse | null)[] = requests.map(req => {
    const cacheKey = generateCacheKey(req.reference, req.entities);
    return matchCache.has(cacheKey) ? matchCache.get(cacheKey)! : null;
  });

  // Find indices of requests that need API call
  const uncachedIndices = results
    .map((result, idx) => (result === null ? idx : -1))
    .filter(idx => idx !== -1);

  if (uncachedIndices.length === 0) {
    console.log(`[AI EntityMatcher] All ${requests.length} requests satisfied from cache`);
    return results as EntityMatchResponse[];
  }

  try {
    console.log(
      `[AI EntityMatcher] Batch matching ${uncachedIndices.length} references ` +
      `(${results.length - uncachedIndices.length} from cache)`
    );

    const uncachedRequests = uncachedIndices.map(idx => requests[idx]);

    const response = await fetch(`${API_BASE_URL}/api/match-entities-batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(uncachedRequests),
    });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}: ${response.statusText}`);
    }

    const batchResults: EntityMatchResponse[] = await response.json();

    // Update cache and results
    uncachedIndices.forEach((reqIdx, batchIdx) => {
      const result = batchResults[batchIdx];
      const req = requests[reqIdx];
      const cacheKey = generateCacheKey(req.reference, req.entities);

      matchCache.set(cacheKey, result);
      results[reqIdx] = result;
    });

    return results as EntityMatchResponse[];
  } catch (error) {
    console.error(`[AI EntityMatcher] ✗ Batch matching failed:`, error);

    // Fill uncached slots with failures
    uncachedIndices.forEach(idx => {
      results[idx] = {
        success: false,
        entity_id: null,
        confidence: 0,
        reasoning: `Batch matching failed: ${error}`,
        is_aggregate: false,
      };
    });

    return results as EntityMatchResponse[];
  }
}

/**
 * Clear the match cache.
 * Useful when entities are updated or deleted.
 */
export function clearMatchCache(): void {
  const size = matchCache.size;
  matchCache.clear();
  console.log(`[AI EntityMatcher] Cleared match cache (${size} entries)`);
}

/**
 * Helper: Match a location to an entity with AI fallback
 *
 * @param locationLabel - The location label/name (e.g., "Paris")
 * @param locationId - The location ID (e.g., "paris")
 * @param locationData - Additional location data (coordinates, description)
 * @param entities - Available entities
 * @returns Entity ID or null
 */
export async function matchLocationToEntity(
  locationLabel: string,
  locationId: string,
  locationData: Record<string, any>,
  entities: Entity[]
): Promise<string | null> {
  const result = await matchEntityWithAI({
    reference: locationLabel,
    reference_type: 'location_name',
    context: {
      location_id: locationId,
      ...locationData,
    },
    entities,
  });

  return result.entity_id;
}

/**
 * Helper: Match a component key to an entity with AI fallback
 *
 * @param componentKey - The component key (e.g., "winner-transport", "metric_card_paris")
 * @param componentProps - Component props for context
 * @param entities - Available entities
 * @returns Match result with entity_id and is_aggregate flag
 */
export async function matchComponentKeyToEntity(
  componentKey: string,
  componentProps: Record<string, any>,
  entities: Entity[]
): Promise<{ entity_id: string | null; is_aggregate: boolean }> {
  const result = await matchEntityWithAI({
    reference: componentKey,
    reference_type: 'component_key',
    context: componentProps,
    entities,
  });

  return {
    entity_id: result.entity_id,
    is_aggregate: result.is_aggregate,
  };
}
