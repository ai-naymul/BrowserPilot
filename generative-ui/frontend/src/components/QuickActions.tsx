/**
 * QuickActions - Contextual Action Menu
 *
 * Appears on hover over cards, charts, and other interactive modules.
 * Follows Fitts's Law (large, near targets) and Hick's Law (few choices).
 *
 * Design Principles:
 * - Appear within 50ms of hover
 * - 2-3 actions maximum (reduce decision time)
 * - Large, reachable buttons
 * - Position near pointer (top-right of parent)
 * - Stop propagation to prevent parent clicks
 */

import { motion, AnimatePresence } from 'framer-motion';

export interface QuickAction {
  id: string;
  label: string;
  onClick?: () => void;
  tone?: 'default' | 'danger' | 'success';
  icon?: string;
}

interface QuickActionsProps {
  items: QuickAction[];
  className?: string;
}

export const QuickActions = ({ items, className = '' }: QuickActionsProps) => {
  if (items.length === 0) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.85, y: -10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.85, y: -10 }}
        transition={{ duration: 0.15, ease: "easeOut" }}
        className={`absolute right-3 top-3 z-20 flex gap-2 ${className}`}
      >
        {items.map((item) => (
          <motion.button
            key={item.id}
            onClick={(e) => {
              e.stopPropagation(); // Prevent parent click
              item.onClick?.();
            }}
            whileHover={{ scale: 1.08, y: -2 }}
            whileTap={{ scale: 0.95 }}
            className={`
              rounded-lg px-4 py-2 text-xs font-semibold
              backdrop-blur-xl shadow-lg
              transition-all duration-150
              ${getToneClasses(item.tone)}
            `}
            style={{
              backdropFilter: 'blur(20px) saturate(180%)',
            }}
          >
            {item.icon && <span className="mr-1.5">{item.icon}</span>}
            {item.label}
          </motion.button>
        ))}
      </motion.div>
    </AnimatePresence>
  );
};

function getToneClasses(tone: QuickAction['tone'] = 'default'): string {
  switch (tone) {
    case 'danger':
      return 'bg-red-500/30 text-red-100 hover:bg-red-500/40 hover:shadow-[0_4px_20px_rgba(239,68,68,0.4)] border border-red-400/50';
    case 'success':
      return 'bg-green-500/30 text-green-100 hover:bg-green-500/40 hover:shadow-[0_4px_20px_rgba(34,197,94,0.4)] border border-green-400/50';
    case 'default':
    default:
      return 'bg-zinc-800/80 text-zinc-100 hover:bg-zinc-700/90 hover:shadow-[0_4px_20px_rgba(0,0,0,0.5)] border border-zinc-600/50';
  }
}
