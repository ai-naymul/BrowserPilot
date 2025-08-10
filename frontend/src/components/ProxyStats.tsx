import React from 'react';
import { Shield, CheckCircle, XCircle, RotateCcw } from 'lucide-react';

interface ProxyStatsProps {
  stats: {
    available: number;
    healthy: number;
    blocked: number;
    retry_count: number;
  };
}

export const ProxyStats: React.FC<ProxyStatsProps> = ({ stats }) => {
  return (
    <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-sm border border-stone-200/60 overflow-hidden transition-all duration-300 hover:shadow-md hover:bg-white/80">
      <div className="p-6">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-stone-400 to-stone-500 dark:from-stone-500 dark:to-stone-600 rounded-xl flex items-center justify-center shadow-md">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-medium text-stone-800 dark:text-stone-200">Proxy Network</h2>
            <p className="text-sm text-stone-600 dark:text-stone-400 font-light">Smart rotation & health</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-sage-50/80 to-sage-100/50 dark:from-stone-800/50 dark:to-stone-700/50 p-4 rounded-xl border border-sage-200/40 dark:border-stone-600/40 group hover:shadow-sm transition-all duration-300 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle className="w-4 h-4 text-sage-600 dark:text-sage-400" />
              <span className="text-xs text-sage-600/70 dark:text-sage-400/70 font-medium tracking-wide">AVAILABLE</span>
            </div>
            <div className="text-2xl font-light text-sage-700 dark:text-sage-300 mb-1">{stats.available}</div>
            <div className="text-sm text-sage-600/80 dark:text-sage-400/80 font-light">Proxies</div>
          </div>

          <div className="bg-gradient-to-br from-sky-50/80 to-sky-100/50 dark:from-stone-800/50 dark:to-stone-700/50 p-4 rounded-xl border border-sky-200/40 dark:border-stone-600/40 group hover:shadow-sm transition-all duration-300 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle className="w-4 h-4 text-sky-600 dark:text-sky-400 fill-current" />
              <span className="text-xs text-sky-600/70 dark:text-sky-400/70 font-medium tracking-wide">HEALTHY</span>
            </div>
            <div className="text-2xl font-light text-sky-700 dark:text-sky-300 mb-1">{stats.healthy}</div>
            <div className="text-sm text-sky-600/80 dark:text-sky-400/80 font-light">Active</div>
          </div>

          <div className="bg-gradient-to-br from-honey-50/80 to-honey-100/50 dark:from-stone-800/50 dark:to-stone-700/50 p-4 rounded-xl border border-honey-200/40 dark:border-stone-600/40 group hover:shadow-sm transition-all duration-300 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-2">
              <XCircle className="w-4 h-4 text-honey-600 dark:text-honey-400" />
              <span className="text-xs text-honey-600/70 dark:text-honey-400/70 font-medium tracking-wide">BLOCKED</span>
            </div>
            <div className="text-2xl font-light text-honey-700 dark:text-honey-300 mb-1">{stats.blocked}</div>
            <div className="text-sm text-honey-600/80 dark:text-honey-400/80 font-light">Proxies</div>
          </div>

          <div className="bg-gradient-to-br from-blush-50/80 to-blush-100/50 dark:from-stone-800/50 dark:to-stone-700/50 p-4 rounded-xl border border-blush-200/40 dark:border-stone-600/40 group hover:shadow-sm transition-all duration-300 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-2">
              <RotateCcw className="w-4 h-4 text-blush-600 dark:text-blush-400" />
              <span className="text-xs text-blush-600/70 dark:text-blush-400/70 font-medium tracking-wide">RETRIES</span>
            </div>
            <div className="text-2xl font-light text-blush-700 dark:text-blush-300 mb-1">{stats.retry_count}</div>
            <div className="text-sm text-blush-600/80 dark:text-blush-400/80 font-light">Count</div>
          </div>
        </div>
      </div>
    </div>
  );
};