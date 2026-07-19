import { useEffect, useRef, useMemo } from 'react';
import { MapPin, Info } from 'lucide-react';
import { Entity } from '@/types/entity';
import { extractEntityLocation, formatAttributeValue } from '@/utils/attributeIntelligence';

// Declare Leaflet global from CDN
declare const L: any;

interface LocationMarker {
  id: string;
  entity: Entity;
  position: [number, number];
  label: string;
  address?: string;
  details: Array<{ label: string; value: string; icon: string }>;
  type?: 'city' | 'attraction';  // Marker type
  parentEntity?: string;  // Parent entity name for attractions
  description?: string;  // For attraction descriptions
}

interface MapViewEnhancedProps {
  entities: Entity[];
  onSelectEntity?: (entity: Entity) => void;
}

// Component to auto-fit map bounds
const useMapBounds = (map: any, markers: LocationMarker[]) => {
  useEffect(() => {
    if (!map || markers.length === 0) return;

    const bounds = markers.map(m => m.position);
    
    if (bounds.length === 1) {
      map.setView(bounds[0], 12);
    } else if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, markers]);
};

export const MapView = ({ entities, onSelectEntity }: MapViewEnhancedProps) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);

  // Extract ALL location markers from ALL entities
  const markers = useMemo(() => {
    console.log('=== MAP VIEW DEBUG ===');
    console.log('Total entities:', entities.length);
    console.log('Entities:', entities.map(e => ({ id: e.id, name: e.public_identifier, type: e.type })));
    const allMarkers: LocationMarker[] = [];

    entities.forEach((entity, index) => {
      console.log(`Processing entity ${index + 1}:`, entity.public_identifier);
      console.log('  Entity attributes:', entity.attributes.map(a => a.name));
      const location = extractEntityLocation(entity);
      console.log('  Location extracted:', location);
      
      if (location) {
        // Extract key details for popup
        const details: Array<{ label: string; value: string; icon: string }> = [];

        // Add financial attributes
        entity.attributes.forEach(attr => {
          if (attr.widget === 'currency') {
            const formatted = formatAttributeValue(attr.value, 'currency');
            if (formatted !== '-') {
              details.push({
                label: attr.name.replace(/_/g, ' '),
                value: formatted,
                icon: '💰'
              });
            }
          } else if (attr.widget === 'rating') {
            const formatted = formatAttributeValue(attr.value, 'rating');
            if (formatted !== '-') {
              details.push({
                label: attr.name.replace(/_/g, ' '),
                value: formatted,
                icon: '⭐'
              });
            }
          } else if (attr.widget === 'date' && attr.name.toLowerCase().includes('date')) {
            const formatted = formatAttributeValue(attr.value, 'date');
            if (formatted !== '-') {
              details.push({
                label: attr.name.replace(/_/g, ' '),
                value: formatted,
                icon: '📅'
              });
            }
          }
        });

        const marker = {
          id: entity.id,
          entity,
          position: [location.lat, location.lng] as [number, number],
          label: entity.public_identifier,
          address: location.address,
          details: details.slice(0, 4), // Limit to 4 details for popup
          type: 'city' as const
        };
        console.log('  ✓ City marker created:', { label: marker.label, position: marker.position });
        allMarkers.push(marker);
        
        // EXTRACT ATTRACTION SUB-MARKERS from top_attractions array
        const attractionsAttr = entity.attributes.find(
          attr => attr.name === 'top_attractions' && Array.isArray(attr.value)
        );
        
        if (attractionsAttr && Array.isArray(attractionsAttr.value)) {
          console.log(`  → Found ${attractionsAttr.value.length} attractions in ${entity.public_identifier}`);
          console.log(`  → Raw attractions array:`, attractionsAttr.value);
          
          attractionsAttr.value.forEach((attraction: any, idx: number) => {
            // Handle both string arrays and object arrays
            if (typeof attraction === 'string') {
              console.log(`    [${idx}] String-only attraction: "${attraction}" - skipping (no coordinates)`);
              return; // Skip string-only entries
            }
            
            // It's an object - check for coordinates
            if (typeof attraction === 'object' && attraction !== null) {
              console.log(`    [${idx}] Checking attraction object:`, attraction.name);
              
              if (attraction.coordinates && typeof attraction.coordinates === 'object') {
                // Try to extract coordinates regardless of exact format
                const lat = attraction.coordinates.lat || attraction.coordinates.latitude;
                const lng = attraction.coordinates.lng || attraction.coordinates.longitude;
                
                if (typeof lat === 'number' && typeof lng === 'number') {
                  const attractionMarker = {
                    id: `${entity.id}-attraction-${idx}`,
                    entity,
                    position: [lat, lng] as [number, number],
                    label: attraction.name || `Attraction ${idx + 1}`,
                    description: attraction.description || '',
                    address: `${entity.public_identifier}, ${attraction.name}`,
                    details: [],
                    type: 'attraction' as const,
                    parentEntity: entity.public_identifier
                  };
                  
                  console.log(`    ✓ Attraction marker created: ${attractionMarker.label}`, attractionMarker.position);
                  allMarkers.push(attractionMarker);
                } else {
                  console.log(`    ✗ Invalid coordinate types - lat: ${typeof lat}, lng: ${typeof lng}`);
                }
              } else {
                console.log(`    ✗ No coordinates in attraction object`);
              }
            }
          });
        }
      } else {
        console.log('  ✗ No location found for entity');
      }
    });

    console.log('=== FINAL MARKER COUNT ===');
    console.log('Total markers (cities + attractions):', allMarkers.length);
    console.log('City markers:', allMarkers.filter(m => m.type === 'city').length);
    console.log('Attraction markers:', allMarkers.filter(m => m.type === 'attraction').length);
    return allMarkers;
  }, [entities]);

  // Calculate map center
  const center = useMemo((): [number, number] => {
    if (markers.length === 0) return [37.7749, -122.4194]; // SF default
    if (markers.length === 1) return markers[0].position;

    // Calculate average position
    const avgLat = markers.reduce((sum, m) => sum + m.position[0], 0) / markers.length;
    const avgLng = markers.reduce((sum, m) => sum + m.position[1], 0) / markers.length;
    return [avgLat, avgLng];
  }, [markers]);

  // Initialize map
  useEffect(() => {
    if (!mapRef.current || typeof L === 'undefined') return;

    // Initialize map if not already done
    if (!mapInstanceRef.current) {
      mapInstanceRef.current = L.map(mapRef.current, {
        zoomControl: true,
        scrollWheelZoom: true
      }).setView(center, 4);

      // Add OpenStreetMap tiles
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
      }).addTo(mapInstanceRef.current);
    }

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add new markers for each location
    markers.forEach((markerData, index) => {
      // Determine color and size based on marker type
      const isAttraction = markerData.type === 'attraction';
      const entityColor = markerData.entity.color || '#7dd3fc';
      
      // For attractions, use a lighter/different shade of the parent entity color
      const color = isAttraction 
        ? `${entityColor}CC`  // Add transparency to make lighter
        : entityColor;
      
      // Different sizes for city vs attraction markers
      const iconSize = isAttraction ? 20 : 32;
      const iconHeight = isAttraction ? 25 : 40;
      const centerSize = isAttraction ? 4 : 6;

      const customIcon = L.divIcon({
        html: `
          <div style="position: relative;">
            <svg width="${iconSize}" height="${iconHeight}" viewBox="0 0 ${iconSize} ${iconHeight}" xmlns="http://www.w3.org/2000/svg">
              <path d="M${iconSize/2} 0C${iconSize*0.225} 0 0 ${iconSize*0.225} 0 ${iconSize/2}c0 ${iconSize/2} ${iconSize/2} ${iconHeight-iconSize/2} ${iconSize/2} ${iconHeight-iconSize/2}s${iconSize/2}-${iconSize/2} ${iconSize/2}-${iconHeight-iconSize/2}c0-${iconSize*0.275}-${iconSize*0.225}-${iconSize/2}-${iconSize/2}-${iconSize/2}z" fill="${color}"/>
              <circle cx="${iconSize/2}" cy="${iconSize/2}" r="${centerSize}" fill="white"/>
            </svg>
            ${isAttraction ? `<div style="position:absolute; top:-8px; right:-8px; background:white; border-radius:50%; width:16px; height:16px; display:flex; align-items:center; justify-content:center; font-size:10px; box-shadow:0 1px 3px rgba(0,0,0,0.2);">📍</div>` : ''}
          </div>
        `,
        className: `custom-marker ${isAttraction ? 'attraction-marker' : 'city-marker'}`,
        iconSize: [iconSize, iconHeight],
        iconAnchor: [iconSize/2, iconHeight],
        popupAnchor: [0, -iconHeight]
      });

      const marker = L.marker(markerData.position, { icon: customIcon })
        .addTo(mapInstanceRef.current);

      // Create rich popup content - different for city vs attraction
      const popupContent = isAttraction ? `
        <div style="min-width: 220px; padding: 8px;">
          <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 2px solid #e5e7eb;">
            <div style="font-weight: 700; font-size: 15px; color: #111827; margin-bottom: 4px;">
              ${markerData.label}
            </div>
            <div style="font-size: 11px; color: #6b7280; display: flex; align-items: center; gap: 4px;">
              <span>📍</span>
              <span>${markerData.parentEntity}</span>
            </div>
          </div>
          
          ${markerData.description ? `
            <div style="font-size: 13px; color: #4b5563; line-height: 1.5; margin-bottom: 12px;">
              ${markerData.description}
            </div>
          ` : ''}
          
          <button
            onclick="console.log('[MapView] Attraction clicked:', '${markerData.id}'); window.dispatchEvent(new CustomEvent('marker-click', { detail: '${markerData.entity.id}' }))"
            style="
              width: 100%;
              padding: 6px 12px;
              background: ${entityColor};
              color: white;
              border: none;
              border-radius: 6px;
              font-size: 12px;
              font-weight: 600;
              cursor: pointer;
              transition: all 0.15s ease;
            "
            onmouseover="this.style.opacity='0.9'"
            onmouseout="this.style.opacity='1'"
          >
            View ${markerData.parentEntity}
          </button>
        </div>
      ` : `
        <div style="min-width: 250px; padding: 8px;">
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 2px solid #e5e7eb;">
            <span style="font-size: 32px;">${markerData.entity.icon}</span>
            <div>
              <div style="font-weight: 700; font-size: 16px; color: #111827;">
                ${markerData.label}
              </div>
              <div style="font-size: 12px; color: #6b7280; text-transform: capitalize;">
                ${markerData.entity.type.replace(/_/g, ' ')}
              </div>
            </div>
          </div>
          
          ${markerData.address ? `
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; color: #6b7280; font-size: 13px;">
              <span>📍</span>
              <span>${markerData.address}</span>
            </div>
          ` : ''}
          
          ${markerData.details.length > 0 ? `
            <div style="display: grid; gap: 8px; margin-bottom: 12px;">
              ${markerData.details.map(detail => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 8px; background: #f9fafb; border-radius: 6px;">
                  <span style="font-size: 12px; color: #6b7280; display: flex; align-items: center; gap: 6px; text-transform: capitalize;">
                    <span>${detail.icon}</span>
                    ${detail.label}
                  </span>
                  <span style="font-size: 13px; font-weight: 600; color: #111827;">
                    ${detail.value}
                  </span>
                </div>
              `).join('')}
            </div>
          ` : ''}
          
          <button
            onclick="console.log('[MapView] Button clicked for entity:', '${markerData.entity.id}'); window.dispatchEvent(new CustomEvent('marker-click', { detail: '${markerData.entity.id}' }))"
            style="
              width: 100%;
              padding: 8px 16px;
              background: linear-gradient(to right, #7dd3fc, #38bdf8);
              color: #050608;
              border: none;
              border-radius: 8px;
              font-size: 14px;
              font-weight: 600;
              cursor: pointer;
              transition: all 0.15s ease;
              display: flex;
              align-items: center;
              justify-content: center;
              gap: 6px;
            "
            onmouseover="this.style.background='linear-gradient(to right, #38bdf8, #0ea5e9)'"
            onmouseout="this.style.background='linear-gradient(to right, #7dd3fc, #38bdf8)'"
          >
            <span>👁️</span>
            View Details
          </button>
        </div>
      `;

      marker.bindPopup(popupContent, {
        maxWidth: 300,
        className: 'custom-popup'
      });

      markersRef.current.push(marker);
    });

    // Auto-fit bounds
    if (markers.length > 0) {
      const bounds = markers.map(m => m.position);
      if (bounds.length === 1) {
        mapInstanceRef.current.setView(bounds[0], 12);
      } else if (bounds.length > 1) {
        mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50] });
      }
    }

    // Cleanup
    return () => {
      if (mapInstanceRef.current) {
        markersRef.current.forEach(marker => marker.remove());
        markersRef.current = [];
      }
    };
  }, [markers, center]);

  // Handle marker click events
  useEffect(() => {
    console.log('[MapView] Setting up marker-click event listener');
    
    const handleMarkerClick = (event: CustomEvent) => {
      console.log('[MapView] marker-click event received:', event.detail);
      const entityId = event.detail;
      const entity = entities.find(e => e.id === entityId);
      console.log('[MapView] Found entity:', entity?.public_identifier);
      
      if (entity && onSelectEntity) {
        console.log('[MapView] Calling onSelectEntity');
        onSelectEntity(entity);
      } else {
        console.warn('[MapView] Cannot select entity - entity or onSelectEntity missing');
      }
    };

    window.addEventListener('marker-click' as any, handleMarkerClick as any);
    console.log('[MapView] Event listener attached');
    
    return () => {
      console.log('[MapView] Removing marker-click event listener');
      window.removeEventListener('marker-click' as any, handleMarkerClick as any);
    };
  }, [entities, onSelectEntity]);

  // No locations found
  if (markers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border-2 border-dashed border-blue-300">
        <MapPin className="w-16 h-16 text-blue-400 mb-4" />
        <h3 className="text-lg font-bold text-gray-900 mb-2">
          No Locations Found
        </h3>
        <p className="text-sm text-gray-600 text-center max-w-md">
          Add location data to your entities to see them on the map. The system will automatically detect and display any entity with location attributes.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full h-full space-y-4">
      {/* Map Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-blue-600" />
              Map View
            </h3>
            <p className="text-sm text-gray-600">
              {markers.length} {markers.length === 1 ? 'location' : 'locations'} displayed
            </p>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span>Click markers for details</span>
            </div>
          </div>
        </div>
      </div>

      {/* Map Container - Responsive */}
      <div className="relative rounded-lg overflow-hidden shadow-lg border border-gray-200">
        <div
          ref={mapRef}
          className="w-full"
          style={{ 
            height: 'calc(100vh - 280px)', 
            minHeight: '400px',
            maxHeight: '800px'
          }}
        />
      </div>
      
      {/* Mobile Responsive Adjustments */}
      <style>{`
        @media (max-width: 768px) {
          .custom-popup .leaflet-popup-content {
            min-width: 200px !important;
          }
        }
        
        .leaflet-container {
          font-family: inherit;
        }
        
        .custom-popup .leaflet-popup-content-wrapper {
          border-radius: 12px;
          box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        
        .custom-marker {
          transition: transform 0.15s ease;
        }

        .custom-marker:hover {
          transform: scale(1.1);
          z-index: 1000 !important;
        }
      `}</style>
    </div>
  );
};
