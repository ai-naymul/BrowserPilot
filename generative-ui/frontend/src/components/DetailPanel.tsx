/**
 * DetailPanel - Right Pane Entity Details
 *
 * Features:
 * - Clean, organized entity details
 * - Tabbed interface (Overview | Costs | Notes)
 * - Editable fields with immediate feedback
 * - Suggested actions for entity
 *
 * Lighter weight than LocationPanel, designed for inline use in AppPanel
 */

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { X, MapPin, DollarSign, FileText, Star, ExternalLink } from 'lucide-react';
import { formatCurrencyOrNull, formatRatingOrNull, humanize, truncate } from '@/utils/formatters';
import { isValueMeaningful } from '@/utils/validators';

interface DetailPanelProps {
  entity: any;
  onClose: () => void;
  onAction?: (action: any) => void;
  onAttributeChange?: (entityId: string, attributeName: string, newValue: any) => void;
}

type TabId = 'overview' | 'costs' | 'notes';

export const DetailPanel = ({ entity, onClose, onAction, onAttributeChange }: DetailPanelProps) => {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [editingValues, setEditingValues] = useState<Record<string, any>>({});

  // Group attributes by category
  const sections = useMemo(() => {
    if (!entity?.attributes) {
      return { overview: [], costs: [], notes: [] };
    }

    const overview: any[] = [];
    const costs: any[] = [];
    const notes: any[] = [];

    entity.attributes.forEach((attr: any) => {
      const name = attr.name?.toLowerCase() || '';

      // Skip identifiers (shown in header)
      if (attr.function === 'identifier' || attr.function === 'publicIdentifier') {
        return;
      }

      // Cost-related
      if (
        name.includes('cost') ||
        name.includes('price') ||
        name.includes('budget') ||
        name.includes('fee') ||
        attr.widget === 'currency'
      ) {
        costs.push(attr);
      }
      // Notes/descriptions
      else if (
        name.includes('note') ||
        name.includes('description') ||
        name.includes('summary') ||
        attr.widget === 'long_text'
      ) {
        notes.push(attr);
      }
      // Overview
      else if (isValueMeaningful(attr.value)) {
        overview.push(attr);
      }
    });

    return { overview, costs, notes };
  }, [entity]);

  // Determine visible tabs
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

  // Entity display info
  const title = entity?.public_identifier || entity?.name || 'Details';
  const rating = entity?.attributes?.find((a: any) =>
    a.name?.toLowerCase().includes('rating') || a.widget === 'rating'
  )?.value;

  // Render editable field
  const renderEditableField = (attr: any) => {
    const currentValue = editingValues[attr.name] ?? attr.value;

    const handleChange = (newValue: any) => {
      setEditingValues(prev => ({ ...prev, [attr.name]: newValue }));
      onAttributeChange?.(entity.id, attr.name, newValue);
    };

    // Currency/Number input
    if (attr.widget === 'currency' || attr.widget === 'number') {
      return (
        <input
          type="number"
          value={currentValue || ''}
          onChange={(e) => handleChange(parseFloat(e.target.value) || 0)}
          className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:ring-2 focus:ring-primary focus:border-primary transition-all"
          placeholder="Enter value"
        />
      );
    }

    // Text input
    if (attr.widget === 'short_text' || !attr.widget) {
      return (
        <input
          type="text"
          value={currentValue || ''}
          onChange={(e) => handleChange(e.target.value)}
          className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:ring-2 focus:ring-primary focus:border-primary transition-all"
          placeholder="Enter value"
        />
      );
    }

    // Fallback to display value
    return renderValue(attr);
  };

  // Render attribute value
  const renderValue = (attr: any) => {
    const value = attr.value;

    if (!isValueMeaningful(value)) {
      return <span className="text-muted-foreground text-xs">—</span>;
    }

    if (attr.widget === 'currency') {
      return (
        <span className="font-medium text-foreground">
          {formatCurrencyOrNull(value) || value}
        </span>
      );
    }

    if (attr.widget === 'rating') {
      return (
        <span className="flex items-center gap-1 text-amber-300">
          <Star className="h-3.5 w-3.5 fill-current" />
          {formatRatingOrNull(value) || value}
        </span>
      );
    }

    if (Array.isArray(value)) {
      return (
        <div className="flex flex-wrap gap-1">
          {value.slice(0, 5).map((item: any, idx: number) => (
            <span key={idx} className="px-2 py-0.5 text-xs bg-accent/10 rounded-full text-muted-foreground">
              {typeof item === 'string' ? item : item.name || item.label || JSON.stringify(item)}
            </span>
          ))}
          {value.length > 5 && (
            <span className="text-xs text-muted-foreground">+{value.length - 5} more</span>
          )}
        </div>
      );
    }

    if (typeof value === 'object' && value !== null) {
      return (
        <div className="text-xs text-muted-foreground">
          {Object.entries(value).slice(0, 3).map(([k, v]) => (
            <div key={k}>{humanize(k)}: {String(v)}</div>
          ))}
        </div>
      );
    }

    const strValue = String(value);
    return (
      <span className="text-foreground">
        {strValue.length > 150 ? truncate(strValue, 150) : strValue}
      </span>
    );
  };

  if (!entity) return null;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 p-4 border-b border-border bg-gradient-to-r from-primary/5 to-transparent">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-foreground truncate">{title}</h3>
          {rating && (
            <div className="flex items-center gap-1 mt-1">
              <Star className="h-4 w-4 text-amber-300 fill-current" />
              <span className="text-sm font-medium text-amber-300">{rating}</span>
            </div>
          )}
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-accent/10 text-muted-foreground hover:text-foreground transition-all"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Tabs */}
      {visibleTabs.length > 1 && (
        <div className="flex border-b border-border bg-background/50 px-4">
          {visibleTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium transition-colors ${
                  isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
                {isActive && (
                  <motion.div
                    layoutId="detailActiveTab"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-3">
          {sections[activeTab].map((attr: any, idx: number) => (
            <motion.div
              key={`${attr.name}-${idx}`}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.02 }}
              className="rounded-lg border border-border bg-card/50 p-3"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {humanize(attr.name)}
                </div>
                {attr.editable && (
                  <span className="text-xs text-primary">Editable</span>
                )}
              </div>
              <div className="text-sm">
                {attr.editable ? renderEditableField(attr) : renderValue(attr)}
              </div>
            </motion.div>
          ))}

          {sections[activeTab].length === 0 && (
            <div className="text-center text-muted-foreground py-8 text-sm">
              No {activeTab} information available
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      {entity.metadata?.suggested_actions && entity.metadata.suggested_actions.length > 0 && (
        <div className="border-t border-border p-4 bg-background/50">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
            Quick Actions
          </h4>
          <div className="flex flex-wrap gap-2">
            {entity.metadata.suggested_actions.slice(0, 3).map((action: string, idx: number) => (
              <button
                key={idx}
                onClick={() => onAction?.({ type: 'refine_query', params: { query: action } })}
                className="px-3 py-1.5 text-xs font-medium rounded-lg border border-primary/30 bg-primary/10 text-primary hover:bg-primary/20 transition-all"
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
