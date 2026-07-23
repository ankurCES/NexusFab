import type { LineOEE } from '../types/api';
import OEEGauge from './OEEGauge';

function statusFromOee(oee: number, failures: number): { label: string; color: string } {
  if (failures > 3) return { label: 'DOWN', color: 'bg-red-500' };
  if (oee < 0.5) return { label: 'DEGRADED', color: 'bg-yellow-500' };
  return { label: 'RUNNING', color: 'bg-green-500' };
}

interface Props {
  line: LineOEE;
}

export default function LineStatusCard({ line }: Props) {
  const status = statusFromOee(line.oee, line.failures);

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="font-semibold text-sm text-white">{line.name}</span>
        <span className={`${status.color} text-xs font-bold px-2 py-0.5 rounded text-white`}>
          {status.label}
        </span>
      </div>
      <div className="flex justify-center mb-3">
        <OEEGauge value={line.oee} label="OEE" size={100} />
      </div>
      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <div>
          <div className="text-slate-400">Avail</div>
          <div className="text-white font-medium">{Math.round(line.availability * 100)}%</div>
        </div>
        <div>
          <div className="text-slate-400">Perf</div>
          <div className="text-white font-medium">{Math.round(line.performance * 100)}%</div>
        </div>
        <div>
          <div className="text-slate-400">Qual</div>
          <div className="text-white font-medium">{Math.round(line.quality * 100)}%</div>
        </div>
      </div>
      <div className="mt-2 text-xs text-slate-500 text-center">
        {line.units_produced.toLocaleString()} units · {Math.round(line.downtime_minutes)}min downtime
      </div>
    </div>
  );
}
