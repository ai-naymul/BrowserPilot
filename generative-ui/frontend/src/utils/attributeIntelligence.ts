import { EntityAttribute, Entity } from '@/types/entity';

/**
 * Intelligent attribute extraction and prioritization system
 * Works with ANY entity type - no hardcoding!
 */

export interface ScoredAttribute extends EntityAttribute {
  score: number;
  category: 'key' | 'detail' | 'list' | 'meta';
  icon?: string;
}

// Key terms that indicate important attributes
const KEY_TERMS = {
  financial: ['cost', 'price', 'salary', 'total', 'budget', 'fee', 'rate', 'comp', 'pay', 'equity', 'bonus'],
  location: ['location', 'address', 'city', 'country', 'place', 'venue', 'office'],
  temporal: ['date', 'time', 'duration', 'deadline', 'schedule', 'when'],
  quality: ['rating', 'score', 'review', 'quality', 'rank'],
  identity: ['name', 'title', 'company', 'person', 'contact'],
  status: ['status', 'state', 'progress', 'done', 'complete']
};

/**
 * Score an attribute based on its importance
 * Higher score = more important to display
 */
export function scoreAttribute(attr: EntityAttribute): number {
  let score = 0;
  const nameLower = attr.name.toLowerCase();
  
  // 1. Widget type priority
  const highPriorityWidgets = ['currency', 'location', 'date', 'rating'];
  const mediumPriorityWidgets = ['short_text', 'number', 'percentage', 'progress'];
  const lowPriorityWidgets = ['long_text', 'array', 'object'];
  
  if (highPriorityWidgets.includes(attr.widget)) score += 15;
  else if (mediumPriorityWidgets.includes(attr.widget)) score += 8;
  else if (lowPriorityWidgets.includes(attr.widget)) score -= 5;
  
  // 2. Name-based priority
  Object.values(KEY_TERMS).flat().forEach(term => {
    if (nameLower.includes(term)) score += 10;
  });
  
  // 3. Value meaningfulness
  if (attr.value !== null && attr.value !== undefined && attr.value !== '' && attr.value !== 0) {
    score += 5;
  } else {
    score -= 10; // Penalize empty/null values
  }
  
  // 4. Computed fields - slight penalty (usually derived)
  if (attr.function === 'compute') score -= 3;
  
  // 5. Special attribute metadata roles (if exists)
  const role = attr.metadata?.role;
  if (role === 'identifier') score += 20;
  if (role === 'thumbnail') score += 15;
  if (role === 'public_identifier') score += 18;
  if (role === 'hidden') score -= 100;
  if (role && typeof role === 'string') {
    if (role.includes('sortable')) score += 3;
    if (role.includes('filterable')) score += 3;
  }
  
  return Math.max(0, score); // Never negative
}

/**
 * Categorize attribute based on its characteristics
 */
export function categorizeAttribute(attr: ScoredAttribute): 'key' | 'detail' | 'list' | 'meta' {
  const nameLower = attr.name.toLowerCase();
  
  // Key metrics
  const isFinancial = KEY_TERMS.financial.some(term => nameLower.includes(term));
  const isLocation = KEY_TERMS.location.some(term => nameLower.includes(term));
  const isTemporal = KEY_TERMS.temporal.some(term => nameLower.includes(term));
  const isQuality = KEY_TERMS.quality.some(term => nameLower.includes(term));
  
  if (isFinancial || isLocation || isTemporal || isQuality) {
    return 'key';
  }
  
  // Lists/arrays
  if (attr.widget === 'array' || Array.isArray(attr.value)) {
    return 'list';
  }
  
  // Metadata
  if (nameLower.includes('id') || nameLower.includes('meta') || nameLower.includes('created') || nameLower.includes('updated')) {
    return 'meta';
  }
  
  // Everything else is detail
  return 'detail';
}

/**
 * Get icon for attribute based on its type
 */
export function getAttributeIcon(attr: EntityAttribute): string {
  const nameLower = attr.name.toLowerCase();
  
  // Widget-based icons
  if (attr.widget === 'currency') return '💰';
  if (attr.widget === 'location') return '📍';
  if (attr.widget === 'date' || attr.widget === 'time') return '📅';
  if (attr.widget === 'rating') return '⭐';
  if (attr.widget === 'contact_card') return '👤';
  
  // Name-based icons
  if (KEY_TERMS.financial.some(term => nameLower.includes(term))) return '💵';
  if (KEY_TERMS.location.some(term => nameLower.includes(term))) return '🗺️';
  if (KEY_TERMS.temporal.some(term => nameLower.includes(term))) return '⏰';
  if (KEY_TERMS.quality.some(term => nameLower.includes(term))) return '✨';
  if (KEY_TERMS.identity.some(term => nameLower.includes(term))) return '🏷️';
  if (KEY_TERMS.status.some(term => nameLower.includes(term))) return '📊';
  
  return '📄';
}

/**
 * Extract and score all attributes from an entity
 */
export function getKeyAttributes(entity: Entity, limit: number = 5): ScoredAttribute[] {
  const scored = entity.attributes.map(attr => {
    const score = scoreAttribute(attr);
    const scoredAttr: ScoredAttribute = {
      ...attr,
      score,
      category: 'detail' as any,
      icon: getAttributeIcon(attr)
    };
    scoredAttr.category = categorizeAttribute(scoredAttr);
    return scoredAttr;
  });
  
  // Sort by score (highest first) and take top N
  return scored
    .filter(attr => attr.score > 0) // Remove negative scores
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}

/**
 * Group attributes by category
 */
export function groupAttributesByCategory(entity: Entity): {
  key: ScoredAttribute[];
  detail: ScoredAttribute[];
  list: ScoredAttribute[];
  meta: ScoredAttribute[];
} {
  const scored = entity.attributes.map(attr => {
    const score = scoreAttribute(attr);
    const scoredAttr: ScoredAttribute = {
      ...attr,
      score,
      category: 'detail' as any,
      icon: getAttributeIcon(attr)
    };
    scoredAttr.category = categorizeAttribute(scoredAttr);
    return scoredAttr;
  });
  
  return {
    key: scored.filter(a => a.category === 'key').sort((a, b) => b.score - a.score),
    detail: scored.filter(a => a.category === 'detail').sort((a, b) => b.score - a.score),
    list: scored.filter(a => a.category === 'list').sort((a, b) => b.score - a.score),
    meta: scored.filter(a => a.category === 'meta').sort((a, b) => b.score - a.score)
  };
}

/**
 * Format attribute value based on widget type
 */
export function formatAttributeValue(value: any, widget: string): string {
  if (value === null || value === undefined) return '-';
  
  switch (widget) {
    case 'currency':
      const num = typeof value === 'number' ? value : parseFloat(value);
      if (isNaN(num)) return '-';
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(num);
      
    case 'date':
      try {
        const date = new Date(value);
        if (isNaN(date.getTime())) return String(value);
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
      } catch {
        return String(value);
      }
      
    case 'percentage':
      return `${value}%`;
      
    case 'rating':
      const rating = typeof value === 'number' ? value : parseFloat(value);
      if (isNaN(rating)) return String(value);
      const stars = '⭐'.repeat(Math.round(rating / 2));
      return `${rating}/10 ${stars}`;
      
    case 'location':
      if (typeof value === 'object' && value !== null) {
        if (value.city) return value.city;
        if (value.name) return value.name;
        if (value.address) return value.address;
        return JSON.stringify(value).slice(0, 50);
      }
      return String(value);
      
    case 'array':
      if (Array.isArray(value)) {
        if (value.length === 0) return 'Empty';
        if (value.length <= 3 && value.every(v => typeof v === 'string')) {
          return value.join(', ');
        }
        return `${value.length} items`;
      }
      return String(value);
      
    case 'progress':
      const progress = typeof value === 'number' ? value : parseFloat(value);
      if (isNaN(progress)) return String(value);
      return `${Math.round(progress)}%`;
      
    case 'long_text':
      const text = String(value);
      return text.length > 50 ? text.slice(0, 50) + '...' : text;
      
    default:
      if (typeof value === 'object') {
        return JSON.stringify(value).slice(0, 50) + '...';
      }
      return String(value);
  }
}

/**
 * Extract numeric value for sorting/comparison
 */
export function getNumericValue(value: any, widget: string): number {
  if (widget === 'currency' || widget === 'number' || widget === 'rating' || widget === 'progress' || widget === 'percentage') {
    const num = typeof value === 'number' ? value : parseFloat(value);
    return isNaN(num) ? 0 : num;
  }
  
  if (widget === 'date' || widget === 'time') {
    try {
      return new Date(value).getTime();
    } catch {
      return 0;
    }
  }
  
  if (widget === 'array' && Array.isArray(value)) {
    return value.length;
  }
  
  return 0;
}

/**
 * Get comparable attributes across multiple entities
 * Returns attribute names that appear in multiple entities
 */
export function getComparableAttributes(entities: Entity[]): string[] {
  if (entities.length === 0) return [];
  
  // Count how many entities have each attribute
  const attributeCounts = new Map<string, number>();
  entities.forEach(entity => {
    entity.attributes.forEach(attr => {
      attributeCounts.set(attr.name, (attributeCounts.get(attr.name) || 0) + 1);
    });
  });
  
  // Return attributes that appear in at least 50% of entities
  const threshold = Math.ceil(entities.length * 0.5);
  return Array.from(attributeCounts.entries())
    .filter(([_, count]) => count >= threshold)
    .map(([name, _]) => name)
    .sort();
}

// REMOVED: Hardcoded CITY_COORDINATES - now using dynamic geocoding!
// Backend generates coordinates via LLM or Nominatim API
// Frontend can fallback to Nominatim if needed (see geocoding.ts)

/**
 * Extract location coordinates from any entity
 */
export function extractEntityLocation(entity: Entity): { lat: number; lng: number; address?: string } | null {
  // Check all attributes for location data
  for (const attr of entity.attributes) {
    const nameLower = attr.name.toLowerCase();
    const isLocationField = nameLower.includes('location') || 
                           nameLower.includes('address') || 
                           nameLower.includes('city') ||
                           attr.widget === 'location';
    
    if (!isLocationField) continue;
    
    // Case 1: Value is already an object with lat/lng (from LLM)
    if (typeof attr.value === 'object' && attr.value !== null) {
      const val = attr.value as any;
      if (typeof val.lat === 'number' && typeof val.lng === 'number') {
        return {
          lat: val.lat,
          lng: val.lng,
          address: val.address || val.city || val.name
        };
      }
      if (typeof val.latitude === 'number' && typeof val.longitude === 'number') {
        return {
          lat: val.latitude,
          lng: val.longitude,
          address: val.address || val.city || val.name
        };
      }
    }
    
    // Case 2: Look for separate "coordinates" attribute
    const coordsAttr = entity.attributes.find(a => a.name === 'coordinates');
    if (coordsAttr) {
      // Handle object format: { lat: 48.8566, lng: 2.3522 }
      if (typeof coordsAttr.value === 'object' && coordsAttr.value !== null) {
        const coords = coordsAttr.value as any;
        if (typeof coords.lat === 'number' && typeof coords.lng === 'number') {
          return {
            lat: coords.lat,
            lng: coords.lng,
            address: typeof attr.value === 'string' ? attr.value : undefined
          };
        }
      }
      
      // Handle string format: "48.8566, 2.3522"
      if (typeof coordsAttr.value === 'string') {
        const parts = coordsAttr.value.split(',').map(s => s.trim());
        if (parts.length === 2) {
          const lat = parseFloat(parts[0]);
          const lng = parseFloat(parts[1]);
          if (!isNaN(lat) && !isNaN(lng)) {
            return {
              lat,
              lng,
              address: typeof attr.value === 'string' ? attr.value : undefined
            };
          }
        }
      }
    }
  }
  
  // If no coordinates found, return null
  // Frontend can use geocoding fallback (see MapView geocoding hook)
  return null;
}
