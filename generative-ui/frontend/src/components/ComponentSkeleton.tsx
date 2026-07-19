import { motion } from 'framer-motion';

/**
 * Loading skeleton for components during streaming
 */

interface ComponentSkeletonProps {
  type?: 'card' | 'chart' | 'table' | 'map';
  count?: number;
}

const SkeletonCard = () => (
  <div className="rounded-xl border border-border bg-card p-6 animate-pulse">
    <div className="h-4 bg-muted rounded w-24 mb-4" />
    <div className="h-12 bg-muted rounded w-32 mb-2" />
    <div className="h-3 bg-muted rounded w-20" />
  </div>
);

const SkeletonChart = () => (
  <div className="rounded-xl border border-border bg-card p-6 animate-pulse">
    <div className="h-4 bg-muted rounded w-32 mb-6" />
    <div className="space-y-3">
      <div className="h-2 bg-muted rounded w-full" />
      <div className="h-2 bg-muted rounded w-3/4" />
      <div className="h-2 bg-muted rounded w-5/6" />
      <div className="h-2 bg-muted rounded w-2/3" />
      <div className="h-2 bg-muted rounded w-full" />
      <div className="h-2 bg-muted rounded w-4/5" />
    </div>
  </div>
);

const SkeletonTable = () => (
  <div className="rounded-xl border border-border bg-card overflow-hidden animate-pulse">
    <div className="bg-secondary p-4">
      <div className="flex gap-4">
        <div className="h-4 bg-muted rounded w-32" />
        <div className="h-4 bg-muted rounded w-24" />
        <div className="h-4 bg-muted rounded w-28" />
      </div>
    </div>
    <div className="p-4 space-y-3">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex gap-4">
          <div className="h-4 bg-muted rounded w-32" />
          <div className="h-4 bg-muted rounded w-24" />
          <div className="h-4 bg-muted rounded w-28" />
        </div>
      ))}
    </div>
  </div>
);

const SkeletonMap = () => (
  <div className="rounded-xl border border-border bg-card h-96 animate-pulse">
    <div className="h-full bg-muted flex items-center justify-center">
      <div className="text-muted-foreground">Loading map...</div>
    </div>
  </div>
);

export const ComponentSkeleton = ({ type = 'card', count = 1 }: ComponentSkeletonProps) => {
  const Skeleton = {
    card: SkeletonCard,
    chart: SkeletonChart,
    table: SkeletonTable,
    map: SkeletonMap,
  }[type];

  return (
    <>
      {Array.from({ length: count }).map((_, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.1 }}
        >
          <Skeleton />
        </motion.div>
      ))}
    </>
  );
};

/**
 * Streaming progress indicator
 */
interface StreamingProgressProps {
  bytesReceived?: number;
  componentsReceived?: number;
}

export const StreamingProgress = ({ bytesReceived, componentsReceived }: StreamingProgressProps) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed bottom-4 right-4 bg-card border border-border rounded-lg shadow-lg p-4 z-50"
    >
      <div className="flex items-center gap-3">
        {/* Animated spinner */}
        <div className="relative h-8 w-8">
          <div className="absolute inset-0 rounded-full border-2 border-primary/20" />
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-primary border-t-transparent"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
        </div>

        <div className="text-sm">
          <div className="font-semibold text-foreground">Generating UI...</div>
          <div className="text-muted-foreground">
            {componentsReceived ? (
              <span>{componentsReceived} components loaded</span>
            ) : bytesReceived ? (
              <span>{(bytesReceived / 1024).toFixed(1)} KB received</span>
            ) : (
              <span>Connecting...</span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
