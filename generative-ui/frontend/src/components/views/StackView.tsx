import React, { useState } from 'react';
import { Entity } from '@/types/entity';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronRight, Edit, Trash2, Info } from 'lucide-react';
import { DynamicWidget } from '@/components/widgets/DynamicWidget';
import {
  groupAttributesByCategory,
  formatAttributeValue,
  ScoredAttribute
} from '@/utils/attributeIntelligence';

interface StackViewEnhancedProps {
  entities: Entity[];
  onSelectEntity?: (entity: Entity) => void;
  onAttributeChange?: (entityId: string, attrName: string, newValue: any) => void;
  onDeleteEntity?: (entityId: string) => void;
}

interface EntityStackCardProps {
  entity: Entity;
  onSelect: () => void;
  onAttributeChange?: (attrName: string, newValue: any) => void;
  onDelete?: () => void;
}

const EntityStackCard = ({
  entity,
  onSelect,
  onAttributeChange,
  onDelete
}: EntityStackCardProps) => {
  const [expanded, setExpanded] = useState(false);
  const [showMeta, setShowMeta] = useState(false);

  const groups = groupAttributesByCategory(entity);

  // Determine gradient based on entity type
  const getGradient = (type: string) => {
    const typeLower = type.toLowerCase();
    if (typeLower.includes('destination') || typeLower.includes('trip')) return 'from-purple-500 to-pink-500';
    if (typeLower.includes('offer') || typeLower.includes('job')) return 'from-orange-500 to-red-500';
    if (typeLower.includes('venue') || typeLower.includes('location')) return 'from-green-500 to-emerald-500';
    if (typeLower.includes('budget') || typeLower.includes('expense')) return 'from-yellow-500 to-orange-500';
    if (typeLower.includes('plan') || typeLower.includes('checklist')) return 'from-indigo-500 to-blue-500';
    return 'from-gray-500 to-gray-600';
  };

  return (
    <div className="bg-card rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden border border-border">
      {/* Hero Section with Gradient */}
      <div 
        className={`bg-gradient-to-r ${getGradient(entity.type)} p-6 cursor-pointer`}
        onClick={onSelect}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-5xl">{entity.icon}</span>
            <div>
              <h3 className="text-xl font-bold text-white">
                {entity.public_identifier}
              </h3>
              <p className="text-white/80 text-sm capitalize mt-1">
                {entity.type.replace(/_/g, ' ')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onDelete && (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm(`Delete ${entity.public_identifier}?`)) {
                    onDelete();
                  }
                }}
                className="text-white hover:bg-black/20 transition-colors"
              >
                <Trash2 className="w-5 h-5" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(!expanded);
              }}
              className="text-white hover:bg-black/20 transition-colors"
            >
              {expanded ? (
                <ChevronDown className="w-6 h-6" />
              ) : (
                <ChevronRight className="w-6 h-6" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      {groups.key.length > 0 && (
        <div className="p-6 bg-muted/30">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {groups.key.map((attr) => (
              <div
                key={attr.name}
                className="bg-card rounded-lg p-4 border border-border shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">{attr.icon}</span>
                  <span className="text-xs font-medium text-muted-foreground capitalize">
                    {attr.name.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="text-lg font-bold text-foreground">
                  {formatAttributeValue(attr.value, attr.widget || 'short_text')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Expanded Details */}
      {expanded && (
        <div className="p-6 space-y-6 bg-background border-t border-border">
          {/* Details Section */}
          {groups.detail.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-foreground uppercase tracking-wide flex items-center gap-2">
                <Info className="w-4 h-4" />
                Details
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {groups.detail.map((attr) => (
                  <div key={attr.name} className="space-y-1">
                    {onAttributeChange ? (
                      <DynamicWidget
                        attribute={attr}
                        onChange={(val) => onAttributeChange(attr.name, val)}
                      />
                    ) : (
                      <div>
                        <label className="text-xs font-medium text-muted-foreground capitalize flex items-center gap-1">
                          <span>{attr.icon}</span>
                          {attr.name.replace(/_/g, ' ')}
                        </label>
                        <div className="text-sm font-medium text-foreground mt-1">
                          {formatAttributeValue(attr.value, attr.widget || 'short_text')}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Lists Section */}
          {groups.list.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-foreground uppercase tracking-wide">
                Additional Information
              </h4>
              <div className="space-y-4">
                {groups.list.map((attr) => (
                  <div key={attr.name} className="bg-secondary rounded-lg p-4 border border-border">
                    {onAttributeChange ? (
                      <DynamicWidget
                        attribute={attr}
                        onChange={(val) => onAttributeChange(attr.name, val)}
                      />
                    ) : (
                      <div>
                        <label className="text-xs font-medium text-muted-foreground capitalize flex items-center gap-1 mb-2">
                          <span>{attr.icon}</span>
                          {attr.name.replace(/_/g, ' ')}
                        </label>
                        <div className="text-sm text-foreground">
                          {formatAttributeValue(attr.value, attr.widget || 'short_text')}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata Section (collapsible) */}
          {groups.meta.length > 0 && (
            <div className="pt-4 border-t border-border">
              <button
                onClick={() => setShowMeta(!showMeta)}
                className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-2 transition-colors"
              >
                {showMeta ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
                <span>Metadata ({groups.meta.length} fields)</span>
              </button>

              {showMeta && (
                <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                  {groups.meta.map((attr) => (
                    <div key={attr.name} className="flex flex-col gap-1">
                      <span className="text-muted-foreground capitalize">
                        {attr.name.replace(/_/g, ' ')}:
                      </span>
                      <span className="text-foreground font-mono">
                        {String(attr.value).slice(0, 50)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const StackView = ({
  entities,
  onSelectEntity,
  onAttributeChange,
  onDeleteEntity
}: StackViewEnhancedProps) => {
  if (entities.length === 0) {
    return (
      <div className="flex items-center justify-center p-12 bg-secondary rounded-lg border-2 border-dashed border-border">
        <div className="text-center">
          <p className="text-lg font-medium text-foreground">No entities to display</p>
          <p className="text-sm text-muted-foreground mt-1">Start by creating entities</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {entities.map((entity) => (
        <EntityStackCard
          key={entity.id}
          entity={entity}
          onSelect={() => onSelectEntity?.(entity)}
          onAttributeChange={
            onAttributeChange
              ? (attrName, newValue) => onAttributeChange(entity.id, attrName, newValue)
              : undefined
          }
          onDelete={
            onDeleteEntity
              ? () => onDeleteEntity(entity.id)
              : undefined
          }
        />
      ))}
    </div>
  );
};
