/**
 * AppPanel - Tri-Pane Layout Container (OpenAI-style)
 *
 * Layout:
 * - Left: EntityList (scrollable list of entities with key stats)
 * - Center: Primary visual (Map or main chart)
 * - Right: DetailPanel (selected entity details)
 *
 * Inspired by: 温泉コンシェルジュ / OpenAI ChatGPT built-in apps
 */

import { useState, useMemo, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Map as MapIcon, BarChart3, ChevronRight, Sparkles } from 'lucide-react';
import { EntityList } from './EntityList';
import { DetailPanel } from './DetailPanel';
import { MapWidget } from './MapWidget';
import { DynamicComponentRenderer } from './DynamicComponentRenderer';
import { useEntityStore } from '@/store/EntityStore';
import { useUIContext } from '@/contexts/UIContext';
import { ComponentSpec } from '@/types/api';

interface AppPanelProps {
  title?: string;
  subtitle?: string;
  components: ComponentSpec[];
  primaryEntityType?: string;
  onAction?: (action: any) => void;
  onDeleteEntity?: (entityId: string) => void;
  onAttributeChange?: (entityId: string, attributeName: string, newValue: any) => void;
  suggestedActions?: Array<{ label: string; query?: string; icon?: string }>;
  loadingActionId?: string | null;
  allEntities?: any[]; // Pass entities directly from parent
}

type CenterViewMode = 'map' | 'chart';

export const AppPanel = ({
  title,
  subtitle,
  components,
  primaryEntityType,
  onAction,
  onDeleteEntity,
  onAttributeChange,
  suggestedActions = [],
  loadingActionId,
  allEntities = [],
}: AppPanelProps) => {
  const entityStore = useEntityStore();
  const { setLocationPanel } = useUIContext();

  // Selection state for tri-pane synchronization
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [centerViewMode, setCenterViewMode] = useState<CenterViewMode>('map');
  const [isDetailPanelOpen, setIsDetailPanelOpen] = useState(true); // Start open

  // Get entities - ALWAYS filter through EntityStore to respect deleted entities
  const visibleEntities = useMemo(() => {
    // CRITICAL: Always use getVisibleEntities() to filter out deleted entities
    // This ensures delete/undo works correctly in all views
    return entityStore.getVisibleEntities();
  }, [entityStore, entityStore.version]);

  // Filter primary entities - entities with coordinates (destinations) or matching prefix
  const primaryEntities = useMemo(() => {
    if (!visibleEntities || visibleEntities.length === 0) return [];

    // Filter entities that are "primary" - have coordinates or type starts with "Destination"
    const destinations = visibleEntities.filter(e => {
      // Check if type contains "Destination" (handles Destination_Paris, Destination_Rome, etc.)
      const isDestination = e.type?.toLowerCase().includes('destination');

      // Check if entity has coordinates
      const hasCoords = e.attributes?.some((a: any) =>
        a.name === 'coordinates' && a.value?.lat && a.value?.lng
      );

      return isDestination || hasCoords;
    });

    console.log('[AppPanel] Primary entities (destinations):', destinations.length, destinations.map(e => e.public_identifier));
    return destinations.length > 0 ? destinations : visibleEntities.slice(0, 5);
  }, [visibleEntities]);

  // Auto-select first entity if none selected
  useEffect(() => {
    if (!selectedEntityId && primaryEntities.length > 0) {
      setSelectedEntityId(primaryEntities[0].id);
    }
  }, [primaryEntities, selectedEntityId]);

  // Get selected entity
  const selectedEntity = useMemo(() => {
    if (!selectedEntityId) return primaryEntities[0] || null;
    return visibleEntities.find(e => e.id === selectedEntityId) || null;
  }, [selectedEntityId, visibleEntities, primaryEntities]);

  // Aesthetic color palette for entities (soft, balanced)
  const entityColorPalette = ['#7dd3fc', '#c4b5fd', '#f9a8d4', '#facc15'];

  // Assign color to entity based on index
  const getEntityColor = (idx: number) => entityColorPalette[idx % entityColorPalette.length];

  // Extract map locations from entities - ALWAYS include attractions
  const mapLocations = useMemo(() => {
    const allLocations: any[] = [];

    primaryEntities.forEach((entity, idx) => {
      const coords = entity.attributes?.find((a: any) =>
        a.name === 'coordinates'
      )?.value;

      const entityColor = entity.color || getEntityColor(idx);

      // Add main destination marker
      if (coords?.lat && coords?.lng) {
        allLocations.push({
          id: entity.id,
          lat: coords.lat,
          lng: coords.lng,
          label: entity.public_identifier || entity.name || entity.id,
          description: `${entity.icon || ''} ${entity.public_identifier}`,
          color: entityColor,
          entityId: entity.id,
          entity: entity,
          isMainDestination: true,
        });
      }

      // Add attraction markers - use softer accent color
      const attractions = entity.attributes?.find((a: any) =>
        a.name === 'top_attractions' && Array.isArray(a.value)
      )?.value || [];

      attractions.forEach((attraction: any) => {
        if (attraction.coordinates?.lat && attraction.coordinates?.lng) {
          allLocations.push({
            id: `${entity.id}_${attraction.name?.replace(/\s+/g, '_') || 'attraction'}`,
            lat: attraction.coordinates.lat,
            lng: attraction.coordinates.lng,
            label: attraction.name || 'Attraction',
            description: attraction.description || `Part of ${entity.public_identifier}`,
            color: '#E8A85C', // Warm amber for attractions
            entityId: entity.id,
            entity: entity,
            isAttraction: true,
          });
        }
      });
    });

    console.log('[AppPanel] Extracted map locations from entities:', allLocations.length);
    return allLocations;
  }, [primaryEntities, components, visibleEntities]);

  // Extract all renderable components for Analysis view (charts, tables, expandable sections, etc.)
  // Exclude: metric_cards (shown in left panel), maps (shown in Map view), action_buttons (shown in chat)
  // CRITICAL: Also filter out components whose entity has been deleted
  const renderableComponents = useMemo(() => {
    const deletedIds = new Set(visibleEntities.length > 0 ?
      entityStore.getAllEntities().filter(e => !visibleEntities.find(v => v.id === e.id)).map(e => e.id) :
      []);

    const filtered = components.filter(c => {
      // Filter by type
      if (c.type === 'metric_card' || c.type === 'map' || c.type === 'action_button') {
        return false;
      }

      // Filter out components associated with deleted entities
      const entityId = c.props?.entityId;
      if (entityId && deletedIds.has(entityId)) {
        return false;
      }

      return true;
    });

    console.log('[AppPanel] Renderable components:', filtered.length, 'types:', filtered.map(c => c.type));
    return filtered;
  }, [components, visibleEntities, entityStore]);

  // Handle entity selection (unified for cards, map, list)
  const handleSelectEntity = useCallback((entityId: string) => {
    console.log('[AppPanel] Entity selected:', entityId);
    setSelectedEntityId(entityId);
    setIsDetailPanelOpen(true);
  }, []);

  // Handle map marker click
  const handleMapMarkerClick = useCallback((entityId: string) => {
    console.log('[AppPanel] Map marker clicked:', entityId);
    handleSelectEntity(entityId);
  }, [handleSelectEntity]);

  // Close detail panel
  const handleCloseDetail = useCallback(() => {
    setIsDetailPanelOpen(false);
  }, []);

  // Build entity map for components
  const entitiesById = useMemo(() => {
    const map: Record<string, any> = {};
    visibleEntities.forEach(e => { map[e.id] = e; });
    return map;
  }, [visibleEntities]);

  // Determine if we have data for each pane
  const hasMapData = mapLocations.length > 0;
  const hasComponentData = renderableComponents.length > 0;
  const hasCenterContent = hasMapData || hasComponentData;

  return (
    <div className="app-panel flex flex-col h-full bg-background rounded-2xl border border-border overflow-hidden shadow-xl">
      {/* Tri-Pane Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Pane: Entity List */}
        <div className="w-80 flex-shrink-0 border-r border-border bg-card/30 overflow-hidden flex flex-col">
          <EntityList
            entities={primaryEntities}
            selectedEntityId={selectedEntityId}
            onSelectEntity={handleSelectEntity}
            onDeleteEntity={onDeleteEntity}
          />
        </div>

        {/* Center Pane: Map or Chart */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* View toggle */}
          {hasMapData && hasComponentData && (
            <div className="flex items-center gap-1 p-2 border-b border-border bg-background/50">
              <button
                onClick={() => setCenterViewMode('map')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  centerViewMode === 'map'
                    ? 'bg-primary/10 text-primary border border-primary/30'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/10'
                }`}
              >
                <MapIcon className="h-3.5 w-3.5" />
                Map
              </button>
              <button
                onClick={() => setCenterViewMode('chart')}
                className={`relative flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  centerViewMode === 'chart'
                    ? 'bg-primary/10 text-primary border border-primary/30'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/10'
                }`}
              >
                <BarChart3 className="h-3.5 w-3.5" />
                Analysis
                {centerViewMode === 'map' && renderableComponents.length > 0 && (
                  <span className="absolute -top-1 -right-1 h-2 w-2 bg-primary rounded-full animate-pulse" />
                )}
              </button>
            </div>
          )}

          {/* Center content */}
          <div className="flex-1 overflow-hidden relative">
            <AnimatePresence mode="wait">
              {centerViewMode === 'map' && hasMapData ? (
                <motion.div
                  key="map"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0"
                >
                  <MapWidget
                    locations={mapLocations}
                    entities={visibleEntities}
                    onSelectEntity={handleMapMarkerClick}
                    zoom={5}
                    center={{ lat: 45, lng: 7 }}
                  />
                </motion.div>
              ) : hasComponentData && renderableComponents.length > 0 ? (
                <motion.div
                  key="analysis"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="p-6 h-full overflow-auto"
                >
                  {/* `tabular` gives every number in the dashboard tabular figures
                      so columns align (cascades to tables, charts, cards). */}
                  <div className="space-y-6 tabular">
                    {renderableComponents.map((component, idx) => (
                      <motion.div
                        key={`${component.type}-${idx}`}
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: Math.min(idx * 0.06, 0.5), duration: 0.35, ease: "easeOut" }}
                      >
                        <DynamicComponentRenderer
                          spec={component}
                          onAction={onAction}
                          entities={visibleEntities}
                          entityMap={entitiesById}
                        />
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              ) : hasMapData ? (
                <motion.div
                  key="map-fallback"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0"
                >
                  <MapWidget
                    locations={mapLocations}
                    entities={visibleEntities}
                    onSelectEntity={handleMapMarkerClick}
                    zoom={5}
                    center={{ lat: 45, lng: 7 }}
                  />
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center justify-center h-full text-muted-foreground"
                >
                  <div className="text-center">
                    <Sparkles className="h-12 w-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">Processing data...</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Right Pane: Detail Panel */}
        <AnimatePresence mode="wait">
          {isDetailPanelOpen && selectedEntity && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 360, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="flex-shrink-0 border-l border-border bg-card/50 overflow-hidden"
            >
              <DetailPanel
                entity={selectedEntity}
                onClose={handleCloseDetail}
                onAction={onAction}
                onAttributeChange={onAttributeChange}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Collapsed detail indicator */}
        {!isDetailPanelOpen && selectedEntity && (
          <button
            onClick={() => setIsDetailPanelOpen(true)}
            className="absolute right-0 top-1/2 -translate-y-1/2 bg-primary text-primary-foreground p-2 rounded-l-lg shadow-lg hover:bg-primary/90 transition-all"
          >
            <ChevronRight className="h-4 w-4 rotate-180" />
          </button>
        )}
      </div>
    </div>
  );
};
