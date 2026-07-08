import { ChevronDown, ChevronRight, LayoutGrid, TrendingUp, TrendingDown } from 'lucide-react';
import { useState, useMemo } from 'react';
import { Entity } from '@/types/entity';
import { cn } from '@/lib/utils';

interface EntitySidebarProps {
  entities: Entity[];
  selectedId?: string;
  onSelect: (entity: Entity) => void;
  onSwitchToCards?: (entityType?: string) => void; // Callback to switch to Cards view and scroll to type
}

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

// Type Group Section Component
const TypeGroupSection = ({
  typeName,
  entities,
  selectedId,
  onSelect,
  onSwitchToCards,
}: {
  typeName: string;
  entities: Entity[];
  selectedId?: string;
  onSelect: (entity: Entity) => void;
  onSwitchToCards?: (entityType: string) => void;
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  // Compute stats for this type
  const stats = useMemo(() => {
    const prices = entities.map(extractPriceValue).filter((p): p is number => p !== null);
    const ratings = entities.map(extractRatingValue).filter((r): r is number => r !== null);

    return {
      count: entities.length,
      minPrice: prices.length > 0 ? Math.min(...prices) : null,
      maxPrice: prices.length > 0 ? Math.max(...prices) : null,
      avgRating: ratings.length > 0 ? ratings.reduce((a, b) => a + b, 0) / ratings.length : null,
    };
  }, [entities]);

  // Format type name
  const title = typeName
    .replace(/^(entity_|item_)/i, '')
    .replace(/(_\d+|_option)$/i, '')
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');

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

  return (
    <div className="mb-4">
      {/* Type Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-muted/30 rounded-md">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 flex-1 text-left"
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          <div className="flex-1">
            <div className="text-sm font-semibold text-foreground">{title}</div>
            <div className="text-xs text-muted-foreground">
              {stats.count} {stats.count === 1 ? 'item' : 'items'}
              {summaryParts.length > 0 && ` · ${summaryParts.join(' · ')}`}
            </div>
          </div>
        </button>

        {/* View in Cards button */}
        {onSwitchToCards && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSwitchToCards(typeName);
            }}
            className="p-1.5 hover:bg-muted rounded text-muted-foreground hover:text-foreground transition-colors"
            title="View in Cards"
          >
            <LayoutGrid className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Entity List */}
      {isExpanded && (
        <div className="mt-1 space-y-0.5">
          {entities.map((entity) => (
            <EntityTreeItem
              key={entity.id}
              entity={entity}
              selectedId={selectedId}
              onSelect={onSelect}
              level={0}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const EntityTreeItem = ({ entity, selectedId, onSelect, level = 0 }: { 
  entity: Entity; 
  selectedId?: string; 
  onSelect: (entity: Entity) => void;
  level?: number;
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = entity.children && entity.children.length > 0;
  const isSelected = entity.id === selectedId;

  return (
    <div>
      <div
        onClick={() => onSelect(entity)}
        className={cn(
          "flex items-center gap-2 px-3 py-2 cursor-pointer transition-colors rounded-md",
          "hover:bg-muted/50",
          isSelected && "bg-accent/10 border-l-2 border-accent",
          !isSelected && "border-l-2 border-transparent"
        )}
        style={{ paddingLeft: `${level * 12 + 12}px` }}
      >
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            className="p-0 hover:bg-muted rounded"
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        )}
        {!hasChildren && <div className="w-4" />}
        <span className="text-base">{entity.icon}</span>
        <span className="text-sm font-medium flex-1 truncate">
          {entity.public_identifier}
        </span>
        {entity.tags?.map((tag) => (
          <span
            key={tag}
            className="text-xs px-1.5 py-0.5 bg-tag-info/20 text-tag-info rounded"
          >
            {tag}
          </span>
        ))}
      </div>
      {hasChildren && isExpanded && (
        <div>
          {entity.children!.map((child) => (
            <EntityTreeItem
              key={child.id}
              entity={child}
              selectedId={selectedId}
              onSelect={onSelect}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const EntitySidebar = ({ entities, selectedId, onSelect, onSwitchToCards }: EntitySidebarProps) => {
  // Group entities by type
  const entityGroups = useMemo(() => {
    const groups: Record<string, Entity[]> = {};

    // Flatten the hierarchy to group all entities by type
    const flattenEntities = (entityList: Entity[]): Entity[] => {
      const flat: Entity[] = [];
      entityList.forEach((entity) => {
        flat.push(entity);
        if (entity.children && entity.children.length > 0) {
          flat.push(...flattenEntities(entity.children));
        }
      });
      return flat;
    };

    const allEntities = flattenEntities(entities);

    allEntities.forEach((entity) => {
      const type = entity.type || 'Unknown';
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(entity);
    });

    // Sort groups by count (descending)
    return Object.entries(groups).sort(([, a], [, b]) => b.length - a.length);
  }, [entities]);

  return (
    <div className="w-60 bg-sidebar border-r border-sidebar-border overflow-y-auto">
      <div className="p-4">
        <h2 className="text-sm font-semibold text-muted-foreground mb-4">
          All Entities ({entityGroups.reduce((sum, [, ents]) => sum + ents.length, 0)})
        </h2>
        <div className="space-y-2">
          {entityGroups.map(([typeName, typeEntities]) => (
            <TypeGroupSection
              key={`type-${typeName}`}
              typeName={typeName}
              entities={typeEntities}
              selectedId={selectedId}
              onSelect={onSelect}
              onSwitchToCards={onSwitchToCards}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
