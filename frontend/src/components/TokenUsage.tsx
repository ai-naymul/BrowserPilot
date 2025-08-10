import React from 'react';
import { BarChart3, TrendingUp, Zap, Activity } from 'lucide-react';

interface TokenUsageProps {
  usage: {
    prompt_tokens: number;
    response_tokens: number;
    total_tokens: number;
    api_calls: number;
  };
}

export const TokenUsage: React.FC<TokenUsageProps> = ({ usage }) => {
  return (
    <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-sm border border-stone-200/60 overflow-hidden transition-all duration-300 hover:shadow-md hover:bg-white/80">
      <div className="p-6">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-stone-400 to-stone-500 dark:from-stone-500 dark:to-stone-600 rounded-xl flex items-center justify-center shadow-md">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-medium text-stone-800 dark:text-stone-200">Token Usage</h2>
            <p className="text-sm text-stone-600 dark:text-stone-400 font-light">AI model consumption</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-stone-50/80 to-stone-100/50 dark:from-stone-800/50 dark:to-stone-700/50 p-4 rounded-xl border border-stone-200/40 dark:border-stone-600/40 group hover:shadow-sm transition-all duration-300 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-4 h-4 text-stone-600 dark:text-stone-400" />
              <span className="text-xs text-stone-600/70 dark:text-stone-400/70 font-medium tracking-wide">TOTAL</span>
            </div>
            <div className="text-2xl font-light text-stone-700 dark:text-stone-300 mb-1">{usage.total_tokens.toLocaleString()}</div>
            <div className="text-sm text-stone-600/80 dark:text-stone-400/80 font-light">Tokens</div>
          </div>

          <div className="bg-gradient-to-br from-sage-50/80 to-sage-100/50 dark:from-stone-800/50 dark:to-stone-700/50 p-4 rounded-xl border border-sage-200/40 dark:border-stone-600/40 group hover:shadow-sm transition-all duration-300 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-4 h-4 text-sage-600 dark:text-sage-400" />
              <span className="text-xs text-sage-600/70 dark:text-sage-400/70 font-medium tracking-wide">INPUT</span>
            </div>
            <div className="text-2xl font-light text-sage-700 dark:text-sage-300 mb-1">{usage.prompt_tokens.toLocaleString()}</div>
            <div className="text-sm text-sage-600/80 dark:text-sage-400/80 font-light">Prompt</div>
          </div>

          <div className="bg-gradient-to-br from-lavender-50/80 to-lavender-100/50 dark:from-stone-800/50 dark:to-stone-700/50 p-4 rounded-xl border border-lavender-200/40 dark:border-stone-600/40 group hover:shadow-sm transition-all duration-300 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-2">
              <Zap className="w-4 h-4 text-lavender-600 dark:text-lavender-400" />
              <span className="text-xs text-lavender-600/70 dark:text-lavender-400/70 font-medium tracking-wide">OUTPUT</span>
            </div>
            <div className="text-2xl font-light text-lavender-700 dark:text-lavender-300 mb-1">{usage.response_tokens.toLocaleString()}</div>
            <div className="text-sm text-lavender-600/80 dark:text-lavender-400/80 font-light">Response</div>
          </div>

          <div className="bg-gradient-to-br from-peach-50/80 to-peach-100/50 dark:from-stone-800/50 dark:to-stone-700/50 p-4 rounded-xl border border-peach-200/40 dark:border-stone-600/40 group hover:shadow-sm transition-all duration-300 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-4 h-4 text-peach-600 dark:text-peach-400" />
              <span className="text-xs text-peach-600/70 dark:text-peach-400/70 font-medium tracking-wide">CALLS</span>
            </div>
            <div className="text-2xl font-light text-peach-700 dark:text-peach-300 mb-1">{usage.api_calls}</div>
            <div className="text-sm text-peach-600/80 dark:text-peach-400/80 font-light">API Requests</div>
          </div>
        </div>
      </div>
    </div>
  );
};