import { TrendingUp, TrendingDown, Minus, LucideIcon } from 'lucide-react';

interface MetricBadgeWidgetProps {
  label: string;
  value: number | string;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple' | 'gray';
  icon?: LucideIcon;
  size?: 'sm' | 'md' | 'lg';
}

export const MetricBadgeWidget = ({
  label,
  value,
  unit,
  trend,
  color = 'blue',
  icon: Icon,
  size = 'md'
}: MetricBadgeWidgetProps) => {
  
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    gray: 'bg-gray-50 text-gray-700 border-gray-200',
  };
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  };
  
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  
  return (
    <div className={`
      inline-flex items-center gap-2 rounded-lg border
      ${colorClasses[color]}
      ${sizeClasses[size]}
      font-medium transition-all hover:scale-105
    `}>
      {Icon && <Icon className="h-4 w-4" />}
      <div className="flex flex-col">
        <span className="text-xs opacity-80 uppercase tracking-wide">{label}</span>
        <div className="flex items-center gap-1">
          <span className="font-bold">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </span>
          {unit && <span className="text-xs opacity-70">{unit}</span>}
          {trend && <TrendIcon className="h-3 w-3" />}
        </div>
      </div>
    </div>
  );
};
