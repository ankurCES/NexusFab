import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { EnergyOptimization, EnergyReport } from '../types/api';

const PLANTS = ['PLT-001', 'PLT-002', 'PLT-003', 'PLT-004', 'PLT-005'];

export default function Energy() {
  const [report, setReport] = useState<EnergyReport | null>(null);
  const [optimization, setOptimization] = useState<EnergyOptimization | null>(null);
  const [plant, setPlant] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.energy(plant || undefined),
      api.energyOptimize(plant || undefined),
    ])
      .then(([r, o]) => { setReport(r); setOptimization(o); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [plant]);

  if (error) return <div className="p-6 text-red-400">{error}</div>;

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Energy Optimization</h1>
          <p className="text-sm text-slate-400">Off-peak scheduling &amp; consumption tracking</p>
        </div>
        <select
          value={plant}
          onChange={(e) => setPlant(e.target.value)}
          className="bg-slate-800 text-white rounded px-3 py-2 text-sm border border-slate-700"
        >
          <option value="">All Plants</option>
          {PLANTS.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </header>

      {loading ? (
        <div className="text-slate-400 animate-pulse">Loading energy data...</div>
      ) : (
        <>
          {/* Summary cards */}
          {report && optimization && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <Card label="Total kWh" value={`${report.total_kwh.toLocaleString()}`} />
              <Card label="Total Cost" value={`$${report.total_cost.toLocaleString()}`} />
              <Card label="CO2 (kg)" value={`${report.total_co2_kg.toLocaleString()}`} />
              <Card label="kWh/ton" value={report.kwh_per_ton.toFixed(1)} />
            </div>
          )}

          {/* Off-peak optimization */}
          {optimization && (
            <section className="mb-6">
              <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
                Off-Peak Scheduling Savings
              </h2>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <Card label="Baseline Cost" value={`$${optimization.baseline_cost.toLocaleString()}`} />
                <Card
                  label="Optimized Cost"
                  value={`$${optimization.optimized_cost.toLocaleString()}`}
                  highlight
                />
                <Card
                  label="Savings"
                  value={`$${optimization.total_savings.toLocaleString()} (${optimization.savings_pct.toFixed(1)}%)`}
                  highlight
                />
              </div>

              {/* Tariff schedule */}
              <div className="bg-slate-800 rounded-lg p-4 mb-4">
                <h3 className="text-xs font-semibold text-slate-400 mb-2 uppercase">Tariff Periods</h3>
                <div className="flex gap-2">
                  {optimization.tariff_schedule.map((t) => (
                    <div
                      key={`${t.start}-${t.end}`}
                      className={`flex-1 rounded p-2 text-center text-xs ${
                        t.period === 'off-peak'
                          ? 'bg-green-900/40 text-green-300'
                          : t.period === 'shoulder'
                          ? 'bg-yellow-900/40 text-yellow-300'
                          : 'bg-red-900/40 text-red-300'
                      }`}
                    >
                      <div className="font-semibold">{t.period}</div>
                      <div>{t.start}:00 - {t.end}:00</div>
                      <div>{t.rate_multiplier}x</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Shifted equipment */}
              {optimization.slots.length > 0 && (
                <div className="bg-slate-800 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-900 text-slate-400 text-xs uppercase">
                      <tr>
                        <th className="px-4 py-2 text-left">Equipment</th>
                        <th className="px-4 py-2 text-left">Line</th>
                        <th className="px-4 py-2 text-right">kWh</th>
                        <th className="px-4 py-2 text-right">Baseline</th>
                        <th className="px-4 py-2 text-right">Optimized</th>
                        <th className="px-4 py-2 text-right">Savings</th>
                      </tr>
                    </thead>
                    <tbody className="text-slate-300">
                      {optimization.slots.map((s, i) => (
                        <tr key={i} className="border-t border-slate-700">
                          <td className="px-4 py-2 font-mono text-xs">{s.equipment_type}</td>
                          <td className="px-4 py-2">{s.line}</td>
                          <td className="px-4 py-2 text-right">{s.kwh.toLocaleString()}</td>
                          <td className="px-4 py-2 text-right">${s.baseline_cost.toFixed(2)}</td>
                          <td className="px-4 py-2 text-right text-green-400">${s.optimized_cost.toFixed(2)}</td>
                          <td className="px-4 py-2 text-right text-green-400">${s.savings.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {/* kWh by line */}
          {optimization && Object.keys(optimization.kwh_by_line).length > 0 && (
            <section className="mb-6">
              <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
                kWh by Line
              </h2>
              <div className="bg-slate-800 rounded-lg p-4">
                {Object.entries(optimization.kwh_by_line)
                  .sort(([, a], [, b]) => b - a)
                  .map(([line, kwh]) => {
                    const max = Math.max(...Object.values(optimization.kwh_by_line));
                    return (
                      <div key={line} className="flex items-center gap-3 mb-2">
                        <span className="text-xs text-slate-400 w-24 shrink-0">{line}</span>
                        <div className="flex-1 h-5 bg-slate-700 rounded overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded"
                            style={{ width: `${(kwh / max) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-300 w-24 text-right">
                          {kwh.toLocaleString()} kWh
                        </span>
                      </div>
                    );
                  })}
              </div>
            </section>
          )}

          {/* Savings opportunities */}
          {report && report.savings_opportunities.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
                Savings Opportunities
              </h2>
              <div className="bg-slate-800 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-900 text-slate-400 text-xs uppercase">
                    <tr>
                      <th className="px-4 py-2 text-left">Description</th>
                      <th className="px-4 py-2 text-left">Priority</th>
                      <th className="px-4 py-2 text-right">Annual Savings</th>
                      <th className="px-4 py-2 text-right">Payback</th>
                    </tr>
                  </thead>
                  <tbody className="text-slate-300">
                    {report.savings_opportunities.map((s, i) => (
                      <tr key={i} className="border-t border-slate-700">
                        <td className="px-4 py-2">{s.description}</td>
                        <td className="px-4 py-2">
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            s.priority === 'high' ? 'bg-red-900/50 text-red-300' : 'bg-yellow-900/50 text-yellow-300'
                          }`}>{s.priority}</span>
                        </td>
                        <td className="px-4 py-2 text-right text-green-400">${s.annual_cost_savings.toLocaleString()}</td>
                        <td className="px-4 py-2 text-right">{s.payback_months.toFixed(0)} mo</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function Card({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="text-xs text-slate-400 uppercase mb-1">{label}</div>
      <div className={`text-lg font-bold ${highlight ? 'text-green-400' : 'text-white'}`}>{value}</div>
    </div>
  );
}
