import type { ScheduleRun } from '../types/api';

const LINE_COLORS = [
  '#3b82f6', '#8b5cf6', '#06b6d4', '#f59e0b', '#10b981',
  '#ef4444', '#ec4899', '#6366f1', '#14b8a6', '#f97316',
];

interface Props {
  runs: ScheduleRun[];
  horizonHours: number;
}

export default function GanttChart({ runs, horizonHours }: Props) {
  if (!runs.length) return <div className="text-slate-500 text-sm p-4">No schedule data</div>;

  const lines = [...new Set(runs.map((r) => r.line))].sort();
  const colorMap = Object.fromEntries(lines.map((l, i) => [l, LINE_COLORS[i % LINE_COLORS.length]]));

  const timeMin = Math.min(...runs.map((r) => new Date(r.start).getTime()));
  const timeMax = timeMin + horizonHours * 3600 * 1000;
  const span = timeMax - timeMin;

  const toLeft = (iso: string) => ((new Date(iso).getTime() - timeMin) / span) * 100;
  const toWidth = (start: string, end: string) =>
    ((new Date(end).getTime() - new Date(start).getTime()) / span) * 100;

  return (
    <div className="bg-slate-800 rounded-lg p-4 overflow-x-auto">
      <h3 className="text-sm font-semibold text-white mb-3">Production Schedule</h3>
      <div className="min-w-[600px]">
        {lines.map((line) => (
          <div key={line} className="flex items-center mb-2">
            <div className="w-28 text-xs text-slate-400 shrink-0 truncate pr-2">{line}</div>
            <div className="flex-1 relative h-7 bg-slate-900 rounded">
              {runs
                .filter((r) => r.line === line)
                .map((r) => {
                  const left = toLeft(r.start);
                  const width = toWidth(r.start, r.end);
                  return (
                    <div
                      key={r.order_id}
                      className="absolute top-0.5 bottom-0.5 rounded text-[10px] text-white flex items-center px-1 overflow-hidden cursor-default"
                      style={{
                        left: `${left}%`,
                        width: `${Math.max(width, 0.5)}%`,
                        backgroundColor: colorMap[line],
                      }}
                      title={`${r.product} (${r.quantity} units)\n${r.start} → ${r.end}`}
                    >
                      {width > 5 ? r.product : ''}
                    </div>
                  );
                })}
            </div>
          </div>
        ))}
        <div className="flex mt-2 ml-28">
          <div className="text-[10px] text-slate-500">
            {new Date(timeMin).toLocaleDateString()}
          </div>
          <div className="flex-1" />
          <div className="text-[10px] text-slate-500">
            +{horizonHours}h
          </div>
        </div>
      </div>
    </div>
  );
}
