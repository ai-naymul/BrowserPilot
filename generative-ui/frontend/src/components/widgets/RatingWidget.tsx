import { useState } from 'react';
import { Info, ChevronDown, ChevronUp } from 'lucide-react';
import { EntityAttribute } from '@/types/entity';

interface RatingWidgetProps {
  attribute: EntityAttribute;
  reasoningAttribute?: EntityAttribute; // Optional reasoning attribute
  compact?: boolean;
}

export const RatingWidget = ({ attribute, reasoningAttribute, compact }: RatingWidgetProps) => {
  const [showReasoning, setShowReasoning] = useState(false);
  
  const rating = typeof attribute.value === 'number' ? attribute.value : parseFloat(attribute.value);
  const isValidRating = !isNaN(rating) && rating >= 0 && rating <= 10;
  
  if (!isValidRating) {
    return (
      <div className="text-sm text-muted-foreground">
        {attribute.name.replace(/_/g, ' ')}: Invalid rating
      </div>
    );
  }
  
  // Calculate star display
  const fullStars = Math.floor(rating / 2);
  const hasHalfStar = (rating % 2) >= 1;
  const stars = '⭐'.repeat(fullStars) + (hasHalfStar ? '½' : '');
  
  // Determine color based on rating (muted palette)
  const getColorClass = () => {
    if (rating >= 8) return 'text-green-400';
    if (rating >= 6) return 'text-amber-300';
    return 'text-sky-400';
  };
  
  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <span className={`text-lg font-bold ${getColorClass()}`}>
          {rating.toFixed(1)}/10
        </span>
        <span className="text-sm">{stars}</span>
        {reasoningAttribute && (
          <button
            onClick={() => setShowReasoning(!showReasoning)}
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="Show reasoning"
          >
            <Info className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }
  
  return (
    <div className="space-y-2">
      {/* Rating Header */}
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground capitalize">
          {attribute.name.replace(/_/g, ' ')}
        </label>
        
        <div className="flex items-center gap-2">
          <span className={`text-xl font-bold ${getColorClass()}`}>
            {rating.toFixed(1)}/10
          </span>
          <span className="text-lg">{stars}</span>
          
          {reasoningAttribute && (
            <button
              onClick={() => setShowReasoning(!showReasoning)}
              className="ml-2 p-1 rounded-full hover:bg-gray-100 transition-colors text-blue-500 hover:text-blue-700"
              title={showReasoning ? "Hide reasoning" : "Show reasoning"}
            >
              {showReasoning ? (
                <ChevronUp className="w-5 h-5" />
              ) : (
                <Info className="w-5 h-5" />
              )}
            </button>
          )}
        </div>
      </div>
      
      {/* Visual Bar */}
      <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`absolute inset-y-0 left-0 rounded-full transition-all duration-150 ease ${
            rating >= 8 ? 'bg-green-400' : rating >= 6 ? 'bg-amber-300' : 'bg-sky-400'
          }`}
          style={{ width: `${(rating / 10) * 100}%` }}
        />
      </div>
      
      {/* Reasoning Section (Expandable) */}
      {showReasoning && reasoningAttribute && (
        <div className="mt-3 p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-3 animate-in slide-in-from-top duration-200">
          <div className="flex items-start gap-2">
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">
                Why {rating.toFixed(1)}/10?
              </h4>
              <p className="text-sm text-foreground leading-relaxed">
                {reasoningAttribute.value}
              </p>
            </div>
          </div>
          
          {/* Rating Breakdown if provided in metadata */}
          {reasoningAttribute.metadata?.breakdown && (
            <div className="mt-3 pt-3 border-t border-blue-200 space-y-2">
              <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Rating Breakdown:
              </h5>
              {Object.entries(reasoningAttribute.metadata.breakdown).map(([key, value]: [string, any]) => (
                <div key={key} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className="font-semibold text-foreground">{value}/10</span>
                </div>
              ))}
            </div>
          )}
          
          {/* Source Attribution */}
          {reasoningAttribute.metadata?.source && (
            <div className="mt-2 pt-2 border-t border-blue-200">
              <p className="text-xs text-muted-foreground italic">
                Source: {reasoningAttribute.metadata.source}
              </p>
            </div>
          )}
        </div>
      )}
      
      {/* Placeholder if no reasoning */}
      {showReasoning && !reasoningAttribute && (
        <div className="mt-3 p-4 bg-secondary border border-border rounded-lg">
          <p className="text-sm text-muted-foreground italic">
            No reasoning provided for this rating.
          </p>
        </div>
      )}
    </div>
  );
};
