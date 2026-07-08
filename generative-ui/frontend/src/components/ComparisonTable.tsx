import { motion } from "framer-motion";
import { useState, useMemo } from "react";
import { ArrowUpDown, ChevronDown, ChevronUp, Plus, X } from "lucide-react";
import { isValueMeaningful } from "@/utils/validators";
import {
  formatCurrencyOrNull,
  formatNumberOrNull,
  formatDateOrNull,
  formatPercentageOrNull,
  formatRatingOrNull
} from "@/utils/formatters";

interface Column {
  key: string;
  label: string;
  render?: (value: any, item: any) => React.ReactNode;
  sortable?: boolean;
  highlightBest?: boolean;
  compareType?: "higher" | "lower";
}

interface ComparisonTableProps {
  items: Array<{ id: string; [key: string]: any }>;
  columns: Column[];
  onRowClick?: (item: any) => void;
  onRowDelete?: (item: any) => void; // New: delete handler
  highlightBest?: boolean;
  striped?: boolean;
}

export const ComparisonTable = ({
  items = [],
  columns = [],
  onRowClick,
  onRowDelete,
  highlightBest = false,
  striped = true,
}: ComparisonTableProps) => {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  // Comprehensive validation
  if (!Array.isArray(items) || !Array.isArray(columns)) {
    console.error('ComparisonTable: items or columns are not arrays', { items, columns });
    return (
      <div className="rounded-xl border border-border bg-card p-6">
        <p className="text-muted-foreground">No data available</p>
      </div>
    );
  }

  // Deduplicate columns by key (keep first occurrence)
  const uniqueColumns = columns.reduce((acc: Column[], col) => {
    if (!acc.some((c) => c.key === col.key)) {
      acc.push(col);
    }
    return acc;
  }, []);

  // Filter out columns where ALL values are empty
  const meaningfulColumns = useMemo(() => {
    return uniqueColumns.filter((col) => {
      const values = items.map((item) => item[col.key]);
      return values.some(isValueMeaningful);
    });
  }, [uniqueColumns, items]);

  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-6">
        <p className="text-center text-sm text-muted-foreground">No items to display</p>
      </div>
    );
  }

  if (meaningfulColumns.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-6">
        <p className="text-center text-sm text-muted-foreground">No columns configured</p>
      </div>
    );
  }

  // Filter out rows where all values are empty/meaningless
  const meaningfulItems = items.filter((item) => {
    const values = meaningfulColumns.map((col) => item[col.key]);
    return values.some(isValueMeaningful);
  });

  // Show empty state if no meaningful items
  if (meaningfulItems.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex flex-col items-center justify-center gap-3 py-8">
          <div className="empty-chip">
            <Plus className="h-4 w-4" />
            <span>Add items to compare</span>
          </div>
          <p className="text-xs text-muted-foreground">No data available for comparison</p>
        </div>
      </div>
    );
  }

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const sortedItems = sortKey
    ? [...meaningfulItems].sort((a, b) => {
        const aVal = a[sortKey];
        const bVal = b[sortKey];
        const multiplier = sortDirection === "asc" ? 1 : -1;

        if (typeof aVal === "number" && typeof bVal === "number") {
          return (aVal - bVal) * multiplier;
        }
        return String(aVal).localeCompare(String(bVal)) * multiplier;
      })
    : meaningfulItems;

  const getBestValue = (column: Column) => {
    if (!column.highlightBest || !column.compareType) return null;

    const values = meaningfulItems.map((item) => item[column.key]).filter((v) => typeof v === "number");
    if (values.length === 0) return null;

    return column.compareType === "higher" ? Math.max(...values) : Math.min(...values);
  };

  // Smart formatter based on value type
  const formatValue = (value: any, columnKey: string): string | null => {
    // Try currency
    if (columnKey.toLowerCase().includes('cost') ||
        columnKey.toLowerCase().includes('price') ||
        columnKey.toLowerCase().includes('budget') ||
        (typeof value === 'string' && value.includes('$'))) {
      const formatted = formatCurrencyOrNull(value);
      if (formatted !== null) return formatted;
    }

    // Try date
    if (columnKey.toLowerCase().includes('date') ||
        columnKey.toLowerCase().includes('time')) {
      const formatted = formatDateOrNull(value);
      if (formatted !== null) return formatted;
    }

    // Try percentage
    if (columnKey.toLowerCase().includes('percent') ||
        columnKey.toLowerCase().includes('rate') ||
        (typeof value === 'string' && value.includes('%'))) {
      const formatted = formatPercentageOrNull(value);
      if (formatted !== null) return formatted;
    }

    // Try rating
    if (columnKey.toLowerCase().includes('rating') ||
        columnKey.toLowerCase().includes('score')) {
      const formatted = formatRatingOrNull(value);
      if (formatted !== null) return formatted;
    }

    // Try number
    if (typeof value === 'number') {
      return formatNumberOrNull(value);
    }

    // Return string as-is if meaningful
    if (isValueMeaningful(value)) {
      return String(value);
    }

    return null; // Not meaningful
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="overflow-hidden rounded-xl border border-border bg-card"
    >
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-secondary">
            <tr>
              {meaningfulColumns.map((column, colIdx) => (
                <th
                  key={column.key || `col-${colIdx}`}
                  className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
                >
                  {column.sortable ? (
                    <button
                      onClick={() => handleSort(column.key)}
                      className="flex items-center gap-2 hover:text-foreground transition-colors"
                    >
                      {column.label}
                      {sortKey === column.key ? (
                        sortDirection === "asc" ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )
                      ) : (
                        <ArrowUpDown className="h-4 w-4 opacity-50" />
                      )}
                    </button>
                  ) : (
                    column.label
                  )}
                </th>
              ))}
              {/* Actions column header (if delete handler provided) */}
              {onRowDelete && (
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground w-16">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {sortedItems.map((item, idx) => {
              // Generate stable key with fallback
              const rowKey = item.id || item.key || `row-${idx}-${JSON.stringify(item).slice(0, 20)}`;

              return (
                <motion.tr
                  key={rowKey}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: Math.min(idx * 0.05, 0.5) }} // Cap delay at 0.5s
                  onMouseEnter={() => setHoveredRow(rowKey)}
                  onMouseLeave={() => setHoveredRow(null)}
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent event bubbling
                    onRowClick?.(item);
                  }}
                  className={`
                    border-t border-border transition-colors
                    ${onRowClick ? "cursor-pointer hover:bg-muted/50" : ""}
                    ${striped && idx % 2 === 1 ? "bg-muted/20" : ""}
                  `}
                >
                {meaningfulColumns.map((column) => {
                  const value = item[column.key];
                  const bestValue = getBestValue(column);
                  const isBest = highlightBest && bestValue !== null && value === bestValue;

                  let renderedValue: React.ReactNode;

                  if (column.render) {
                    // Use custom renderer if provided
                    try {
                      renderedValue = column.render(value, item);
                    } catch (error) {
                      console.error('ComparisonTable: Error rendering cell', { column: column.key, error });
                      renderedValue = String(value || '—');
                    }
                  } else {
                    // Use smart formatter
                    const formatted = formatValue(value, column.key);

                    if (formatted !== null) {
                      renderedValue = formatted;
                    } else {
                      // Show "+ Add value" chip for empty cells
                      renderedValue = (
                        <button
                          className="text-xs text-muted-foreground hover:text-primary transition-colors px-2 py-1 rounded border border-dashed border-border hover:border-primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Could trigger edit mode in future
                            console.log('[Table] Add value for:', column.key, item.id);
                          }}
                        >
                          + Add value
                        </button>
                      );
                    }
                  }

                  return (
                    <td
                      key={column.key}
                      className={`px-4 py-3 text-sm ${
                        isBest ? "bg-primary/10 font-semibold text-primary" : "text-foreground"
                      }`}
                    >
                      {renderedValue}
                    </td>
                  );
                })}

                {/* Actions column - delete button */}
                {onRowDelete && (
                  <td className="px-4 py-3 text-right">
                    {hoveredRow === rowKey && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRowDelete(item);
                        }}
                        className="inline-flex items-center justify-center p-1 rounded-md bg-destructive/10 hover:bg-destructive/20 text-destructive transition-colors"
                        title="Delete this item"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </td>
                )}
              </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
};
