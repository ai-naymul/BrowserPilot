/**
 * Modern Skeleton Loading Components
 * Following HCI principles: Show mockup of content structure while loading
 */

import { motion } from 'framer-motion';

// Shimmer animation for skeleton elements
const shimmer = {
  animate: {
    backgroundPosition: ['200% 0', '-200% 0'],
  },
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'linear',
  },
};

// Base skeleton element with shimmer effect
const SkeletonBox = ({ className = '', delay = 0 }: { className?: string; delay?: number }) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{
      opacity: 1,
      backgroundPosition: ['200% 0', '-200% 0'],
    }}
    transition={{
      opacity: { delay },
      backgroundPosition: {
        duration: 2,
        repeat: Infinity,
        ease: 'linear',
      },
    }}
    className={`bg-gradient-to-r from-muted/40 via-muted/60 to-muted/40 bg-[length:200%_100%] rounded-lg ${className}`}
    style={{
      backgroundPosition: '200% 0',
    }}
  />
);

/**
 * Skeleton for Initial Generation (Tri-Pane Layout)
 */
export const TriPaneSkeleton = () => (
  <div className="flex h-full gap-0 overflow-hidden">
    {/* Left Panel Skeleton */}
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="w-80 border-r border-border bg-card/30 p-4 space-y-3"
    >
      <div className="space-y-2">
        <SkeletonBox className="h-6 w-32" delay={0} />
        <SkeletonBox className="h-4 w-48" delay={0.05} />
      </div>

      {/* Entity Cards */}
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 + i * 0.1 }}
          className="p-4 rounded-xl border border-border/50 space-y-3"
        >
          <div className="flex items-center gap-3">
            <SkeletonBox className="h-10 w-10 rounded-full" delay={0.2 + i * 0.1} />
            <div className="flex-1 space-y-2">
              <SkeletonBox className="h-4 w-24" delay={0.25 + i * 0.1} />
              <SkeletonBox className="h-3 w-16" delay={0.3 + i * 0.1} />
            </div>
          </div>
          <SkeletonBox className="h-8 w-full" delay={0.35 + i * 0.1} />
        </motion.div>
      ))}
    </motion.div>

    {/* Center Panel Skeleton */}
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.2 }}
      className="flex-1 flex flex-col"
    >
      {/* Toggle Buttons */}
      <div className="flex gap-2 p-3 border-b border-border">
        <SkeletonBox className="h-8 w-20" delay={0.3} />
        <SkeletonBox className="h-8 w-24" delay={0.35} />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-6 space-y-4">
        <SkeletonBox className="h-64 w-full rounded-2xl" delay={0.4} />
        <div className="grid grid-cols-3 gap-4">
          <SkeletonBox className="h-32 rounded-xl" delay={0.45} />
          <SkeletonBox className="h-32 rounded-xl" delay={0.5} />
          <SkeletonBox className="h-32 rounded-xl" delay={0.55} />
        </div>
      </div>
    </motion.div>

    {/* Right Panel Skeleton */}
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 }}
      className="w-80 border-l border-border bg-card/50 p-4 space-y-4"
    >
      <div className="flex items-center justify-between">
        <SkeletonBox className="h-6 w-32" delay={0.4} />
        <SkeletonBox className="h-8 w-8 rounded-lg" delay={0.45} />
      </div>

      {/* Detail Sections */}
      {[0, 1, 2, 3].map((i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 + i * 0.05 }}
          className="space-y-2"
        >
          <SkeletonBox className="h-3 w-20" delay={0.5 + i * 0.05} />
          <SkeletonBox className="h-10 w-full rounded-lg" delay={0.55 + i * 0.05} />
        </motion.div>
      ))}
    </motion.div>
  </div>
);

/**
 * Skeleton for Refinement/Follow-up (Compact)
 */
export const RefinementSkeleton = () => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="max-w-4xl mx-auto p-6 space-y-4"
  >
    {/* New Analysis Section */}
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.1 }}
      className="rounded-2xl border border-border/50 bg-card/30 p-6 space-y-4"
    >
      <div className="flex items-center justify-between">
        <SkeletonBox className="h-6 w-48" delay={0.15} />
        <SkeletonBox className="h-8 w-8 rounded-full" delay={0.2} />
      </div>

      {/* Content Blocks */}
      <div className="space-y-3">
        <SkeletonBox className="h-4 w-full" delay={0.25} />
        <SkeletonBox className="h-4 w-5/6" delay={0.3} />
        <SkeletonBox className="h-4 w-4/6" delay={0.35} />
      </div>

      {/* Chart Skeleton */}
      <SkeletonBox className="h-48 w-full rounded-xl" delay={0.4} />

      {/* Action Buttons */}
      <div className="flex gap-2">
        <SkeletonBox className="h-8 w-32 rounded-full" delay={0.45} />
        <SkeletonBox className="h-8 w-40 rounded-full" delay={0.5} />
      </div>
    </motion.div>
  </motion.div>
);

/**
 * Inline Skeleton for specific component updates
 */
export const InlineSkeleton = ({ type = 'section' }: { type?: 'section' | 'chart' | 'table' }) => {
  if (type === 'chart') {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="p-6 space-y-4"
      >
        <SkeletonBox className="h-6 w-40" />
        <SkeletonBox className="h-64 w-full rounded-xl" delay={0.1} />
      </motion.div>
    );
  }

  if (type === 'table') {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="p-6 space-y-3"
      >
        <SkeletonBox className="h-6 w-48" />
        <div className="space-y-2">
          {[0, 1, 2, 3].map((i) => (
            <SkeletonBox key={i} className="h-12 w-full" delay={i * 0.05} />
          ))}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-6 space-y-3"
    >
      <SkeletonBox className="h-6 w-40" />
      <SkeletonBox className="h-4 w-full" delay={0.05} />
      <SkeletonBox className="h-4 w-5/6" delay={0.1} />
    </motion.div>
  );
};
