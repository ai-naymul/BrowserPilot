import React, { useState, useMemo } from 'react';
import { Entity } from '@/types/entity';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp, Eye, Edit, Trash2, Filter } from 'lucide-react';
import {
  getKeyAttributes,
  formatAttributeValue,
  getComparableAttributes,
  getNumericValue,
  ScoredAttribute
} from '@/utils/attributeIntelligence';

interface TableViewEnhancedProps {
  entities: Entity[];
  onSelectEntity?: (entity: Entity) => void;
  onEditEntity?: (entity: Entity) => void;
  onDeleteEntity?: (entityId: string) => void;
}

type SortOrder = 'asc' | 'desc';

export const TableView = ({
  entities,
  onSelectEntity,
  onEditEntity,
  onDeleteEntity
}: TableViewEnhancedProps) => {
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [filterType, setFilterType] = useState<string | null>(null);

  // Get unique entity types for filtering
  const entityTypes = useMemo(() => 
    Array.from(new Set(entities.map(e => e.type))),
    [entities]
  );

  // Get comparable attributes across entities
  const columnAttributes = useMemo(() => {
    const comparable = getComparableAttributes(entities);
    
    // Get a representative entity to score attributes
    if (entities.length === 0) return [];
    
    const representativeEntity = entities[0];
    const scored = getKeyAttributes(representativeEntity, 10);
    
    // Filter to only attributes that are comparable
    return scored.filter(attr => comparable.includes(attr.name));
  }, [entities]);

  // Filter entities by type
  const filteredEntities = useMemo(() => {
    if (!filterType) return entities;
    return entities.filter(e => e.type === filterType);
  }, [entities, filterType]);

  // Sort entities
  const sortedEntities = useMemo(() => {
    if (!sortBy) return filteredEntities;

    return [...filteredEntities].sort((a, b) => {
      const aAttr = a.attributes.find(attr => attr.name === sortBy);
      const bAttr = b.attributes.find(attr => attr.name === sortBy);

      if (!aAttr && !bAttr) return 0;
      if (!aAttr) return 1;
      if (!bAttr) return -1;

      // Get numeric values for comparison
      const aNum = getNumericValue(aAttr.value, aAttr.widget || 'short_text');
      const bNum = getNumericValue(bAttr.value, bAttr.widget || 'short_text');

      // If both are numbers, compare numerically
      if (aNum !== 0 || bNum !== 0) {
        return sortOrder === 'asc' ? aNum - bNum : bNum - aNum;
      }

      // Otherwise compare as strings
      const aStr = String(aAttr.value || '');
      const bStr = String(bAttr.value || '');
      const comparison = aStr.localeCompare(bStr);
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [filteredEntities, sortBy, sortOrder]);

  const handleSort = (attrName: string) => {
    if (sortBy === attrName) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(attrName);
      setSortOrder('asc');
    }
  };

  const handleRowClick = (entity: Entity) => {
    console.log('[TableView] Row clicked:', entity.public_identifier);
    if (onSelectEntity) {
      console.log('[TableView] Calling onSelectEntity');
      onSelectEntity(entity);
    } else {
      console.warn('[TableView] onSelectEntity not provided!');
    }
  };

  if (entities.length === 0) {
    return (
      <div className="flex items-center justify-center p-12 bg-secondary rounded-lg border-2 border-dashed border-border">
        <div className="text-center">
          <p className="text-lg font-medium text-foreground">No data to display</p>
          <p className="text-sm text-muted-foreground mt-1">Start by creating entities</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-4">
      {/* Header with filters and stats */}
      <div className="flex items-center justify-between bg-secondary p-4 rounded-lg border border-border">
        <div>
          <h3 className="text-lg font-bold text-foreground">
            Comparison Table
          </h3>
          <p className="text-sm text-muted-foreground">
            {sortedEntities.length} {sortedEntities.length === 1 ? 'item' : 'items'}
            {filterType && ` · Filtered by ${filterType.replace(/_/g, ' ')}`}
          </p>
        </div>

        {/* Type Filter */}
        {entityTypes.length > 1 && (
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <select
              value={filterType || ''}
              onChange={(e) => setFilterType(e.target.value || null)}
              className="px-3 py-2 border border-border rounded-lg text-sm bg-background text-foreground hover:border-primary transition-colors focus:ring-2 focus:ring-ring focus:outline-none"
            >
              <option value="">All Types</option>
              {entityTypes.map(type => (
                <option key={type} value={type}>
                  {type.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-card rounded-lg border border-border shadow-sm">
        <table className="w-full">
          <thead className="bg-secondary border-b border-border">
            <tr>
              {/* Entity column */}
              <th className="px-6 py-4 text-left">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-foreground">Entity</span>
                </div>
              </th>

              {/* Dynamic attribute columns */}
              {columnAttributes.map((attr) => (
                <th
                  key={attr.name}
                  onClick={() => handleSort(attr.name)}
                  className="px-4 py-4 text-left cursor-pointer hover:bg-muted/50 transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xs">{attr.icon}</span>
                    <span className="text-sm font-semibold text-foreground capitalize">
                      {attr.name.replace(/_/g, ' ')}
                    </span>
                    {sortBy === attr.name && (
                      <span className="ml-1">
                        {sortOrder === 'asc' ? (
                          <ChevronUp className="w-4 h-4 text-primary" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-primary" />
                        )}
                      </span>
                    )}
                    {sortBy !== attr.name && (
                      <ChevronDown className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    )}
                  </div>
                </th>
              ))}

              {/* Actions column */}
              <th className="px-4 py-4 text-right">
                <span className="text-sm font-semibold text-foreground">Actions</span>
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-border">
            {sortedEntities.map((entity, idx) => {
              const isEven = idx % 2 === 0;
              
              return (
                <tr
                  key={entity.id}
                  onClick={() => handleRowClick(entity)}
                  className={`
                    transition-all cursor-pointer
                    ${isEven ? 'bg-card' : 'bg-muted/30'}
                    hover:bg-muted/50 hover:shadow-sm
                  `}
                >
                  {/* Entity info */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{entity.icon}</span>
                      <div>
                        <div className="font-medium text-foreground">
                          {entity.public_identifier}
                        </div>
                        <div className="text-xs text-muted-foreground capitalize">
                          {entity.type.replace(/_/g, ' ')}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Dynamic attribute cells */}
                  {columnAttributes.map((columnAttr) => {
                    const entityAttr = entity.attributes.find(
                      a => a.name === columnAttr.name
                    );

                    return (
                      <td key={columnAttr.name} className="px-4 py-4">
                        {entityAttr ? (
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-foreground">
                              {formatAttributeValue(entityAttr.value, entityAttr.widget || 'short_text')}
                            </span>
                          </div>
                        ) : (
                          <span className="text-sm text-muted-foreground">-</span>
                        )}
                      </td>
                    );
                  })}

                  {/* Actions */}
                  <td className="px-4 py-4">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectEntity?.(entity);
                        }}
                        className="hover:bg-accent"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>

                      {onEditEntity && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onEditEntity(entity);
                          }}
                          className="hover:bg-accent"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                      )}

                      {onDeleteEntity && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm(`Delete ${entity.public_identifier}?`)) {
                              onDeleteEntity(entity.id);
                            }
                          }}
                          className="hover:bg-destructive/10"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4 text-destructive" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Empty state for filtered results */}
      {sortedEntities.length === 0 && entities.length > 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <p>No entities match the current filter</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFilterType(null)}
            className="mt-2"
          >
            Clear Filter
          </Button>
        </div>
      )}
    </div>
  );
};
