/**
 * ExpandedMetricCard - Inline Expanded View
 *
 * Shows detailed breakdown when a metric card is expanded.
 * Renders instantly with entity data, fully dynamic.
 *
 * Features:
 * - Detailed attribute breakdown from entity
 * - Child entities/sub-items display
 * - Contextual action suggestions from entity metadata
 * - <100ms render time (local first)
 */

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { bus } from '@/utils/eventBus';
import { Sparkles, Copy, Check } from 'lucide-react';

interface ExpandedMetricCardProps {
  entityId: string;
  entity?: any; // Full entity object with attributes
  relatedEntities?: any[]; // Related entities for suggestions
  onAction?: (action: any) => void;
}

export const ExpandedMetricCard = ({
  entityId,
  entity,
  relatedEntities = [],
  onAction
}: ExpandedMetricCardProps) => {
  const [copiedValue, setCopiedValue] = useState<string | null>(null);

  useEffect(() => {
    // Emit event for analytics/tracking
    bus.emit('DETAILS_VIEWED', { entityId });
  }, [entityId]);

  // Copy to clipboard handler
  const handleCopy = async (value: string, label: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedValue(label);
      setTimeout(() => setCopiedValue(null), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  // Extract detailed attributes (non-identifier, non-computed)
  const detailAttributes = useMemo(() => {
    if (!entity?.attributes) return [];

    return entity.attributes.filter((attr: any) => {
      const role = attr.function || attr.metadata?.role;
      const isHidden = attr.metadata?.hidden || role === 'identifier';
      const isMainField = role === 'publicIdentifier' || attr.metadata?.thumbnail;

      // Show detail fields, but not identifiers or main display fields
      return !isHidden && !isMainField && attr.value !== null && attr.value !== undefined;
    });
  }, [entity]);

  // Extract array/child attributes for separate display
  const arrayAttributes = useMemo(() => {
    if (!entity?.attributes) return [];

    return entity.attributes.filter((attr: any) =>
      attr.data_type === 'array' && Array.isArray(attr.value) && attr.value.length > 0
    );
  }, [entity]);

  // Generate contextual suggestions based on entity type and available actions
  const suggestions = useMemo(() => {
    const actions: string[] = [];

    // If there are similar entities, suggest comparison
    const similarEntities = relatedEntities.filter((e: any) => e.type === entity?.type);
    if (similarEntities.length > 0) {
      actions.push(`Compare with ${similarEntities[0].attributes?.find((a: any) => a.function === 'publicIdentifier')?.value || 'others'}`);
    }

    // Add metadata-defined suggestions
    if (entity?.metadata?.suggested_actions) {
      actions.push(...entity.metadata.suggested_actions);
    }

    // Add generic actions if none exist
    if (actions.length === 0) {
      actions.push('View full details', 'Share');
    }

    return actions;
  }, [entity, relatedEntities]);

  // If no entity data, show minimal loading state
  if (!entity) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.1 }}
        className="mt-3 rounded-md border border-zinc-800 bg-zinc-900/40 p-3 text-center text-sm text-zinc-500"
      >
        Loading details...
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.15 }}
      className="mt-3 rounded-md border border-zinc-800 bg-zinc-900/40 p-3"
    >
      {/* Detailed Attributes with interactive copy */}
      {detailAttributes.length > 0 && (
        <div className="mb-3">
          <div className="mb-2 text-xs font-medium text-zinc-400">Details</div>
          <div className="space-y-1.5">
            {detailAttributes.map((attr: any, idx: number) => {
              const formattedValue = formatAttributeValue(attr);
              const isCopied = copiedValue === attr.name;

              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="group flex items-start justify-between gap-2 text-sm"
                >
                  <span className="text-zinc-400">{attr.name.replace(/_/g, ' ')}:</span>
                  <div className="flex flex-1 items-center justify-end gap-2">
                    <span className="font-medium text-zinc-100">
                      {formattedValue}
                    </span>
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => handleCopy(String(formattedValue), attr.name)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity rounded p-1 hover:bg-zinc-800"
                      title="Copy to clipboard"
                    >
                      {isCopied ? (
                        <Check className="h-3 w-3 text-green-500" />
                      ) : (
                        <Copy className="h-3 w-3 text-zinc-500" />
                      )}
                    </motion.button>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Array/List Attributes (e.g., top_attractions, tasks, etc.) */}
      {arrayAttributes.map((attr: any, idx: number) => (
        <div key={idx} className="mb-3">
          <div className="mb-2 text-xs font-medium text-zinc-400">
            {attr.name.replace(/_/g, ' ')}
          </div>
          <div className="space-y-1">
            {attr.value.slice(0, 5).map((item: any, itemIdx: number) => (
              <div key={itemIdx} className="rounded bg-zinc-800/50 px-2 py-1 text-xs text-zinc-300">
                {typeof item === 'object' ? item.name || item.title || JSON.stringify(item) : item}
              </div>
            ))}
            {attr.value.length > 5 && (
              <div className="text-xs text-zinc-500">
                +{attr.value.length - 5} more
              </div>
            )}
          </div>
        </div>
      ))}

      {/* Insights from metadata */}
      {entity.metadata?.insights && entity.metadata.insights.length > 0 && (
        <div className="mb-3 rounded bg-zinc-800/50 p-2">
          <div className="mb-1 flex items-center gap-1 text-xs font-medium text-primary">
            <Sparkles className="h-3 w-3" />
            <span>Insights</span>
          </div>
          <ul className="space-y-0.5 text-xs text-zinc-400">
            {entity.metadata.insights.map((insight: string, idx: number) => (
              <li key={idx}>• {insight}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Contextual Action Suggestions */}
      {suggestions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion: string, idx: number) => (
            <button
              key={idx}
              className="rounded-full border border-zinc-700 bg-zinc-800/40 px-3 py-1 text-xs text-zinc-300 transition-all hover:border-primary hover:bg-primary/10 hover:text-primary"
              onClick={() => {
                bus.emit('SUGGESTION_CLICKED', { entityId, suggestion });
                onAction?.({ type: 'refine_query', params: { query: suggestion } });
              }}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </motion.div>
  );
};

/**
 * Format attribute value for display
 */
function formatAttributeValue(attr: any): string {
  const value = attr.value;

  // Handle currency
  if (attr.widget === 'currency' && typeof value === 'number') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  }

  // Handle dates
  if ((attr.widget === 'date' || attr.widget === 'datetime') && value) {
    try {
      return new Date(value).toLocaleDateString();
    } catch {
      return String(value);
    }
  }

  // Handle percentages
  if (attr.widget === 'percentage' && typeof value === 'number') {
    return `${value}%`;
  }

  // Handle objects
  if (typeof value === 'object' && value !== null) {
    // Extract lat/lng for location
    if ('lat' in value && 'lng' in value) {
      return `${value.lat}, ${value.lng}`;
    }
    return JSON.stringify(value);
  }

  return String(value);
}