/**
 * DynamicEntitySections - Auto-generates sections for entity types
 *
 * Watches EntityStore and renders sections for non-primary entity types
 * (e.g., flights, hotels, activities) that appear after follow-up actions.
 *
 * Schema-aware and fully dynamic - no hardcoding to specific use cases.
 */

import { useMemo, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useEntityStore } from '@/store/EntityStore';
import { ComparisonTable } from './ComparisonTable';
import { Plane, Hotel, Activity, Package, ChevronDown, ChevronUp } from 'lucide-react';

interface DynamicEntitySectionsProps {
  primaryEntityType?: string; // e.g., "Destination" - entities of this type won't create sections
  newEntityTypes?: Set<string>; // Entity types that were just added (for auto-expand)
  onDeleteEntity?: (entityId: string) => void; // Callback to delete an entity
}

export const DynamicEntitySections = ({ primaryEntityType, newEntityTypes = new Set(), onDeleteEntity }: DynamicEntitySectionsProps) => {
  const entityStore = useEntityStore();
  // Use getVisibleEntities to exclude deleted entities and get fresh data for data-only refines
  const entities = entityStore.getVisibleEntities();

  // Track collapsed state for each section (default: expanded)
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());

  // Auto-expand new entity types (keep them out of collapsedSections)
  useEffect(() => {
    if (newEntityTypes.size > 0) {
      setCollapsedSections(prev => {
        const updated = new Set(prev);
        // Remove new types from collapsed set to ensure they're expanded
        newEntityTypes.forEach(type => updated.delete(type));
        return updated;
      });
      console.log('[DynamicEntitySections] Auto-expanding new entity types:', Array.from(newEntityTypes));
    }
  }, [newEntityTypes]);

  const toggleSection = (typeName: string) => {
    setCollapsedSections(prev => {
      const updated = new Set(prev);
      if (updated.has(typeName)) {
        updated.delete(typeName);
      } else {
        updated.add(typeName);
      }
      return updated;
    });
  };

  // Group entities by type, excluding primary type
  const entityGroups = useMemo(() => {
    const groups: Record<string, any[]> = {};

    entities.forEach((entity) => {
      const type = entity.type || 'Unknown';

      // Skip primary entity type (e.g., destinations in a trip)
      if (primaryEntityType && type.toLowerCase().includes(primaryEntityType.toLowerCase())) {
        return;
      }

      if (!groups[type]) {
        groups[type] = [];
      }

      groups[type].push(entity);
    });

    return groups;
  }, [entities, primaryEntityType]);

  // Generate icon based on type name
  const getTypeIcon = (typeName: string) => {
    const name = typeName.toLowerCase();
    if (name.includes('flight') || name.includes('plane')) return Plane;
    if (name.includes('hotel') || name.includes('accommodation')) return Hotel;
    if (name.includes('activity') || name.includes('tour')) return Activity;
    return Package;
  };

  // Generate human-readable section title
  const getTypeTitle = (typeName: string) => {
    // Remove common prefixes/suffixes
    let cleaned = typeName.replace(/^(entity_|item_)/i, '').replace(/(_\d+|_option)$/i, '');

    // Convert snake_case or CamelCase to Title Case
    cleaned = cleaned
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .trim();

    // Capitalize first letter of each word
    return cleaned
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  // Extract price-like values from entity attributes
  const extractPriceValue = (entity: any): number | null => {
    const priceAttrs = entity.attributes?.filter((attr: any) =>
      ['price', 'cost', 'fare', 'total', 'amount'].some(keyword =>
        attr.name?.toLowerCase().includes(keyword)
      )
    ) || [];

    for (const attr of priceAttrs) {
      if (typeof attr.value === 'number') return attr.value;
      if (typeof attr.value === 'string') {
        const num = parseFloat(attr.value.replace(/[^0-9.-]/g, ''));
        if (!isNaN(num)) return num;
      }
    }
    return null;
  };

  // Extract rating-like values
  const extractRatingValue = (entity: any): number | null => {
    const ratingAttrs = entity.attributes?.filter((attr: any) =>
      ['rating', 'score', 'review'].some(keyword =>
        attr.name?.toLowerCase().includes(keyword)
      )
    ) || [];

    for (const attr of ratingAttrs) {
      if (typeof attr.value === 'number') return attr.value;
      if (typeof attr.value === 'string') {
        const num = parseFloat(attr.value);
        if (!isNaN(num)) return num;
      }
    }
    return null;
  };

  // Compute stats for a group of entities
  const computeStats = (typeEntities: any[]) => {
    const prices = typeEntities.map(extractPriceValue).filter((p): p is number => p !== null);
    const ratings = typeEntities.map(extractRatingValue).filter((r): r is number => r !== null);

    return {
      minPrice: prices.length > 0 ? Math.min(...prices) : null,
      maxPrice: prices.length > 0 ? Math.max(...prices) : null,
      avgPrice: prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : null,
      avgRating: ratings.length > 0 ? ratings.reduce((a, b) => a + b, 0) / ratings.length : null,
    };
  };

  // Format price
  const formatPrice = (price: number | null) => {
    if (price === null) return null;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  // Extract columns from entities' attributes
  const getColumnsForType = (typeEntities: any[]) => {
    if (typeEntities.length === 0) return [];

    // Collect all unique attribute names across entities
    const attrNames = new Set<string>();
    typeEntities.forEach((entity) => {
      entity.attributes?.forEach((attr: any) => {
        // Skip identifiers (already shown as row label)
        if (attr.function === 'identifier' || attr.function === 'publicIdentifier') return;
        // Skip very long text fields in tables
        if (attr.widget === 'long_text') return;
        attrNames.add(attr.name);
      });
    });

    // Prioritize important columns
    const priorityNames = ['price', 'cost', 'rating', 'duration', 'airline', 'departure', 'arrival'];
    const sortedNames = Array.from(attrNames).sort((a, b) => {
      const aHasPriority = priorityNames.some((p) => a.toLowerCase().includes(p));
      const bHasPriority = priorityNames.some((p) => b.toLowerCase().includes(p));

      if (aHasPriority && !bHasPriority) return -1;
      if (!aHasPriority && bHasPriority) return 1;
      return a.localeCompare(b);
    });

    // Take top 6 columns (name + 5 others)
    const topColumns = sortedNames.slice(0, 5);

    return [
      // Always include entity name/identifier as first column
      {
        key: 'name',
        label: 'Name',
        sortable: true,
      },
      ...topColumns.map((name) => ({
        key: name,
        label: name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
        sortable: true,
      })),
    ];
  };

  // Transform entities to table rows
  const getRowsForType = (typeEntities: any[]) => {
    return typeEntities.map((entity) => {
      // Extract name/identifier
      const name =
        entity.attributes?.find((a: any) => a.function === 'publicIdentifier')?.value ||
        entity.name ||
        entity.id;

      // Build row object with attribute values
      const row: any = {
        id: entity.id,
        name,
      };

      entity.attributes?.forEach((attr: any) => {
        // Skip identifier (already in name column)
        if (attr.function === 'identifier' || attr.function === 'publicIdentifier') return;
        // Skip long text
        if (attr.widget === 'long_text') return;

        row[attr.name] = attr.value;
      });

      return row;
    });
  };

  // Render sections for each entity type
  const sections = Object.entries(entityGroups);

  if (sections.length === 0) {
    return null; // No secondary entity types to display
  }

  return (
    <div className="space-y-6">
      {sections.map(([typeName, typeEntities]) => {
        const Icon = getTypeIcon(typeName);
        const title = getTypeTitle(typeName);
        const columns = getColumnsForType(typeEntities);
        const rows = getRowsForType(typeEntities);
        const stats = computeStats(typeEntities);
        const isCollapsed = collapsedSections.has(typeName);
        const isNew = newEntityTypes.has(typeName);

        // Generate section ID for scroll target
        const sectionId = `section-${typeName.toLowerCase().replace(/\s+/g, '-')}`;

        // Build summary text
        const summaryParts: string[] = [];
        if (stats.minPrice !== null && stats.maxPrice !== null) {
          if (stats.minPrice === stats.maxPrice) {
            summaryParts.push(formatPrice(stats.minPrice)!);
          } else {
            summaryParts.push(`${formatPrice(stats.minPrice)} - ${formatPrice(stats.maxPrice)}`);
          }
        }
        if (stats.avgRating !== null) {
          summaryParts.push(`★ ${stats.avgRating.toFixed(1)}`);
        }
        const summaryText = summaryParts.length > 0 ? summaryParts.join(' · ') : null;

        return (
          <motion.section
            key={`section-${typeName}`}
            id={sectionId}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`space-y-3 scroll-mt-20 rounded-lg ${
              isNew ? 'ring-2 ring-primary/50 shadow-lg shadow-primary/20 p-4 bg-primary/5' : ''
            }`}
          >
            {/* Section Header - Clickable to toggle collapse */}
            <button
              onClick={() => toggleSection(typeName)}
              className="w-full flex items-center gap-3 text-left hover:opacity-80 transition-opacity"
            >
              <div className="rounded-lg bg-primary/10 p-2">
                <Icon className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <h2 className="text-lg font-semibold text-foreground">{title}</h2>
                  <span className="text-sm text-muted-foreground">
                    {typeEntities.length} {typeEntities.length === 1 ? 'option' : 'options'}
                  </span>
                </div>
                {summaryText && (
                  <p className="text-sm text-muted-foreground">{summaryText}</p>
                )}
              </div>
              <div className="flex-shrink-0">
                {isCollapsed ? (
                  <ChevronDown className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <ChevronUp className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
            </button>

            {/* Table - Collapsible */}
            <AnimatePresence initial={false}>
              {!isCollapsed && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2, ease: 'easeInOut' }}
                  style={{ overflow: 'hidden' }}
                >
                  <ComparisonTable
                    items={rows}
                    columns={columns}
                    striped={true}
                    highlightBest={false}
                    onRowClick={(item) => {
                      console.log('[DynamicEntitySections] Row clicked:', item);
                      // Could open entity details here
                    }}
                    onRowDelete={onDeleteEntity ? (item) => {
                      onDeleteEntity(item.id);
                    } : undefined}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.section>
        );
      })}
    </div>
  );
};
