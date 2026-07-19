/**
 * Data validation utilities
 */

/**
 * Safely parse and validate ISO date strings
 * Only accepts YYYY-MM-DD format with years between 1900-2100
 * @param dateStr - Input date string
 * @returns Normalized YYYY-MM-DD string or null if invalid
 */
export function parseISODateSafe(dateStr: string | null | undefined): string | null {
  if (!dateStr || typeof dateStr !== 'string') {
    return null;
  }

  // Heuristics: detect strings that are clearly NOT dates (to avoid console spam)
  const trimmed = dateStr.trim();

  // Contains hour markers → duration, not a date
  if (/\d+h|\bhours?\b/i.test(trimmed)) {
    return null;
  }

  // Contains parentheses → likely a note or context, not a date
  if (/[()]/.test(trimmed)) {
    return null;
  }

  // Too short or too long to be YYYY-MM-DD (which is 10 chars)
  if (trimmed.length < 8 || trimmed.length > 12) {
    return null;
  }

  // Match YYYY-MM-DD format
  const isoPattern = /^(\d{4})-(\d{2})-(\d{2})$/;
  const match = trimmed.match(isoPattern);

  if (!match) {
    // Only log warning if it looks like it MIGHT be a date attempt
    if (/\d{4}/.test(trimmed) || /\d{1,2}[-/]\d{1,2}/.test(trimmed)) {
      console.warn('[Validator] Invalid date format:', dateStr);
    }
    return null;
  }

  const [, yearStr, monthStr, dayStr] = match;
  const year = parseInt(yearStr, 10);
  const month = parseInt(monthStr, 10);
  const day = parseInt(dayStr, 10);

  // Validate year range
  if (year < 1900 || year > 2100) {
    console.warn('[Validator] Year out of range:', year);
    return null;
  }

  // Validate month
  if (month < 1 || month > 12) {
    console.warn('[Validator] Invalid month:', month);
    return null;
  }

  // Validate day
  if (day < 1 || day > 31) {
    console.warn('[Validator] Invalid day:', day);
    return null;
  }

  // Check if date is valid using Date object
  const testDate = new Date(year, month - 1, day);
  if (
    testDate.getFullYear() !== year ||
    testDate.getMonth() !== month - 1 ||
    testDate.getDate() !== day
  ) {
    console.warn('[Validator] Invalid date:', dateStr);
    return null;
  }

  // Return normalized format
  return `${year.toString().padStart(4, '0')}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
}

/**
 * Check if a value is meaningful (not empty/null/undefined/dash)
 */
export function isValueMeaningful(value: any): boolean {
  if (value === null || value === undefined) {
    return false;
  }

  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed !== '' && trimmed !== '-' && trimmed !== 'N/A' && trimmed !== '---';
  }

  if (typeof value === 'number') {
    return !isNaN(value);
  }

  if (Array.isArray(value)) {
    return value.length > 0;
  }

  if (typeof value === 'object') {
    return Object.keys(value).length > 0;
  }

  return true;
}

/**
 * Humanize attribute names (e.g., "arrival_date" → "Arrival date")
 */
export function humanizeAttributeName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

/**
 * Format currency values
 */
export function formatCurrency(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return '-';
  }

  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue)) {
    return '-';
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numValue);
}

/**
 * Format percentage values
 */
export function formatPercentage(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return '-';
  }

  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue)) {
    return '-';
  }

  return `${numValue.toFixed(1)}%`;
}

/**
 * Format rating values (e.g., 9.5/10)
 */
export function formatRating(value: number | string | null | undefined, maxRating: number = 10): string {
  if (value === null || value === undefined) {
    return '-';
  }

  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue)) {
    return '-';
  }

  return `${numValue.toFixed(1)}/${maxRating}`;
}

/**
 * Convert any date input to strict ISO format (YYYY-MM-DD)
 * Throws error on invalid date - fail fast approach
 */
export function toISODate(input: string | Date | null | undefined): string {
  if (!input) {
    throw new Error('Date is required');
  }

  // If already string, validate and return
  if (typeof input === 'string') {
    const parsed = parseISODateSafe(input);
    if (!parsed) {
      throw new Error(`Invalid date format: "${input}". Expected YYYY-MM-DD between years 1900-2100`);
    }
    return parsed;
  }

  // If Date object, convert to ISO
  if (input instanceof Date) {
    const year = input.getFullYear();
    const month = input.getMonth() + 1;
    const day = input.getDate();

    if (year < 1900 || year > 2100) {
      throw new Error(`Date year out of range: ${year}. Must be between 1900-2100`);
    }

    return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  }

  throw new Error(`Invalid date type: ${typeof input}`);
}

/**
 * Convert value to number or return null
 * Used for chart data to prevent NaN
 */
export function toNumberOrNull(value: any): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === 'number') return isNaN(value) ? null : value;

  // Try parsing as number
  const num = Number(value);
  return isNaN(num) ? null : num;
}
