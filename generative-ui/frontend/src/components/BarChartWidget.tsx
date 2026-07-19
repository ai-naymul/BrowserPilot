import { motion } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface ChartBar {
  dataKey: string;
  name: string;
  color?: string;
}

interface BarChartWidgetProps {
  data: Array<{ [key: string]: any }>;
  bars: ChartBar[];
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number;
  horizontal?: boolean;
  showValues?: boolean;
  formatValue?: (value: any) => string;
}

const defaultColors = ["#7dd3fc", "#c4b5fd", "#f9a8d4", "#facc15"];

export const BarChartWidget = ({
  data,
  bars,
  xAxisLabel,
  yAxisLabel,
  height = 300,
  horizontal = false,
  showValues = false,
  formatValue,
}: BarChartWidgetProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-border bg-card p-6"
    >
      {yAxisLabel && (
        <h4 className="mb-4 text-sm font-medium text-muted-foreground">{yAxisLabel}</h4>
      )}

      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
          {horizontal ? (
            <>
              <XAxis type="number" stroke="hsl(var(--muted-foreground))" style={{ fontSize: "0.75rem" }} />
              <YAxis type="category" dataKey="label" stroke="hsl(var(--muted-foreground))" style={{ fontSize: "0.75rem" }} />
            </>
          ) : (
            <>
              <XAxis dataKey="label" stroke="hsl(var(--muted-foreground))" style={{ fontSize: "0.75rem" }} />
              <YAxis stroke="hsl(var(--muted-foreground))" style={{ fontSize: "0.75rem" }} tickFormatter={formatValue} />
            </>
          )}
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "0.5rem",
              fontSize: "0.875rem",
            }}
            {...(formatValue && typeof formatValue === 'function' ? { formatter: formatValue } : {})}
          />
          <Legend wrapperStyle={{ fontSize: "0.875rem", paddingTop: "1rem" }} />
          {bars.map((bar, idx) => (
            <Bar
              key={bar.dataKey}
              dataKey={bar.dataKey}
              name={bar.name}
              fill={bar.color || defaultColors[idx % defaultColors.length]}
              radius={[4, 4, 0, 0]}
              animationDuration={1000}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
};
