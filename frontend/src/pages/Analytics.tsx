import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { KpiTrending } from '../types/api';

const PLANTS = ['PLT-001', 'PLT-002', 'PLT-003', 'PLT-004', 'PLT-005'];
const METRICS = ['oee', 'otif', 'waste_pct', 'energy_kwh', 'energy_cost', 'failures'] as const;
type Metric = typeof METRICS[number];

const METRIC_LABELS: Record<Metric, string> = {
  oee: 'OEE',
  otif: 'OTIF',
  waste_pct: 'Waste %',
  energy_kwh: 'Energy (kWh)',
  energy_cost: 'Energy Cost ($)',
  failures: 'Failures',
};

export default function Analytics() {
  const [data, setData] = useState<KpiTrending | null>(null);
  const [plant, setPlant] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [metric, setMetric] = useState<Metric>('oee');

  useEffect(() => {
    setLoading(true);
    api.kpiTrending(plant || undefined, 8)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [plant]);

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Analytics</h1>
          <p className="text-sm text-slate-400">KPI trending across periods</p>
        </div>
        <select
          value={plant}
          onChange={(e) => setPlant(e.target.value)}
          className="bg-slate-800 text-white rounded px-3 py-2 text-sm border border-slate-700"
        >
          <option value="">Network-wide</option>
          {PLANTS.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </header>

      {loading ? (
        <div className="text-slate-400 animate-pulse">Loading KPI data...</div>
      ) : data ? (
        <>
          {/* Metric selector */}
          <div className="flex gap-2 mb-6 flex-wrap">
            {METRICS.map((m) => (
              <button
                key={m}
                onClick={() => setMetric(m)}
                className={`px-3 py-1.5 rounded text-xs ${metric === m ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
              >
                {METRIC_LABELS[m]}
              </button>
            ))}
          </div>

          {/* Bar chart */}
          <section className="bg-slate-800 rounded-lg p-6 mb-6">
            <h2 className="text-sm font-semibold text-slate-300 mb-4">{METRIC_LABELS[metric]} by Period</h2>
            <BarChart data={data.trending} metric={metric} />
          </section>

          {/* Summary table */}
          <section className="bg-slate-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-900 text-slate-400 text-xs uppercase">
                <tr>
                  <th className="px-4 py-2 text-left">Period</th>
                  <th className="px-4 py-2 text-right">OEE</th>
                  <th className="px-4 py-2 text-right">OTIF</th>
                  <th className="px-4 py-2 text-right">Waste</th>
                  <th className="px-4 py-2 text-right">Units</th>
                  <th className="px-4 py-2 text-right">Failures</th>
                  <th className="px-4 py-2 text-right">Energy kWh</th>
                  <th className="px-4 py-2 text-right">Energy $</th>
                  <th className="px-4 py-2 text-right">kWh/ton</th>
                </tr>
              </thead>
              <tbody className="text-slate-300">
                {data.trending.map((t) => (
                  <tr key={t.period} className="border-t border-slate-700">
                    <td className="px-4 py-2">Week {t.period}</td>
                    <td className="px-4 py-2 text-right">{(t.oee * 100).toFixed(1)}%</td>
                    <td className="px-4 py-2 text-right">{(t.otif * 100).toFixed(1)}%</td>
                    <td className="px-4 py-2 text-right">{(t.waste_pct * 100).toFixed(1)}%</td>
                    <td className="px-4 py-2 text-right">{t.total_units.toLocaleString()}</td>
                    <td className="px-4 py-2 text-right">{t.failures}</td>
                    <td className="px-4 py-2 text-right">{t.energy_kwh.toLocaleString()}</td>
                    <td className="px-4 py-2 text-right">${t.energy_cost.toLocaleString()}</td>
                    <td className="px-4 py-2 text-right">{t.kwh_per_ton.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      ) : null}
    </div>
  );
}

function BarChart({ data, metric }: { data: KpiTrending['trending']; metric: Metric }) {
  const values = data.map((d) => d[metric] as number);
  const max = Math.max(...values, 0.001);
  const isPct = metric === 'oee' || metric === 'otif' || metric === 'waste_pct';

  return (
    <div className="flex items-end gap-2 h-48">
      {data.map((d, i) => {
        const val = values[i];
        const height = (val / max) * 100;
        const color = metric === 'failures'
          ? 'bg-red-500'
          : metric === 'waste_pct'
          ? 'bg-yellow-500'
          : 'bg-blue-500';

        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <span className="text-xs text-slate-400">
              {isPct ? `${(val * 100).toFixed(1)}%` : val.toLocaleString()}
            </span>
            <div className="w-full flex items-end" style={{ height: '160px' }}>
              <div
                className={`w-full ${color} rounded-t transition-all`}
                style={{ height: `${Math.max(height, 2)}%` }}
              />
            </div>
            <span className="text-xs text-slate-500">W{d.period}</span>
          </div>
        );
      })}
    </div>
  );
}
