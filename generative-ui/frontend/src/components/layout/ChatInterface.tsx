import { useState } from 'react';
import { Send, ChevronDown, ChevronUp } from 'lucide-react';
import { ChatMessage } from '@/types/entity';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  suggestions?: string[];
  onSubmit: (message: string) => void;
  isLoading?: boolean;
  isVisible?: boolean;
  onToggleVisibility?: () => void;
}

export const ChatInterface = ({
  messages,
  suggestions,
  onSubmit,
  isLoading,
  isVisible = true,
  onToggleVisibility
}: ChatInterfaceProps) => {
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (input.trim()) {
      onSubmit(input);
      setInput('');
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    onSubmit(suggestion);
  };

  return (
    <div className="flex flex-col items-center gap-3 w-full max-w-3xl mx-auto">
      {/* Suggestion Chips - Only when expanded */}
      <AnimatePresence>
        {isVisible && suggestions && suggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="flex gap-2 flex-wrap justify-center"
          >
            {suggestions.slice(0, 4).map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={isLoading}
                className="px-3 py-1.5 text-xs font-medium rounded-full border border-border/50 bg-card/90 backdrop-blur-xl hover:bg-accent/10 hover:border-primary/30 transition-all disabled:opacity-50 shadow-sm"
              >
                {suggestion}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Bar - Compact (ChatGPT Style) */}
      <div className="relative w-full">
        <div className="relative flex items-center gap-2 bg-card/95 backdrop-blur-xl border border-border/50 rounded-full shadow-xl hover:shadow-2xl hover:border-border transition-all">
          {/* Expand/Collapse Toggle */}
          {onToggleVisibility && (
            <button
              onClick={onToggleVisibility}
              className="pl-4 pr-2 text-muted-foreground hover:text-foreground transition-colors"
              title={isVisible ? "Collapse" : "Expand suggestions"}
            >
              {isVisible ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronUp className="h-4 w-4" />
              )}
            </button>
          )}

          {/* Input Field */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder={isLoading ? "Processing..." : "Ask anything..."}
            disabled={isLoading}
            className="flex-1 px-3 py-3 bg-transparent text-foreground text-sm placeholder:text-muted-foreground/50 focus:outline-none disabled:opacity-50"
          />

          {/* Send Button */}
          <div className="pr-2">
            <Button
              onClick={handleSubmit}
              disabled={!input.trim() || isLoading}
              size="icon"
              className="h-8 w-8 rounded-full shadow-md hover:shadow-lg transition-all disabled:opacity-50"
            >
              {isLoading ? (
                <span className="h-3.5 w-3.5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send className="h-3.5 w-3.5" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
