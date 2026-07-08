import { EntityAttribute } from '@/types/entity';
import { Input } from '@/components/ui/input';
import { Calendar } from 'lucide-react';

interface DateWidgetProps {
  attribute: EntityAttribute;
  compact?: boolean;
  onChange?: (newValue: any) => void;
}

export const DateWidget = ({ attribute, compact, onChange }: DateWidgetProps) => {
  // Ensure value is proper date format (yyyy-MM-dd)
  const rawValue = attribute.value as string;
  const value = rawValue && rawValue.includes(':') && !rawValue.includes('T') 
    ? '' // Clear invalid time-only values
    : rawValue;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: '2-digit',
      day: '2-digit',
      year: 'numeric',
    });
  };

  const displayValue = attribute.widget === 'time' 
    ? attribute.value 
    : formatDate(attribute.value);

  if (compact) {
    return (
      <div>
        <label className="text-xs font-medium text-muted-foreground capitalize">
          {attribute.name.replace('_', ' ')}
        </label>
        <div className="text-sm mt-1">{displayValue}</div>
      </div>
    );
  }

  return (
    <div>
      <label className="text-sm font-medium capitalize block mb-2">
        {attribute.name.replace('_', ' ')}
      </label>
      <div className="relative">
        <Input
          type="date"
          value={value || ''}
          onChange={(e) => onChange?.(e.target.value)}
          className="w-full border border-border rounded-md px-3 py-2 bg-background text-foreground"
          placeholder="yyyy-mm-dd"
          readOnly={!onChange || attribute.editable === false}
        />
        <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      </div>
    </div>
  );
};
