/**
 * MetricCard - Interactive Card with Expand/Hover Support
 *
 * Features:
 * - Inline expansion (click or press E when selected)
 * - Hover quick actions
 * - Keyboard navigation support
 * - Command history integration (undo/redo)
 * - Event bus communication
 * - Fully backward compatible with existing props
 */

import { useState, useCallback, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { LucideIcon, CheckCircle } from "lucide-react";
import { useUIContext } from "@/contexts/UIContext";
import { bus } from "@/utils/eventBus";
import { QuickActions, QuickAction } from "./QuickActions";
import { useEntity } from "@/store/EntityStore";

interface MetricCardProps {
  // Original props (backward compatible)
  label: string;
  value: string | number;
  sublabel?: string;
  trend?: {
    direction: "up" | "down";
    value: number;
  };
  icon?: LucideIcon;
  onClick?: () => void;

  // NEW: Enhanced interaction props
  id?: string; // Stable module ID (e.g., "metric_card_tokyo")
  entityId?: string; // Entity ID this card represents
  entity?: any; // Full entity object for expansion
  relatedEntities?: any[]; // Related entities for comparison
  onAction?: (action: any) => void; // Action handler
  onDelete?: (cardId: string) => void; // Delete handler
  enableExpand?: boolean; // Enable inline expansion (default: true)
  enableQuickActions?: boolean; // Enable hover quick actions (default: true)
}

export const MetricCard = ({
  label,
  value,
  sublabel,
  trend,
  icon: Icon,
  onClick,
  // NEW props
  id,
  entityId,
  entity,
  relatedEntities = [],
  onAction,
  onDelete,
  enableExpand = false, // Disabled by default - use sidebar instead
  enableQuickActions = true,
}: MetricCardProps) => {
  const [hovered, setHovered] = useState(false);
  const [flashHighlight, setFlashHighlight] = useState(false);
  const [previewHighlight, setPreviewHighlight] = useState(false);
  const { setSelected, selectedEntityId, selectedEntityIds, setLocationPanel } = useUIContext();

  // Get live entity data from store if entityId provided
  const liveEntity = useEntity(entityId);

  // Use live entity data for label if available, otherwise fall back to props
  const displayLabel = liveEntity?.public_identifier || label;
  const displayEntity = liveEntity || entity;

  // CRITICAL: Compute value from live entity if available (for real-time updates)
  const displayValue = useMemo(() => {
    if (!liveEntity?.attributes) return value;

    // Strategy 1: If sublabel indicates a specific attribute, show that attribute's value
    // Example: sublabel "Accommodation Cost" should match attribute "accommodation_cost"
    if (sublabel) {
      const normalizedSublabel = sublabel.toLowerCase().replace(/\s+/g, '_');
      const specificAttr = liveEntity.attributes.find((a: any) =>
        a.name.toLowerCase() === normalizedSublabel ||
        a.name.toLowerCase().replace(/_/g, ' ') === sublabel.toLowerCase()
      );

      if (specificAttr) {
        // Format based on widget type
        if (specificAttr.widget === 'currency') {
          const num = Number(specificAttr.value);
          return isNaN(num) ? value : `$${num.toLocaleString()}`;
        }
        return specificAttr.value;
      }
    }

    // Strategy 2: If this is a general entity card (no specific sublabel), show computed total
    // Only look for computed total if sublabel suggests this is a "total" or "estimated cost" card
    const isTotalCard = !sublabel ||
      sublabel.toLowerCase().includes('total') ||
      sublabel.toLowerCase().includes('estimated') ||
      sublabel.toLowerCase().includes('7-day cost');

    if (isTotalCard) {
      const computedTotal = liveEntity.attributes.find((a: any) =>
        a.function === 'computed' && a.name.includes('total') && a.widget === 'currency'
      );

      if (computedTotal) {
        const num = Number(computedTotal.value);
        return isNaN(num) ? value : `$${num.toLocaleString()}`;
      }
    }

    // Fallback to original value prop (for backward compatibility)
    return value;
  }, [liveEntity, value, sublabel]);

  // Generate stable ID if not provided
  const cardId = id || `metric_card_${entityId || label.toLowerCase().replace(/\s+/g, '_')}`;
  const isSelected = selectedEntityId === entityId;
  const isMultiSelected = entityId ? selectedEntityIds.includes(entityId) : false;

  // Extract 2-3 dynamic chips from entity (highlights/glimpses)
  const dynamicChips = useMemo(() => {
    if (!liveEntity?.attributes) return [];

    const chips: Array<{ label: string; value: string; type: string }> = [];

    // Find recently updated or important attributes
    const importantAttrs = liveEntity.attributes.filter((attr: any) => {
      // Skip identifiers and computed fields
      if (attr.function === 'identifier' || attr.function === 'publicIdentifier') return false;
      if (!attr.value) return false;

      // Prioritize: costs, counts, recent additions, dates
      const name = (attr.name || '').toLowerCase();
      const isCost = name.includes('cost') || name.includes('price') || name.includes('budget');
      const isCount = name.includes('count') || name.includes('total') || name.includes('number');
      const isDate = attr.widget === 'date' || name.includes('date');

      return isCost || isCount || isDate;
    }).slice(0, 3); // Max 3 chips

    importantAttrs.forEach((attr: any) => {
      let formattedValue = String(attr.value);

      // Format by widget type
      if (attr.widget === 'currency' && !isNaN(Number(attr.value))) {
        formattedValue = `$${Number(attr.value).toLocaleString()}`;
      } else if (attr.widget === 'date') {
        try {
          formattedValue = new Date(attr.value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch {}
      } else if (typeof attr.value === 'number') {
        formattedValue = attr.value.toLocaleString();
      }

      // Truncate long values
      if (formattedValue.length > 20) {
        formattedValue = formattedValue.substring(0, 17) + '...';
      }

      chips.push({
        label: attr.name.replace(/_/g, ' '),
        value: formattedValue,
        type: attr.widget || 'text'
      });
    });

    return chips;
  }, [liveEntity]);

  // Listen for related module updates (flash highlight)
  useEffect(() => {
    const unsubscribe = bus.on('MODULE_UPDATED', (event: any) => {
      if (event.moduleId === cardId) {
        setFlashHighlight(true);
        setTimeout(() => setFlashHighlight(false), 300);
      }
    });
    return unsubscribe;
  }, [cardId]);

  // Listen for hover preview (from related modules)
  useEffect(() => {
    const unsubscribePreview = bus.on('RELATED_MODULE_PREVIEW', (event: any) => {
      if (event.moduleId === cardId) {
        setPreviewHighlight(true);
      }
    });

    const unsubscribeUnhover = bus.on('MODULE_UNHOVERED', () => {
      setPreviewHighlight(false);
    });

    return () => {
      unsubscribePreview();
      unsubscribeUnhover();
    };
  }, [cardId]);

  // Handle click - open sidebar for details
  const handleClick = useCallback(() => {
    // Set selection context
    if (entityId) {
      setSelected(entityId, cardId);
      // Emit for analytics and entity inference
      bus.emit('ENTITY_SELECTED', { entityId, source: 'metric_card' });
    }

    // Call original onClick if provided
    if (onClick) {
      onClick();
    } else if (displayEntity) {
      // Default: open sidebar for full details
      openDetails();
    }
  }, [entityId, cardId, onClick, displayEntity, setSelected]);

  // Open sidebar details
  const openDetails = useCallback((e?: React.MouseEvent) => {
    e?.stopPropagation();

    if (displayEntity) {
      console.log('[MetricCard] Opening LocationPanel for:', displayEntity.id || entityId);
      setLocationPanel(displayEntity);

      // Emit event for analytics
      bus.emit('DETAILS_OPENED', {
        entityId: entityId || '',
        source: 'metric_card'
      });
    } else {
      console.warn('[MetricCard] No entity available for details');
    }
  }, [displayEntity, entityId, setLocationPanel]);

  // Build quick actions dynamically
  const quickActions: QuickAction[] = useMemo(() => {
    const actions: QuickAction[] = [];

    // Details action opens sidebar (not inline expansion)
    if (enableExpand && displayEntity) {
      actions.push({
        id: 'details',
        label: 'Details',
        onClick: openDetails,
      });
    }

    if (relatedEntities.length > 0) {
      actions.push({
        id: 'compare',
        label: 'Compare',
        onClick: () => {
          onAction?.({
            type: 'refine_query',
            params: { query: `Compare ${displayLabel} with others` },
          });
        },
      });
    }

    if (onDelete) {
      actions.push({
        id: 'delete',
        label: 'Delete',
        tone: 'danger',
        onClick: () => onDelete(cardId),
      });
    }

    return actions;
  }, [enableExpand, displayEntity, relatedEntities.length, displayLabel, onAction, onDelete, cardId, openDetails]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{
        scale: 1.03,
        y: -6,
        transition: { duration: 0.15, ease: "easeOut" }
      }}
      whileTap={{ scale: 0.98 }}
      onClick={handleClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={`group relative overflow-visible rounded-xl backdrop-blur-sm transition-all duration-300
        ${hovered
          ? "shadow-[0_8px_24px_rgba(0,0,0,0.12)] border-primary/50"
          : "shadow-[0_1px_3px_rgba(0,0,0,0.08),0_1px_2px_rgba(0,0,0,0.06)]"
        }
        ${isSelected
          ? "border-primary bg-card ring-1 ring-primary ring-offset-1 ring-offset-background"
          : "border-border/50 bg-card/95"
        }
        ${onClick || enableExpand ? "cursor-pointer" : ""}
        ${flashHighlight ? "flash-highlight" : ""}
        ${previewHighlight ? "preview-highlight" : ""}
        border p-6`}
      style={{
        transform: hovered ? 'translateZ(0)' : undefined,
      }}
      role="button"
      tabIndex={0}
      aria-expanded={false}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      {/* Multi-select checkmark indicator */}
      {isMultiSelected && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          exit={{ scale: 0 }}
          className="multi-select-indicator"
        >
          <CheckCircle className="h-6 w-6 text-green-500 fill-green-500/20" />
        </motion.div>
      )}

      {/* Original card content */}
      <div className="flex flex-col items-center gap-2 text-center">
        {Icon && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <Icon className="h-8 w-8 text-primary" />
          </motion.div>
        )}

        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {displayLabel}
        </p>

        <motion.h3
          className="text-4xl font-bold text-foreground"
          initial={{ scale: 0.5 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
        >
          {displayValue}
        </motion.h3>

        {sublabel && (
          <p className="text-sm text-muted-foreground">{sublabel}</p>
        )}

        {trend && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className={`flex items-center gap-1 text-sm font-medium ${
              trend.direction === "up" ? "text-green-500" : "text-red-500"
            }`}
          >
            <span>{trend.direction === "up" ? "↑" : "↓"}</span>
            <span>{trend.value}%</span>
          </motion.div>
        )}

        {/* Dynamic glimpse chips (2-3 highlights) */}
        {dynamicChips.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mt-2 flex flex-wrap justify-center gap-2"
          >
            {dynamicChips.map((chip, idx) => (
              <div
                key={idx}
                className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary border border-primary/20"
                title={chip.label}
              >
                {chip.value}
              </div>
            ))}
          </motion.div>
        )}
      </div>

      {/* Hover quick actions */}
      {hovered && enableQuickActions && quickActions.length > 0 && (
        <QuickActions items={quickActions} />
      )}

      {/* Apple-style gradient overlay and glow effect */}
      <motion.div
        className="pointer-events-none absolute inset-0 rounded-xl bg-gradient-to-br from-primary/10 via-primary/5 to-transparent"
        initial={{ opacity: 0 }}
        animate={{ opacity: hovered ? 1 : 0 }}
        transition={{ duration: 0.3 }}
      />

      {/* Glow effect when hovered */}
      {hovered && (
        <motion.div
          className="pointer-events-none absolute -inset-[1px] rounded-xl bg-gradient-to-r from-primary/20 via-primary/30 to-primary/20 blur-md"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          style={{ zIndex: -1 }}
        />
      )}
    </motion.div>
  );
};
