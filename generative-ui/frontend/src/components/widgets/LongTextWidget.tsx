import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { EntityAttribute } from '@/types/entity';

interface LongTextWidgetProps {
  attribute: EntityAttribute;
  onChange?: (value: any) => void;
  compact?: boolean;
}

/**
 * Widget for displaying long text with expand/collapse functionality
 * Perfect for reasoning, descriptions, notes, etc.
 */
export const LongTextWidget = ({ attribute, onChange, compact = false }: LongTextWidgetProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const text = String(attribute.value || '');
  const TRUNCATE_LENGTH = compact ? 60 : 120;
  const isLong = text.length > TRUNCATE_LENGTH;
  const truncated = text.slice(0, TRUNCATE_LENGTH) + '...';
  
  // Check if this is a reasoning attribute
  const isReasoning = attribute.name.includes('_reasoning');
  const displayName = attribute.name.replace(/_/g, ' ').replace(' reasoning', '');
  
  if (compact) {
    return (
      <div className="flex items-start gap-2">
        <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-foreground leading-relaxed">
            {isExpanded ? text : truncated}
          </p>
          {isLong && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="mt-1 text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-3 h-3" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="w-3 h-3" />
                  Read more
                </>
              )}
            </button>
          )}
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-2">
      {/* Label */}
      {!isReasoning && (
        <label className="block text-sm font-medium text-foreground capitalize">
          {displayName}
        </label>
      )}
      
      {/* Content box */}
      <div className={`rounded-lg border transition-colors ${
        isReasoning 
          ? 'bg-blue-50 border-blue-200' 
          : 'bg-secondary border-border'
      }`}>
        <div className="p-4">
          {/* Icon and title for reasoning */}
          {isReasoning && (
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5 text-blue-600" />
              <h4 className="text-sm font-semibold text-blue-900">
                Why this {displayName.replace('rating', 'rating')}?
              </h4>
            </div>
          )}
          
          {/* Text content */}
          <p className={`text-sm leading-relaxed ${
            isReasoning ? 'text-foreground' : 'text-muted-foreground'
          }`}>
            {isExpanded || !isLong ? text : truncated}
          </p>
          
          {/* Expand/Collapse button */}
          {isLong && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className={`mt-3 text-sm font-medium flex items-center gap-1 transition-colors ${
                isReasoning 
                  ? 'text-blue-600 hover:text-blue-700' 
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Read more ({text.length - TRUNCATE_LENGTH} more characters)
                </>
              )}
            </button>
          )}
        </div>
      </div>
      
      {/* Edit mode (if onChange provided) */}
      {onChange && (
        <textarea
          value={text}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 bg-background text-foreground border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm placeholder:text-muted-foreground"
          rows={5}
          placeholder="Enter text..."
        />
      )}
    </div>
  );
};
