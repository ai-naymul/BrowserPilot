/**
 * Dynamic Component Mapper
 * 
 * Maps entity attributes to UI components based on metadata (widget type, function role)
 * NO HARDCODED ATTRIBUTE NAMES - uses only widget types and function roles
 */

import { Entity, Attribute } from '@/lib/api';
import { ComponentSpec } from '@/types/api';
import { isValueMeaningful, parseISODateSafe, formatCurrency as formatCurrencyUtil, humanizeAttributeName } from './validators';
import { classifyFieldSemantic, getFieldPriority } from './formatters';

// ============================================================================
// ENTITY CONTEXT INJECTION & RENDER GUARDS
// ============================================================================

/**
 * Infer entity ID from component key with robust matching
 * Handles patterns like:
 * - "metric-tokyo-total" → matches entity with "tokyo" in public_identifier
 * - "metric-barcelona/bali" → extracts "barcelona", matches entity
 * - "card-destination_tokyo" → matches "destination_tokyo" id
 * - Uses selection context when available
 *
 * @param key - Component key to extract entity from
 * @param entities - Available entities
 * @param selectedEntityId - Currently selected entity (priority fallback)
 * @param coordinates - Optional { lat, lng } for coordinate-based matching
 */
export function inferEntityIdFromKey(
  key: string | undefined,
  entities: Entity[],
  selectedEntityId?: string,
  coordinates?: { lat: number; lng: number }
): string | undefined {
  if (!key || entities.length === 0) return undefined;

  const keyLower = key.toLowerCase();

  // Strategy 1: Direct ID match in key
  for (const entity of entities) {
    if (keyLower.includes(entity.id.toLowerCase())) {
      return entity.id;
    }
  }

  // Strategy 2: Match public_identifier substring
  for (const entity of entities) {
    const identifier = (entity.public_identifier || '').toLowerCase();
    if (identifier && keyLower.includes(identifier)) {
      return entity.id;
    }
  }

  // Strategy 3: Extract label from metric-{label}-{suffix} or action-{label} patterns
  const patterns = [
    /(?:metric|action|card)-([^-\/]+)/,
    /([a-z]+)-(?:map|chart|table)/
  ];

  for (const pattern of patterns) {
    const match = key.match(pattern);
    if (match && match[1]) {
      const label = match[1].toLowerCase();

      for (const entity of entities) {
        const identifier = (entity.public_identifier || entity.name || '').toLowerCase();
        const entityType = (entity.type || '').toLowerCase();

        // Bidirectional substring match on identifier or type
        if (
          (identifier && identifier.includes(label)) ||
          (identifier && label.includes(identifier)) ||
          (entityType && entityType.includes(label)) ||
          (label.includes(entityType))
        ) {
          return entity.id;
        }
      }
    }
  }

  // Strategy 4: Coordinate-based matching (for maps, location-related actions)
  if (coordinates) {
    const RADIUS = 0.1; // ~11km
    for (const entity of entities) {
      const coordsAttr = entity.attributes.find((a: any) =>
        a.name === 'coordinates' &&
        a.value?.lat !== undefined &&
        a.value?.lng !== undefined
      );

      if (coordsAttr) {
        const dist = Math.sqrt(
          Math.pow(coordsAttr.value.lat - coordinates.lat, 2) +
          Math.pow(coordsAttr.value.lng - coordinates.lng, 2)
        );

        if (dist < RADIUS) {
          return entity.id;
        }
      }
    }
  }

  // Strategy 5: Use selection context (currently focused entity)
  if (selectedEntityId && entities.some(e => e.id === selectedEntityId)) {
    return selectedEntityId;
  }

  // Strategy 6: Trip plan or main entity (for global actions)
  const mainEntity = entities.find(e =>
    e.id.includes('trip_plan') ||
    e.id.includes('main') ||
    e.type?.toLowerCase().includes('plan')
  );
  if (mainEntity && (keyLower.includes('trip') || keyLower.includes('plan') || keyLower.includes('budget'))) {
    return mainEntity.id;
  }

  // Strategy 7: Only use first entity if key suggests it's generic/global
  const isGenericAction = keyLower.includes('action-') && !entities.some(e =>
    keyLower.includes(e.id.toLowerCase()) ||
    keyLower.includes((e.public_identifier || '').toLowerCase())
  );

  if (isGenericAction && entities.length > 0) {
    // No warning - generic actions target first/main entity by design
    return entities[0].id;
  }

  // No match - return undefined instead of guessing
  return undefined;
}

/**
 * Inject entity context into component nodes
 * Adds { entityId, entity } to props if not already present
 */
export function injectEntityContext(
  node: ComponentSpec,
  entitiesById: Record<string, Entity>,
  selectedEntityId?: string
): ComponentSpec {
  // Skip if already has entity context
  if (node.props?.entityId && node.props?.entity) {
    return node;
  }

  const entities = Object.values(entitiesById);

  // Try to get entityId from props or infer from key
  let entityId = node.props?.entityId || inferEntityIdFromKey(
    node.key,
    entities,
    selectedEntityId,
    node.props?.coordinates // For location-based components
  );

  // Inject context if we found an entityId
  if (entityId && entitiesById[entityId]) {
    return {
      ...node,
      props: {
        ...node.props,
        entityId,
        entity: entitiesById[entityId],
      },
    };
  }

  return node;
}

/**
 * Check if a component node should be rendered
 * Filters out nodes with empty/meaningless content
 */
export function shouldRenderNode(node: ComponentSpec): boolean {
  const { type, props } = node;

  // Always render structural components
  if (['expandable_section', 'action_button'].includes(type)) {
    return true;
  }

  // metric_card: only if label and value are meaningful
  if (type === 'metric_card') {
    if (!isValueMeaningful(props?.label) || !isValueMeaningful(props?.value)) {
      console.log('[RenderGuard] Filtering empty metric_card:', props?.label);
      return false;
    }
  }

  // comparison_table: only if has meaningful rows
  if (type === 'comparison_table') {
    const items = props?.items || props?.data || [];
    if (!Array.isArray(items) || items.length === 0) {
      console.log('[RenderGuard] Filtering empty comparison_table');
      return false;
    }
  }

  // bar_chart/line_chart: only if has data
  if (type.includes('chart')) {
    const data = props?.data || [];
    if (!Array.isArray(data) || data.length === 0) {
      console.log('[RenderGuard] Filtering empty chart:', type);
      return false;
    }
  }

  // map: only if has locations
  if (type === 'map') {
    const locations = props?.locations || [];
    if (!Array.isArray(locations) || locations.length === 0) {
      console.log('[RenderGuard] Filtering empty map');
      return false;
    }
  }

  return true;
}

/**
 * Deduplicate component nodes by type + stable key
 */
export function deduplicateNodes(nodes: ComponentSpec[]): ComponentSpec[] {
  const seen = new Set<string>();
  const deduplicated: ComponentSpec[] = [];

  for (const node of nodes) {
    // Generate stable key
    const stableKey = node.key || `${node.type}:${JSON.stringify(node.props?.id || node.props?.label || '')}`;
    const dedupeKey = `${node.type}:${stableKey}`;

    if (!seen.has(dedupeKey)) {
      seen.add(dedupeKey);
      deduplicated.push(node);
    } else {
      console.log('[Dedupe] Filtered duplicate:', dedupeKey);
    }
  }

  return deduplicated;
}

/**
 * Group components into logical sections
 * Returns sections with metadata for rendering (collapsed by default for new ones)
 */
export interface ComponentSection {
  id: string;
  title: string;
  components: ComponentSpec[];
  isNew?: boolean; // Newly added sections default to collapsed
  icon?: string;
}

export function groupIntoSections(nodes: ComponentSpec[]): ComponentSection[] {
  const sections: ComponentSection[] = [];

  // Categorize components
  const costs: ComponentSpec[] = [];
  const weather: ComponentSpec[] = [];
  const safety: ComponentSpec[] = [];
  const logistics: ComponentSpec[] = [];
  const overview: ComponentSpec[] = [];
  const other: ComponentSpec[] = [];

  nodes.forEach(node => {
    const key = node.key?.toLowerCase() || '';
    const label = node.props?.label?.toLowerCase() || '';
    const type = node.type;

    // Weather
    if (key.includes('weather') || label.includes('weather') || label.includes('temperature')) {
      weather.push(node);
    }
    // Costs
    else if (
      type === 'metric_card' &&
      (node.props?.value?.includes('$') || key.includes('cost') || label.includes('cost') || label.includes('price') || label.includes('budget'))
    ) {
      costs.push(node);
    }
    // Safety & Ratings
    else if (
      key.includes('safety') ||
      key.includes('rating') ||
      label.includes('safety') ||
      label.includes('rating')
    ) {
      safety.push(node);
    }
    // Logistics (flights, hotels, packing)
    else if (
      key.includes('flight') ||
      key.includes('hotel') ||
      key.includes('packing') ||
      key.includes('accommodation') ||
      label.includes('flight') ||
      label.includes('hotel')
    ) {
      logistics.push(node);
    }
    // Overview (maps, tables, key metrics)
    else if (type === 'map' || type === 'comparison_table' || type === 'metric_card') {
      overview.push(node);
    }
    // Everything else
    else {
      other.push(node);
    }
  });

  // Build sections (only include non-empty ones)
  if (overview.length > 0) {
    sections.push({
      id: 'overview',
      title: 'Overview',
      components: overview,
      isNew: false,
      icon: 'LayoutGrid',
    });
  }

  if (costs.length > 0) {
    sections.push({
      id: 'costs',
      title: `Costs (${costs.length})`,
      components: costs,
      isNew: costs.length > 3, // Collapse if many cost items
      icon: 'DollarSign',
    });
  }

  if (weather.length > 0) {
    sections.push({
      id: 'weather',
      title: `Weather (${weather.length})`,
      components: weather,
      isNew: true, // Weather typically added via follow-up
      icon: 'Cloud',
    });
  }

  if (safety.length > 0) {
    sections.push({
      id: 'safety',
      title: `Safety & Ratings (${safety.length})`,
      components: safety,
      isNew: safety.length > 3,
      icon: 'Shield',
    });
  }

  if (logistics.length > 0) {
    sections.push({
      id: 'logistics',
      title: `Logistics (${logistics.length})`,
      components: logistics,
      isNew: true,
      icon: 'Plane',
    });
  }

  if (other.length > 0) {
    sections.push({
      id: 'other',
      title: `More (${other.length})`,
      components: other,
      isNew: false,
      icon: 'MoreHorizontal',
    });
  }

  return sections;
}

/**
 * Process component tree: inject context, filter empties, deduplicate
 */
export function processComponentTree(
  nodes: ComponentSpec[],
  entitiesById: Record<string, Entity>,
  selectedEntityId?: string
): ComponentSpec[] {
  // Step 1: Inject entity context with selection context
  const withContext = nodes.map(node => injectEntityContext(node, entitiesById, selectedEntityId));

  // Step 2: Filter empty nodes
  const filtered = withContext.filter(shouldRenderNode);

  // Step 3: Deduplicate
  const deduplicated = deduplicateNodes(filtered);

  console.log(`[ProcessTree] ${nodes.length} → ${deduplicated.length} nodes (after context/filter/dedupe)`);

  return deduplicated;
}

// ============================================================================
// ENTITY FILTERING FOR CHARTS
// ============================================================================

/**
 * Filter entities for a specific chart based on configuration
 * This prevents secondary entities (e.g., seasonal weather) from contaminating primary charts
 *
 * Priority order:
 * 1. Explicit entity_ids from spec
 * 2. Explicit entity_type(s) from spec
 * 3. Primary entity type (passed from Index.tsx)
 * 4. Fallback: all entities
 */
export function getEntitiesForChart(
  spec: ComponentSpec | null,
  allEntities: Entity[],
  primaryEntityType?: string
): Entity[] {
  if (!allEntities || allEntities.length === 0) return [];

  // Strategy 1: Explicit entity IDs in spec
  const entityIds = spec?.props?.entity_ids || spec?.config?.entity_ids;
  if (entityIds && Array.isArray(entityIds) && entityIds.length > 0) {
    const filtered = allEntities.filter(e => entityIds.includes(e.id));
    console.log(`[ChartFilter] Using explicit entity_ids: ${entityIds.length} entities`);
    return filtered;
  }

  // Strategy 2: Explicit entity type(s) in spec
  const entityType = spec?.props?.entity_type || spec?.config?.entity_type;
  const entityTypes = spec?.props?.entity_types || spec?.config?.entity_types;

  if (entityType) {
    const filtered = allEntities.filter(e => e.type === entityType);
    console.log(`[ChartFilter] Using explicit entity_type "${entityType}": ${filtered.length} entities`);
    return filtered;
  }

  if (entityTypes && Array.isArray(entityTypes) && entityTypes.length > 0) {
    const filtered = allEntities.filter(e => entityTypes.includes(e.type));
    console.log(`[ChartFilter] Using explicit entity_types ${JSON.stringify(entityTypes)}: ${filtered.length} entities`);
    return filtered;
  }

  // Strategy 3: Primary entity type (e.g., "Destination" for the initial task)
  if (primaryEntityType) {
    const filtered = allEntities.filter(e => matchesPrimaryEntityType(e.type, primaryEntityType));
    if (filtered.length > 0) {
      console.log(`[ChartFilter] Using primary type "${primaryEntityType}": ${filtered.length} entities`);
      return filtered;
    }
    // If no entities match primary type, log warning and fall through
    console.warn(`[ChartFilter] No entities found for primary type "${primaryEntityType}", using all entities`);
  }

  // Strategy 4: Fallback - return all entities
  console.log(`[ChartFilter] No filter specified, using all ${allEntities.length} entities`);
  return allEntities;
}

// ============================================================================
// COMPONENT GENERATION
// ============================================================================

/**
 * Check if an entity matches the primary entity type
 * Handles both exact matches and prefix matches (e.g., "Destination_Paris" matches "Destination")
 */
function matchesPrimaryEntityType(entityType: string | undefined, primaryEntityType: string | undefined): boolean {
  if (!entityType || !primaryEntityType) return false;

  // Exact match
  if (entityType === primaryEntityType) return true;

  // Prefix match - extract base type before underscore
  // "Destination_Paris" → "Destination"
  const entityPrefix = entityType.split('_')[0];
  const primaryPrefix = primaryEntityType.split('_')[0];

  return entityPrefix === primaryPrefix;
}

/**
 * Generate components dynamically from entities
 * This replaces all hardcoded component generation logic
 *
 * @param entities - All available entities
 * @param primaryEntityType - The primary entity type for this task (e.g., "Destination")
 */
export function generateComponentsFromEntities(
  entities: Entity[],
  primaryEntityType?: string
): ComponentSpec[] {
  const components: ComponentSpec[] = [];

  console.log(`[ComponentGen] Generating for ${entities.length} entities, primary type: ${primaryEntityType || 'none'}`);

  // 1. Generate metric cards (ONLY for primary entities)
  const metricCards = generateMetricCards(entities, primaryEntityType);
  components.push(...metricCards);

  // 2. Generate comparison table if multiple PRIMARY entities
  if (primaryEntityType) {
    const primaryEntities = entities.filter(e => matchesPrimaryEntityType(e.type, primaryEntityType));
    console.log(`[ComponentGen] Found ${primaryEntities.length} primary entities for comparison (type: ${primaryEntityType})`);
    if (primaryEntities.length >= 2) {
      const comparisonTable = generateComparisonTable(primaryEntities);
      if (comparisonTable) components.push(comparisonTable);
    }
  } else if (entities.length >= 2) {
    const comparisonTable = generateComparisonTable(entities);
    if (comparisonTable) components.push(comparisonTable);
  }

  // 3. Generate charts from numeric attributes (filter to primary type only)
  const charts = generateCharts(entities, primaryEntityType);
  components.push(...charts);

  // 4. Generate map from location attributes (use ALL entities with coordinates)
  const map = generateMap(entities);
  if (map) components.push(map);

  // 5. Generate action buttons from available actions
  const actionButtons = generateActionButtons(entities);
  components.push(...actionButtons);

  console.log(`[ComponentGen] Generated ${components.length} total components`);
  return components;
}

/**
 * Generate metric cards from important numeric attributes
 * ROLE-AWARE: Only generates hero cards for primary entities
 *
 * @param entities - All entities
 * @param primaryEntityType - Primary entity type (e.g., "Destination")
 * @returns Array of metric card component specs
 */
function generateMetricCards(entities: Entity[], primaryEntityType?: string): ComponentSpec[] {
  const cards: ComponentSpec[] = [];

  // CRITICAL FILTER: Only generate hero cards for primary entities
  // Breakdown entities (seasonal, daily, etc.) should NOT get hero cards
  const heroEntities = primaryEntityType
    ? entities.filter(e => matchesPrimaryEntityType(e.type, primaryEntityType))
    : entities;

  if (heroEntities.length === 0) {
    console.log('[MetricCards] No primary entities found for type:', primaryEntityType);
    return cards;
  }

  console.log(`[MetricCards] Generating hero cards for ${heroEntities.length} primary entities (type: ${primaryEntityType || 'all'})`);

  heroEntities.forEach(entity => {
    // Find hero-eligible attributes using semantic classification
    const heroMetrics = entity.attributes.filter(attr => {
      // Skip identifiers
      if (attr.function === 'identifier' || attr.function === 'publicIdentifier') {
        return false;
      }

      // Use semantic classification to determine eligibility
      const semantic = classifyFieldSemantic(attr.name, attr.value, {
        widget: attr.widget,
        function: attr.function,
      });

      const priority = getFieldPriority(semantic, attr.function);

      // Only include hero and supporting priority fields
      // This excludes: temperature, coordinates, free text, etc.
      return priority === 'hero' || priority === 'supporting';
    });

    // Score and sort metrics by importance
    const scoredMetrics = heroMetrics.map(attr => {
      const semantic = classifyFieldSemantic(attr.name, attr.value, {
        widget: attr.widget,
        function: attr.function,
      });
      const priority = getFieldPriority(semantic, attr.function);

      let score = 0;

      // Priority scoring
      if (priority === 'hero') score += 100;
      else if (priority === 'supporting') score += 50;

      // Function scoring
      if (attr.function === 'computed') score += 30;
      else if (attr.function === 'display') score += 10;

      // Semantic scoring (prefer totals/costs over counts)
      if (semantic === 'currency') score += 20;
      else if (semantic === 'rating') score += 15;
      else if (semantic === 'count') score += 5;

      // CRITICAL: Prioritize total/estimated costs over component costs
      const attrNameLower = attr.name.toLowerCase();
      if (semantic === 'currency') {
        if (attrNameLower.includes('total') || attrNameLower.includes('estimated')) {
          score += 40; // Strong boost for totals
        } else if (attrNameLower.includes('accommodation') ||
                   attrNameLower.includes('food') ||
                   attrNameLower.includes('transport') ||
                   attrNameLower.includes('activity')) {
          score -= 10; // Penalize component costs (prefer showing them in breakdowns, not hero cards)
        }
      }

      return { attr, score, semantic };
    });

    // Take top 1-2 most important metrics per entity
    const topMetrics = scoredMetrics
      .sort((a, b) => b.score - a.score)
      .slice(0, 2);

    // Generate cards for top metrics
    topMetrics.forEach(({ attr, semantic }) => {
      const labelAttr = entity.attributes.find(a => a.function === 'publicIdentifier');
      const label = labelAttr?.value || entity.public_identifier;

      cards.push({
        type: 'metric_card',
        key: `metric-${entity.id}-${attr.name}`,
        props: {
          label,
          value: formatAttributeValue(attr),
          sublabel: formatAttributeName(attr.name),
          icon: getIconForEntityType(entity.type),
          entityId: entity.id,
          // Store semantic type for potential styling
          _semantic: semantic,
          onClick: {
            type: 'expand_card',
            params: { entityId: entity.id }
          }
        }
      });
    });
  });

  console.log(`[MetricCards] Generated ${cards.length} hero cards`);
  return cards;
}

/**
 * Map entity type to appropriate Lucide icon
 */
function getIconForEntityType(entityType: string): string {
  const type = entityType.toLowerCase();
  if (type.includes('destination') || type.includes('location') || type.includes('place')) return 'MapPin';
  if (type.includes('product') || type.includes('phone') || type.includes('smartphone')) return 'Smartphone';
  if (type.includes('person') || type.includes('user')) return 'User';
  if (type.includes('event')) return 'Calendar';
  if (type.includes('flight')) return 'Plane';
  if (type.includes('hotel')) return 'Hotel';
  if (type.includes('stock') || type.includes('finance')) return 'TrendingUp';
  return 'Circle';
}

/**
 * Generate comparison table from entities (more aggressive)
 */
function generateComparisonTable(entities: Entity[]): ComponentSpec | null {
  if (entities.length < 2) return null;
  
  // Find common attributes (at least 50% overlap is ok)
  const allAttributes = entities.flatMap(e => e.attributes.map(a => a.name));
  const attributeCounts = allAttributes.reduce((acc, name) => {
    acc[name] = (acc[name] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  // Show attributes that appear in at least 50% of entities
  const threshold = Math.ceil(entities.length * 0.5);
  const displayAttributes = Object.entries(attributeCounts)
    .filter(([_, count]) => count >= threshold)
    .map(([name]) => name)
    .filter(attrName => {
      // Skip identifiers
      const sampleAttr = entities[0].attributes.find(a => a.name === attrName);
      return sampleAttr && sampleAttr.function !== 'identifier';
    })
    .slice(0, 6); // Show max 6 columns
  
  if (displayAttributes.length === 0) {
    // Fallback: show top 3 attributes from first entity
    displayAttributes.push(
      ...entities[0].attributes
        .filter(a => a.function !== 'identifier')
        .slice(0, 3)
        .map(a => a.name)
    );
  }
  
  // Build table data
  const items = entities.map(entity => {
    const row: any = { id: entity.id };
    
    // Add public identifier as first column
    const labelAttr = entity.attributes.find(a => a.function === 'publicIdentifier');
    row.name = labelAttr?.value || entity.public_identifier;
    
    // Add other attributes
    displayAttributes.forEach(attrName => {
      const attr = entity.attributes.find(a => a.name === attrName);
      if (attr) {
        row[attrName] = formatAttributeValue(attr);
      }
    });
    
    return row;
  });
  
  // Build columns
  const columns = [
    { key: 'name', label: 'Name', sortable: true },
    ...displayAttributes.map(attrName => ({
      key: attrName,
      label: formatAttributeName(attrName),
      sortable: true
    }))
  ];
  
  return {
    type: 'comparison_table',
    key: 'comparison-table',
    props: {
      items,
      columns,
      highlightBest: true
    }
  };
}

/**
 * Generate charts from numeric attributes
 * @param entities - All available entities
 * @param primaryEntityType - Primary entity type to filter by (prevents seasonal/secondary entities from contaminating primary charts)
 */
function generateCharts(entities: Entity[], primaryEntityType?: string): ComponentSpec[] {
  const charts: ComponentSpec[] = [];

  if (entities.length < 2) return charts;

  // CRITICAL FIX: Filter to primary entity type only for the main comparison chart
  // This prevents seasonal/weather entities from contaminating the cost comparison
  const chartEntities = primaryEntityType
    ? entities.filter(e => matchesPrimaryEntityType(e.type, primaryEntityType))
    : entities;

  if (chartEntities.length < 2) {
    console.log(`[ChartGen] Skipping chart - only ${chartEntities.length} entities of primary type "${primaryEntityType}"`);
    return charts;
  }

  console.log(`[ChartGen] Creating bar chart for ${chartEntities.length} entities of type "${primaryEntityType || 'all'}"`);

  // Find ANY numeric attributes across the FILTERED entities (don't require common)
  const allNumericAttributes = new Set<string>();
  chartEntities.forEach(entity => {
    entity.attributes.forEach(attr => {
      if (attr.function === 'identifier') return;

      const isNumeric = typeof attr.value === 'number' || !isNaN(Number(attr.value));
      if (isNumeric) {
        allNumericAttributes.add(attr.name);
      }
    });
  });

  const numericAttributes = Array.from(allNumericAttributes).slice(0, 4); // Max 4 bars

  if (numericAttributes.length === 0) return charts;

  // Create bar chart comparing PRIMARY entities only across numeric dimensions
  const barData = chartEntities.map(entity => {
    const row: any = {};

    // Get label
    const labelAttr = entity.attributes.find(a => a.function === 'publicIdentifier');
    row.label = (labelAttr?.value || entity.public_identifier).split(',')[0].trim();

    // Add numeric values
    numericAttributes.forEach(attrName => {
      const attr = entity.attributes.find(a => a.name === attrName);
      if (attr) {
        row[attrName] = Number(attr.value) || 0;
      }
    });

    return row;
  });

  const bars = numericAttributes.map((attrName, idx) => {
    const colors = ['#7dd3fc', '#c4b5fd', '#f9a8d4', '#facc15'];
    return {
      dataKey: attrName,
      name: formatAttributeName(attrName),
      color: colors[idx % colors.length]
    };
  });

  charts.push({
    type: 'bar_chart',
    key: 'bar-chart',
    props: {
      data: barData,
      bars,
      height: 350,
      showValues: false,
      // Store metadata for future filtering if needed
      entity_type: primaryEntityType,
      entity_ids: chartEntities.map(e => e.id),
    }
  });

  return charts;
}

/**
 * Generate map from location attributes
 */
function generateMap(entities: Entity[]): ComponentSpec | null {
  const locations: any[] = [];
  
  entities.forEach(entity => {
    // Find coordinates attribute (object type with lat/lng)
    const coordsAttr = entity.attributes.find(attr =>
      attr.widget === 'object' && attr.data_type === 'dict' &&
      attr.value && typeof attr.value === 'object' &&
      'lat' in attr.value && 'lng' in attr.value
    );
    
    if (coordsAttr && coordsAttr.value) {
      const coords = coordsAttr.value as any;
      const labelAttr = entity.attributes.find(a => a.function === 'publicIdentifier');
      
      locations.push({
        id: entity.id,
        lat: coords.lat,
        lng: coords.lng,
        label: labelAttr?.value || entity.public_identifier,
        color: entity.color,
        description: entity.public_identifier,
        entity: entity // CRITICAL: Include full entity for LocationPanel
      });
    }
  });
  
  if (locations.length === 0) return null;
  
  // Calculate center
  const avgLat = locations.reduce((sum, loc) => sum + loc.lat, 0) / locations.length;
  const avgLng = locations.reduce((sum, loc) => sum + loc.lng, 0) / locations.length;
  
  return {
    type: 'map',
    key: 'map',
    props: {
      locations,
      center: { lat: avgLat, lng: avgLng },
      zoom: locations.length === 1 ? 10 : 2,
      height: 450
    }
  };
}

/**
 * Generate action buttons
 */
function generateActionButtons(entities: Entity[]): ComponentSpec[] {
  const buttons: ComponentSpec[] = [];
  
  // Add entity button (generic)
  buttons.push({
    type: 'action_button',
    key: 'action-add-entity',
    props: {
      label: `Add another ${entities[0]?.type || 'item'}`,
      icon: 'Plus',
      variant: 'secondary',
      onClick: {
        type: 'add_entity',
        params: {
          entityType: entities[0]?.type || 'entity'
        }
      }
    }
  });
  
  return buttons;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if entities are comparable (same type or similar structure)
 */
function areComparable(entities: Entity[]): boolean {
  if (entities.length < 2) return false;
  
  // Check if they have similar attribute structures
  const firstEntityAttrs = new Set(entities[0].attributes.map(a => a.name));
  
  // At least 50% of attributes should overlap
  return entities.every(entity => {
    const overlap = entity.attributes.filter(a => firstEntityAttrs.has(a.name)).length;
    return overlap / firstEntityAttrs.size >= 0.5;
  });
}

/**
 * Find attributes common to all entities
 */
function findCommonAttributes(entities: Entity[]): string[] {
  if (entities.length === 0) return [];
  
  const firstEntityAttrs = entities[0].attributes.map(a => a.name);
  
  return firstEntityAttrs.filter(attrName =>
    entities.every(entity => entity.attributes.some(a => a.name === attrName))
  );
}

/**
 * Find numeric attributes common to all entities
 */
function findCommonNumericAttributes(entities: Entity[]): string[] {
  const commonAttrs = findCommonAttributes(entities);
  
  return commonAttrs.filter(attrName => {
    const sampleAttr = entities[0].attributes.find(a => a.name === attrName);
    return sampleAttr && (
      sampleAttr.widget === 'number' ||
      sampleAttr.widget === 'currency' ||
      sampleAttr.widget === 'percentage' ||
      sampleAttr.widget === 'rating'
    ) && sampleAttr.function !== 'identifier';
  });
}

/**
 * Format attribute value for display
 */
function formatAttributeValue(attr: Attribute): any {
  // Handle null/undefined
  if (attr.value === null || attr.value === undefined) {
    return '-';
  }
  
  // Handle objects (coordinates, nested data)
  if (typeof attr.value === 'object' && !Array.isArray(attr.value)) {
    // Special case: coordinates
    if ('lat' in attr.value && 'lng' in attr.value) {
      return `${Number(attr.value.lat).toFixed(4)}, ${Number(attr.value.lng).toFixed(4)}`;
    }
    // Special case: location with name
    if ('name' in attr.value) {
      return attr.value.name;
    }
    // Generic object - return JSON or first meaningful value
    return JSON.stringify(attr.value);
  }
  
  // Handle arrays
  if (Array.isArray(attr.value)) {
    if (attr.value.length === 0) return '-';
    // If array of objects, return count
    if (typeof attr.value[0] === 'object') {
      return `${attr.value.length} items`;
    }
    // If array of primitives, join with comma
    return attr.value.join(', ');
  }
  
  // Handle by widget type
  switch (attr.widget) {
    case 'currency':
      return formatCurrency(attr.value);
    case 'percentage':
      return `${attr.value}%`;
    case 'rating':
      return `${attr.value}/10`;
    case 'date':
      try {
        return new Date(attr.value).toLocaleDateString();
      } catch {
        return attr.value;
      }
    default:
      // Return string representation
      return String(attr.value);
  }
}

/**
 * Format currency value
 */
function formatCurrency(value: any): string {
  const num = Number(value);
  if (isNaN(num)) return '$0';
  return `$${num.toLocaleString()}`;
}

/**
 * Format attribute name for display
 */
function formatAttributeName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
}
