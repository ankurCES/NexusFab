import { PieChart, Pie, Cell } from 'recharts';

function oeeColor(val: number): string {
  if (val >= 0.75) return '#22c55e';
  if (val >= 0.60) return '#eab308';
  return '#ef4444';
}

interface Props {
  value: number;
  label: string;
  size?: number;
}

export default function OEEGauge({ value, label, size = 120 }: Props) {
  const pct = Math.round(value * 100);
  const color = oeeColor(value);
  const data = [
    { value: pct },
    { value: 100 - pct },
  ];

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size * 0.6 }}>
        <PieChart width={size} height={size * 0.6}>
          <Pie
            data={data}
            cx={size / 2}
            cy={size * 0.55}
            startAngle={180}
            endAngle={0}
            innerRadius={size * 0.3}
            outerRadius={size * 0.45}
            dataKey="value"
            stroke="none"
          >
            <Cell fill={color} />
            <Cell fill="#1e293b" />
          </Pie>
        </PieChart>
        <div
          className="absolute inset-0 flex items-end justify-center pb-0.5"
          style={{ color }}
        >
          <span className="text-lg font-bold">{pct}%</span>
        </div>
      </div>
      <span className="text-xs text-slate-400 mt-1">{label}</span>
    </div>
  );
}
