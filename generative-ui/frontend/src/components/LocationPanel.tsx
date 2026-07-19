/**
 * LocationPanel - Curated Side Panel for Entity Details
 *
 * Opens when a card or map marker is clicked. Features:
 * - Digestible, curated summary (not full raw form)
 * - Tabbed interface (Overview | Costs | Notes)
 * - Proper array/object formatting
 * - Text truncation with expand
 * - No React key warnings
 */

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { X, MapPin, DollarSign, FileText, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { bus } from '@/utils/eventBus';
import { useEntityStore } from '@/store/EntityStore';
import { formatCurrencyOrNull, formatRatingOrNull, humanize, truncate } from '@/utils/formatters';
import { isValueMeaningful } from '@/utils/validators';

interface LocationPanelProps {
  entity: any;
  onClose: () => void;
  onAction?: (action: any) => void;
}

type TabId = 'overview' | 'costs' | 'notes';

export const LocationPanel = ({ entity, onClose, onAction }: LocationPanelProps) => {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [expandedFields, setExpandedFields] = useState<Set<string>>(new Set());
  const entityStore = useEntityStore();

  // Get live entity from store
  const liveEntity = entityStore.getEntity(entity?.id) || entity;

  useEffect(() => {
    if (liveEntity?.id) {
      bus.emit('PANEL_OPENED', { entityId: liveEntity.id });
    }
  }, [liveEntity?.id]);

  // Group attributes by category with schema-aware logic
  const sections = useMemo(() => {
    if (!liveEntity?.attributes) {
      return { overview: [], costs: [], notes: [] };
    }

    const overview: any[] = [];
    const costs: any[] = [];
    const notes: any[] = [];

    liveEntity.attributes.forEach((attr: any) => {
      const name = attr.name?.toLowerCase() || '';

      // Skip identifiers (already shown in header)
      if (attr.function === 'identifier' || attr.function === 'publicIdentifier') {
        return;
      }

      // Cost-related attributes
      if (
        name.includes('cost') ||
        name.includes('price') ||
        name.includes('budget') ||
        name.includes('fee') ||
        name.includes('accommodation') ||
        name.includes('transport') ||
        name.includes('food') ||
        name.includes('activities') ||
        attr.widget === 'currency'
      ) {
        costs.push(attr);
      }
      // Notes/long descriptions/reasoning
      else if (
        name.includes('note') ||
        name.includes('description') ||
        name.includes('reasoning') ||
        name.includes('summary') ||
        attr.widget === 'long_text'
      ) {
        notes.push(attr);
      }
      // Overview: key facts, ratings, arrays, important info
      else if (
        attr.widget === 'rating' ||
        attr.widget === 'array' ||
        name.includes('rating') ||
        name.includes('top_') ||
        name.includes('best_') ||
        name.includes('language') ||
        name.includes('currency') ||
        name.includes('country') ||
        name.includes('location') ||
        (attr.function !== 'computed' && isValueMeaningful(attr.value))
      ) {
        overview.push(attr);
      }
    });

    return { overview, costs, notes };
  }, [liveEntity]);

  // Determine which tabs to show
  const visibleTabs = useMemo(() => {
    const tabs: Array<{ id: TabId; label: string; icon: any; count: number }> = [];

    if (sections.overview.length > 0) {
      tabs.push({ id: 'overview', label: 'Overview', icon: MapPin, count: sections.overview.length });
    }

    if (sections.costs.length > 0) {
      tabs.push({ id: 'costs', label: 'Costs', icon: DollarSign, count: sections.costs.length });
    }

    if (sections.notes.length > 0) {
      tabs.push({ id: 'notes', label: 'Notes', icon: FileText, count: sections.notes.length });
    }

    return tabs;
  }, [sections]);

  // Auto-select first visible tab
  useEffect(() => {
    if (visibleTabs.length > 0 && !visibleTabs.find((t) => t.id === activeTab)) {
      setActiveTab(visibleTabs[0].id);
    }
  }, [visibleTabs, activeTab]);

  // Get title
  const title =
    liveEntity?.attributes?.find((a: any) => a.function === 'publicIdentifier')?.value ||
    liveEntity?.public_identifier ||
    liveEntity?.name ||
    'Details';

  // Copy to clipboard
  const handleCopy = (value: string, fieldName: string) => {
    navigator.clipboard.writeText(value);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  };

  // Toggle field expansion
  const toggleExpand = (fieldKey: string) => {
    setExpandedFields((prev) => {
      const next = new Set(prev);
      if (next.has(fieldKey)) {
        next.delete(fieldKey);
      } else {
        next.add(fieldKey);
      }
      return next;
    });
  };

  // Render attribute value with proper formatting
  const renderValue = (attr: any, fieldKey: string) => {
    const value = attr.value;

    // Empty/meaningless value
    if (!isValueMeaningful(value)) {
      return (
        <button
          onClick={() => {
            console.log('[LocationPanel] Edit field:', attr.name);
          }}
          className="text-xs text-muted-foreground hover:text-primary transition-colors px-2 py-1 rounded border border-dashed border-border hover:border-primary"
        >
          + Add details
        </button>
      );
    }

    // Format based on widget
    if (attr.widget === 'currency') {
      const formatted = formatCurrencyOrNull(value);
      return <div className="text-sm font-medium text-foreground">{formatted || value}</div>;
    }

    if (attr.widget === 'rating') {
      const formatted = formatRatingOrNull(value);
      return <div className="text-sm font-medium text-primary">{formatted || value}</div>;
    }

    // Array: render as clean list with object support
    if (Array.isArray(value)) {
      const isExpanded = expandedFields.has(fieldKey);
      const displayItems = isExpanded ? value : value.slice(0, 3);

      return (
        <div className="space-y-2">
          {displayItems.map((item: any, idx: number) => {
            if (typeof item === 'object' && item !== null) {
              // Object in array (e.g., attraction, flight option)
              const name = item.name || item.title || item.label || `Item ${idx + 1}`;
              const description = item.description || item.summary || '';

              return (
                <div
                  key={`${fieldKey}-item-${idx}`}
                  className="rounded border border-white/10 bg-white/5 p-2 text-sm"
                >
                  <div className="font-medium text-foreground">{name}</div>
                  {description && (
                    <div className="mt-1 text-xs text-muted-foreground">
                      {truncate(description, 120)}
                    </div>
                  )}
                </div>
              );
            } else {
              // Primitive in array
              return (
                <div key={`${fieldKey}-item-${idx}`} className="text-sm text-foreground">
                  • {String(item)}
                </div>
              );
            }
          })}

          {value.length > 3 && (
            <button
              onClick={() => toggleExpand(fieldKey)}
              className="text-xs text-primary hover:underline flex items-center gap-1"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3 w-3" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3" />
                  Show {value.length - 3} more
                </>
              )}
            </button>
          )}
        </div>
      );
    }

    // Object: render key-value pairs
    if (typeof value === 'object' && value !== null) {
      const entries = Object.entries(value);
      return (
        <div className="space-y-1 text-xs">
          {entries.map(([key, val]) => (
            <div key={key} className="flex justify-between gap-2">
              <span className="text-muted-foreground">{humanize(key)}:</span>
              <span className="font-medium text-foreground">{String(val)}</span>
            </div>
          ))}
        </div>
      );
    }

    // String: truncate if long
    const strValue = String(value);
    const isExpanded = expandedFields.has(fieldKey);

    if (strValue.length > 200 && !isExpanded) {
      return (
        <div className="text-sm text-foreground space-y-2">
          <div>{truncate(strValue, 200)}</div>
          <button
            onClick={() => toggleExpand(fieldKey)}
            className="text-xs text-primary hover:underline flex items-center gap-1"
          >
            <ChevronDown className="h-3 w-3" />
            Show more
          </button>
        </div>
      );
    } else if (strValue.length > 200 && isExpanded) {
      return (
        <div className="text-sm text-foreground space-y-2">
          <div>{strValue}</div>
          <button
            onClick={() => toggleExpand(fieldKey)}
            className="text-xs text-primary hover:underline flex items-center gap-1"
          >
            <ChevronUp className="h-3 w-3" />
            Show less
          </button>
        </div>
      );
    }

    return <div className="text-sm text-foreground">{strValue}</div>;
  };

  if (!liveEntity) return null;

  return (
    <>
      {/* Panel */}
      <motion.aside
        key={`panel-${liveEntity.id}`}
        initial={{ x: '100%', opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: '100%', opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="fixed right-0 top-0 z-50 glass-dark border-l border-white/10 shadow-apple-xl"
        style={{
          width: 'clamp(340px, 28vw, 480px)',
          height: '100vh',
          backdropFilter: 'blur(40px) saturate(180%)',
          WebkitBackdropFilter: 'blur(40px) saturate(180%)',
        }}
      >
        {/* Header */}
        <div className="relative flex items-center justify-between border-b border-white/10 bg-gradient-to-r from-primary/10 to-transparent p-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="rounded-lg bg-primary/20 p-2 flex-shrink-0">
              <MapPin className="h-5 w-5 text-primary" />
            </div>
            <h2 className="text-lg font-semibold text-zinc-50 truncate">{title}</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-zinc-400 transition-apple hover:bg-white/10 hover:text-zinc-100 hover:scale-110 flex-shrink-0"
            aria-label="Close panel"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        {visibleTabs.length > 1 && (
          <div className="flex border-b border-white/10 bg-black/20 px-4">
            {visibleTabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`relative flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                    isActive ? 'text-primary' : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                  {isActive && (
                    <motion.div
                      layoutId={`activeTab-${liveEntity.id}`}
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                    />
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* Content with scroll */}
        <div className="overflow-y-auto" style={{ height: 'calc(100vh - 120px)' }}>
          <div className="px-4 py-4 space-y-3">
            {sections[activeTab].map((attr: any, idx: number) => {
              const fieldKey = `${activeTab}-${attr.name}-${idx}`;
              const isCopied = copiedField === fieldKey;

              return (
                <motion.div
                  key={fieldKey}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: Math.min(idx * 0.03, 0.3) }}
                  className="rounded-lg border border-white/10 bg-white/5 p-3 transition-apple hover:bg-white/10 hover:border-white/20"
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
                      {humanize(attr.name)}
                    </div>
                    {isValueMeaningful(attr.value) && typeof attr.value === 'string' && (
                      <button
                        onClick={() => handleCopy(String(attr.value), fieldKey)}
                        className="p-1 rounded hover:bg-white/10 transition-colors"
                        aria-label="Copy to clipboard"
                      >
                        {isCopied ? (
                          <Check className="h-3 w-3 text-green-500" />
                        ) : (
                          <Copy className="h-3 w-3 text-zinc-500" />
                        )}
                      </button>
                    )}
                  </div>
                  {renderValue(attr, fieldKey)}
                  {attr.help_text && <div className="mt-1 text-xs text-zinc-500">{attr.help_text}</div>}
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Quick Actions */}
        {liveEntity.metadata?.suggested_actions && liveEntity.metadata.suggested_actions.length > 0 && (
          <div className="border-t border-white/10 p-4 bg-black/20">
            <h3 className="mb-3 text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Quick Actions
            </h3>
            <div className="flex flex-wrap gap-2">
              {liveEntity.metadata.suggested_actions.map((action: string, idx: number) => (
                <button
                  key={`action-${idx}`}
                  onClick={() => {
                    onAction?.({ type: 'refine_query', params: { query: action } });
                  }}
                  className="rounded-lg border border-primary/30 bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary transition-apple hover:border-primary/50 hover:bg-primary/20"
                >
                  {action}
                </button>
              ))}
            </div>
          </div>
        )}
      </motion.aside>

      {/* Backdrop */}
      <motion.div
        key={`backdrop-${liveEntity.id}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
      />
    </>
  );
};
