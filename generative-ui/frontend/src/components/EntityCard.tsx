import { useState } from 'react';
import { Entity } from '@/types/entity';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp, Trash2, Edit2 } from 'lucide-react';
import { DynamicWidget } from '@/components/widgets/DynamicWidget';

interface EntityCardProps {
  entity: Entity;
  onAttributeChange?: (entityId: string, attributeName: string, newValue: any) => void;
  onDelete?: (entityId: string) => void;
  defaultExpanded?: boolean;
}

export const EntityCard = ({ 
  entity, 
  onAttributeChange, 
  onDelete,
  defaultExpanded = false 
}: EntityCardProps) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  
  // Filter out ID attributes for cleaner display
  const displayAttributes = entity.attributes.filter(
    attr => attr.name !== 'id' && attr.function !== 'identifier'
  );
  
  // Check if entity has array/object attributes (complex data)
  const hasComplexData = entity.attributes.some(
    attr => attr.widget === 'array' || attr.widget === 'object' || attr.data_type === 'array'
  );
  
  // Get summary attributes (first 3-4 important ones)
  const summaryAttributes = displayAttributes.slice(0, hasComplexData ? 2 : 4);
  const detailAttributes = displayAttributes.slice(hasComplexData ? 2 : 4);

  // Generate gradient dynamically based on entity color or use default
  // This is fully domain-agnostic and works for any entity type
  const getGradientStyle = (): React.CSSProperties => {
    if (entity.color) {
      // Use entity's color property to generate a complementary gradient
      return {
        background: `linear-gradient(135deg, ${entity.color} 0%, ${entity.color}dd 100%)`,
      };
    }
    // Fallback: Generate gradient from entity type hash for consistency
    const hash = entity.type.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const hue = hash % 360;
    return {
      background: `linear-gradient(135deg, hsl(${hue}, 70%, 50%) 0%, hsl(${hue + 30}, 70%, 40%) 100%)`,
    };
  };
  
  return (
    <Card className="w-full hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 animate-in fade-in slide-in-from-bottom-4 overflow-hidden border-0">
      {/* Gradient Header */}
      <div className="px-6 py-4" style={getGradientStyle()}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <span className="text-3xl flex-shrink-0 leading-none select-none">{entity.icon}</span>
            <div className="flex-1 min-w-0 overflow-hidden">
              <h3 className="font-bold text-xl text-white leading-tight break-words truncate">{entity.public_identifier}</h3>
              <p className="text-sm text-white/80 truncate capitalize">{entity.type.replace(/_/g, ' ')}</p>
            </div>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            {detailAttributes.length > 0 && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-2 rounded-lg bg-black/20 hover:bg-black/30 backdrop-blur-sm transition-colors"
              >
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4 text-white" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-white" />
                )}
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(entity.id)}
                className="p-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 backdrop-blur-sm transition-colors"
              >
                <Trash2 className="h-4 w-4 text-white" />
              </button>
            )}
          </div>
        </div>
      </div>
      {/* End Gradient Header */}
      <CardContent className="space-y-4 w-full pt-6">
        {/* Summary attributes - always visible */}
        <div className="grid grid-cols-1 gap-4 w-full">
          {summaryAttributes.map((attr) => (
            <DynamicWidget
              key={attr.name}
              attribute={attr}
              compact={false}
              onChange={(newValue) => onAttributeChange?.(entity.id, attr.name, newValue)}
            />
          ))}
        </div>
        
        {/* Expandable detail attributes */}
        {isExpanded && detailAttributes.length > 0 && (
          <div className="pt-4 border-t border-gray-200 space-y-4 animate-in fade-in slide-in-from-top-2 duration-300 w-full">
            <div className="grid grid-cols-1 gap-4 w-full">
              {detailAttributes.map((attr) => (
                <DynamicWidget
                  key={attr.name}
                  attribute={attr}
                  compact={false}
                  onChange={(newValue) => onAttributeChange?.(entity.id, attr.name, newValue)}
                />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
