import React from 'react';
import { Brain, Trash2, Clock, Target, Lightbulb } from 'lucide-react';

interface DecisionLogProps {
  decisions: any[];
  onClear: () => void;
}

export const DecisionLog: React.FC<DecisionLogProps> = ({ decisions, onClear }) => {
  return (
    <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-sm border border-stone-200/60 overflow-hidden transition-all duration-300 hover:shadow-md hover:bg-white/80">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-stone-400 to-stone-500 dark:from-stone-500 dark:to-stone-600 rounded-xl flex items-center justify-center shadow-md">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-medium text-stone-800 dark:text-stone-200">AI Decision Log</h2>
              <p className="text-sm text-stone-600 dark:text-stone-400 font-light">Real-time reasoning & actions</p>
            </div>
          </div>

          <button
            onClick={onClear}
            className="px-4 py-2 text-xs bg-stone-100/80 dark:bg-stone-700/80 text-stone-600 dark:text-stone-400 rounded-lg hover:bg-stone-200/80 dark:hover:bg-stone-600/80 transition-all duration-200 flex items-center space-x-2 group backdrop-blur-sm"
          >
            <Trash2 className="w-3 h-3 group-hover:scale-110 transition-transform duration-200" />
            <span>Clear Log</span>
          </button>
        </div>

        <div className="bg-stone-50/80 dark:bg-stone-800/50 backdrop-blur-sm rounded-xl border border-stone-200/60 dark:border-stone-600/60 h-80 overflow-y-auto">
          {decisions.length === 0 ? (
            <div className="flex items-center justify-center h-full text-stone-500 dark:text-stone-400">
              <div className="text-center animate-in fade-in duration-500">
                <Lightbulb className="w-12 h-12 text-stone-400 dark:text-stone-500 mx-auto mb-4" />
                <p className="text-sm font-medium mb-2">No decisions yet</p>
                <p className="text-xs text-stone-400 dark:text-stone-500 font-light">AI reasoning will appear here as tasks run</p>
              </div>
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {decisions.map((decision, index) => (
                <div
                  key={index}
                  className="bg-white/80 dark:bg-stone-700/50 backdrop-blur-sm p-4 rounded-xl border-l-4 border-stone-400 dark:border-stone-500 shadow-sm hover:shadow-md transition-all duration-300 animate-in fade-in slide-in-from-bottom-2"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <Target className="w-4 h-4 text-stone-600 dark:text-stone-400" />
                      <span className="font-medium text-stone-600 dark:text-stone-400 text-sm tracking-wide">
                        {decision.action?.toUpperCase() || 'THINKING'}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1 text-xs text-stone-500 dark:text-stone-400">
                      <Clock className="w-3 h-3" />
                      <span>{new Date().toLocaleTimeString()}</span>
                    </div>
                  </div>
                  <p className="text-stone-700 dark:text-stone-300 text-sm mb-2 leading-relaxed font-light">
                    {decision.reason || 'Processing...'}
                  </p>
                  {decision.text && (
                    <p className="text-xs text-stone-500 dark:text-stone-400 font-mono bg-stone-100/80 dark:bg-stone-600/50 px-3 py-2 rounded-lg backdrop-blur-sm">
                      "{decision.text}"
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};