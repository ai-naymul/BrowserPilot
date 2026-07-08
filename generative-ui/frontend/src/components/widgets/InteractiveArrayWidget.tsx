import { useState } from 'react';
import { EntityAttribute } from '@/types/entity';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Trash2, Plus, Edit2, Check, X, ArrowUpDown } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';

interface InteractiveArrayWidgetProps {
  attribute: EntityAttribute;
  onChange?: (newValue: any) => void;
  compact?: boolean;
}

export const InteractiveArrayWidget = ({ attribute, onChange, compact }: InteractiveArrayWidgetProps) => {
  const [data, setData] = useState<Record<string, any>[]>(() => {
    // Parse string representation if needed
    let parsedData = attribute.value;
    if (typeof parsedData === 'string') {
      try {
        // Replace Python-style dict syntax with JSON
        const jsonStr = parsedData
          .replace(/'/g, '"')
          .replace(/True/g, 'true')
          .replace(/False/g, 'false')
          .replace(/None/g, 'null');
        parsedData = JSON.parse(jsonStr);
      } catch (e) {
        console.error('Failed to parse array data:', e);
        parsedData = [];
      }
    }
    return Array.isArray(parsedData) ? parsedData : [];
  });
  
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingRow, setEditingRow] = useState<Record<string, any>>({});
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [newRow, setNewRow] = useState<Record<string, any>>({});

  if (data.length === 0 && !isAddingNew) {
    const keys = attribute.value && Array.isArray(attribute.value) && attribute.value[0] 
      ? Object.keys(attribute.value[0])
      : [];
    
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium capitalize">
            {attribute.name.replace(/_/g, ' ')}
          </label>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              const template: Record<string, any> = {};
              keys.forEach(key => {
                if (key.includes('done') || key.includes('completed') || key.includes('purchased')) {
                  template[key] = false;
                } else if (key.includes('count') || key.includes('time') || key.includes('quantity')) {
                  template[key] = 0;
                } else {
                  template[key] = '';
                }
              });
              setNewRow(template);
              setIsAddingNew(true);
            }}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Item
          </Button>
        </div>
        <div className="text-sm text-muted-foreground border rounded-lg p-4 text-center">
          No items yet. Click "Add Item" to get started.
        </div>
      </div>
    );
  }

  const keys = data.length > 0 ? Object.keys(data[0]) : Object.keys(newRow);

  const handleSort = (key: string) => {
    if (sortBy === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(key);
      setSortOrder('asc');
    }
  };

  const sortedData = sortBy ? [...data].sort((a, b) => {
    const aVal = a[sortBy];
    const bVal = b[sortBy];
    
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    }
    
    if (typeof aVal === 'boolean' && typeof bVal === 'boolean') {
      return sortOrder === 'asc' 
        ? (aVal === bVal ? 0 : aVal ? 1 : -1)
        : (aVal === bVal ? 0 : bVal ? 1 : -1);
    }
    
    const aStr = String(aVal || '');
    const bStr = String(bVal || '');
    return sortOrder === 'asc' 
      ? aStr.localeCompare(bStr)
      : bStr.localeCompare(aStr);
  }) : data;

  const handleEdit = (index: number) => {
    setEditingIndex(index);
    setEditingRow({ ...data[index] });
  };

  const handleSave = () => {
    if (editingIndex !== null) {
      const newData = [...data];
      newData[editingIndex] = editingRow;
      setData(newData);
      onChange?.(newData);
      setEditingIndex(null);
    }
  };

  const handleDelete = (index: number) => {
    const newData = data.filter((_, i) => i !== index);
    setData(newData);
    onChange?.(newData);
    // Force recalculation
    setTimeout(() => onChange?.(newData), 0);
  };

  const handleAddNew = () => {
    const newData = [...data, newRow];
    setData(newData);
    setNewRow({});
    setIsAddingNew(false);
    onChange?.(newData);
    // Force recalculation
    setTimeout(() => onChange?.(newData), 0);
  };

  const handleCancelAdd = () => {
    setIsAddingNew(false);
    setNewRow({});
  };

  const handleCancelEdit = () => {
    setEditingIndex(null);
    setEditingRow({});
  };

  const renderCell = (key: string, value: any, isEditing: boolean, onUpdate: (key: string, val: any) => void) => {
    const isBooleanField = typeof value === 'boolean' || 
      key.includes('done') || key.includes('completed') || key.includes('purchased') || 
      key.includes('rsvp') || key.includes('plus_one');

    if (isBooleanField) {
      if (isEditing) {
        return (
          <Checkbox
            checked={!!value}  // Always boolean
            onCheckedChange={(checked) => onUpdate(key, !!checked)}
          />
        );
      }
      return value ? '✓' : '✗';
    }

    // Handle nested objects (like coordinates)
    if (typeof value === 'object' && value !== null) {
      // Special case: coordinates object
      if (value.lat !== undefined && value.lng !== undefined) {
        return (
          <span className="text-xs text-muted-foreground">
            {value.lat.toFixed(4)}, {value.lng.toFixed(4)}
          </span>
        );
      }
      
      // Special case: coordinates with latitude/longitude
      if (value.latitude !== undefined && value.longitude !== undefined) {
        return (
          <span className="text-xs text-muted-foreground">
            {value.latitude.toFixed(4)}, {value.longitude.toFixed(4)}
          </span>
        );
      }
      
      // Generic object display (compact)
      const entries = Object.entries(value);
      if (entries.length === 0) return '-';
      if (entries.length <= 2) {
        return (
          <span className="text-xs text-muted-foreground">
            {entries.map(([k, v]) => `${k}: ${v}`).join(', ')}
          </span>
        );
      }
      
      // Too complex, show count
      return (
        <span className="text-xs text-muted-foreground italic">
          {entries.length} fields
        </span>
      );
    }

    if (isEditing) {
      return (
        <Input
          value={String(value || '')}
          onChange={(e) => onUpdate(key, e.target.value)}
          className="h-8 text-sm"
        />
      );
    }

    if (value === null || value === undefined || value === '') return '-';
    if (typeof value === 'number' && Math.abs(value) > 100) {
      return `$${value.toLocaleString()}`;
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

  // Calculate totals/summaries
  const totals = keys.reduce((acc, key) => {
    if (key.includes('cost') || key.includes('price') || key.includes('budget')) {
      acc[key] = data.reduce((sum, row) => sum + (Number(row[key]) || 0), 0);
    } else if (key.includes('time') && typeof data[0]?.[key] === 'number') {
      acc[key] = data.reduce((sum, row) => sum + (Number(row[key]) || 0), 0);
    } else if (key.includes('done') || key.includes('completed') || key.includes('purchased')) {
      const completed = data.filter(row => row[key] === true || row[key] === 'true').length;
      acc[key] = { completed, total: data.length, percentage: Math.round((completed / data.length) * 100) };
    }
    return acc;
  }, {} as Record<string, any>);

  const hasComputedTotals = Object.keys(totals).length > 0;

  return (
    <div className="space-y-2 w-full">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium capitalize">
          {attribute.name.replace(/_/g, ' ')}
        </label>
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            const template: Record<string, any> = {};
            keys.forEach(key => {
              if (key.includes('done') || key.includes('completed') || key.includes('purchased')) {
                template[key] = false;
              } else if (key.includes('count') || key.includes('time') || key.includes('price')) {
                template[key] = 0;
              } else {
                template[key] = '';
              }
            });
            setNewRow(template);
            setIsAddingNew(true);
          }}
        >
          <Plus className="h-4 w-4 mr-1" />
          Add Item
        </Button>
      </div>

      <div className="border rounded-lg overflow-hidden w-full">
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-sm border-collapse">
            <thead className="bg-secondary border-b sticky top-0">
              <tr>
                {keys.map(key => (
                  <th 
                    key={key}
                    className="px-3 py-2 text-left text-xs font-medium text-foreground capitalize cursor-pointer hover:bg-accent/10 transition-colors"
                    onClick={() => handleSort(key)}
                  >
                    <div className="flex items-center gap-1">
                      <span className="capitalize text-xs">{key.replace(/_/g, ' ')}</span>
                      {sortBy === key && (
                        <ArrowUpDown className="h-3 h-3" />
                      )}
                    </div>
                  </th>
                ))}
                <th className="px-3 py-2 text-right font-medium text-foreground w-24">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {sortedData.map((row, idx) => (
                <tr 
                  key={idx}
                  className="hover:bg-accent/10 transition-colors"
                >
                  {keys.map(key => (
                    <td key={key} className="px-3 py-2">
                      {editingIndex === idx ? (
                        renderCell(key, editingRow[key], true, (k, v) => {
                          setEditingRow({ ...editingRow, [k]: v });
                        })
                      ) : (
                        renderCell(key, row[key], false, () => {})
                      )}
                    </td>
                  ))}
                  <td className="px-3 py-2 text-right">
                    {editingIndex === idx ? (
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={handleSave}
                          className="h-7 w-7 p-0"
                        >
                          <Check className="h-4 w-4 text-green-600" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={handleCancelEdit}
                          className="h-7 w-7 p-0"
                        >
                          <X className="h-4 w-4 text-red-600" />
                        </Button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleEdit(idx)}
                          className="h-7 w-7 p-0"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDelete(idx)}
                          className="h-7 w-7 p-0 text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
              
              {/* Add new row */}
              {isAddingNew && (
                <tr className="bg-blue-50">
                  {keys.map(key => (
                    <td key={key} className="px-3 py-2">
                      {renderCell(key, newRow[key], true, (k, v) => {
                        setNewRow({ ...newRow, [k]: v });
                      })}
                    </td>
                  ))}
                  <td className="px-3 py-2 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleAddNew}
                        className="h-7 w-7 p-0"
                      >
                        <Check className="h-4 w-4 text-green-600" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleCancelAdd}
                        className="h-7 w-7 p-0"
                      >
                        <X className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Summary/Totals Footer */}
        <div className="bg-secondary border-t">
          <div className="px-4 py-2 text-xs text-muted-foreground flex items-center justify-between">
            <span>
              {data.length} {data.length === 1 ? 'item' : 'items'}
              {sortBy && ` • Sorted by ${sortBy.replace(/_/g, ' ')} (${sortOrder})`}
            </span>
          </div>
          
          {hasComputedTotals && (
            <div className="px-4 pb-3 pt-1 space-y-1">
              {Object.entries(totals).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between text-xs">
                  <span className="font-medium capitalize text-foreground">
                    {key.includes('cost') || key.includes('price') ? 'Total ' : ''}
                    {key.replace(/_/g, ' ')}:
                  </span>
                  <span className="font-semibold text-foreground">
                    {typeof value === 'object' && 'completed' in value ? (
                      <span className="flex items-center gap-2">
                        <span>{value.completed}/{value.total}</span>
                        <span className="text-green-600">({value.percentage}%)</span>
                        <div className="w-20 h-2 bg-secondary rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-green-500 transition-all"
                            style={{ width: `${value.percentage}%` }}
                          />
                        </div>
                      </span>
                    ) : key.includes('cost') || key.includes('price') || key.includes('budget') ? (
                      `$${value.toLocaleString()}`
                    ) : key.includes('time') ? (
                      `${value} min`
                    ) : (
                      value
                    )}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
