/**
 * Frontend geocoding using Nominatim (OpenStreetMap)
 * Only used as fallback if backend didn't provide coordinates
 * 
 * Usage:
 * const coords = await geocode("Tokyo, Japan");
 * // Returns: { lat: 35.6762, lng: 139.6503 } or null
 */

const NOMINATIM_URL = 'https://nominatim.openstreetmap.org';

// Cache to avoid repeated requests
const geocodeCache = new Map<string, { lat: number; lng: number } | null>();

// Rate limiting: last request timestamp
let lastRequestTime = 0;

/**
 * Geocode a location string to coordinates
 * Uses Nominatim API with rate limiting (1 req/sec)
 */
export async function geocode(location: string): Promise<{ lat: number; lng: number } | null> {
  console.log(`[Frontend Geocoding] Request for: "${location}"`);
  
  // Check cache
  if (geocodeCache.has(location)) {
    const cached = geocodeCache.get(location);
    console.log(`[Frontend Geocoding] Cache hit:`, cached);
    return cached || null;
  }
  
  try {
    // Rate limiting: wait at least 1 second between requests
    const now = Date.now();
    const timeSinceLast = now - lastRequestTime;
    
    if (timeSinceLast < 1000) {
      const waitTime = 1000 - timeSinceLast;
      console.log(`[Frontend Geocoding] Rate limiting: waiting ${waitTime}ms`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    lastRequestTime = Date.now();
    
    console.log(`[Frontend Geocoding] Calling Nominatim API...`);
    
    const response = await fetch(
      `${NOMINATIM_URL}/search?` + new URLSearchParams({
        q: location,
        format: 'json',
        limit: '1'
      }),
      {
        headers: {
          'User-Agent': 'GenerativeUIBrowser/1.0 (Educational Project)'
        }
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      
      if (data && Array.isArray(data) && data.length > 0) {
        const result = data[0];
        const coords = {
          lat: parseFloat(result.lat),
          lng: parseFloat(result.lon)
        };
        
        console.log(`[Frontend Geocoding] ✓ Found:`, coords);
        
        // Cache result
        geocodeCache.set(location, coords);
        return coords;
      } else {
        console.warn(`[Frontend Geocoding] ✗ No results for: "${location}"`);
      }
    } else {
      console.error(`[Frontend Geocoding] ✗ HTTP ${response.status}`);
    }
  } catch (error) {
    console.error(`[Frontend Geocoding] ✗ Error:`, error);
  }
  
  // Cache failure to avoid retrying
  geocodeCache.set(location, null);
  return null;
}

/**
 * Reverse geocode coordinates to location string
 */
export async function reverseGeocode(lat: number, lng: number): Promise<string | null> {
  const cacheKey = `${lat},${lng}`;
  console.log(`[Frontend Reverse Geocoding] Request for: ${cacheKey}`);
  
  // Check cache
  if (geocodeCache.has(cacheKey)) {
    const cached = geocodeCache.get(cacheKey);
    return cached ? JSON.stringify(cached) : null;
  }
  
  try {
    // Rate limiting
    const now = Date.now();
    const timeSinceLast = now - lastRequestTime;
    
    if (timeSinceLast < 1000) {
      await new Promise(resolve => setTimeout(resolve, 1000 - timeSinceLast));
    }
    
    lastRequestTime = Date.now();
    
    const response = await fetch(
      `${NOMINATIM_URL}/reverse?` + new URLSearchParams({
        lat: lat.toString(),
        lon: lng.toString(),
        format: 'json'
      }),
      {
        headers: {
          'User-Agent': 'GenerativeUIBrowser/1.0 (Educational Project)'
        }
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      
      if (data && data.display_name) {
        console.log(`[Frontend Reverse Geocoding] ✓ Found:`, data.display_name);
        return data.display_name;
      }
    }
  } catch (error) {
    console.error(`[Frontend Reverse Geocoding] ✗ Error:`, error);
  }
  
  return null;
}

/**
 * Batch geocode multiple locations
 * Uses rate limiting to avoid overwhelming API
 */
export async function geocodeBatch(locations: string[]): Promise<Map<string, { lat: number; lng: number } | null>> {
  console.log(`[Frontend Geocoding] Batch request for ${locations.length} locations`);
  
  const results = new Map<string, { lat: number; lng: number } | null>();
  
  for (const location of locations) {
    const coords = await geocode(location);
    results.set(location, coords);
  }
  
  console.log(`[Frontend Geocoding] Batch complete: ${results.size} results`);
  return results;
}

/**
 * Clear the geocoding cache
 */
export function clearGeocodeCache() {
  geocodeCache.clear();
  console.log('[Frontend Geocoding] Cache cleared');
}
