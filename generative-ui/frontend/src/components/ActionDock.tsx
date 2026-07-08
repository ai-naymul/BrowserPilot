/**
 * ActionDock - Persistent action buttons at the top of Cards view
 *
 * Design principles:
 * - Shows 3-4 primary AI-suggested actions prominently
 * - Baseline actions (Add Item, Share) in a "More" dropdown
 * - Overflow actions also in "More" dropdown
 * - Updates dynamically after each refine
 */

import { useMemo } from 'react';
import {
  Plus,
  RefreshCw,
  Share2,
  Sparkles,
  TrendingUp,
  FileText,
  Search,
  Zap,
  MoreHorizontal,
  ChevronDown,
  Loader2,
  type LucideIcon
} from 'lucide-react';
import type { Action } from '@/types/api';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ActionDockProps {
  suggestedActions?: Array<{
    label: string;
    query?: string;
    icon?: string;
    action?: Action;
  }>;
  onAction: (action: Action) => void;
  loadingActionId?: string | null; // Query string of action currently loading
}

// Domain-agnostic baseline actions that work for any use case
const BASELINE_ACTIONS: Array<{
  id: string;
  label: string;
  icon: LucideIcon;
  action: Action;
  isPrimary: boolean;
}> = [
  {
    id: 'add-item',
    label: 'Add Item',
    icon: Plus,
    action: {
      type: 'add_entity',
      params: {},
    },
    isPrimary: false,
  },
  {
    id: 'share',
    label: 'Share',
    icon: Share2,
    action: {
      type: 'refine_query',
      params: { query: 'Share this view' },
    },
    isPrimary: false,
  },
];

// Map icon names to Lucide components
const ICON_MAP: Record<string, LucideIcon> = {
  sparkles: Sparkles,
  trending: TrendingUp,
  file: FileText,
  search: Search,
  zap: Zap,
  plus: Plus,
  refresh: RefreshCw,
  share: Share2,
};

// Get icon component from name or return default
function getIconComponent(iconName?: string): LucideIcon {
  if (!iconName) return Sparkles;
  return ICON_MAP[iconName.toLowerCase()] || Sparkles;
}

export function ActionDock({ suggestedActions = [], onAction, loadingActionId }: ActionDockProps) {
  const MAX_PRIMARY_ACTIONS = 4;

  // Convert suggested actions to internal format (memoized to prevent infinite re-renders)
  const dynamicActions = useMemo(() => {
    return suggestedActions.map((suggestion, idx) => {
      const action: Action = suggestion.action || {
        type: 'refine_query',
        params: { query: suggestion.query || suggestion.label },
      };

      return {
        id: `suggested-${idx}`,
        label: suggestion.label,
        query: suggestion.query || suggestion.label, // Store query for loading state comparison
        icon: getIconComponent(suggestion.icon),
        action,
        isPrimary: true, // AI suggestions are primary
      };
    });
  }, [suggestedActions]);

  // Split into primary (visible) and overflow (in More menu) - memoized
  const primaryActions = useMemo(
    () => dynamicActions.slice(0, MAX_PRIMARY_ACTIONS),
    [dynamicActions]
  );

  const overflowActions = useMemo(
    () => dynamicActions.slice(MAX_PRIMARY_ACTIONS),
    [dynamicActions]
  );

  // Baseline actions always go in More menu - memoized
  const moreMenuActions = useMemo(
    () => [...overflowActions, ...BASELINE_ACTIONS],
    [overflowActions]
  );

  const hasMoreActions = moreMenuActions.length > 0;

  return (
    <div className="action-dock border-b border-border bg-gradient-to-r from-background/95 to-background/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="mx-auto max-w-7xl px-6 py-3">
        <div className="flex items-center gap-3">
          {/* Primary AI-suggested actions */}
          <div className="flex items-center gap-2 flex-1">
            {primaryActions.map(({ id, label, query, icon: Icon, action }) => {
              const isLoading = loadingActionId === query;
              return (
                <button
                  key={id}
                  onClick={() => onAction(action)}
                  disabled={isLoading}
                  className="inline-flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/10 px-4 py-2 text-sm font-medium text-primary shadow-sm transition-all duration-150 hover:bg-primary/20 hover:border-primary/50 hover:shadow-md hover:scale-105 active:scale-100 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                  <span>{label}</span>
                </button>
              );
            })}

            {primaryActions.length === 0 && (
              <div className="text-sm text-muted-foreground italic">
                Choose an action or ask a follow-up question...
              </div>
            )}
          </div>

          {/* More menu for overflow + baseline actions */}
          {hasMoreActions && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-sm text-muted-foreground shadow-sm transition-all duration-150 hover:bg-accent hover:text-foreground">
                  <MoreHorizontal className="h-4 w-4" />
                  <span>More</span>
                  <ChevronDown className="h-3 w-3" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                {overflowActions.map(({ id, label, icon: Icon, action }) => (
                  <DropdownMenuItem
                    key={id}
                    onClick={() => onAction(action)}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <Icon className="h-4 w-4 text-primary" />
                    <span>{label}</span>
                  </DropdownMenuItem>
                ))}

                {overflowActions.length > 0 && BASELINE_ACTIONS.length > 0 && (
                  <DropdownMenuSeparator />
                )}

                {BASELINE_ACTIONS.map(({ id, label, icon: Icon, action }) => (
                  <DropdownMenuItem
                    key={id}
                    onClick={() => onAction(action)}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <Icon className="h-4 w-4" />
                    <span>{label}</span>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </div>
  );
}
