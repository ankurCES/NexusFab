import { useEffect, useRef, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api/client';
import type { AllergenMatrix, CcpReport, CipSchedule, ComplianceScore } from '../types/api';

const PLANTS = ['PLT-001', 'PLT-002', 'PLT-003', 'PLT-004', 'PLT-005'];

function ccpBadge(status: string) {
  if (status === 'FAIL') return 'bg-red-900/40 text-red-300';
  if (status === 'WARN') return 'bg-yellow-900/40 text-yellow-300';
  return 'bg-green-900/40 text-green-300';
}

function ccpBar(status: string) {
  if (status === 'FAIL') return 'bg-red-500';
  if (status === 'WARN') return 'bg-yellow-500';
  return 'bg-green-500';
}

function cipBadge(status: string) {
  if (status === 'overdue') return 'bg-red-900/60 text-red-300 font-bold';
  if (status === 'in_progress') return 'bg-blue-900/40 text-blue-300';
  if (status === 'completed') return 'bg-green-900/40 text-green-300';
  return 'bg-slate-700 text-slate-400';
}

function allergenCell(s: string) {
  if (s === 'CONTAINS') return 'bg-red-900/60 text-red-300 font-semibold';
  if (s === 'MAY_CONTAIN') return 'bg-yellow-900/40 text-yellow-300';
  return 'bg-slate-800 text-slate-600';
}

function allergenGlyph(s: string) {
  if (s === 'CONTAINS') return '●';
  if (s === 'MAY_CONTAIN') return '◐';
  return '○';
}

function scoreColor(v: number) {
  if (v >= 95) return 'text-green-400';
  if (v >= 85) return 'text-yellow-400';
  return 'text-red-400';
}

function scoreBarColor(v: number) {
  if (v >= 95) return 'bg-green-500';
  if (v >= 85) return 'bg-yellow-500';
  return 'bg-red-500';
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString([], {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function Countdown({ deadline }: { deadline: string }) {
  const [secs, setSecs] = useState(0);
  useEffect(() => {
    const tick = () => setSecs(Math.max(0, Math.floor((new Date(deadline).getTime() - Date.now()) / 1000)));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [deadline]);
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  return (
    <span className={`font-mono text-xs ${secs < 3600 ? 'text-red-400 animate-pulse' : 'text-yellow-400'}`}>
      {h}h {String(m).padStart(2, '0')}m {String(s).padStart(2, '0')}s
    </span>
  );
}

export default function Compliance() {
  const [plant, setPlant] = useState('PLT-001');
  const [ccps, setCcps] = useState<CcpReport | null>(null);
  const [allergens, setAllergens] = useState<AllergenMatrix | null>(null);
  const [cip, setCip] = useState<CipSchedule | null>(null);
  const [score, setScore] = useState<ComplianceScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function fetchAll(plantId: string, showSpinner = true) {
    if (showSpinner) setLoading(true);
    Promise.all([
      api.complianceCcps(plantId),
      api.complianceAllergens(plantId),
      api.complianceCip(plantId),
      api.complianceScore(plantId),
    ])
      .then(([c, a, ci, s]) => { setCcps(c); setAllergens(a); setCip(ci); setScore(s); setError(''); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchAll(plant);
    intervalRef.current = setInterval(() => fetchAll(plant, false), 30_000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [plant]);

  if (error) return <div className="p-6 text-red-400">{error}</div>;

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Compliance & HACCP</h1>
          <p className="text-sm text-slate-400">Food safety — CCPs, allergens, CIP schedule</p>
        </div>
        <select
          value={plant}
          onChange={(e) => setPlant(e.target.value)}
          className="bg-slate-800 text-white rounded px-3 py-2 text-sm border border-slate-700"
        >
          {PLANTS.map((p) => <option key={p}>{p}</option>)}
        </select>
      </header>

      {loading ? (
        <div className="text-slate-400 animate-pulse">Loading compliance data...</div>
      ) : (
        <>
          {/* ── Compliance Score ── */}
          {score && (
            <section className="mb-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="bg-slate-800 rounded-lg p-5 flex flex-col">
                  <div className="text-xs text-slate-400 uppercase mb-1">Plant Compliance Score</div>
                  <div className={`text-5xl font-bold mb-1 ${scoreColor(score.score)}`}>
                    {score.score.toFixed(1)}%
                  </div>
                  <div className="text-xs text-slate-500 mb-4">30-day rolling average</div>
                  <div className="space-y-2">
                    {(
                      [
                        ['Food Safety (40%)', score.food_safety_score],
                        ['Allergen Mgmt (30%)', score.allergen_score],
                        ['Documentation (30%)', score.documentation_score],
                      ] as [string, number][]
                    ).map(([label, val]) => (
                      <div key={label} className="flex items-center gap-2">
                        <span className="text-xs text-slate-400 w-36 shrink-0">{label}</span>
                        <div className="flex-1 h-1.5 bg-slate-700 rounded overflow-hidden">
                          <div className={`h-full rounded ${scoreBarColor(val)}`} style={{ width: `${val}%` }} />
                        </div>
                        <span className={`text-xs w-10 text-right ${scoreColor(val)}`}>{val.toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="lg:col-span-2 bg-slate-800 rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-slate-400 mb-3 uppercase">30-Day Score Trend</h3>
                  <ResponsiveContainer width="100%" height={150}>
                    <LineChart data={score.trend} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#94a3b8' }} tickFormatter={(d: string) => d.slice(5)} interval={4} />
                      <YAxis domain={[75, 100]} tick={{ fontSize: 9, fill: '#94a3b8' }} />
                      <Tooltip
                        contentStyle={{ background: '#1e293b', border: 'none', fontSize: 12 }}
                        formatter={(v) => [`${Number(v).toFixed(1)}%`, 'Score']}
                      />
                      <Line type="monotone" dataKey="score" stroke="#22d3ee" dot={false} strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </section>
          )}

          {/* ── CCP Monitoring ── */}
          {ccps && ccps.ccps.length > 0 && (
            <section className="mb-6">
              <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
                CCP Monitoring
                <span className="text-slate-500 normal-case font-normal text-xs ml-2">polls every 30s</span>
              </h2>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {ccps.ccps.map((ccp) => {
                  const pct = Math.min(100, Math.max(0,
                    ((ccp.current_value - ccp.critical_lower) / (ccp.critical_upper - ccp.critical_lower)) * 100,
                  ));
                  const decimals = ccp.current_value < 10 ? 3 : 1;
                  return (
                    <div key={ccp.id} className="bg-slate-800 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="text-sm font-semibold text-white">{ccp.name}</div>
                          <div className="text-xs text-slate-400">{ccp.parameter}</div>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${ccpBadge(ccp.status)}`}>
                          {ccp.status}
                        </span>
                      </div>
                      <div className="text-2xl font-bold text-white mb-1">
                        {ccp.current_value.toFixed(decimals)}
                        <span className="text-sm text-slate-400 ml-1">{ccp.unit}</span>
                      </div>
                      <div className="text-xs text-slate-500 mb-2">
                        Limits: {ccp.lower_limit}–{ccp.upper_limit} {ccp.unit}
                      </div>
                      <div className="h-1.5 bg-slate-700 rounded overflow-hidden mb-2">
                        <div className={`h-full rounded transition-all ${ccpBar(ccp.status)}`} style={{ width: `${pct}%` }} />
                      </div>
                      <div className="flex justify-between text-xs text-slate-400">
                        <span>30d: <span className="text-white">{ccp.compliance_rate_30d}%</span></span>
                        <span>{new Date(ccp.last_checked).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* ── Allergen Matrix ── */}
          {allergens && allergens.products.length > 0 && (
            <section className="mb-6">
              <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
                Allergen Matrix
              </h2>
              <div className="bg-slate-800 rounded-lg overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-slate-900 text-slate-400">
                    <tr>
                      <th className="px-3 py-2 text-left">SKU / Product</th>
                      {allergens.allergens.map((a) => (
                        <th key={a} className="px-2 py-2 text-center">{a}</th>
                      ))}
                      <th className="px-3 py-2 text-center">CIP Class</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allergens.products.map((prod) => (
                      <tr
                        key={prod.sku}
                        className={`border-t border-slate-700 ${prod.is_current_production ? 'bg-blue-900/20' : ''}`}
                      >
                        <td className="px-3 py-2">
                          <div className="font-mono text-slate-300">{prod.sku}</div>
                          <div className="text-slate-500 max-w-[150px] truncate">{prod.name}</div>
                          {prod.is_current_production && (
                            <span className="text-blue-400">▶ running</span>
                          )}
                        </td>
                        {allergens.allergens.map((a) => {
                          const st = prod.allergen_status[a] ?? 'FREE';
                          return (
                            <td key={a} className={`px-2 py-2 text-center ${allergenCell(st)}`} title={st}>
                              {allergenGlyph(st)}
                            </td>
                          );
                        })}
                        <td className="px-3 py-2 text-center">
                          {prod.next_changeover_cip_class ? (
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              prod.next_changeover_cip_class === 'CLASS_A'
                                ? 'bg-red-900/50 text-red-300'
                                : prod.next_changeover_cip_class === 'CLASS_B'
                                ? 'bg-yellow-900/50 text-yellow-300'
                                : 'bg-slate-700 text-slate-400'
                            }`}>
                              {prod.next_changeover_cip_class.replace('_', ' ')}
                            </span>
                          ) : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="px-3 py-2 border-t border-slate-700 flex gap-4 text-xs text-slate-400">
                  <span>● CONTAINS</span>
                  <span>◐ MAY CONTAIN</span>
                  <span>○ FREE</span>
                </div>
              </div>
            </section>
          )}

          {/* ── CIP Schedule ── */}
          {cip && cip.events.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
                CIP Schedule
                <span className="text-slate-500 normal-case font-normal text-xs ml-2">past 7d + next 24h</span>
              </h2>
              <div className="bg-slate-800 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-900 text-slate-400 text-xs uppercase">
                    <tr>
                      <th className="px-4 py-2 text-left">Line</th>
                      <th className="px-4 py-2 text-left">Type</th>
                      <th className="px-4 py-2 text-left">Status</th>
                      <th className="px-4 py-2 text-left">Scheduled</th>
                      <th className="px-4 py-2 text-right">Duration</th>
                      <th className="px-4 py-2 text-right">Hard Deadline</th>
                    </tr>
                  </thead>
                  <tbody className="text-slate-300">
                    {cip.events.map((ev) => (
                      <tr key={ev.id} className={`border-t border-slate-700 ${ev.status === 'overdue' ? 'bg-red-900/10' : ''}`}>
                        <td className="px-4 py-2">
                          <div className="font-mono text-xs">{ev.line}</div>
                          {ev.is_uht_aseptic && <div className="text-xs text-cyan-400">UHT/Aseptic</div>}
                        </td>
                        <td className="px-4 py-2 text-xs">{ev.type.replace(/_/g, ' ')}</td>
                        <td className="px-4 py-2">
                          <span className={`px-2 py-0.5 rounded text-xs ${cipBadge(ev.status)}`}>
                            {ev.status.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-xs text-slate-400">{fmtTime(ev.scheduled_start)}</td>
                        <td className="px-4 py-2 text-right text-xs">{ev.duration_minutes}m</td>
                        <td className="px-4 py-2 text-right">
                          {ev.hard_deadline && ev.status === 'upcoming'
                            ? <Countdown deadline={ev.hard_deadline} />
                            : <span className="text-slate-600 text-xs">—</span>}
                        </td>
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
