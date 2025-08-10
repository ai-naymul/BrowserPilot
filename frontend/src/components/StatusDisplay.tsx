import React, { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, Info, X, Sparkles } from 'lucide-react';

interface StatusDisplayProps {
  status: {
    message: string;
    type: 'success' | 'error' | 'info';
  };
  onDismiss: () => void;
}

export const StatusDisplay: React.FC<StatusDisplayProps> = ({ status, onDismiss }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    setIsVisible(true);
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onDismiss, 300);
    }, 6000);

    return () => clearTimeout(timer);
  }, [status, onDismiss]);

  const getStatusConfig = () => {
    switch (status.type) {
      case 'success':
        return {
          icon: CheckCircle,
          bgColor: 'bg-emerald-50/90 border-emerald-200/60',
          textColor: 'text-emerald-800',
          iconColor: 'text-emerald-600',
          accentColor: 'bg-emerald-500'
        };
      case 'error':
        return {
          icon: AlertCircle,
          bgColor: 'bg-rose-50/90 border-rose-200/60',
          textColor: 'text-rose-800',
          iconColor: 'text-rose-600',
          accentColor: 'bg-rose-500'
        };
      default:
        return {
          icon: Info,
          bgColor: 'bg-blue-50/90 border-blue-200/60',
          textColor: 'text-blue-800',
          iconColor: 'text-blue-600',
          accentColor: 'bg-blue-500'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div 
      className={`
        ${config.bgColor} border rounded-xl p-4 shadow-sm backdrop-blur-sm transition-all duration-500 relative overflow-hidden
        ${isVisible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 -translate-y-2 scale-95'}
      `}
    >
      {/* Animated accent bar */}
      <div className={`absolute top-0 left-0 h-1 ${config.accentColor} animate-pulse`} style={{ width: '100%' }}></div>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Icon className={`w-6 h-6 ${config.iconColor}`} />
            {status.type === 'info' && (
              <Sparkles className="w-3 h-3 text-blue-400 absolute -top-1 -right-1 animate-pulse" />
            )}
          </div>
          <div>
            <span className={`text-sm font-medium ${config.textColor} leading-relaxed`}>
              {status.message}
            </span>
          </div>
        </div>
        <button
          onClick={() => {
            setIsVisible(false);
            setTimeout(onDismiss, 300);
          }}
          className={`${config.textColor} hover:opacity-70 transition-all duration-200 p-1 rounded-lg hover:bg-white/20`}
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};