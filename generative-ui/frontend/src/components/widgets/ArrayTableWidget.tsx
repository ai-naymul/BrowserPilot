import { useState } from 'react';
import { EntityAttribute } from '@/types/entity';
import { ChevronDown, ChevronUp, ArrowUpDown } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ArrayTableWidgetProps {
  attribute: EntityAttribute;
  onChange?: (newValue: any) => void;
  compact?: boolean;
}

export const ArrayTableWidget = ({ attribute, onChange, compact }: ArrayTableWidgetProps) => {
  const data = (attribute.value || []) as Record<string, any>[];
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [expanded, setExpanded] = useState(true);

  if (!data || data.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        <label className="text-sm font-medium capitalize block mb-2">
          {attribute.name.replace(/_/g, ' ')}
        </label>
        <div className="text-xs">No items</div>
      </div>
    );
  }

  // Get all keys from first object
  const keys = Object.keys(data[0] || {});
  
  // Sort data if sortBy is set
  const sortedData = sortBy ? [...data].sort((a, b) => {
    const aVal = a[sortBy];
    const bVal = b[sortBy];
    
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    }
    
    const aStr = String(aVal || '');
    const bStr = String(bVal || '');
    return sortOrder === 'asc' 
      ? aStr.localeCompare(bStr)
      : bStr.localeCompare(aStr);
  }) : data;

  const handleSort = (key: string) => {
    if (sortBy === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(key);
      setSortOrder('asc');
    }
  };

  const formatValue = (value: any) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'boolean') return value ? '✓' : '✗';
    if (typeof value === 'number') {
      // Check if it looks like currency
      if (Math.abs(value) > 100) {
        return `$${value.toLocaleString()}`;
      }
      return value.toLocaleString();
    }
    return String(value);
  };

  if (compact) {
    return (
      <div>
        <label className="text-xs font-medium text-muted-foreground capitalize">
          {attribute.name.replace(/_/g, ' ')}
        </label>
        <div className="text-sm font-medium mt-1">
          {data.length} items
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium capitalize">
          {attribute.name.replace(/_/g, ' ')}
        </label>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </div>

      {expanded && (
        <div className="border rounded-lg overflow-hidden">
          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-sm">
              <thead className="bg-secondary border-b sticky top-0">
                <tr>
                  {keys.map(key => (
                    <th 
                      key={key}
                      className="px-4 py-3 text-left text-xs font-medium text-foreground capitalize cursor-pointer hover:bg-accent/10 transition-colors"
                      onClick={() => handleSort(key)}
                    >
                      <div className="flex items-center gap-1">
                        <span className="capitalize">{key.replace(/_/g, ' ')}</span>
                        {sortBy === key && (
                          <ArrowUpDown className="h-3 w-3" />
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                {sortedData.map((row, idx) => (
                  <tr 
                    key={idx}
                    className="hover:bg-accent/10 transition-colors"
                  >
                    {keys.map(key => (
                      <td key={key} className="px-4 py-3">
                        {formatValue(row[key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="bg-secondary px-4 py-2 border-t text-xs text-muted-foreground">
            {data.length} {data.length === 1 ? 'item' : 'items'}
            {sortBy && ` • Sorted by ${sortBy.replace(/_/g, ' ')} (${sortOrder})`}
          </div>
        </div>
      )}
    </div>
  );
};
