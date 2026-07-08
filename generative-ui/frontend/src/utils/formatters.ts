/**
 * Formatting utilities for data display
 * Returns null for invalid/empty values to enable "Add value" chips
 */

import { toNumberOrNull, parseISODateSafe } from './validators';

/**
 * Format currency, returning null if invalid
 * Enables UI to show "Add value" chip instead of "—"
 */
export function formatCurrencyOrNull(value: any): string | null {
  const num = toNumberOrNull(value);
  if (num === null) return null;

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

/**
 * Format number with locale, returning null if invalid
 */
export function formatNumberOrNull(value: any, options?: Intl.NumberFormatOptions): string | null {
  const num = toNumberOrNull(value);
  if (num === null) return null;

  return new Intl.NumberFormat('en-US', options).format(num);
}

/**
 * Format percentage, returning null if invalid
 */
export function formatPercentageOrNull(value: any): string | null {
  const num = toNumberOrNull(value);
  if (num === null) return null;

  return `${num.toFixed(1)}%`;
}

/**
 * Format rating (e.g., "9.5/10"), returning null if invalid
 */
export function formatRatingOrNull(value: any, maxRating: number = 10): string | null {
  const num = toNumberOrNull(value);
  if (num === null) return null;

  return `${num.toFixed(1)}/${maxRating}`;
}

/**
 * Format date to readable string, returning null if invalid
 */
export function formatDateOrNull(value: any): string | null {
  const isoDate = parseISODateSafe(value);
  if (!isoDate) return null;

  try {
    const date = new Date(isoDate);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  } catch {
    return null;
  }
}

/**
 * Format compact number (e.g., "1.2K", "3.4M")
 */
export function formatCompactNumber(value: any): string | null {
  const num = toNumberOrNull(value);
  if (num === null) return null;

  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(num);
}

/**
 * Truncate text to maxLength with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (!text || text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '…';
}

/**
 * Humanize attribute name: "arrival_date" → "Arrival Date"
 */
export function humanize(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

/**
 * Generate stable key from object properties
 */
export function generateStableKey(obj: any, prefix: string = 'item'): string {
  if (obj.id) return `${prefix}-${obj.id}`;
  if (obj.key) return `${prefix}-${obj.key}`;
  if (obj.name) return `${prefix}-${String(obj.name).replace(/\s+/g, '-')}`;

  // Fallback: hash of object properties
  const props = [obj.lat, obj.lng, obj.label, obj.value].filter(Boolean).join('|');
  return `${prefix}-${props.slice(0, 32)}`;
}

// ============================================================================
// SEMANTIC FIELD CLASSIFICATION (for role-aware visual grammar)
// ============================================================================

/**
 * Field semantic types for intelligent component selection
 */
export type FieldSemantic =
  | 'currency'      // $, €, cost, price → hero metrics, bar charts
  | 'percentage'    // %, rate → progress bars, normalized charts
  | 'rating'        // score, rating /10 → badges, star displays
  | 'count'         // quantity, number of items → small metrics
  | 'duration'      // days, hours, length → timeline charts
  | 'temperature'   // degrees, weather → breakdown only (not hero)
  | 'coordinate'    // lat/lng → maps only
  | 'date'          // ISO dates, timestamps → timelines
  | 'text'          // free text → detail sections, NOT cards
  | 'number';       // generic numeric → fallback

/**
 * Field priority for hero metric selection
 * Higher = more likely to be a hero metric
 */
export type FieldPriority = 'hero' | 'supporting' | 'detail' | 'hidden';

/**
 * Classify an attribute's semantic type based on name, value, and metadata
 *
 * @param attrName - Attribute name (e.g., "total_cost", "avg_temperature")
 * @param value - Attribute value
 * @param metadata - Optional attribute metadata (widget, function, unit, etc.)
 * @returns Semantic type classification
 */
export function classifyFieldSemantic(
  attrName: string,
  value: any,
  metadata?: { widget?: string; function?: string; unit?: string; data_type?: string }
): FieldSemantic {
  const lowerName = attrName.toLowerCase();
  const strValue = String(value || '').toLowerCase();

  // 1. Check explicit metadata first
  if (metadata?.widget === 'currency' || metadata?.unit === 'USD' || metadata?.unit === 'EUR') {
    return 'currency';
  }
  if (metadata?.widget === 'percentage' || metadata?.unit === '%') {
    return 'percentage';
  }
  if (metadata?.widget === 'rating') {
    return 'rating';
  }
  if (metadata?.data_type === 'date' || metadata?.widget === 'date') {
    return 'date';
  }

  // 2. Infer from attribute name patterns
  // Currency
  if (lowerName.includes('cost') || lowerName.includes('price') || lowerName.includes('budget') ||
      lowerName.includes('fee') || lowerName.includes('expense') || lowerName.includes('revenue')) {
    return 'currency';
  }

  // Percentage
  if (lowerName.includes('percent') || lowerName.includes('rate') || lowerName.includes('ratio')) {
    return 'percentage';
  }

  // Rating / Score
  if (lowerName.includes('rating') || lowerName.includes('score') || lowerName.includes('rank')) {
    return 'rating';
  }

  // Temperature (weather - breakdown only)
  if (lowerName.includes('temperature') || lowerName.includes('temp') ||
      lowerName.includes('weather') || lowerName.includes('climate')) {
    return 'temperature';
  }

  // Duration
  if (lowerName.includes('duration') || lowerName.includes('length') ||
      lowerName.includes('days') || lowerName.includes('hours') || lowerName.includes('time')) {
    return 'duration';
  }

  // Count
  if (lowerName.includes('count') || lowerName.includes('quantity') ||
      lowerName.includes('number_of') || lowerName.includes('num_')) {
    return 'count';
  }

  // Coordinates
  if ((lowerName === 'lat' || lowerName === 'latitude') ||
      (lowerName === 'lng' || lowerName === 'longitude')) {
    return 'coordinate';
  }

  // Date
  if (lowerName.includes('date') || lowerName.includes('time') || lowerName.includes('timestamp')) {
    return 'date';
  }

  // 3. Infer from value patterns
  if (strValue.includes('$') || strValue.includes('€') || strValue.includes('£')) {
    return 'currency';
  }
  if (strValue.includes('%')) {
    return 'percentage';
  }

  // 4. Check if value is numeric
  const numValue = toNumberOrNull(value);
  if (numValue !== null) {
    return 'number';
  }

  // 5. Long text → detail only
  if (typeof value === 'string' && value.length > 100) {
    return 'text';
  }

  // 6. Fallback
  return typeof value === 'string' ? 'text' : 'number';
}

/**
 * Determine field priority for hero metric selection
 *
 * Hero metrics should be:
 * - Stable totals (cost, score, value)
 * - Not breakdowns (temperature, daily details)
 * - Not free text
 *
 * @param semantic - Field semantic type
 * @param attrFunction - Attribute function role (e.g., 'computed', 'identifier')
 * @returns Priority level
 */
export function getFieldPriority(
  semantic: FieldSemantic,
  attrFunction?: string
): FieldPriority {
  // Identifiers are never hero metrics
  if (attrFunction === 'identifier' || attrFunction === 'publicIdentifier') {
    return 'hidden';
  }

  switch (semantic) {
    // Hero-worthy: totals, costs, scores
    case 'currency':
    case 'rating':
      return attrFunction === 'computed' ? 'hero' : 'supporting';

    // Supporting: counts, durations, percentages
    case 'count':
    case 'duration':
    case 'percentage':
      return 'supporting';

    // Detail only: weather, coordinates, text
    case 'temperature':
    case 'coordinate':
    case 'text':
      return 'detail';

    // Dates: supporting if computed, else detail
    case 'date':
      return attrFunction === 'computed' ? 'supporting' : 'detail';

    // Generic numbers: supporting
    case 'number':
      return attrFunction === 'computed' ? 'supporting' : 'detail';

    default:
      return 'detail';
  }
}

/**
 * Check if a field should be eligible for hero metric cards
 *
 * @param attrName - Attribute name
 * @param value - Attribute value
 * @param metadata - Attribute metadata
 * @returns true if this field is hero-worthy
 */
export function isHeroMetricEligible(
  attrName: string,
  value: any,
  metadata?: { widget?: string; function?: string; unit?: string }
): boolean {
  const semantic = classifyFieldSemantic(attrName, value, metadata);
  const priority = getFieldPriority(semantic, metadata?.function);

  return priority === 'hero' || priority === 'supporting';
}
