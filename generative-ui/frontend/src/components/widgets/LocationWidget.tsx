import { EntityAttribute } from '@/types/entity';
import { Input } from '@/components/ui/input';
import { MapPin } from 'lucide-react';

interface LocationWidgetProps {
  attribute: EntityAttribute;
  compact?: boolean;
  onChange?: (newValue: any) => void;
}

export const LocationWidget = ({ attribute, compact, onChange }: LocationWidgetProps) => {
  // Handle object values
  let displayValue = attribute.value;
  if (typeof displayValue === 'object' && displayValue !== null) {
    if (displayValue.address) {
      displayValue = displayValue.address;
    } else if (displayValue.name) {
      displayValue = displayValue.name;
    } else if (displayValue.city && displayValue.state) {
      displayValue = `${displayValue.city}, ${displayValue.state}`;
    } else {
      displayValue = JSON.stringify(displayValue);
    }
  }
  
  if (compact) {
    return (
      <div>
        <label className="text-xs font-medium text-muted-foreground capitalize">
          {attribute.name.replace('_', ' ')}
        </label>
        <div className="text-sm mt-1 flex items-center gap-1">
          <MapPin className="h-3 w-3 text-muted-foreground" />
          {displayValue || '-'}
        </div>
      </div>
    );
  }

  return (
    <div>
      <label className="text-sm font-medium capitalize block mb-2">
        {attribute.name.replace('_', ' ')}
      </label>
      <div className="relative">
        <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none z-10" />
        <input
          type="text"
          value={displayValue || ''}
          onChange={(e) => onChange?.(e.target.value)}
          className="w-full border border-border rounded-md pl-10 pr-3 py-2 bg-background text-foreground"
          readOnly={!onChange || attribute.editable === false}
          placeholder="Enter location"
        />
      </div>
    </div>
  );
};
