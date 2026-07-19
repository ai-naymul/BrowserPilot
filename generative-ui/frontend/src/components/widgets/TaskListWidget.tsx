import { useState } from 'react';
import { EntityAttribute } from '@/types/entity';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface TaskListWidgetProps {
  attribute: EntityAttribute;
  onChange?: (newValue: any) => void;
  compact?: boolean;
}

interface Task {
  task: string;
  done: boolean;
  priority?: 'high' | 'medium' | 'low';
  category?: string;
  phase?: string;
  due_date?: string;
}

export const TaskListWidget = ({ attribute, onChange, compact }: TaskListWidgetProps) => {
  const tasks = (attribute.value || []) as Task[];
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const handleToggleTask = (index: number) => {
    const updatedTasks = [...tasks];
    updatedTasks[index].done = !updatedTasks[index].done;
    onChange?.(updatedTasks);
  };

  // Group tasks by category or phase
  const groupBy = tasks[0]?.category ? 'category' : tasks[0]?.phase ? 'phase' : null;
  
  const grouped: Record<string, Task[]> = {};
  if (groupBy) {
    tasks.forEach(task => {
      const key = (task as any)[groupBy] || 'Other';
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(task);
    });
  }

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const completedCount = tasks.filter(t => t.done).length;
  const totalCount = tasks.length;
  const completionPercentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  if (compact) {
    return (
      <div>
        <label className="text-xs font-medium text-muted-foreground capitalize">
          {attribute.name.replace(/_/g, ' ')}
        </label>
        <div className="text-sm font-medium mt-1">
          {completedCount} / {totalCount} completed ({completionPercentage}%)
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium capitalize">
          {attribute.name.replace(/_/g, ' ')}
        </label>
        <div className="flex items-center gap-2">
          <div className="text-xs text-muted-foreground">
            {completedCount}/{totalCount} done
          </div>
          <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-green-500 transition-all duration-300"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
        </div>
      </div>

      <div className="space-y-1 max-h-96 overflow-y-auto">
        {groupBy ? (
          Object.entries(grouped).map(([category, categoryTasks]) => (
            <div key={category} className="border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleCategory(category)}
                className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-2">
                  {expandedCategories.has(category) ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronUp className="h-4 w-4" />
                  )}
                  <span className="font-medium text-sm">{category}</span>
                  <span className="text-xs text-muted-foreground">
                    ({categoryTasks.filter(t => t.done).length}/{categoryTasks.length})
                  </span>
                </div>
              </button>
              
              {expandedCategories.has(category) && (
                <div className="p-2 space-y-1">
                  {categoryTasks.map((task, idx) => {
                    const globalIdx = tasks.indexOf(task);
                    return (
                      <div
                        key={idx}
                        className="flex items-start gap-3 p-2 rounded hover:bg-gray-50 transition-colors"
                      >
                        <Checkbox
                          checked={task.done}
                          onCheckedChange={() => handleToggleTask(globalIdx)}
                          className="mt-0.5"
                        />
                        <div className="flex-1 min-w-0">
                          <div className={`text-sm ${task.done ? 'line-through text-muted-foreground' : ''}`}>
                            {task.task}
                          </div>
                          {task.priority && (
                            <Badge variant="outline" className={`text-xs mt-1 ${getPriorityColor(task.priority)}`}>
                              {task.priority}
                            </Badge>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))
        ) : (
          tasks.map((task, idx) => (
            <div
              key={idx}
              className="flex items-start gap-3 p-3 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Checkbox
                checked={task.done}
                onCheckedChange={() => handleToggleTask(idx)}
                className="mt-0.5"
              />
              <div className="flex-1 min-w-0">
                <div className={`text-sm ${task.done ? 'line-through text-muted-foreground' : ''}`}>
                  {task.task}
                </div>
                {task.priority && (
                  <Badge variant="outline" className={`text-xs mt-1 ${getPriorityColor(task.priority)}`}>
                    {task.priority}
                  </Badge>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
