import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import type { PlantOEE, ScheduleResponse } from '../types/api';
import OEEGauge from '../components/OEEGauge';
import LineStatusCard from '../components/LineStatusCard';
import GanttChart from '../components/GanttChart';

export default function PlantDetail() {
  const { plantId } = useParams<{ plantId: string }>();
  const [oee, setOee] = useState<PlantOEE | null>(null);
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!plantId) return;
    setLoading(true);
    Promise.all([
      api.plantOee(plantId, 168),
      api.schedule(plantId, 20),
    ])
      .then(([o, s]) => { setOee(o); setSchedule(s); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [plantId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-400 animate-pulse">Loading plant data...</div>
      </div>
    );
  }

  if (error || !oee) {
    return (
      <div className="p-6">
        <Link to="/" className="text-blue-400 text-sm hover:underline">← Back</Link>
        <div className="text-red-400 mt-4">{error || 'Plant not found'}</div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      <Link to="/" className="text-blue-400 text-sm hover:underline">← Dashboard</Link>

      <header className="flex items-center justify-between mt-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">{oee.plant_name}</h1>
          <p className="text-sm text-slate-400">
            {oee.lines.length} lines · {oee.total_units.toLocaleString()} units · {oee.total_failures} failures
          </p>
        </div>
        <OEEGauge value={oee.plant_oee} label="Plant OEE" size={140} />
      </header>

      <section className="mb-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
          Line Status
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {oee.lines.map((line) => (
            <LineStatusCard key={line.name} line={line} />
          ))}
        </div>
      </section>

      {schedule && (
        <section>
          <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
            Production Schedule
          </h2>
          <GanttChart runs={schedule.schedule} horizonHours={schedule.horizon_hours} />
          <div className="flex gap-4 mt-2 text-xs text-slate-500">
            <span>{schedule.total_runs} runs</span>
            <span>Changeover: {schedule.total_changeover_minutes}min (saved {schedule.improvement_pct}%)</span>
            {schedule.unscheduled_orders.length > 0 && (
              <span className="text-yellow-500">
                {schedule.unscheduled_orders.length} unscheduled
              </span>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
