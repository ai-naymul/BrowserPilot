import { motion } from "framer-motion";
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  ScatterChart, 
  Scatter, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from "recharts";

interface ChartLine {
  dataKey: string;
  name: string;
  color?: string;
}

interface ChartWidgetProps {
  data: Array<{ [key: string]: any }>;
  lines?: ChartLine[];
  chartType?: 'line' | 'area' | 'pie' | 'scatter';
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  formatTooltip?: (value: any) => string;
  formatYAxis?: (value: any) => string;
  // Pie chart specific
  nameKey?: string;
  valueKey?: string;
}

const defaultColors = ["#7dd3fc", "#c4b5fd", "#f9a8d4", "#facc15"];

export const ChartWidget = ({
  data,
  lines = [],
  chartType = 'line',
  xAxisLabel,
  yAxisLabel,
  height = 300,
  showGrid = true,
  showLegend = true,
  formatTooltip,
  formatYAxis,
  nameKey = 'name',
  valueKey = 'value',
}: ChartWidgetProps) => {
  // Render pie chart
  const renderPieChart = () => (
    <PieChart>
      <Pie
        data={data}
        dataKey={valueKey}
        nameKey={nameKey}
        cx="50%"
        cy="50%"
        outerRadius={height / 3}
        animationDuration={1000}
        label={(entry) => entry[nameKey]}
      >
        {data.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={defaultColors[index % defaultColors.length]} />
        ))}
      </Pie>
      <Tooltip
        contentStyle={{
          backgroundColor: "hsl(var(--card))",
          border: "1px solid hsl(var(--border))",
          borderRadius: "0.5rem",
          fontSize: "0.875rem",
        }}
      />
      {showLegend && <Legend wrapperStyle={{ fontSize: "0.875rem" }} />}
    </PieChart>
  );

  // Render scatter chart
  const renderScatterChart = () => (
    <ScatterChart margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
      {showGrid && (
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
      )}
      <XAxis
        dataKey="x"
        stroke="hsl(var(--muted-foreground))"
        style={{ fontSize: "0.75rem" }}
        label={xAxisLabel ? { value: xAxisLabel, position: "insideBottom", offset: -5 } : undefined}
      />
      <YAxis
        dataKey="y"
        stroke="hsl(var(--muted-foreground))"
        style={{ fontSize: "0.75rem" }}
        tickFormatter={formatYAxis}
      />
      <Tooltip
        cursor={{ strokeDasharray: '3 3' }}
        contentStyle={{
          backgroundColor: "hsl(var(--card))",
          border: "1px solid hsl(var(--border))",
          borderRadius: "0.5rem",
          fontSize: "0.875rem",
        }}
      />
      {showLegend && <Legend wrapperStyle={{ fontSize: "0.875rem" }} />}
      {lines.map((line, idx) => (
        <Scatter
          key={line.dataKey}
          name={line.name}
          data={data}
          fill={line.color || defaultColors[idx % defaultColors.length]}
          animationDuration={1000}
        />
      ))}
    </ScatterChart>
  );

  // Render line or area chart
  const renderLineOrAreaChart = () => {
    const ChartComponent = chartType === 'area' ? AreaChart : LineChart;
    
    return (
      <ChartComponent data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        {showGrid && (
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
        )}
        <XAxis
          dataKey="x"
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "0.75rem" }}
          label={xAxisLabel ? { value: xAxisLabel, position: "insideBottom", offset: -5 } : undefined}
        />
        <YAxis
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "0.75rem" }}
          tickFormatter={formatYAxis}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "0.5rem",
            fontSize: "0.875rem",
          }}
          formatter={formatTooltip}
        />
        {showLegend && (
          <Legend
            wrapperStyle={{ fontSize: "0.875rem", paddingTop: "1rem" }}
            iconType={chartType === 'area' ? 'rect' : 'line'}
          />
        )}
        {lines.map((line, idx) => {
          const color = line.color || defaultColors[idx % defaultColors.length];
          
          if (chartType === 'area') {
            return (
              <Area
                key={line.dataKey}
                type="monotone"
                dataKey={line.dataKey}
                name={line.name}
                stroke={color}
                fill={color}
                fillOpacity={0.3}
                strokeWidth={2}
                animationDuration={1000}
              />
            );
          }
          
          return (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name}
              stroke={color}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              animationDuration={1000}
            />
          );
        })}
      </ChartComponent>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-border bg-card p-6"
    >
      {(xAxisLabel || yAxisLabel) && (
        <div className="mb-4">
          {yAxisLabel && (
            <h4 className="text-sm font-medium text-muted-foreground">{yAxisLabel}</h4>
          )}
        </div>
      )}

      <ResponsiveContainer width="100%" height={height}>
        {chartType === 'pie' ? renderPieChart() : 
         chartType === 'scatter' ? renderScatterChart() : 
         renderLineOrAreaChart()}
      </ResponsiveContainer>
    </motion.div>
  );
};
