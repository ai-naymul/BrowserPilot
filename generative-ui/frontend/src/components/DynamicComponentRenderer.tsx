import { motion } from "framer-motion";
import { ComponentSpec } from "@/types/api";
import { MetricCard } from "./MetricCard";
import { ActionButton } from "./ActionButton";
import { ChartWidget } from "./ChartWidget";
import { BarChartWidget } from "./BarChartWidget";
import { ComparisonTable } from "./ComparisonTable";
import { CollapsibleSection } from "./CollapsibleSection";
import { NewsHighlight } from "./NewsHighlight";
import { MapWidget } from "./MapWidget";
import { DataGrid } from "./DataGrid";
import { X } from "lucide-react";
import * as LucideIcons from "lucide-react";
import { bus } from "@/utils/eventBus";
import { useState, useEffect } from "react";
import { matchComponentKeyToEntity, matchLocationToEntity } from "@/utils/aiEntityMatcher";

interface DynamicComponentRendererProps {
  spec: ComponentSpec;
  onAction?: (action: any) => void;
  onDelete?: (componentKey: string) => void;
  // NEW: Entity context for enhanced components
  entities?: any[]; // All entities for relationships
  entityMap?: Record<string, any>; // Quick lookup by entity ID
}

/**
 * Icon Mapper - Converts icon name strings to React components
 */
const getIconComponent = (iconName?: string) => {
  if (!iconName) return undefined;
  
  // Map icon name to Lucide icon component
  const IconComponent = (LucideIcons as any)[iconName];
  
  if (!IconComponent) {
    console.warn(`Icon "${iconName}" not found in lucide-react`);
    return undefined;
  }
  
  return IconComponent;
};

/**
 * Extract Entity ID from Component Key
 *
 * Backend components have keys like "metric-tokyo-total" but don't include entityId.
 * This function extracts entity identifiers from keys and matches them to actual entity IDs.
 *
 * Examples:
 * - "metric-tokyo-total" → "destination_tokyo"
 * - "metric-barcelona-total" → "destination_barcelona"
 * - "tokyo-map" → "destination_tokyo"
 * - "trip-planner-card" → "trip_planner_1"
 */
const extractEntityIdFromKey = (key: string, entities: any[]): string | undefined => {
  if (!key || entities.length === 0) return undefined;

  // Normalize key: lowercase, remove special chars
  const normalizedKey = key.toLowerCase();

  // Strategy 1: Try exact match first (for keys that might be entity IDs)
  const exactMatch = entities.find(e => e.id === key);
  if (exactMatch) {
    console.log(`[EntityExtractor] Exact match "${key}" → "${exactMatch.id}"`);
    return exactMatch.id;
  }

  // Strategy 2: Extract potential entity name from key patterns
  // Patterns: "metric-{name}-{suffix}", "metric-{name}", "{name}-map", "{type}-{name}-card"
  const patterns = [
    /metric-(\w+)$/,           // metric-paris → paris (no suffix)
    /metric-(\w+)-/,           // metric-tokyo-total → tokyo
    /(\w+)-map/,               // tokyo-map → tokyo
    /(\w+)-card/,              // tokyo-card → tokyo
    /card-(\w+)/,              // card-tokyo → tokyo
    /-(\w+)-/,                 // any-tokyo-any → tokyo
  ];

  for (const pattern of patterns) {
    const match = normalizedKey.match(pattern);
    if (match && match[1]) {
      const extractedName = match[1];

      // IMPORTANT: Try MOST SPECIFIC matches first
      // 1. Try exact entity ID match with underscore
      let foundEntity = entities.find(e => {
        const entityId = e.id.toLowerCase();
        return entityId === `${extractedName}` ||
               entityId === `destination_${extractedName}` ||
               entityId === `${extractedName}_destination`;
      });

      if (foundEntity) {
        console.log(`[EntityExtractor] Direct match "${key}" → "${foundEntity.id}" (extracted: ${extractedName})`);
        return foundEntity.id;
      }

      // 2. Try matching against public_identifier (city name)
      foundEntity = entities.find(e => {
        const publicId = (e.public_identifier || '').toLowerCase();
        const publicIdFirst = publicId.split(',')[0].trim(); // "Paris, France" → "paris"
        return publicIdFirst === extractedName;
      });

      if (foundEntity) {
        console.log(`[EntityExtractor] Public ID match "${key}" → "${foundEntity.id}" (extracted: ${extractedName})`);
        return foundEntity.id;
      }

      // 3. Try substring match in entity ID (but prefer exact boundaries)
      foundEntity = entities.find(e => {
        const entityId = e.id.toLowerCase();
        // Only match if extracted name is a complete word boundary in entity ID
        return entityId.includes(`_${extractedName}_`) ||
               entityId.includes(`_${extractedName}`) ||
               entityId.includes(`${extractedName}_`);
      });

      if (foundEntity) {
        console.log(`[EntityExtractor] Substring match "${key}" → "${foundEntity.id}" (extracted: ${extractedName})`);
        return foundEntity.id;
      }
    }
  }

  // Strategy 3: Fuzzy match - check if any entity ID appears in the key
  for (const entity of entities) {
    const entityId = entity.id.toLowerCase();
    const entityName = (entity.name || entity.label || '').toLowerCase();

    if (normalizedKey.includes(entityId) ||
        (entityName && normalizedKey.includes(entityName))) {
      console.log(`[EntityExtractor] Fuzzy matched "${key}" → "${entity.id}"`);
      return entity.id;
    }
  }

  // No match found - will try AI fallback
  // Note: Don't warn here - AI fallback will determine if this is aggregate or unmatched
  console.log(`[EntityExtractor] No hardcoded match for "${key}" - will try AI fallback`);
  return undefined;
};

/**
 * Component Registry - Maps component type strings to React components
 *
 * This is the heart of the dynamic UI system. Add new components here
 * to make them available for LLM-generated UIs.
 */
const COMPONENT_REGISTRY: Record<string, React.ComponentType<any>> = {
  // Main components
  metric_card: MetricCard,
  action_button: ActionButton,
  
  // Chart components
  line_chart: ChartWidget,
  area_chart: (props: any) => <ChartWidget {...props} chartType="area" />,
  pie_chart: (props: any) => <ChartWidget {...props} chartType="pie" />,
  scatter_chart: (props: any) => <ChartWidget {...props} chartType="scatter" />,
  bar_chart: BarChartWidget,
  
  // Data components
  comparison_table: ComparisonTable,
  data_grid: DataGrid,
  
  // Interactive components
  expandable_section: CollapsibleSection,
  news_highlight: NewsHighlight,
  map: MapWidget,
  
  // Layout components
  text: ({ children, className }: any) => (
    <div className={className || "text-foreground"}>{children}</div>
  ),
  divider: () => <hr className="my-4 border-border" />,
  spacer: ({ height = 16 }: any) => <div style={{ height: `${height}px` }} />,
  
  // Container components
  grid: ({ children, columns = 3, gap = 16, className }: any) => (
    <div 
      className={className || "grid"}
      style={{ 
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
        gap: `${gap}px`
      }}
    >
      {children}
    </div>
  ),
  stack: ({ children, gap = 16, className }: any) => (
    <div 
      className={className || "flex flex-col"}
      style={{ gap: `${gap}px` }}
    >
      {children}
    </div>
  ),
};

/**
 * DynamicComponentRenderer - Renders component specs dynamically
 * 
 * This component:
 * 1. Looks up the component type in the registry
 * 2. Recursively renders children
 * 3. Passes action handlers to interactive components
 * 4. Shows error state for unknown components
 */
export const DynamicComponentRenderer = ({
  spec,
  onAction,
  onDelete,
  entities = [],
  entityMap = {},
}: DynamicComponentRendererProps) => {
  // State for AI-matched entity ID (used when hardcoded matching fails)
  const [aiMatchedEntityId, setAiMatchedEntityId] = useState<string | null | undefined>(undefined);
  const [isAggregate, setIsAggregate] = useState(false);
  const [aiMatchingAttempted, setAiMatchingAttempted] = useState(false);

  // Enable AI matching via environment variable (default: disabled for performance)
  const AI_MATCHING_ENABLED = import.meta.env.VITE_ENABLE_AI_MATCHING === 'true';

  const Component = COMPONENT_REGISTRY[spec.type];

  // Entity matching - tries hardcoded first, optionally falls back to AI
  useEffect(() => {
    // Only try matching if we have a key and entities
    if (!spec.key || entities.length === 0) {
      setAiMatchedEntityId(undefined);
      return;
    }

    // Skip if already attempted matching for this key
    if (aiMatchingAttempted) return;

    // Skip matching if component already has entityId in props
    if (spec.props.entityId) {
      setAiMatchedEntityId(spec.props.entityId);
      setAiMatchingAttempted(true);
      return;
    }

    // Try hardcoded matching first (fast, always enabled)
    const hardcodedMatch = extractEntityIdFromKey(spec.key, entities);

    if (hardcodedMatch) {
      // Hardcoded match succeeded - use it
      setAiMatchedEntityId(hardcodedMatch);
      setAiMatchingAttempted(true);
      return;
    }

    // Hardcoded matching failed
    // Check if this looks like an aggregate component (comparison/analysis)
    const aggregateKeywords = ['winner', 'comparison', 'compare', 'analysis', 'breakdown', 'section', 'chart', 'table'];
    const isLikelyAggregate = aggregateKeywords.some(keyword =>
      spec.key.toLowerCase().includes(keyword)
    );

    if (isLikelyAggregate) {
      // Likely an aggregate component - suppress warnings
      console.log(`[DynamicRenderer] "${spec.key}" appears to be an aggregate component (no single entity)`);
      setIsAggregate(true);
      setAiMatchedEntityId(null);
      setAiMatchingAttempted(true);
      return;
    }

    // AI matching fallback (optional, requires backend)
    if (AI_MATCHING_ENABLED) {
      console.log(`[DynamicRenderer] Hardcoded match failed for key "${spec.key}" - trying AI matching`);

      matchComponentKeyToEntity(spec.key, spec.props, entities)
        .then(result => {
          if (result.is_aggregate) {
            console.log(`[DynamicRenderer] AI determined "${spec.key}" is an aggregate component`);
            setIsAggregate(true);
            setAiMatchedEntityId(null);
          } else if (result.entity_id) {
            console.log(`[DynamicRenderer] ✓ AI matched "${spec.key}" → "${result.entity_id}"`);
            setAiMatchedEntityId(result.entity_id);
          } else {
            console.log(`[DynamicRenderer] No entity match for key "${spec.key}"`);
            setAiMatchedEntityId(null);
          }
          setAiMatchingAttempted(true);
        })
        .catch(error => {
          console.log(`[DynamicRenderer] AI matching unavailable for "${spec.key}" (backend may not be running)`);
          setAiMatchedEntityId(null);
          setAiMatchingAttempted(true);
        });
    } else {
      // AI matching disabled - just mark as attempted
      console.log(`[DynamicRenderer] No entity match for "${spec.key}" (AI matching disabled)`);
      setAiMatchedEntityId(null);
      setAiMatchingAttempted(true);
    }
  }, [spec.key, entities.length, aiMatchingAttempted, AI_MATCHING_ENABLED]); // Only re-run when key or entity count changes

  if (!Component) {
    console.warn(`Component type "${spec.type}" not found in registry`);
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        <p className="font-semibold">Unknown component: {spec.type}</p>
        <p className="text-sm mt-1">
          This component is not registered. Available types:{" "}
          {Object.keys(COMPONENT_REGISTRY).join(", ")}
        </p>
      </div>
    );
  }

  // Fix props for specific component types
  let enhancedProps = { ...spec.props };

  // NEW: For metric_card, inject full entity data and related entities
  if (spec.type === 'metric_card') {
    // Use AI-matched entity ID if available, fall back to props entityId
    const entityId = aiMatchedEntityId ?? spec.props.entityId;

    // Find the entity
    const entity = entityId ? entityMap[entityId] : undefined;

    if (entity) {
      enhancedProps = {
        ...enhancedProps,
        id: spec.key || `metric_card_${entityId}`,
        entity, // Full entity object for ExpandedMetricCard
        relatedEntities: entities.filter((e: any) => e.type === entity.type && e.id !== entityId),
        entityId,
        onAction,
        onDelete: onDelete ? (cardId: string) => onDelete(cardId) : undefined,
      };

      console.log(`[DynamicRenderer] Injected entity context for card:`, {
        key: spec.key,
        entityId,
        entityLabel: entity.label || entity.name,
        matchSource: aiMatchedEntityId === undefined ? 'props' : 'AI',
      });
    } else if (entityId && !isAggregate) {
      // Only warn if we have an entity ID but can't find the entity AND it's not an aggregate
      console.warn(`[DynamicRenderer] Entity not found for ID: ${entityId} (key: ${spec.key})`);
    }
    // else: suppress warning for aggregate components (expected behavior)
  }

  // Expandable sections should start expanded to show refinement results immediately
  if (spec.type === 'expandable_section') {
    enhancedProps = {
      ...enhancedProps,
      defaultExpanded: true, // Auto-expand to show analysis results
    };
  }

  // Chart components need entity filtering to prevent secondary entities from contaminating
  if (spec.type === 'bar_chart' || spec.type === 'line_chart' || spec.type === 'area_chart') {
    // If chart has data but also has entity_type or entity_ids metadata, we may need to refilter
    // This handles cases where backend provides chart data that includes all entities
    const chartEntityType = enhancedProps.entity_type;
    const chartEntityIds = enhancedProps.entity_ids;

    // If chart specifies entity filtering and we have entities available
    if (entities && entities.length > 0 && (chartEntityType || chartEntityIds)) {
      // Filter entities based on chart spec
      let chartEntities = entities;

      if (chartEntityIds && Array.isArray(chartEntityIds) && chartEntityIds.length > 0) {
        chartEntities = entities.filter(e => chartEntityIds.includes(e.id));
        console.log(`[DynamicRenderer] Chart filtered to ${chartEntities.length} entities by IDs`);
      } else if (chartEntityType) {
        chartEntities = entities.filter(e => e.type === chartEntityType);
        console.log(`[DynamicRenderer] Chart filtered to ${chartEntities.length} entities of type "${chartEntityType}"`);
      }

      // Pass filtered entities as metadata (charts use props.data directly, but this is for future extensions)
      enhancedProps._filteredEntities = chartEntities;
    }
  }

  // Map components need entity context for LocationPanel integration
  if (spec.type === 'map') {
    // Always pass full entities array for entity matching
    enhancedProps = {
      ...enhancedProps,
      entities, // Full entity list for fuzzy matching
      onSelectEntity: onAction ? (entityId: string) => {
        bus.emit('ENTITY_SELECTED', { entityId, source: 'map' });
      } : undefined,
    };

    // Enhance location data with entity references if possible
    if (enhancedProps.locations && Array.isArray(enhancedProps.locations)) {
      enhancedProps.locations = enhancedProps.locations.map((loc: any) => {
        // Try to find matching entity for this location using precise matching
        let matchingEntity = null;

        // Strategy 1: Exact ID match
        if (loc.id) {
          matchingEntity = entities.find(e => e.id === loc.id);
          if (matchingEntity) {
            console.log(`[DynamicRenderer] Linked map location "${loc.label}" to entity "${matchingEntity.id}" (exact ID)`);
            return { ...loc, entity: matchingEntity, entityId: matchingEntity.id };
          }
        }

        // Strategy 2: Substring match on entity ID (e.g., "paris" matches "destination_paris")
        if (loc.id) {
          const normalizedLocId = String(loc.id).toLowerCase().trim();
          matchingEntity = entities.find(e => {
            const normalizedEntityId = e.id.toLowerCase().trim();
            // Check for exact word boundary matches (with underscore)
            return normalizedEntityId === `destination_${normalizedLocId}` ||
                   normalizedEntityId === `${normalizedLocId}` ||
                   normalizedEntityId.includes(`_${normalizedLocId}_`) ||
                   normalizedEntityId.includes(`_${normalizedLocId}`) ||
                   normalizedEntityId.includes(`${normalizedLocId}_`);
          });

          if (matchingEntity) {
            console.log(`[DynamicRenderer] Linked map location "${loc.label}" to entity "${matchingEntity.id}" (substring ID match)`);
            return { ...loc, entity: matchingEntity, entityId: matchingEntity.id };
          }
        }

        // Strategy 3: Match on public_identifier (most reliable for city names)
        if (loc.label) {
          const normalizedLabel = loc.label.toLowerCase().trim();

          matchingEntity = entities.find(e => {
            // Check BOTH top-level property AND attributes
            const topLevelPublicId = (e.public_identifier || '').toLowerCase().trim();
            const attrPublicId = e.attributes?.find((a: any) => a.function === 'publicIdentifier')?.value;
            const normalizedAttrPublicId = attrPublicId ? String(attrPublicId).toLowerCase().trim() : '';

            // Use whichever is available
            const publicId = topLevelPublicId || normalizedAttrPublicId;
            if (!publicId) return false;

            // Extract city name from "City, Country" format
            const cityName = publicId.split(',')[0].trim();
            const labelCityName = normalizedLabel.split(',')[0].trim();

            return cityName === labelCityName || publicId === normalizedLabel;
          });

          if (matchingEntity) {
            console.log(`[DynamicRenderer] Linked map location "${loc.label}" to entity "${matchingEntity.id}" (public_identifier match)`);
            return { ...loc, entity: matchingEntity, entityId: matchingEntity.id };
          }
        }

        // Strategy 4: Match on label substring in entity ID
        if (loc.label) {
          const normalizedLabel = loc.label.toLowerCase().trim();
          matchingEntity = entities.find(e => {
            const normalizedEntityId = e.id.toLowerCase().trim();
            return normalizedEntityId.includes(normalizedLabel) || normalizedLabel.includes(normalizedEntityId);
          });

          if (matchingEntity) {
            console.log(`[DynamicRenderer] Linked map location "${loc.label}" to entity "${matchingEntity.id}" (label substring match)`);
            return { ...loc, entity: matchingEntity, entityId: matchingEntity.id };
          }
        }

        // Strategy 5: Coordinate-based matching (within 0.05° = ~5.5km)
        if (loc.lat !== undefined && loc.lng !== undefined) {
          matchingEntity = entities.find(e => {
            const coordsAttr = e.attributes?.find((a: any) =>
              a.name === 'coordinates' && a.value?.lat !== undefined && a.value?.lng !== undefined
            );

            if (!coordsAttr) return false;

            const dist = Math.sqrt(
              Math.pow(coordsAttr.value.lat - loc.lat, 2) +
              Math.pow(coordsAttr.value.lng - loc.lng, 2)
            );

            return dist < 0.05; // Tighter radius for precision
          });

          if (matchingEntity) {
            console.log(`[DynamicRenderer] Linked map location "${loc.label}" to entity "${matchingEntity.id}" (coordinate match)`);
            return { ...loc, entity: matchingEntity, entityId: matchingEntity.id };
          }
        }

        // No hardcoded match - will be handled by MapWidget's AI fallback
        console.log(`[DynamicRenderer] No hardcoded match for location "${loc.label}" (${loc.id}) - MapWidget will try AI fallback`);
        return loc;
      });
    }
  }

  // ComparisonTable expects 'items' but backend might send 'data'
  if (spec.type === 'comparison_table') {
    if (spec.props.data && !spec.props.items) {
      enhancedProps.items = spec.props.data;
    }
    // Convert column names to column objects if needed
    if (spec.props.columns && Array.isArray(spec.props.columns) && typeof spec.props.columns[0] === 'string') {
      enhancedProps.columns = spec.props.columns.map((col: string) => ({
        key: col,
        label: col.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        sortable: true
      }));
    }
  }
  
  // Convert icon name string to React component
  enhancedProps.icon = typeof spec.props.icon === 'string' ? getIconComponent(spec.props.icon) : spec.props.icon;
  
  // Handle onClick actions
  if (spec.props.onClick) {
    enhancedProps.onClick = () => {
      // If onClick is an action object, call onAction handler
      if (spec.props.onClick && typeof spec.props.onClick === 'object') {
        onAction?.(spec.props.onClick);
      }
      // Also call the original onClick if it's a function
      if (typeof spec.props.onClick === 'function') {
        spec.props.onClick();
      }
    };
  }

  // Recursively render children with entity context
  const children = spec.children?.map((child, idx) => (
    <DynamicComponentRenderer
      key={child.key || `child-${idx}`}
      spec={child}
      onAction={onAction}
      onDelete={onDelete}
      entities={entities}
      entityMap={entityMap}
    />
  ));

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`relative group ${spec.props.containerClassName || ''}`}
    >
      {/* Delete Button - Only show for non-metric-card components */}
      {onDelete && spec.key && spec.type !== 'text' && spec.type !== 'divider' && spec.type !== 'spacer' && (
        <button
          onClick={() => onDelete(spec.key!)}
          className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity bg-destructive text-destructive-foreground rounded-full p-1.5 hover:bg-destructive/90 shadow-lg"
          title="Delete component"
        >
          <X className="h-4 w-4" />
        </button>
      )}
      
      <Component {...enhancedProps}>
        {children || spec.props.children}
      </Component>
    </motion.div>
  );
};

/**
 * Export the registry for debugging/testing
 */
export { COMPONENT_REGISTRY };
