"""
Dynamic geocoding service using Nominatim (OpenStreetMap)
Free, no API key required, rate limit: 1 request/second
"""
import httpx
import asyncio
import re
from typing import Optional, Dict
from datetime import datetime


class GeocodingService:
    """
    Free geocoding using Nominatim (OpenStreetMap)
    No API key needed, rate limit: 1 request/second
    """
    
    BASE_URL = "https://nominatim.openstreetmap.org"
    
    def __init__(self):
        self.last_request_time = 0.0
        self.cache: Dict[str, Optional[Dict[str, float]]] = {}
        
    async def geocode(self, location: str) -> Optional[Dict[str, float]]:
        """
        Convert location string to coordinates
        
        Args:
            location: "Tokyo, Japan" or "123 Main St, San Francisco" or "Marina Bay Sands"
            
        Returns:
            {"lat": 35.6762, "lng": 139.6503, "display_name": "Tokyo, Japan"} or None
        """
        # Check cache first
        if location in self.cache:
            print(f"[Geocoding] Cache hit for: {location}")
            return self.cache[location]
        
        try:
            # Respect rate limit (1 req/sec for Nominatim)
            await self._rate_limit()
            
            print(f"[Geocoding] Requesting coordinates for: {location}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search",
                    params={
                        "q": location,
                        "format": "json",
                        "limit": 1,
                        "addressdetails": 1
                    },
                    headers={
                        "User-Agent": "GenerativeUIBrowser/1.0 (Educational Project)"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        result = data[0]
                        coords = {
                            "lat": float(result["lat"]),
                            "lng": float(result["lon"]),
                            "display_name": result.get("display_name", location)
                        }
                        
                        print(f"[Geocoding] ✓ Found: {coords['lat']}, {coords['lng']}")
                        
                        # Cache result
                        self.cache[location] = coords
                        return coords
                    else:
                        print(f"[Geocoding] ✗ No results for: {location}")
                else:
                    print(f"[Geocoding] ✗ HTTP {response.status_code} for: {location}")
                        
        except Exception as e:
            print(f"[Geocoding] ✗ Error for '{location}': {e}")
        
        # Cache failure to avoid retry
        self.cache[location] = None
        return None
    
    async def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Convert coordinates to location string
        
        Args:
            lat: 35.6762
            lng: 139.6503
            
        Returns:
            "Tokyo, Japan" or None
        """
        cache_key = f"{lat},{lng}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return cached.get("display_name") if cached else None
        
        try:
            await self._rate_limit()
            
            print(f"[Reverse Geocoding] Requesting address for: {lat}, {lng}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/reverse",
                    params={
                        "lat": lat,
                        "lon": lng,
                        "format": "json"
                    },
                    headers={
                        "User-Agent": "GenerativeUIBrowser/1.0 (Educational Project)"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "display_name" in data:
                        display_name = data["display_name"]
                        print(f"[Reverse Geocoding] ✓ Found: {display_name}")
                        
                        # Cache result
                        self.cache[cache_key] = {
                            "lat": lat,
                            "lng": lng,
                            "display_name": display_name
                        }
                        return display_name
                        
        except Exception as e:
            print(f"[Reverse Geocoding] ✗ Error for ({lat}, {lng}): {e}")
        
        self.cache[cache_key] = None
        return None
    
    async def geocode_batch(self, locations: list[str]) -> Dict[str, Optional[Dict[str, float]]]:
        """
        Geocode multiple locations with rate limiting
        
        Args:
            locations: ["Tokyo", "Paris", "New York"]
            
        Returns:
            {"Tokyo": {"lat": 35.6762, "lng": 139.6503}, ...}
        """
        results = {}
        
        for location in locations:
            coords = await self.geocode(location)
            results[location] = coords
            
        return results
    
    async def _rate_limit(self):
        """
        Enforce 1 request per second rate limit for Nominatim
        """
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < 1.0:
            wait_time = 1.0 - time_since_last
            print(f"[Geocoding] Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            
        self.last_request_time = asyncio.get_event_loop().time()
    
    def clear_cache(self):
        """Clear the geocoding cache"""
        self.cache.clear()
        print("[Geocoding] Cache cleared")


# Singleton instance
geocoding_service = GeocodingService()
