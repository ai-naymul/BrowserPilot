import { Entity } from '@/types/entity';
import { TrendingUp, MapPin, DollarSign, Clock, Star, Check } from 'lucide-react';

interface ComparisonCardWidgetProps {
  entity: Entity;
  isSelected?: boolean;
  onSelect?: () => void;
  compact?: boolean;
}

export const ComparisonCardWidget = ({
  entity,
  isSelected = false,
  onSelect,
  compact = false
}: ComparisonCardWidgetProps) => {
  
  // Extract key metrics
  const getAttributeValue = (name: string) => {
    const attr = entity.attributes.find(a => a.name === name);
    return attr?.value;
  };
  
  const totalCost = getAttributeValue('total_cost') || getAttributeValue('total_comp_year1');
  const location = getAttributeValue('location') || getAttributeValue('city');
  const highlights = getAttributeValue('highlights') || [];
  const country = getAttributeValue('country');
  
  // Get gradient based on entity type
  const gradients = {
    'Destination': 'from-purple-500 to-pink-500',
    'Offer': 'from-green-500 to-emerald-500',
    'default': 'from-blue-500 to-cyan-500'
  };
  
  const baseType = entity.type.split('_')[0]; // Get first part (Destination, Offer, etc.)
  const gradient = gradients[baseType as keyof typeof gradients] || gradients.default;
  
  return (
    <div
      onClick={onSelect}
      className={`
        relative bg-card rounded-xl shadow-md hover:shadow-xl transition-all duration-300
        border-2 ${isSelected ? 'border-primary ring-2 ring-primary/20' : 'border-transparent'}
        ${onSelect ? 'cursor-pointer transform hover:-translate-y-1' : ''}
      `}
    >
      {/* Gradient Header */}
      <div className={`h-24 rounded-t-xl bg-gradient-to-r ${gradient} p-4 flex items-center justify-between`}>
        <div className="flex items-center gap-3">
          <span className="text-4xl">{entity.icon}</span>
          <div>
            <h3 className="text-white font-bold text-xl">{entity.public_identifier}</h3>
            {location && (
              <div className="flex items-center gap-1 text-white/90 text-sm mt-1">
                <MapPin className="h-3 w-3" />
                {location}{country && `, ${country}`}
              </div>
            )}
          </div>
        </div>
        
        {/* Total Cost Badge */}
        {totalCost && (
          <div className="bg-black/20 backdrop-blur-sm rounded-lg px-3 py-2">
            <div className="text-white/80 text-xs font-medium">Total</div>
            <div className="text-white font-bold text-lg">
              ${typeof totalCost === 'number' ? totalCost.toLocaleString() : totalCost}
            </div>
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="p-4">
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          {entity.attributes
            .filter(attr => attr.widget === 'currency' && attr.name !== 'total_cost' && attr.name !== 'total_comp_year1' && attr.name !== 'total_comp_4year')
            .slice(0, 4)
            .map(attr => (
              <div key={attr.name} className="bg-secondary rounded-lg p-3">
                <div className="text-xs text-muted-foreground font-medium capitalize mb-1">
                  {attr.name.replace(/_/g, ' ')}
                </div>
                <div className="text-sm font-semibold text-foreground">
                  ${typeof attr.value === 'number' ? attr.value.toLocaleString() : attr.value || 0}
                </div>
              </div>
            ))
          }
        </div>
        
        {/* Additional Info */}
        <div className="space-y-2 mb-4">
          {entity.attributes
            .filter(attr => 
              attr.widget !== 'currency' && 
              attr.widget !== 'array' && 
              attr.function !== 'identifier' &&
              attr.name !== 'id' &&
              !['highlights', 'best_for', 'priority_factors'].includes(attr.name)
            )
            .slice(0, compact ? 2 : 4)
            .map(attr => (
              <div key={attr.name} className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground capitalize">{attr.name.replace(/_/g, ' ')}:</span>
                <span className="text-foreground font-medium">{String(attr.value)}</span>
              </div>
            ))
          }
        </div>
        
        {/* Highlights */}
        {highlights.length > 0 && !compact && (
          <div className="border-t pt-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-foreground mb-2">
              <Star className="h-4 w-4 text-amber-300" />
              Highlights
            </div>
            <div className="space-y-1">
              {highlights.slice(0, 3).map((item: string, i: number) => (
                <div key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{item}</span>
                </div>
              ))}
              {highlights.length > 3 && (
                <div className="text-xs text-muted-foreground ml-6">
                  +{highlights.length - 3} more
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Selection Indicator */}
      {isSelected && (
        <div className="absolute top-2 right-2 bg-blue-500 text-white rounded-full p-1">
          <Check className="h-4 w-4" />
        </div>
      )}
    </div>
  );
};
