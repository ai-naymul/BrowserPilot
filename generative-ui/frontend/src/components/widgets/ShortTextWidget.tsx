import { EntityAttribute } from '@/types/entity';
import { Input } from '@/components/ui/input';

interface ShortTextWidgetProps {
  attribute: EntityAttribute;
  compact?: boolean;
  onChange?: (newValue: any) => void;
}

export const ShortTextWidget = ({ attribute, compact, onChange }: ShortTextWidgetProps) => {
  let value = attribute.value;
  
  // Handle null/undefined
  if (value === null || value === undefined) {
    value = '';
  }
  
  // Handle object/array values
  else if (typeof value === 'object') {
    if (Array.isArray(value)) {
      value = `${value.length} items`;
    } else {
      // Extract meaningful value from object
      if (value.address) {
        value = value.address;
      } else if (value.name) {
        value = value.name;
      } else if (value.city && value.state) {
        value = `${value.city}, ${value.state}`;
      } else {
        const keys = Object.keys(value);
        if (keys.length > 0) {
          value = `${keys.length} properties`;
        } else {
          value = '';
        }
      }
    }
  }
  
  // Handle string values - check for special formats
  else if (typeof value === 'string') {
    // Check for [object Object]
    if (value === '[object Object]') {
      value = '-';
    }
    // Check for Python-style dict/list strings
    else if (value.startsWith('[{') || value.startsWith("[{'}") || value.includes("':")) {
      try {
        const jsonStr = value.replace(/'/g, '"').replace(/True/g, 'true').replace(/False/g, 'false').replace(/None/g, 'null');
        const parsed = JSON.parse(jsonStr);
        if (Array.isArray(parsed)) {
          value = `${parsed.length} items`;
        } else if (typeof parsed === 'object') {
          value = `${Object.keys(parsed).length} properties`;
        }
      } catch (e) {
        // Keep original if parsing fails
      }
    }
  }
  
  // Convert any non-string to string
  value = String(value || '');

  if (compact) {
    return (
      <div>
        <label className="text-xs font-medium text-muted-foreground capitalize">
          {attribute.name.replace('_', ' ')}
        </label>
        <div className="text-sm mt-1">{value}</div>
      </div>
    );
  }

  return (
    <div>
      <label className="text-sm font-medium capitalize block mb-2">
        {attribute.name.replace('_', ' ')}
      </label>
      <input
        type="text"
        value={attribute.value || ''}
        onChange={(e) => onChange?.(e.target.value)}
        className="mt-1 w-full border border-border rounded-md px-3 py-2 bg-background text-foreground"
        readOnly={!onChange || attribute.editable === false}
      />
    </div>
  );
};
