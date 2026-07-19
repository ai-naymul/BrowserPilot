import { useState } from 'react';
import { Entity } from '@/types/entity';
import { Button } from '@/components/ui/button';
import { EntityCard } from '@/components/EntityCard';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { LayoutGrid, Table as TableIcon, Layers, Map as MapIcon } from 'lucide-react';
import { MapView } from '@/components/views/MapView';
import { TableView } from '@/components/views/TableView';
import { StackView } from '@/components/views/StackView';
import { ComparisonView } from '@/components/views/ComparisonView';
import { SummaryBarWidget } from '@/components/widgets/SummaryBarWidget';

interface MainPanelProps {
  allEntities: Entity[];
  selectedEntityId: string | null;
  onEntitySelect?: (entityId: string | null) => void;
  onAttributeChange?: (entityId: string, attributeName: string, newValue: any) => void;
  onDeleteEntity?: (entityId: string) => void;
  loading?: boolean;
}

type ViewMode = 'cards' | 'table' | 'stack' | 'map';

export const MainPanel = ({ 
  allEntities, 
  selectedEntityId,
  onEntitySelect, 
  onAttributeChange, 
  onDeleteEntity,
  loading 
}: MainPanelProps) => {
  const [viewMode, setViewMode] = useState<ViewMode>('cards');
  
  if (!allEntities || allEntities.length === 0) {
    return (
      <div className="flex-1 bg-background flex items-center justify-center p-8">
        <div className="text-center text-muted-foreground">
          <p className="text-lg">No entities to display</p>
          <p className="text-sm mt-2">Start by describing what you want to do</p>
        </div>
      </div>
    );
  }

  // Filter entities based on selection
  const displayEntities = selectedEntityId 
    ? allEntities.filter(e => e.id === selectedEntityId)
    : allEntities;
  
  // Detect comparison scenario
  const isComparisonScenario = allEntities.length >= 3 && allEntities.every(entity => {
    const type = entity.type.toLowerCase();
    return type.includes('destination') || 
           type.includes('offer') || 
           type.includes('option') ||
           type.includes('candidate');
  });
  
  // Get comparison entities (exclude parent comparison entity)
  const comparisonEntities = isComparisonScenario 
    ? allEntities.filter(e => !e.type.toLowerCase().includes('comparison'))
    : [];
  
  // Check if any entity has location data
  const hasLocationData = displayEntities.some(entity => 
    entity.attributes.some(attr => 
      attr.name.includes('address') || 
      attr.name.includes('location') || 
      attr.name.includes('neighborhood') ||
      attr.widget === 'location'
    )
  );

  return (
    <div className="flex-1 bg-background overflow-hidden flex flex-col">
      {/* Header with view controls */}
      {/* View Mode Selector + Entity Filter */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-secondary">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-foreground">
            {displayEntities.length} {displayEntities.length === 1 ? 'Entity' : 'Entities'}
          </h2>
          
          {/* Show All button when filtered */}
          {selectedEntityId && (
            <button
              onClick={() => onEntitySelect?.(null)}
              className="px-3 py-1 text-sm bg-primary/10 text-primary rounded-md hover:bg-primary/20 transition-colors"
            >
              ← Show All ({allEntities.length})
            </button>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* View Mode Selector */}
          <Select value={viewMode} onValueChange={(v) => setViewMode(v as ViewMode)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="cards">
                <div className="flex items-center gap-2">
                  <LayoutGrid className="h-4 w-4" />
                  Cards
                </div>
              </SelectItem>
              <SelectItem value="table">
                <div className="flex items-center gap-2">
                  <TableIcon className="h-4 w-4" />
                  Table
                </div>
              </SelectItem>
              <SelectItem value="stack">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4" />
                  Stack
                </div>
              </SelectItem>
              {hasLocationData && (
                <SelectItem value="map">
                  <div className="flex items-center gap-2">
                    <MapIcon className="h-4 w-4" />
                    Map
                  </div>
                </SelectItem>
              )}
            </SelectContent>
          </Select>

          {loading && (
            <span className="text-sm text-muted-foreground">Updating...</span>
          )}
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Use ComparisonView for comparison scenarios */}
        {isComparisonScenario && !selectedEntityId ? (
          <ComparisonView
            entities={comparisonEntities}
            onSelectEntity={(entity) => onEntitySelect?.(entity.id)}
            onAttributeChange={onAttributeChange}
          />
        ) : (
          <>
        {viewMode === 'cards' && (
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {displayEntities.map((entity, index) => (
                <EntityCard
                  key={entity.id}
                  entity={entity}
                  onAttributeChange={onAttributeChange}
                  onDelete={onDeleteEntity}
                  defaultExpanded={index === 0} // First card expanded by default
                />
              ))}
            </div>
          </div>
        )}

        {viewMode === 'stack' && (
          <div className="max-w-6xl mx-auto">
            <StackView
              entities={displayEntities}
              onSelectEntity={(entity) => onEntitySelect?.(entity.id)}
              onAttributeChange={onAttributeChange}
              onDeleteEntity={onDeleteEntity}
            />
          </div>
        )}

        {viewMode === 'table' && (
          <div className="max-w-7xl mx-auto">
            <TableView
              entities={displayEntities}
              onSelectEntity={(entity) => onEntitySelect?.(entity.id)}
              onDeleteEntity={onDeleteEntity}
            />
          </div>
        )}

        {viewMode === 'map' && (
          <div className="w-full h-full relative">
            {/* Show All button when entity is selected in map view */}
            {selectedEntityId && (
              <div className="absolute top-4 right-4 z-[1000]">
                <button
                  onClick={() => onEntitySelect?.(null)}
                  className="px-4 py-2 bg-card text-primary rounded-lg shadow-lg hover:bg-accent/10 transition-colors font-medium border-2 border-primary"
                >
                  Show All Locations
                </button>
              </div>
            )}
            <MapView
              entities={displayEntities}
              onSelectEntity={(entity) => onEntitySelect?.(entity.id)}
            />
          </div>
        )}
          </>
        )}
      </div>
    </div>
  );
};
