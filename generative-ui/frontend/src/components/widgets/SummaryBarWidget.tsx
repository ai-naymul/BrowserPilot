import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown, Award, AlertCircle } from 'lucide-react';
import { Entity } from '@/types/entity';
import { formatAttributeValue, getNumericValue } from '@/utils/attributeIntelligence';

interface SummaryBarWidgetProps {
  entities: Entity[];
  metricName: string; // e.g., "total_cost", "base_salary"
  label: string;      // e.g., "Total Cost Comparison"
}

export const SummaryBarWidget = ({ entities, metricName, label }: SummaryBarWidgetProps) => {
  // Extract metric values from all entities
  const data = useMemo(() => {
    return entities
      .map((entity) => {
        const attr = entity.attributes.find(a => a.name === metricName);
        if (!attr) return null;

        const numericValue = getNumericValue(attr.value, attr.widget || 'short_text');
        if (numericValue === 0 && attr.value !== 0) return null; // Skip non-numeric

        return {
          id: entity.id,
          name: entity.public_identifier,
          value: numericValue,
          formattedValue: formatAttributeValue(attr.value, attr.widget || 'short_text'),
          color: entity.color || '#7dd3fc',
          icon: entity.icon,
          widget: attr.widget
        };
      })
      .filter((d): d is NonNullable<typeof d> => d !== null && d.value !== 0);
  }, [entities, metricName]);

  if (data.length === 0) {
    return null; // Don't render if no data
  }

  // Calculate stats
  const values = data.map(d => d.value);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const avg = values.reduce((sum, v) => sum + v, 0) / values.length;
  const range = max - min;

  // Sort by value (ascending)
  const sortedData = [...data].sort((a, b) => a.value - b.value);

  return (
    <div className="bg-card rounded-lg border border-border shadow-sm p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-foreground">{label}</h3>
          <p className="text-sm text-muted-foreground">
            Comparing {data.length} {data.length === 1 ? 'item' : 'items'}
          </p>
        </div>
        
        {/* Stats Summary */}
        <div className="flex items-center gap-6 text-sm">
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Lowest</div>
            <div className="font-bold text-green-600">
              {sortedData[0].formattedValue}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Average</div>
            <div className="font-bold text-foreground">
              {formatAttributeValue(avg, data[0].widget)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Highest</div>
            <div className="font-bold text-red-600">
              {sortedData[sortedData.length - 1].formattedValue}
            </div>
          </div>
        </div>
      </div>

      {/* Visual Bars */}
      <div className="space-y-3">
        {sortedData.map((item, index) => {
          const percentage = (item.value / max) * 100;
          const isLowest = item.value === min;
          const isHighest = item.value === max;
          const isNearAvg = Math.abs(item.value - avg) / range < 0.1;

          return (
            <div key={item.id} className="space-y-1">
              {/* Entity Info */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-2xl flex-shrink-0">{item.icon}</span>
                  <span className="text-sm font-medium text-foreground truncate">
                    {item.name}
                  </span>
                  {isLowest && (
                    <span className="flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs font-medium">
                      <TrendingDown className="w-3 h-3" />
                      Best Value
                    </span>
                  )}
                  {isHighest && (
                    <span className="flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-100 text-red-700 text-xs font-medium">
                      <TrendingUp className="w-3 h-3" />
                      Highest
                    </span>
                  )}
                  {!isLowest && !isHighest && isNearAvg && (
                    <span className="flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                      <AlertCircle className="w-3 h-3" />
                      Average
                    </span>
                  )}
                </div>
                <span className="text-sm font-bold text-foreground flex-shrink-0 ml-4">
                  {item.formattedValue}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="relative h-8 bg-gray-100 rounded-lg overflow-hidden">
                <div
                  className={`
                    absolute inset-y-0 left-0 rounded-lg transition-all duration-500
                    ${isLowest ? 'bg-gradient-to-r from-green-400 to-green-500' : ''}
                    ${isHighest ? 'bg-gradient-to-r from-red-400 to-red-500' : ''}
                    ${!isLowest && !isHighest ? 'bg-gradient-to-r from-blue-400 to-blue-500' : ''}
                  `}
                  style={{ width: `${Math.max(percentage, 5)}%` }}
                >
                  {/* Percentage Label */}
                  {percentage > 20 && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xs font-bold text-white">
                        {percentage.toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Percentage Label (outside bar if too small) */}
                {percentage <= 20 && (
                  <div className="absolute inset-y-0 flex items-center" style={{ left: `${percentage}%` }}>
                    <span className="ml-2 text-xs font-bold text-muted-foreground">
                      {percentage.toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Difference from Average */}
              {data.length > 2 && (
                <div className="flex justify-end">
                  <span className="text-xs text-muted-foreground">
                    {item.value > avg ? '+' : ''}
                    {formatAttributeValue(item.value - avg, data[0].widget)} vs avg
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Stats */}
      {range > 0 && (
        <div className="pt-4 border-t border-border flex items-center justify-between text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <span className="font-medium">Range:</span>
            <span>{formatAttributeValue(range, data[0].widget)}</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <span className="font-medium">Spread:</span>
            <span>{((range / avg) * 100).toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  );
};
