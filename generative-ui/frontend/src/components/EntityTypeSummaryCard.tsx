/**
 * EntityTypeSummaryCard - Compact summary card for an entity type
 *
 * Shows when new non-primary entity types appear (Flights, Hotels, etc.)
 * Appears near the top of Cards view, below main metric cards
 *
 * Features:
 * - Count of entities of this type
 * - Basic stats (min/max/avg price, ratings)
 * - CTA to scroll to detailed section
 */

import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Plane,
  Hotel,
  Activity,
  Package,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Star,
  X,
  type LucideIcon
} from 'lucide-react';
import { Card } from '@/components/ui/card';

interface EntityTypeSummaryCardProps {
  entityType: string;
  entities: any[];
  onViewDetails: () => void;
  onDelete?: () => void; // Callback to delete all entities of this type
  isNew?: boolean;
}

// Get icon based on entity type name
function getTypeIcon(typeName: string): LucideIcon {
  const name = typeName.toLowerCase();
  if (name.includes('flight') || name.includes('plane')) return Plane;
  if (name.includes('hotel') || name.includes('accommodation') || name.includes('stay')) return Hotel;
  if (name.includes('activity') || name.includes('tour') || name.includes('itinerary')) return Activity;
  return Package;
}

// Generate human-readable title from entity type
function getTypeTitle(typeName: string): string {
  let cleaned = typeName.replace(/^(entity_|item_)/i, '').replace(/(_\d+|_option)$/i, '');
  cleaned = cleaned.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim();
  return cleaned.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
}

// Extract price-like values from entity attributes
function extractPriceValue(entity: any): number | null {
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
}

// Extract rating-like values
function extractRatingValue(entity: any): number | null {
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
}

export function EntityTypeSummaryCard({
  entityType,
  entities,
  onViewDetails,
  onDelete,
  isNew = false
}: EntityTypeSummaryCardProps) {
  const Icon = getTypeIcon(entityType);
  const title = getTypeTitle(entityType);
  const count = entities.length;
  const [isHovered, setIsHovered] = useState(false);

  // Compute stats
  const stats = useMemo(() => {
    const prices = entities.map(extractPriceValue).filter((p): p is number => p !== null);
    const ratings = entities.map(extractRatingValue).filter((r): r is number => r !== null);

    return {
      minPrice: prices.length > 0 ? Math.min(...prices) : null,
      maxPrice: prices.length > 0 ? Math.max(...prices) : null,
      avgPrice: prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : null,
      avgRating: ratings.length > 0 ? ratings.reduce((a, b) => a + b, 0) / ratings.length : null,
    };
  }, [entities]);

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

  const summaryText = summaryParts.length > 0 ? summaryParts.join(' · ') : 'View details';

  return (
    <motion.div
      initial={{ opacity: 0, y: -10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, type: 'spring', stiffness: 300 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Card
        className={`relative overflow-hidden transition-all duration-200 hover:shadow-lg hover:scale-[1.02] cursor-pointer ${
          isNew ? 'ring-2 ring-primary/50 shadow-primary/20' : ''
        }`}
        onClick={onViewDetails}
      >
        {/* Delete button - appears on hover */}
        {onDelete && isHovered && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="absolute top-2 right-2 p-1 rounded-md bg-destructive/10 hover:bg-destructive/20 text-destructive transition-colors z-10"
            title={`Delete all ${count} ${title.toLowerCase()}`}
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}

        {/* New indicator */}
        {isNew && !isHovered && (
          <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-primary text-primary-foreground text-xs font-medium animate-pulse">
            New
          </div>
        )}

        <div className="p-4">
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className="rounded-lg bg-primary/10 p-2.5 flex-shrink-0">
              <Icon className="h-5 w-5 text-primary" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 mb-1">
                <h3 className="text-base font-semibold text-foreground truncate">
                  {title}
                </h3>
                <span className="text-sm text-muted-foreground flex-shrink-0">
                  {count} {count === 1 ? 'option' : 'options'}
                </span>
              </div>

              <p className="text-sm text-muted-foreground mb-2">
                {summaryText}
              </p>

              {/* CTA */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onViewDetails();
                }}
                className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
              >
                <span>View and compare</span>
                <ChevronRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
