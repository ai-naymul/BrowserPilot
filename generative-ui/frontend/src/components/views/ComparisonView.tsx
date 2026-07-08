import { useState, useMemo } from 'react';
import { Entity } from '@/types/entity';
import { ComparisonCardWidget } from '../widgets/ComparisonCardWidget';
import { SummaryBarWidget } from '../widgets/SummaryBarWidget';
import { ArrowLeftRight, LayoutGrid, Table as TableIcon, Map as MapIcon } from 'lucide-react';
import { TableView } from './TableView';
import { MapView } from './MapView';
import { extractEntityLocation } from '@/utils/attributeIntelligence';

interface ComparisonViewProps {
  entities: Entity[];
  onSelectEntity?: (entity: Entity) => void;
  onAttributeChange?: (entityId: string, attributeName: string, newValue: any) => void;
}

export const ComparisonView = ({ 
  entities, 
  onSelectEntity,
  onAttributeChange 
}: ComparisonViewProps) => {
  const [viewMode, setViewMode] = useState<'cards' | 'table' | 'map'>('cards');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  
  // Check if entities have location data for map view
  const hasLocationData = useMemo(() => 
    entities.some(entity => extractEntityLocation(entity) !== null),
    [entities]
  );
  
  // Detect key metric for summary bar (cost, salary, etc.)
  const summaryMetric = useMemo(() => {
    if (entities.length === 0) return null;
    
    // Check for common comparison metrics
    const commonMetrics = ['total_cost', 'total_comp_year1', 'price', 'cost', 'salary'];
    for (const metric of commonMetrics) {
      if (entities[0].attributes.some(a => a.name === metric)) {
        return { name: metric, label: metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) };
      }
    }
    return null;
  }, [entities]);
  
  const handleSelect = (entity: Entity) => {
    setSelectedId(entity.id);
    onSelectEntity?.(entity);
  };
  
  return (
    <div className="h-full flex flex-col">
      {/* Header with View Controls */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-secondary">
        <div className="flex items-center gap-3">
          <ArrowLeftRight className="h-5 w-5 text-blue-600" />
          <h2 className="text-xl font-bold text-foreground">
            Compare {entities.length} Options
          </h2>
        </div>
        
        <div className="flex items-center gap-2 bg-background rounded-lg p-1 shadow-sm border border-border">
          <button
            onClick={() => setViewMode('cards')}
            className={`
              px-4 py-2 rounded-lg flex items-center gap-2 transition-all font-medium text-sm
              ${viewMode === 'cards' 
                ? 'bg-blue-500 text-white shadow-md' 
                : 'text-muted-foreground hover:bg-muted/50'
              }
            `}
          >
            <LayoutGrid className="h-4 w-4" />
            Cards
          </button>
          
          <button
            onClick={() => setViewMode('table')}
            className={`
              px-4 py-2 rounded-lg flex items-center gap-2 transition-all font-medium text-sm
              ${viewMode === 'table' 
                ? 'bg-blue-500 text-white shadow-md' 
                : 'text-muted-foreground hover:bg-muted/50'
              }
            `}
          >
            <TableIcon className="h-4 w-4" />
            Table
          </button>
          
          {hasLocationData && (
            <button
              onClick={() => setViewMode('map')}
              className={`
                px-4 py-2 rounded-lg flex items-center gap-2 transition-all font-medium text-sm
                ${viewMode === 'map' 
                  ? 'bg-blue-500 text-white shadow-md' 
                  : 'text-muted-foreground hover:bg-muted/50'
                }
              `}
            >
              <MapIcon className="h-4 w-4" />
              Map
            </button>
          )}
        </div>
      </div>
      
      {/* Content Area */}
      <div className="flex-1 overflow-auto p-6 bg-gray-50 space-y-6">
        {/* Summary Bar (if comparable metric exists) */}
        {summaryMetric && (
          <div className="max-w-7xl mx-auto">
            <SummaryBarWidget
              entities={entities}
              metricName={summaryMetric.name}
              label={summaryMetric.label}
            />
          </div>
        )}
        
        {viewMode === 'cards' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
            {entities.map(entity => (
              <ComparisonCardWidget
                key={entity.id}
                entity={entity}
                isSelected={entity.id === selectedId}
                onSelect={() => handleSelect(entity)}
              />
            ))}
          </div>
        )}
        
        {viewMode === 'table' && (
          <div className="max-w-7xl mx-auto">
            <TableView
              entities={entities}
              onSelectEntity={handleSelect}
            />
          </div>
        )}
        
        {viewMode === 'map' && hasLocationData && (
          <div className="max-w-7xl mx-auto">
            <MapView
              entities={entities}
              onSelectEntity={handleSelect}
            />
          </div>
        )}
      </div>
    </div>
  );
};
