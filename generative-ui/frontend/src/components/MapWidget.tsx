/**
 * MapWidget - Interactive Map with Click Handlers
 *
 * Features:
 * - Proper containment and sizing (no overflow)
 * - Marker click selects entity in right detail panel
 * - Auto-zoom to clicked marker
 * - Emits events for related module updates
 * - ResizeObserver for dynamic sizing
 */

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { MapPin } from 'lucide-react';
import { useUIContext } from '@/contexts/UIContext';
import { bus } from '@/utils/eventBus';
import { updateRelated } from '@/utils/relations';
import { generateStableKey } from '@/utils/formatters';

// Declare Leaflet global from CDN
declare const L: any;

interface Location {
  id: string;
  lat: number;
  lng: number;
  label: string;
  description?: string;
  color?: string;
  entityId?: string; // Explicit entity ID for mapping
  entity?: any; // Full entity object for LocationPanel
}

interface MapWidgetProps {
  locations: Location[];
  zoom?: number;
  center?: { lat: number; lng: number };
  height?: number;
  mapboxToken?: string;
  entities?: any[]; // All entities with location data
  onSelectEntity?: (entityId: string) => void;
}

export const MapWidget = ({
  locations,
  zoom = 10,
  center,
  height = 400,
  entities = [],
  onSelectEntity,
}: MapWidgetProps) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapWrapperRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const [isMapReady, setIsMapReady] = useState(false);

  const { setSelected } = useUIContext();

  // Filter valid locations AND locations whose entities still exist (not deleted)
  const validLocations = locations.filter(
    (loc) => {
      // Must have valid coordinates
      const hasValidCoords = typeof loc.lat === 'number' &&
        typeof loc.lng === 'number' &&
        !isNaN(loc.lat) &&
        !isNaN(loc.lng);

      if (!hasValidCoords) return false;

      // If location has explicit entity/entityId, verify entity exists
      if (loc.entityId) {
        const exists = entities.some(e => e.id === loc.entityId);
        if (!exists) {
          console.log(`[MapWidget] Filtering out location "${loc.label}" - entity "${loc.entityId}" deleted`);
          return false;
        }
      }

      return true;
    }
  );

  /**
   * Find entity for a given location using multiple strategies
   * NOW USES SAME LOGIC AS DynamicComponentRenderer for consistency
   */
  const findEntityForLocation = (loc: Location): any | null => {
    // Debug: Log what properties the location has
    console.log(`[MapWidget] Finding entity for location:`, {
      id: loc.id,
      label: loc.label,
      hasEntityId: !!loc.entityId,
      hasEntity: !!loc.entity,
      entityCount: entities.length
    });

    // Strategy 1: Explicit entityId (set by DynamicComponentRenderer)
    if (loc.entityId) {
      const found = entities.find((e: any) => e.id === loc.entityId);
      if (found) {
        console.log(`[MapWidget] ✓ Found via entityId "${loc.entityId}" → "${found.id}"`);
        return found;
      }
    }

    // Strategy 2: Entity object passed directly (set by DynamicComponentRenderer)
    if (loc.entity) {
      console.log(`[MapWidget] ✓ Using pre-linked entity "${loc.entity.id}"`);
      return loc.entity;
    }

    // Strategy 3: Direct ID match
    const directMatch = entities.find((e: any) => e.id === loc.id);
    if (directMatch) {
      console.log(`[MapWidget] Direct ID match "${loc.id}" → "${directMatch.id}"`);
      return directMatch;
    }

    // Strategy 4: Substring match with word boundaries (same as DynamicComponentRenderer)
    if (loc.id && entities.length > 0) {
      const normalizedLocId = String(loc.id).toLowerCase().trim();
      const substringMatch = entities.find((e: any) => {
        const normalizedEntityId = e.id.toLowerCase().trim();
        return normalizedEntityId === `destination_${normalizedLocId}` ||
               normalizedEntityId === `${normalizedLocId}` ||
               normalizedEntityId.includes(`_${normalizedLocId}_`) ||
               normalizedEntityId.includes(`_${normalizedLocId}`) ||
               normalizedEntityId.includes(`${normalizedLocId}_`);
      });

      if (substringMatch) {
        console.log(`[MapWidget] Substring match "${loc.id}" → entity "${substringMatch.id}"`);
        return substringMatch;
      }
    }

    // Strategy 5: Match on public_identifier (check both top-level property AND attributes)
    if (loc.label && entities.length > 0) {
      const normalizedLabel = loc.label.toLowerCase().trim();

      const publicIdMatch = entities.find((e: any) => {
        // Check top-level public_identifier property
        const topLevelPublicId = (e.public_identifier || '').toLowerCase().trim();

        // Also check in attributes
        const attrPublicId = e.attributes?.find((a: any) =>
          a.function === 'publicIdentifier'
        )?.value?.toLowerCase().trim() || '';

        const entityName = (e.name || e.label || '').toLowerCase().trim();

        return normalizedLabel === topLevelPublicId ||
               normalizedLabel === attrPublicId ||
               normalizedLabel === entityName ||
               (topLevelPublicId && normalizedLabel.includes(topLevelPublicId)) ||
               (attrPublicId && normalizedLabel.includes(attrPublicId)) ||
               (entityName && normalizedLabel.includes(entityName));
      });

      if (publicIdMatch) {
        console.log(`[MapWidget] Public ID match "${loc.label}" → entity "${publicIdMatch.id}"`);
        return publicIdMatch;
      }
    }

    // Strategy 5: Nearest coordinate match (within 0.1° radius)
    if (entities.length > 0) {
      const nearby = entities.find((e: any) => {
        const coords = e.attributes?.find((a: any) =>
          a.name === 'coordinates' && a.value?.lat && a.value?.lng
        )?.value;

        if (!coords) return false;

        const distance = Math.sqrt(
          Math.pow(coords.lat - loc.lat, 2) +
          Math.pow(coords.lng - loc.lng, 2)
        );

        return distance < 0.1; // ~11km radius
      });

      if (nearby) {
        console.log(`[MapWidget] Coordinate match for "${loc.label}" → entity "${nearby.id}"`);
        return nearby;
      }
    }

    console.warn(`[MapWidget] No entity found for location: ${loc.id} (${loc.label})`);
    return null;
  };

  // Initialize map with proper sizing guards
  useEffect(() => {
    if (!mapContainerRef.current || !mapWrapperRef.current || validLocations.length === 0) {
      return;
    }

    // Load Leaflet if not already loaded
    if (typeof L === 'undefined') {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(link);

      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.onload = () => {
        // Wait for container to have size before initializing
        waitForContainerSize();
      };
      document.head.appendChild(script);
    } else {
      waitForContainerSize();
    }

    function waitForContainerSize() {
      if (!mapWrapperRef.current) return;

      const checkSize = () => {
        const rect = mapWrapperRef.current!.getBoundingClientRect();

        if (rect.width > 0 && rect.height > 0) {
          initMap();
        } else {
          // Container not yet sized, wait for next frame
          requestAnimationFrame(checkSize);
        }
      };

      checkSize();
    }

    function initMap() {
      if (!mapContainerRef.current || !mapWrapperRef.current) return;

      // Clean up existing map
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) {
          console.warn('[MapWidget] Error removing old map:', e);
        }
        mapInstanceRef.current = null;
      }

      // Verify container has size
      const rect = mapWrapperRef.current.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) {
        console.warn('[MapWidget] Container has zero size, aborting map init');
        return;
      }

      try {
        const mapCenter: [number, number] = center
          ? [center.lat, center.lng]
          : [validLocations[0].lat, validLocations[0].lng];

        const map = L.map(mapContainerRef.current, {
          zoomControl: true,
          attributionControl: true,
        }).setView(mapCenter, zoom);

        mapInstanceRef.current = map;

        // Add OpenStreetMap tiles
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
          attribution: '© OpenStreetMap'
        }).addTo(map);

        // Add markers with entity mapping
        markersRef.current = validLocations.map((loc) => {
          const marker = L.marker([loc.lat, loc.lng], {
            icon: L.divIcon({
              className: 'custom-marker',
              html: `<div style="color: ${loc.color || '#7dd3fc'}; font-size: 24px; cursor: pointer;">📍</div>`,
              iconSize: [30, 30],
              iconAnchor: [15, 30]
            })
          }).addTo(map);

          // Bind popup
          const popupContent = `
            <div style="min-width: 150px;">
              <h3 style="font-weight: 600; margin-bottom: 4px;">${loc.label}</h3>
              ${loc.description ? `<p style="font-size: 12px; color: #666; margin-bottom: 4px;">${loc.description}</p>` : ''}
              <p style="font-size: 11px; color: #999;">${loc.lat.toFixed(4)}, ${loc.lng.toFixed(4)}</p>
            </div>
          `;
          marker.bindPopup(popupContent);

          // Click handler with correct entity mapping
          marker.on('click', () => {
            const entity = findEntityForLocation(loc);

            console.log('[MapWidget] Marker clicked:', {
              locationId: loc.id,
              locationLabel: loc.label,
              entityFound: entity?.id || 'none'
            });

            // Emit analytics event
            bus.emit('MAP_MARKER_CLICKED', {
              locationId: loc.id,
              entityId: entity?.id || loc.id,
              lat: loc.lat,
              lng: loc.lng,
            });

            // Update selection context
            const moduleId = `map_marker_${entity?.id || loc.id}`;
            setSelected(entity?.id || loc.id, moduleId);

            // Fly to marker
            if (mapInstanceRef.current) {
              mapInstanceRef.current.flyTo([loc.lat, loc.lng], 13, {
                animate: true,
                duration: 0.5,
              });
            }

            // Update right detail panel (NOT a separate overlay)
            if (onSelectEntity && entity) {
              console.log('[MapWidget] Selecting entity in detail panel:', entity.id);
              onSelectEntity(entity.id);
            } else {
              console.warn(`[MapWidget] Cannot select: no entity for location "${loc.label}"`);
            }

            // Highlight related components
            updateRelated(moduleId, { reason: 'map-click' });
          });

          return marker;
        });

        // Fit bounds if multiple locations, with size check
        if (validLocations.length > 1 && mapInstanceRef.current) {
          setTimeout(() => {
            if (!mapInstanceRef.current) return;

            try {
              const bounds = validLocations.map(loc => [loc.lat, loc.lng] as [number, number]);
              mapInstanceRef.current.fitBounds(bounds, {
                padding: [50, 50],
                maxZoom: 12
              });
            } catch (e) {
              console.warn('[MapWidget] Error fitting bounds:', e);
            }
          }, 100);
        }

        setIsMapReady(true);
      } catch (error) {
        console.error('[MapWidget] Error initializing map:', error);
        setIsMapReady(false);
      }
    }

    return () => {
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) {
          console.warn('[MapWidget] Error on cleanup:', e);
        }
        mapInstanceRef.current = null;
      }
    };
  }, [validLocations.length, center?.lat, center?.lng, zoom, entities.length]); // Re-init when entities load

  // Handle resize with invalidateSize
  useEffect(() => {
    if (!mapWrapperRef.current || !isMapReady) return;

    const resizeHandler = () => {
      if (mapInstanceRef.current) {
        setTimeout(() => {
          try {
            mapInstanceRef.current?.invalidateSize();
          } catch (e) {
            console.warn('[MapWidget] Error on invalidateSize:', e);
          }
        }, 120);
      }
    };

    // ResizeObserver for container size changes
    resizeObserverRef.current = new ResizeObserver(resizeHandler);
    resizeObserverRef.current.observe(mapWrapperRef.current);

    // Window resize handler
    window.addEventListener('resize', resizeHandler);

    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
      window.removeEventListener('resize', resizeHandler);
    };
  }, [isMapReady]);

  if (validLocations.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-border bg-card p-6"
        style={{ height: `clamp(280px, 45vh, 520px)` }}
      >
        <div className="flex h-full flex-col items-center justify-center text-center">
          <MapPin className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">No Locations</h3>
          <p className="text-sm text-muted-foreground">No valid coordinates provided</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="rounded-2xl border border-border overflow-hidden h-full w-full"
    >
      <div
        ref={mapWrapperRef}
        className="map-wrap"
        style={{
          position: 'relative',
          height: '100%',
          width: '100%',
          minHeight: '300px',
          overflow: 'hidden',
          borderRadius: '16px',
          background: 'hsl(var(--card))'
        }}
      >
        <div
          ref={mapContainerRef}
          style={{
            width: '100%',
            height: '100%',
            position: 'relative',
            zIndex: 0
          }}
        />
      </div>
    </motion.div>
  );
};
