import { EntityAttribute } from '@/types/entity';
import { Input } from '@/components/ui/input';

interface CurrencyWidgetProps {
  attribute: EntityAttribute;
  compact?: boolean;
  onChange?: (newValue: any) => void;
}

export const CurrencyWidget = ({ attribute, compact, onChange }: CurrencyWidgetProps) => {
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
  }).format(attribute.value);

  if (compact) {
    return (
      <div>
        <label className="text-xs font-medium text-muted-foreground capitalize">
          {attribute.name.replace('_', ' ')}
        </label>
        <div className="text-sm font-medium mt-1">{formatted}</div>
      </div>
    );
  }

  return (
    <div>
      <label className="text-sm font-medium capitalize block mb-2">
        {attribute.name.replace('_', ' ')}
      </label>
      <div className="relative">
        <span className="absolute left-3 top-2.5 text-muted-foreground">$</span>
        <input
          type="number"
          value={attribute.value || 0}
          onChange={(e) => onChange?.(parseFloat(e.target.value) || 0)}
          className="pl-8 w-full border border-border rounded-md px-3 py-2 bg-background text-foreground"
          readOnly={!onChange || attribute.editable === false}
          placeholder="0"
        />
      </div>
    </div>
  );
};
