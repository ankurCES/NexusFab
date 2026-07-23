import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { ScenarioResult, ScenarioSummary } from '../types/api';

const PLANTS = ['PLT-001', 'PLT-002', 'PLT-003', 'PLT-004', 'PLT-005'];

export default function Scenarios() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<'seeded' | 'custom'>('seeded');

  // Custom scenario state
  const [customPlant, setCustomPlant] = useState('PLT-001');
  const [customDemand, setCustomDemand] = useState(1.0);
  const [customCip, setCustomCip] = useState(1.0);
  const [customEnergy, setCustomEnergy] = useState(1.0);
  const [customWorkforce, setCustomWorkforce] = useState(1.0);

  useEffect(() => {
    api.scenarios().then(setScenarios);
  }, []);

  const runSeeded = (id: string) => {
    setLoading(true);
    setResult(null);
    api.runScenario(id)
      .then(setResult)
      .finally(() => setLoading(false));
  };

  const runCustom = () => {
    setLoading(true);
    setResult(null);
    api.runCustomScenario({
      name: 'Custom What-If',
      plant_id: customPlant,
      demand_multiplier: customDemand,
      cip_duration_multiplier: customCip,
      energy_rate_multiplier: customEnergy,
      workforce_availability: customWorkforce,
    })
      .then(setResult)
      .finally(() => setLoading(false));
  };

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-1">Scenario Builder</h1>
      <p className="text-sm text-slate-400 mb-6">Run what-if simulations</p>

      {/* Tab toggle */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setTab('seeded')}
          className={`px-4 py-2 rounded text-sm ${tab === 'seeded' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}
        >
          Seeded Scenarios (SIM-001 to SIM-010)
        </button>
        <button
          onClick={() => setTab('custom')}
          className={`px-4 py-2 rounded text-sm ${tab === 'custom' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}
        >
          Custom What-If
        </button>
      </div>

      {tab === 'seeded' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
          {scenarios.map((s) => (
            <button
              key={s.id}
              onClick={() => runSeeded(s.id)}
              disabled={loading}
              className="bg-slate-800 hover:bg-slate-700 rounded-lg p-4 text-left transition-colors disabled:opacity-50"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono text-blue-400">{s.id}</span>
                <span className="text-xs text-slate-500">{s.plant_id}</span>
              </div>
              <div className="text-sm font-semibold text-white">{s.name}</div>
              <div className="text-xs text-slate-400 mt-1">{s.description}</div>
            </button>
          ))}
        </div>
      ) : (
        <div className="bg-slate-800 rounded-lg p-6 mb-6">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Plant</label>
              <select
                value={customPlant}
                onChange={(e) => setCustomPlant(e.target.value)}
                className="w-full bg-slate-700 text-white rounded px-3 py-2 text-sm"
              >
                {PLANTS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <Slider label="Demand Multiplier" value={customDemand} onChange={setCustomDemand} min={0.5} max={5} step={0.1} />
            <Slider label="CIP Duration Mult" value={customCip} onChange={setCustomCip} min={0.5} max={3} step={0.1} />
            <Slider label="Energy Rate Mult" value={customEnergy} onChange={setCustomEnergy} min={0.5} max={3} step={0.1} />
            <Slider label="Workforce Avail" value={customWorkforce} onChange={setCustomWorkforce} min={0.5} max={1.0} step={0.05} />
          </div>
          <button
            onClick={runCustom}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded text-sm disabled:opacity-50"
          >
            {loading ? 'Running...' : 'Run Scenario'}
          </button>
        </div>
      )}

      {loading && <div className="text-slate-400 animate-pulse mb-4">Running simulation...</div>}

      {result && (
        <div className="space-y-4">
          {/* Scenario header */}
          <div className="bg-slate-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-semibold text-white">{result.scenario.name}</h2>
              <span className="text-xs font-mono text-slate-500">{result.scenario.id}</span>
            </div>
            <p className="text-sm text-slate-400">{result.scenario.description}</p>
          </div>

          {/* KPI cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard label="Plant OEE" value={`${(result.plant_oee * 100).toFixed(1)}%`}
              color={result.plant_oee > 0.65 ? 'text-green-400' : result.plant_oee > 0.5 ? 'text-yellow-400' : 'text-red-400'} />
            <KpiCard label="Total Units" value={result.total_units.toLocaleString()} />
            <KpiCard label="Failures" value={String(result.total_failures)}
              color={result.total_failures > 5 ? 'text-red-400' : 'text-white'} />
            <KpiCard label="Duration" value={`${result.duration_hours}h`} />
          </div>

          {/* Impact summary */}
          <div className="bg-slate-800 rounded-lg p-4">
            <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3">Scenario Impact</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
              {result.impact.forced_failure && (
                <ImpactBadge label="Forced Failure" value={`${result.impact.failure_downtime_minutes.toFixed(0)} min downtime`} color="red" />
              )}
              {result.impact.demand_multiplier !== 1.0 && (
                <ImpactBadge label="Demand" value={`${result.impact.demand_multiplier}x`} color={result.impact.demand_multiplier > 1 ? 'yellow' : 'blue'} />
              )}
              {result.impact.capacity_gap_units > 0 && (
                <ImpactBadge label="Capacity Gap" value={`${result.impact.capacity_gap_units.toLocaleString()} units`} color="red" />
              )}
              {result.impact.cip_extra_minutes > 0 && (
                <ImpactBadge label="CIP Extra" value={`${result.impact.cip_extra_minutes.toFixed(0)} min`} color="yellow" />
              )}
              {result.impact.energy_rate_multiplier !== 1.0 && (
                <ImpactBadge label="Energy Rate" value={`${result.impact.energy_rate_multiplier}x`} color="yellow" />
              )}
              {result.impact.workforce_availability < 1.0 && (
                <ImpactBadge label="Workforce" value={`${(result.impact.workforce_availability * 100).toFixed(0)}%`} color="yellow" />
              )}
            </div>
          </div>

          {/* Line details */}
          {result.lines.length > 0 && (
            <div className="bg-slate-800 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-900 text-slate-400 text-xs uppercase">
                  <tr>
                    <th className="px-4 py-2 text-left">Line</th>
                    <th className="px-4 py-2 text-right">OEE</th>
                    <th className="px-4 py-2 text-right">Availability</th>
                    <th className="px-4 py-2 text-right">Performance</th>
                    <th className="px-4 py-2 text-right">Quality</th>
                  </tr>
                </thead>
                <tbody className="text-slate-300">
                  {result.lines.map((l) => (
                    <tr key={l.name} className="border-t border-slate-700">
                      <td className="px-4 py-2 font-mono text-xs">{l.name}</td>
                      <td className="px-4 py-2 text-right">{(l.oee * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2 text-right">{(l.availability * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2 text-right">{(l.performance * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2 text-right">{(l.quality * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Slider({ label, value, onChange, min, max, step }: {
  label: string; value: number; onChange: (v: number) => void; min: number; max: number; step: number;
}) {
  return (
    <div>
      <label className="text-xs text-slate-400 block mb-1">{label}: {value.toFixed(2)}</label>
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-blue-500"
      />
    </div>
  );
}

function KpiCard({ label, value, color = 'text-white' }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="text-xs text-slate-400 uppercase mb-1">{label}</div>
      <div className={`text-lg font-bold ${color}`}>{value}</div>
    </div>
  );
}

function ImpactBadge({ label, value, color }: { label: string; value: string; color: string }) {
  const bg = color === 'red' ? 'bg-red-900/40 text-red-300' : color === 'yellow' ? 'bg-yellow-900/40 text-yellow-300' : 'bg-blue-900/40 text-blue-300';
  return (
    <div className={`rounded p-2 ${bg}`}>
      <div className="text-xs font-semibold">{label}</div>
      <div className="text-sm">{value}</div>
    </div>
  );
}
