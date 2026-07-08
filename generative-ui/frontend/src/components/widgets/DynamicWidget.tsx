import { EntityAttribute, Entity } from '@/types/entity';
import { ShortTextWidget } from './ShortTextWidget';
import { CurrencyWidget } from './CurrencyWidget';
import { DateWidget } from './DateWidget';
import { LocationWidget } from './LocationWidget';
import { ContactCardWidget } from './ContactCardWidget';
import { TaskListWidget } from './TaskListWidget';
import { InteractiveArrayWidget } from './InteractiveArrayWidget';
import { RatingWidget } from './RatingWidget';
import { LongTextWidget } from './LongTextWidget';

interface DynamicWidgetProps {
  attribute: EntityAttribute;
  allAttributes?: EntityAttribute[]; // For finding related reasoning attributes
  compact?: boolean;
  onChange?: (newValue: any) => void;
}

export const DynamicWidget = ({ attribute, allAttributes, compact, onChange }: DynamicWidgetProps) => {
  const widgetType = attribute.widget || 'short_text';
  
  // Auto-detect long text (reasoning, descriptions, notes)
  const textValue = typeof attribute.value === 'string' ? attribute.value : '';
  const isLongText = attribute.name.includes('_reasoning') || 
                     attribute.name.includes('description') ||
                     attribute.name.includes('notes') ||
                     textValue.length > 150;

  // Check if it's a task list array
  const isTaskList = widgetType === 'array' && 
    attribute.value &&
    Array.isArray(attribute.value) &&
    attribute.value.length > 0 &&
    typeof attribute.value[0] === 'object' &&
    ('task' in attribute.value[0] || 'done' in attribute.value[0]);

  // Check if it's a data table array (objects with multiple fields)
  const isDataTable = widgetType === 'array' &&
    attribute.value &&
    Array.isArray(attribute.value) &&
    attribute.value.length > 0 &&
    typeof attribute.value[0] === 'object' &&
    !isTaskList &&
    attribute.item_widget !== 'contact_card';

  // Use LongTextWidget for long text (auto-detected or explicit)
  if (isLongText || widgetType === 'long_text') {
    return <LongTextWidget attribute={attribute} compact={compact} onChange={onChange} />;
  }
  
  switch (widgetType) {
    case 'currency':
      return <CurrencyWidget attribute={attribute} compact={compact} onChange={onChange} />;
    case 'date':
    case 'time':
      return <DateWidget attribute={attribute} compact={compact} onChange={onChange} />;
    case 'location':
      return <LocationWidget attribute={attribute} compact={compact} onChange={onChange} />;
    case 'rating':
      // Look for corresponding reasoning attribute
      const reasoningAttrName = `${attribute.name}_reasoning`;
      const reasoningAttr = allAttributes?.find(a => a.name === reasoningAttrName);
      return <RatingWidget attribute={attribute} reasoningAttribute={reasoningAttr} compact={compact} />;
    case 'contact_card':
      return <ContactCardWidget attribute={attribute} />;
    case 'object':
      // Handle object types (like coordinates)
      const objValue = attribute.value;
      if (typeof objValue === 'object' && objValue !== null) {
        // Special handling for coordinates
        if (objValue.lat !== undefined && objValue.lng !== undefined) {
          const displayValue = `${Number(objValue.lat).toFixed(4)}, ${Number(objValue.lng).toFixed(4)}`;
          if (compact) {
            return <div className="text-sm text-foreground">{displayValue}</div>;
          }
          return (
            <div>
              <label className="text-sm font-medium text-foreground capitalize block mb-1">
                {attribute.name.replace(/_/g, ' ')}
              </label>
              <div className="text-sm text-muted-foreground font-mono bg-secondary px-3 py-2 rounded border border-border">
                📍 {displayValue}
              </div>
            </div>
          );
        }
        
        // Generic object display
        const entries = Object.entries(objValue);
        if (entries.length === 0) return null;
        
        if (compact) {
          return (
            <div className="text-sm text-foreground">
              {entries.map(([k, v]) => `${k}: ${v}`).join(', ')}
            </div>
          );
        }
        
        return (
          <div>
            <label className="text-sm font-medium text-foreground capitalize block mb-1">
              {attribute.name.replace(/_/g, ' ')}
            </label>
            <div className="text-sm bg-secondary px-3 py-2 rounded border border-border">
              {entries.map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <span className="font-medium text-muted-foreground">{k}:</span>
                  <span className="text-foreground">{String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        );
      }
      return null;
    case 'array':
      // Render task list with interactive checkboxes
      if (isTaskList) {
        return <TaskListWidget attribute={attribute} compact={compact} onChange={onChange} />;
      }
      
      // Render contact cards
      if (attribute.item_widget === 'contact_card') {
        return (
          <div className="space-y-3">
            <label className="text-sm font-medium capitalize">
              {attribute.name.replace('_', ' ')}
            </label>
            {(attribute.value as any[]).map((item, idx) => (
              <ContactCardWidget
                key={idx}
                attribute={{ ...attribute, value: item }}
              />
            ))}
          </div>
        );
      }
      
      // Render data tables with full CRUD (add/edit/delete)
      if (isDataTable) {
        return <InteractiveArrayWidget attribute={attribute} compact={compact} onChange={onChange} />;
      }
      
      // Fallback for simple arrays
      return (
        <div>
          <label className="text-sm font-medium capitalize block mb-2">
            {attribute.name.replace('_', ' ')}
          </label>
          <div className="text-sm text-muted-foreground">
            {Array.isArray(attribute.value) 
              ? attribute.value.join(', ')
              : String(attribute.value)}
          </div>
        </div>
      );
    case 'short_text':
    case 'long_text':
    case 'number':
    case 'progress':
    case 'badge':
    default:
      return <ShortTextWidget attribute={attribute} compact={compact} onChange={onChange} />;
  }
};
