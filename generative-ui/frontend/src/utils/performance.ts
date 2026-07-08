/**
 * Performance Monitoring Utilities
 *
 * Tracks interaction performance to ensure <100ms feedback
 * for critical user actions (expand, hover, select).
 *
 * Usage:
 * ```ts
 * const perf = mark('card-expand');
 * // ... do work ...
 * measure(perf, 'card-expand', 100); // Warns if >100ms
 * ```
 */

interface PerformanceMark {
  name: string;
  startTime: number;
}

const THRESHOLDS = {
  expand: 100, // Card expansion
  hover: 50, // Hover quick actions appearance
  select: 100, // Entity selection
  render: 200, // Component render
  action: 150, // Action execution
};

/**
 * Create a performance mark
 */
export function mark(name: string): PerformanceMark {
  const startTime = performance.now();
  performance.mark(`${name}:start`);

  return {
    name,
    startTime,
  };
}

/**
 * Measure elapsed time and warn if threshold exceeded
 */
export function measure(
  mark: PerformanceMark,
  name?: string,
  threshold?: number
): number {
  const endTime = performance.now();
  const duration = endTime - mark.startTime;
  const markName = name || mark.name;

  performance.mark(`${mark.name}:end`);
  performance.measure(mark.name, `${mark.name}:start`, `${mark.name}:end`);

  // Check threshold
  const limit = threshold || THRESHOLDS[markName as keyof typeof THRESHOLDS] || 200;

  if (duration > limit) {
    console.warn(
      `[Performance] ⚠️ ${markName} took ${duration.toFixed(2)}ms (threshold: ${limit}ms)`
    );
  } else {
    console.log(`[Performance] ✓ ${markName} took ${duration.toFixed(2)}ms`);
  }

  return duration;
}

/**
 * Get performance entries for a specific mark
 */
export function getEntries(name: string): PerformanceEntry[] {
  return performance.getEntriesByName(name);
}

/**
 * Clear all performance marks and measures
 */
export function clearMarks(): void {
  performance.clearMarks();
  performance.clearMeasures();
}

/**
 * Get performance summary for all tracked interactions
 */
export function getSummary(): Record<string, { count: number; avg: number; max: number; min: number }> {
  const measures = performance.getEntriesByType('measure');
  const summary: Record<string, { durations: number[] }> = {};

  measures.forEach((entry) => {
    if (!summary[entry.name]) {
      summary[entry.name] = { durations: [] };
    }
    summary[entry.name].durations.push(entry.duration);
  });

  const result: Record<string, { count: number; avg: number; max: number; min: number }> = {};

  Object.keys(summary).forEach((name) => {
    const durations = summary[name].durations;
    result[name] = {
      count: durations.length,
      avg: durations.reduce((a, b) => a + b, 0) / durations.length,
      max: Math.max(...durations),
      min: Math.min(...durations),
    };
  });

  return result;
}

/**
 * Log performance summary to console
 */
export function logSummary(): void {
  const summary = getSummary();

  console.group('[Performance Summary]');
  Object.keys(summary).forEach((name) => {
    const stats = summary[name];
    const threshold = THRESHOLDS[name as keyof typeof THRESHOLDS] || 200;
    const pass = stats.avg < threshold;

    console.log(
      `${pass ? '✓' : '✗'} ${name}:`,
      `avg=${stats.avg.toFixed(2)}ms`,
      `max=${stats.max.toFixed(2)}ms`,
      `min=${stats.min.toFixed(2)}ms`,
      `(n=${stats.count})`
    );
  });
  console.groupEnd();
}
