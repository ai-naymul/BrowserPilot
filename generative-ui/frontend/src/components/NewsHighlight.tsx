import { motion } from "framer-motion";
import { Newspaper, ExternalLink } from "lucide-react";

interface NewsItem {
  id: string;
  headline: string;
  source: string;
  date: string;
  url?: string;
  icon?: React.ReactNode;
}

interface NewsHighlightProps {
  items: NewsItem[];
  maxItems?: number;
  showMoreLink?: boolean;
  onItemClick?: (item: NewsItem) => void;
}

export const NewsHighlight = ({
  items,
  maxItems = 5,
  showMoreLink = false,
  onItemClick,
}: NewsHighlightProps) => {
  const displayItems = items.slice(0, maxItems);

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffHours < 1) return 'just now';
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-border bg-card p-6"
    >
      <div className="mb-4 flex items-center gap-2">
        <Newspaper className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold text-foreground">News Highlights</h3>
      </div>

      <div className="space-y-3">
        {displayItems.map((item, idx) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            onClick={() => onItemClick?.(item)}
            className={`group rounded-lg p-3 transition-all ${
              onItemClick || item.url
                ? "cursor-pointer hover:bg-muted/50"
                : ""
            }`}
          >
            <div className="flex gap-3">
              <div className="mt-1 shrink-0">
                {item.icon || <Newspaper className="h-4 w-4 text-primary" />}
              </div>

              <div className="flex-1 space-y-1">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-medium text-foreground group-hover:underline">
                    {item.headline}
                  </h4>
                  {item.url && (
                    <ExternalLink className="h-3 w-3 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                  )}
                </div>

                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{item.source}</span>
                  <span>•</span>
                  <span>{formatDate(item.date)}</span>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {showMoreLink && items.length > maxItems && (
        <button className="mt-4 text-sm font-medium text-primary hover:underline">
          Show {items.length - maxItems} more →
        </button>
      )}
    </motion.div>
  );
};
