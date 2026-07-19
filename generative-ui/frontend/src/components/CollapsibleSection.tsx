import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { useState, ReactNode } from "react";

interface CollapsibleSectionProps {
  title: string | ReactNode;
  children: ReactNode;
  defaultExpanded?: boolean;
  badge?: string | number;
}

export const CollapsibleSection = ({
  title,
  children,
  defaultExpanded = false,
  badge,
}: CollapsibleSectionProps) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="border-t border-border">
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left transition-colors hover:bg-muted/30"
        whileHover={{ backgroundColor: "hsl(0 0% 18%)" }}
      >
        <div className="flex items-center gap-3">
          {typeof title === "string" ? (
            <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          ) : (
            title
          )}
          {badge && (
            <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-medium text-primary-foreground">
              {badge}
            </span>
          )}
        </div>
        
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.3 }}
        >
          <ChevronDown className="h-5 w-5 text-muted-foreground" />
        </motion.div>
      </motion.button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-6 py-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
