/**
 * EntityList - Scrollable Entity List for Left Pane
 *
 * Features:
 * - Compact entity cards with key stats
 * - Rating, price, and tag badges
 * - Selection highlight with animated indicator
 * - Search/filter support
 *
 * Inspired by: 温泉コンシェルジュ hotel list
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Star, Trash2, MapPin, Globe, DollarSign } from 'lucide-react';
import { formatCurrencyOrNull } from '@/utils/formatters';

interface EntityListProps {
  entities: any[];
  selectedEntityId: string | null;
  onSelectEntity: (entityId: string) => void;
  onDeleteEntity?: (entityId: string) => void;
}

export const EntityList = ({
  entities,
  selectedEntityId,
  onSelectEntity,
  onDeleteEntity,
}: EntityListProps) => {
  const [searchQuery, setSearchQuery] = useState('');

  // Filter entities by search
  const filteredEntities = useMemo(() => {
    if (!searchQuery.trim()) return entities;
    const query = searchQuery.toLowerCase();
    return entities.filter(e => {
      const name = (e.public_identifier || e.name || e.id || '').toLowerCase();
      return name.includes(query);
    });
  }, [entities, searchQuery]);

  // Extract key attributes from entity
  const getEntityStats = (entity: any) => {
    const attrs = entity.attributes || [];

    // Rating
    const rating = attrs.find((a: any) =>
      a.name?.toLowerCase().includes('rating') || a.widget === 'rating'
    )?.value;

    // Price/Cost - Prioritize total/computed costs over individual components
    const price = (() => {
      // Strategy 1: Look for computed total cost first
      const computedTotal = attrs.find((a: any) =>
        a.function === 'computed' &&
        a.widget === 'currency' &&
        (a.name?.toLowerCase().includes('total') || a.name?.toLowerCase().includes('estimated'))
      );
      if (computedTotal) return computedTotal.value;

      // Strategy 2: Look for explicit total_cost or total_budget
      const totalCost = attrs.find((a: any) =>
        (a.name?.toLowerCase() === 'total_cost' ||
         a.name?.toLowerCase() === 'total_budget' ||
         a.name?.toLowerCase() === 'estimated_total_cost') &&
        a.widget === 'currency'
      );
      if (totalCost) return totalCost.value;

      // Strategy 3: Fallback to any cost/price field (but avoid accommodation_cost if total exists)
      const anyCost = attrs.find((a: any) =>
        (a.name?.toLowerCase().includes('cost') ||
         a.name?.toLowerCase().includes('price') ||
         a.name?.toLowerCase().includes('budget')) &&
        a.widget === 'currency'
      );
      return anyCost?.value;
    })();

    // Location
    const location = attrs.find((a: any) =>
      a.name?.toLowerCase().includes('location') ||
      a.name?.toLowerCase().includes('address') ||
      a.name?.toLowerCase().includes('city')
    )?.value;

    // Tags (from attributes or entity tags)
    const tags = entity.tags || attrs.find((a: any) =>
      a.name?.toLowerCase().includes('tag') ||
      a.name?.toLowerCase().includes('feature') ||
      a.data_type === 'array'
    )?.value || [];

    // Description/Summary
    const description = attrs.find((a: any) =>
      a.name?.toLowerCase().includes('description') ||
      a.name?.toLowerCase().includes('summary')
    )?.value;

    return { rating, price, location, tags, description };
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with count */}
      <div className="px-4 py-3 border-b border-border">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            {entities[0]?.type || 'Items'}
          </span>
          <span className="text-xs text-muted-foreground">
            {filteredEntities.length} {filteredEntities.length === 1 ? 'item' : 'items'}
          </span>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
          />
        </div>
      </div>

      {/* Entity List */}
      <div className="flex-1 overflow-y-auto">
        {filteredEntities.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-muted-foreground text-sm">
            No items found
          </div>
        ) : (
          <div className="p-3 space-y-2">
            <AnimatePresence>
              {filteredEntities.map((entity, idx) => {
                const isSelected = entity.id === selectedEntityId;
                const stats = getEntityStats(entity);
                const displayName = entity.public_identifier || entity.name || entity.id;
                const country = entity.attributes?.find((a: any) => a.name === 'country')?.value;

                return (
                  <motion.div
                    key={entity.id}
                    layout
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -20, scale: 0.95 }}
                    transition={{
                      delay: idx * 0.05,
                      type: 'spring',
                      stiffness: 400,
                      damping: 30
                    }}
                    onClick={() => onSelectEntity(entity.id)}
                    className={`group relative p-4 rounded-2xl border cursor-pointer transition-all duration-200 overflow-hidden ${
                      isSelected
                        ? 'bg-primary/15 border-primary/40 shadow-lg shadow-primary/10'
                        : 'bg-card border-border/60 hover:bg-card/90 hover:border-border hover:shadow-md'
                    }`}
                  >
                    {/* Selection indicator */}
                    {isSelected && (
                      <motion.div
                        layoutId="selectedIndicator"
                        className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l-2xl"
                        initial={false}
                        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                      />
                    )}

                    {/* Entity icon */}
                    <div className="flex items-start gap-3">
                      <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-lg ${
                        isSelected ? 'bg-primary/20' : 'bg-muted/30'
                      }`}>
                        {entity.icon || <Globe className="h-5 w-5 text-muted-foreground" />}
                      </div>

                      <div className="flex-1 min-w-0">
                        {/* Name */}
                        <h4 className={`font-semibold text-sm truncate ${
                          isSelected ? 'text-primary' : 'text-foreground'
                        }`}>
                          {displayName}
                        </h4>

                        {/* Country/Location */}
                        {(country || stats.location) && (
                          <div className="flex items-center gap-1 mt-0.5">
                            <MapPin className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground truncate">
                              {country || (typeof stats.location === 'string' ? stats.location : 'Location')}
                            </span>
                          </div>
                        )}

                        {/* Price badge */}
                        {stats.price && (
                          <div className="flex items-center gap-1.5 mt-2">
                            <DollarSign className="h-3.5 w-3.5 text-primary" />
                            <span className="text-sm font-bold text-foreground">
                              {formatCurrencyOrNull(stats.price) || `$${stats.price}`}
                            </span>
                            <span className="text-xs text-muted-foreground">7-day budget</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Rating and Tags row */}
                    <div className="flex items-center gap-2 mt-3 flex-wrap">
                      {/* Rating */}
                      {stats.rating && (
                        <div className="flex items-center gap-1 px-2 py-1 bg-amber-500/15 text-amber-400 rounded-lg">
                          <Star className="h-3 w-3 fill-current" />
                          <span className="text-xs font-semibold">{stats.rating}/10</span>
                        </div>
                      )}

                      {/* Tags */}
                      {Array.isArray(stats.tags) && stats.tags.slice(0, 2).map((tag: string, tagIdx: number) => (
                        <span
                          key={tagIdx}
                          className="px-2 py-1 text-xs bg-muted/50 text-muted-foreground rounded-lg border border-border/50"
                        >
                          {typeof tag === 'string' ? tag : tag.name || tag.label || 'Tag'}
                        </span>
                      ))}
                    </div>

                    {/* Delete button (on hover) */}
                    {onDeleteEntity && (
                      <motion.button
                        initial={{ opacity: 0, scale: 0.8 }}
                        whileHover={{ scale: 1.1 }}
                        animate={{ opacity: isSelected ? 0.7 : 0 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteEntity(entity.id);
                        }}
                        className="absolute top-3 right-3 p-1.5 rounded-lg bg-destructive/10 hover:bg-destructive/20 text-destructive transition-all group-hover:opacity-100"
                        title="Delete"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </motion.button>
                    )}
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
};
