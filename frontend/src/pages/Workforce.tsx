import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { WorkforceReport, EnergyReport } from '../types/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const PLANTS = ['PLT-001', 'PLT-002', 'PLT-003', 'PLT-004', 'PLT-005'];
const SHIFT_COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4'];
const ENERGY_COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#22c55e', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#6366f1'];

export default function Workforce() {
  const [plantId, setPlantId] = useState(PLANTS[0]);
  const [wf, setWf] = useState<WorkforceReport | null>(null);
  const [energy, setEnergy] = useState<EnergyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    Promise.all([api.workforce(plantId), api.energy(plantId)])
      .then(([w, e]) => { setWf(w); setEnergy(e); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [plantId]);

  if (loading) return <div className="flex items-center justify-center min-h-screen text-slate-400 animate-pulse">Loading...</div>;
  if (error) return <div className="p-6 text-red-400">{error}</div>;
  if (!wf || !energy) return null;

  const shiftData = wf.shift_coverage.map((s) => ({
    name: `Shift ${s.shift}`,
    coverage: Math.round(s.coverage_pct * 100),
    fill: SHIFT_COLORS[(s.shift - 1) % SHIFT_COLORS.length],
  }));

  const energyByType = Object.entries(energy.by_equipment_type).map(([type, kwh], i) => ({
    name: type, value: Math.round(kwh), fill: ENERGY_COLORS[i % ENERGY_COLORS.length],
  }));

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Workforce & Energy</h1>
        <select
          value={plantId}
          onChange={(e) => setPlantId(e.target.value)}
          className="bg-slate-800 text-white text-sm rounded px-3 py-1.5 border border-slate-700"
        >
          {PLANTS.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 mb-6">
        <KPI label="Operators" value={wf.total_operators} />
        <KPI label="Avg Skill" value={`${Math.round(wf.avg_skill_score * 100)}%`} />
        <KPI label="Training Gaps" value={wf.training_gaps_count} warn={wf.training_gaps_count > 0} />
        <KPI label="Energy (kWh)" value={energy.total_kwh.toLocaleString()} />
        <KPI label="Energy Cost" value={`$${energy.total_cost.toLocaleString()}`} />
        <KPI label="CO₂ (kg)" value={energy.total_co2_kg.toLocaleString()} />
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Shift coverage */}
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Shift Coverage</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={shiftData}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis domain={[0, 150]} tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
              <Bar dataKey="coverage" name="Coverage %">
                {shiftData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-2 space-y-1">
            {wf.shift_coverage.map((s) => (
              <div key={s.shift} className="flex justify-between text-xs text-slate-400">
                <span>Shift {s.shift}: {s.available}/{s.required} staff</span>
                {s.gaps.length > 0 && <span className="text-yellow-400">Gaps: {s.gaps.join(', ')}</span>}
              </div>
            ))}
          </div>
        </div>

        {/* Energy by equipment */}
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Energy by Equipment Type</h3>
          <div className="flex items-center gap-4">
            <ResponsiveContainer width="50%" height={200}>
              <PieChart>
                <Pie data={energyByType} dataKey="value" cx="50%" cy="50%" outerRadius={80} stroke="none">
                  {energyByType.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-1 text-xs">
              {energyByType.map((d) => (
                <div key={d.name} className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: d.fill }} />
                  <span className="text-slate-400">{d.name}</span>
                  <span className="text-white font-medium ml-auto">{d.value.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Training gaps */}
      {wf.training_gaps.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-yellow-400 mb-3">Training Gaps ({wf.training_gaps_count})</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 text-left text-xs">
                  <th className="pb-2">Operator</th>
                  <th className="pb-2">Skill</th>
                  <th className="pb-2">Current</th>
                  <th className="pb-2">Required</th>
                  <th className="pb-2">Priority</th>
                </tr>
              </thead>
              <tbody>
                {wf.training_gaps.slice(0, 15).map((g, i) => (
                  <tr key={i} className="border-t border-slate-700 text-slate-300">
                    <td className="py-1.5">{g.name}</td>
                    <td>{g.skill}</td>
                    <td>{g.current.toFixed(1)}</td>
                    <td>{g.required.toFixed(1)}</td>
                    <td>
                      <span className={`text-xs font-bold ${g.priority === 'critical' ? 'text-red-400' : g.priority === 'high' ? 'text-yellow-400' : 'text-slate-400'}`}>
                        {g.priority}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Savings opportunities */}
      {energy.savings_opportunities.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-green-400 mb-3">Energy Savings Opportunities</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {energy.savings_opportunities.map((s, i) => (
              <div key={i} className="bg-slate-900 rounded p-3">
                <div className="text-white text-sm font-medium">{s.description}</div>
                <div className="text-xs text-slate-400 mt-1">{s.equipment_type}</div>
                <div className="flex justify-between mt-2 text-xs">
                  <span className="text-green-400">${s.annual_cost_savings.toLocaleString()}/yr</span>
                  <span className="text-slate-500">{s.payback_months}mo payback</span>
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {s.annual_kwh_savings.toLocaleString()} kWh · {s.annual_co2_savings_kg.toLocaleString()} kg CO₂
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function KPI({ label, value, warn }: { label: string; value: string | number; warn?: boolean }) {
  return (
    <div className="bg-slate-800 rounded-lg p-3">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`text-lg font-bold mt-1 ${warn ? 'text-yellow-400' : 'text-white'}`}>{value}</div>
    </div>
  );
}
