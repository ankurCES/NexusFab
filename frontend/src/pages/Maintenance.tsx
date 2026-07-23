import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type {
  EquipmentPrediction,
  FailureHistory,
  MaintenanceAction,
  MaintenanceSchedule,
  PlantPredictions,
  SparePartDetail,
  SparesStatusReport,
} from '../types/api';
import {
  Bar,
  BarChart,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const PLANTS = ['PLT-001', 'PLT-002', 'PLT-003', 'PLT-004', 'PLT-005'];

const ALERT_BG: Record<string, string> = {
  GREEN: 'bg-green-500', YELLOW: 'bg-yellow-400', ORANGE: 'bg-orange-500', RED: 'bg-red-600',
};
const ALERT_FILL: Record<string, string> = {
  GREEN: '#22c55e', YELLOW: '#facc15', ORANGE: '#f97316', RED: '#ef4444',
};
const ALERT_TEXT: Record<string, string> = {
  GREEN: 'text-green-400', YELLOW: 'text-yellow-400', ORANGE: 'text-orange-400', RED: 'text-red-400',
};
const SEV_DOT: Record<string, string> = {
  minor: 'bg-slate-400', major: 'bg-yellow-400', critical: 'bg-red-500',
};
const SEV_TEXT: Record<string, string> = {
  minor: 'text-slate-400', major: 'text-yellow-400', critical: 'text-red-400',
};
const TOOLTIP_STYLE = { background: '#1e293b', border: '1px solid #334155', color: '#fff', fontSize: 12 };

type Tab = 'matrix' | 'rul' | 'schedule' | 'history' | 'spares';
const TABS: { id: Tab; label: string }[] = [
  { id: 'matrix', label: 'Health Matrix' },
  { id: 'rul', label: 'RUL Timeline' },
  { id: 'schedule', label: 'Schedule' },
  { id: 'history', label: 'Failure History' },
  { id: 'spares', label: 'Spare Parts' },
];

function KPI({ label, value, warn }: { label: string; value: string | number; warn?: boolean }) {
  return (
    <div className="bg-slate-800 rounded-lg p-3">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`text-xl font-bold mt-1 ${warn ? 'text-yellow-400' : 'text-white'}`}>{value}</div>
    </div>
  );
}

function AlertKPI({ level, count }: { level: string; count: number }) {
  return (
    <div className="bg-slate-800 rounded-lg p-3 flex items-center gap-3">
      <span className={`w-3 h-3 rounded-full ${ALERT_BG[level]}`} />
      <div>
        <div className="text-xs text-slate-400">{level}</div>
        <div className={`text-xl font-bold ${count > 0 ? ALERT_TEXT[level] : 'text-slate-600'}`}>{count}</div>
      </div>
    </div>
  );
}

// ── Health Matrix ──────────────────────────────────────────────────────────────

function HealthMatrix({
  predictions, onSelect,
}: { predictions: PlantPredictions; onSelect: (e: EquipmentPrediction) => void }) {
  const byLine: Record<string, EquipmentPrediction[]> = {};
  for (const e of predictions.equipment) {
    (byLine[e.line] ??= []).push(e);
  }

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">Equipment Health Matrix</h3>
        <div className="flex gap-3 text-xs text-slate-400">
          {(['GREEN', 'YELLOW', 'ORANGE', 'RED'] as const).map((l) => (
            <span key={l} className="flex items-center gap-1">
              <span className={`w-2.5 h-2.5 rounded-sm ${ALERT_BG[l]}`} />{l}
            </span>
          ))}
        </div>
      </div>
      <div className="space-y-2">
        {Object.entries(byLine).map(([line, equips]) => (
          <div key={line} className="flex items-center gap-3">
            <span className="w-28 text-xs text-slate-400 truncate shrink-0">{line}</span>
            <div className="flex gap-1.5 flex-wrap">
              {equips.map((e) => (
                <button
                  key={e.equipment_name}
                  title={`${e.equipment_name}\nRUL: ${e.rul_hours}h\nHealth: ${(e.health_index * 100).toFixed(0)}%\nAlert: ${e.alert_level}`}
                  onClick={() => onSelect(e)}
                  className={`w-14 h-10 rounded text-xs text-white font-medium hover:opacity-75 transition-opacity flex flex-col items-center justify-center gap-0.5 ${ALERT_BG[e.alert_level]}`}
                >
                  <span className="text-[10px] leading-none">{e.equipment_type.slice(0, 3)}</span>
                  <span className="text-[10px] leading-none opacity-80">{e.rul_hours}h</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── RUL Timeline ───────────────────────────────────────────────────────────────

function RULTimeline({ predictions }: { predictions: PlantPredictions }) {
  const sorted = [...predictions.equipment].sort((a, b) => a.rul_hours - b.rul_hours);
  const maxRul = Math.max(...sorted.map((e) => e.rul_hours), 180);

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-white mb-1">RUL Timeline (hours remaining)</h3>
      <div className="flex gap-4 mb-3 text-xs text-slate-400">
        <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-red-500 inline-block"/>24h emergency</span>
        <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-orange-400 inline-block"/>72h warning</span>
        <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-yellow-400 inline-block"/>168h caution</span>
      </div>
      <ResponsiveContainer width="100%" height={Math.max(sorted.length * 28 + 40, 200)}>
        <BarChart data={sorted} layout="vertical" margin={{ left: 0, right: 20 }}>
          <XAxis type="number" domain={[0, maxRul]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <YAxis type="category" dataKey="equipment_name" width={130} tick={{ fill: '#94a3b8', fontSize: 10 }} />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(v) => [`${v}h`, 'RUL']}
          />
          <ReferenceLine x={24} stroke="#ef4444" strokeDasharray="4 2" />
          <ReferenceLine x={72} stroke="#f97316" strokeDasharray="4 2" />
          <ReferenceLine x={168} stroke="#eab308" strokeDasharray="4 2" />
          <Bar dataKey="rul_hours" radius={[0, 2, 2, 0]}>
            {sorted.map((e, i) => <Cell key={i} fill={ALERT_FILL[e.alert_level]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Gantt Schedule ─────────────────────────────────────────────────────────────

function MaintenanceGantt({ maint }: { maint: MaintenanceSchedule }) {
  const HORIZON = 30;
  const byLine: Record<string, MaintenanceAction[]> = {};
  for (const a of maint.actions) {
    (byLine[a.line] ??= []).push(a);
  }

  const blockColor = (priority: number) =>
    priority === 1 ? 'bg-red-500' : priority === 2 ? 'bg-orange-400' : 'bg-blue-500';

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">30-Day Maintenance Calendar</h3>
        <div className="flex gap-3 text-xs text-slate-400">
          <span><span className="inline-block w-2.5 h-2.5 bg-red-500 rounded mr-1"/>Emergency</span>
          <span><span className="inline-block w-2.5 h-2.5 bg-orange-400 rounded mr-1"/>Predicted</span>
          <span><span className="inline-block w-2.5 h-2.5 bg-blue-500 rounded mr-1"/>Planned</span>
        </div>
      </div>

      {/* Day header */}
      <div className="flex mb-2 pl-28">
        <div className="flex-1 relative h-5">
          {[0, 5, 10, 15, 20, 25, 30].map((d) => (
            <span
              key={d}
              style={{ left: `${(d / HORIZON) * 100}%` }}
              className="absolute text-xs text-slate-500 -translate-x-1/2"
            >
              +{d}d
            </span>
          ))}
        </div>
      </div>

      {/* Rows */}
      <div className="space-y-1.5">
        {Object.entries(byLine).map(([line, acts]) => (
          <div key={line} className="flex items-center">
            <span className="w-28 text-xs text-slate-400 truncate pr-2 shrink-0">{line}</span>
            <div className="flex-1 relative h-7 bg-slate-700 rounded overflow-hidden">
              {acts.map((a, i) => {
                const due = Math.max(0, a.days_until_due);
                const left = (due / HORIZON) * 100;
                if (left >= 100) return null;
                const width = Math.max(0.8, ((a.duration_hours / 24) / HORIZON) * 100);
                return (
                  <div
                    key={i}
                    title={`${a.equipment}: ${a.action} — ${a.duration_hours}h`}
                    style={{ left: `${left}%`, width: `${Math.min(width, 100 - left)}%` }}
                    className={`absolute top-0.5 h-6 rounded text-[10px] text-white px-1 overflow-hidden whitespace-nowrap leading-6 ${blockColor(a.priority)}`}
                  >
                    {a.equipment.split('-').at(-1)}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {maint.total_actions === 0 && (
        <div className="text-center text-slate-500 py-8">No maintenance scheduled in next 30 days</div>
      )}

      <div className="mt-3 text-xs text-slate-500">
        {maint.total_actions} actions · est. ${maint.total_cost.toLocaleString()} · {maint.total_hours}h total
      </div>
    </div>
  );
}

// ── Failure History ────────────────────────────────────────────────────────────

function FailureHistoryTab({ history }: { history: FailureHistory }) {
  const [sevFilter, setSevFilter] = useState('');
  const [lineFilter, setLineFilter] = useState('');

  const lines = [...new Set(history.events.map((e) => e.line))].sort();
  const filtered = history.events.filter(
    (e) => (!sevFilter || e.severity === sevFilter) && (!lineFilter || e.line === lineFilter),
  );

  const totalCost = filtered.reduce((s, e) => s + e.cost, 0);
  const avgMttr = filtered.length
    ? (filtered.reduce((s, e) => s + e.mttr_hours, 0) / filtered.length).toFixed(1)
    : '0';

  return (
    <div className="space-y-4">
      {/* Trend chart */}
      <div className="bg-slate-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-3">Failures per Week (last 90 days)</h3>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={history.by_week}>
            <XAxis dataKey="week" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey="failures" fill="#f97316" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Filters + table */}
      <div className="bg-slate-800 rounded-lg p-4">
        <div className="flex flex-wrap gap-3 mb-4 items-center">
          <h3 className="text-sm font-semibold text-white flex-1">
            Failure Log ({filtered.length} events · avg MTTR {avgMttr}h · ${totalCost.toLocaleString()} cost)
          </h3>
          <select
            value={sevFilter}
            onChange={(e) => setSevFilter(e.target.value)}
            className="bg-slate-700 text-white text-xs rounded px-2 py-1 border border-slate-600"
          >
            <option value="">All Severities</option>
            <option value="minor">Minor</option>
            <option value="major">Major</option>
            <option value="critical">Critical</option>
          </select>
          <select
            value={lineFilter}
            onChange={(e) => setLineFilter(e.target.value)}
            className="bg-slate-700 text-white text-xs rounded px-2 py-1 border border-slate-600"
          >
            <option value="">All Lines</option>
            {lines.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 text-left text-xs border-b border-slate-700">
                <th className="pb-2 pr-3">Date</th>
                <th className="pb-2 pr-3">Equipment</th>
                <th className="pb-2 pr-3">Line</th>
                <th className="pb-2 pr-3">Failure Mode</th>
                <th className="pb-2 pr-3">Severity</th>
                <th className="pb-2 pr-3">MTTR (h)</th>
                <th className="pb-2 text-right">Cost</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 50).map((e, i) => (
                <tr key={i} className="border-t border-slate-700 text-slate-300 text-xs">
                  <td className="py-1.5 pr-3">{e.date}</td>
                  <td className="pr-3 font-mono text-xs">{e.equipment}</td>
                  <td className="pr-3">{e.line}</td>
                  <td className="pr-3 text-slate-400">{e.failure_mode.replace(/_/g, ' ')}</td>
                  <td className="pr-3">
                    <span className={`flex items-center gap-1 ${SEV_TEXT[e.severity]}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${SEV_DOT[e.severity]}`} />
                      {e.severity}
                    </span>
                  </td>
                  <td className="pr-3">{e.mttr_hours}</td>
                  <td className="text-right">${e.cost.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length > 50 && (
            <div className="text-xs text-slate-500 mt-2">Showing 50 of {filtered.length}</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Spare Parts ────────────────────────────────────────────────────────────────

function SparePartsTab({ spares }: { spares: SparesStatusReport }) {
  const sorted = [...spares.parts].sort((a, b) => {
    if (a.needs_reorder !== b.needs_reorder) return a.needs_reorder ? -1 : 1;
    return a.days_to_stockout - b.days_to_stockout;
  });

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="flex flex-wrap gap-4 mb-4 text-xs text-slate-400">
        <span>Total parts: <b className="text-white">{spares.total_parts}</b></span>
        <span>Value: <b className="text-white">${spares.inventory_value.toLocaleString()}</b></span>
        <span className={spares.needs_reorder > 0 ? 'text-yellow-400' : ''}>
          Reorder needed: <b>{spares.needs_reorder}</b>
        </span>
        <span className={spares.high_risk > 0 ? 'text-orange-400' : ''}>
          High risk: <b>{spares.high_risk}</b>
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-400 text-left text-xs border-b border-slate-700">
              <th className="pb-2 pr-3">Part</th>
              <th className="pb-2 pr-3">Type</th>
              <th className="pb-2 pr-3">ABC-XYZ</th>
              <th className="pb-2 pr-3">On Hand</th>
              <th className="pb-2 pr-3">ROP</th>
              <th className="pb-2 pr-3">Days to Stockout</th>
              <th className="pb-2 pr-3">Stockout Risk</th>
              <th className="pb-2 text-right">Unit Cost</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((p: SparePartDetail, i: number) => (
              <tr key={i} className="border-t border-slate-700 text-slate-300 text-xs">
                <td className="py-1.5 pr-3">
                  <span>{p.part}</span>
                  {p.needs_reorder && (
                    <span className="ml-2 bg-red-500 text-white text-[10px] px-1 py-0.5 rounded">REORDER</span>
                  )}
                </td>
                <td className="pr-3 text-slate-400">{p.equipment_type}</td>
                <td className="pr-3">
                  <span className={`font-bold ${p.abc_class === 'A' ? 'text-red-400' : p.abc_class === 'B' ? 'text-yellow-400' : 'text-slate-400'}`}>
                    {p.abc_xyz}
                  </span>
                </td>
                <td className="pr-3">{p.on_hand}</td>
                <td className="pr-3">{p.reorder_point}</td>
                <td className={`pr-3 ${p.days_to_stockout < 14 ? 'text-red-400' : p.days_to_stockout < 30 ? 'text-yellow-400' : ''}`}>
                  {p.days_to_stockout}d
                </td>
                <td className={`pr-3 ${p.stockout_risk > 0.5 ? 'text-red-400' : p.stockout_risk > 0.2 ? 'text-yellow-400' : 'text-slate-400'}`}>
                  {Math.round(p.stockout_risk * 100)}%
                </td>
                <td className="text-right">${p.unit_cost.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Equipment Detail Modal ─────────────────────────────────────────────────────

function EquipmentModal({ equip, onClose }: { equip: EquipmentPrediction; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-slate-800 border border-slate-700 rounded-xl p-6 w-80 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold">{equip.equipment_name}</h3>
          <span className={`text-xs font-bold px-2 py-0.5 rounded ${ALERT_BG[equip.alert_level]} text-white`}>
            {equip.alert_level}
          </span>
        </div>
        <div className="space-y-2 text-sm">
          <Row label="Type" value={equip.equipment_type} />
          <Row label="Line" value={equip.line} />
          <Row
            label="RUL"
            value={`${equip.rul_hours}h`}
            className={ALERT_TEXT[equip.alert_level]}
          />
          <Row label="Health Index" value={`${(equip.health_index * 100).toFixed(1)}%`} />
          <Row label="Anomaly Score" value={equip.anomaly_score.toFixed(3)} />
          <Row label="Confidence" value={`${(equip.confidence * 100).toFixed(0)}%`} />
        </div>
        <button
          onClick={onClose}
          className="mt-5 w-full bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg py-2 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  );
}

function Row({ label, value, className }: { label: string; value: string; className?: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className={`text-white font-medium ${className ?? ''}`}>{value}</span>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function Maintenance() {
  const [plantId, setPlantId] = useState(PLANTS[0]);
  const [activeTab, setActiveTab] = useState<Tab>('matrix');
  const [maint, setMaint] = useState<MaintenanceSchedule | null>(null);
  const [predictions, setPredictions] = useState<PlantPredictions | null>(null);
  const [history, setHistory] = useState<FailureHistory | null>(null);
  const [spares, setSpares] = useState<SparesStatusReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalEquip, setModalEquip] = useState<EquipmentPrediction | null>(null);

  useEffect(() => {
    setLoading(true);
    setError('');
    Promise.all([
      api.maintenance(plantId),
      api.maintenancePredictions(plantId),
      api.maintenanceHistory(plantId),
      api.sparesStatus(plantId),
    ])
      .then(([m, p, h, s]) => { setMaint(m); setPredictions(p); setHistory(h); setSpares(s); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [plantId]);

  if (loading) return <div className="flex items-center justify-center min-h-screen text-slate-400 animate-pulse">Loading…</div>;
  if (error) return <div className="p-6 text-red-400">{error}</div>;
  if (!maint || !predictions || !history || !spares) return null;

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-2xl font-bold text-white">Predictive Maintenance</h1>
        <select
          value={plantId}
          onChange={(e) => setPlantId(e.target.value)}
          className="bg-slate-800 text-white text-sm rounded px-3 py-1.5 border border-slate-700"
        >
          {PLANTS.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 mb-5">
        <KPI label="Equipment" value={predictions.equipment.length} />
        <KPI label="Actions (30d)" value={maint.total_actions} />
        <AlertKPI level="RED" count={predictions.summary.RED} />
        <AlertKPI level="ORANGE" count={predictions.summary.ORANGE} />
        <AlertKPI level="YELLOW" count={predictions.summary.YELLOW} />
        <AlertKPI level="GREEN" count={predictions.summary.GREEN} />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-slate-800 rounded-lg p-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex-1 text-xs py-2 px-2 rounded-md transition-colors ${
              activeTab === t.id
                ? 'bg-slate-600 text-white font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'matrix' && (
        <HealthMatrix predictions={predictions} onSelect={setModalEquip} />
      )}
      {activeTab === 'rul' && <RULTimeline predictions={predictions} />}
      {activeTab === 'schedule' && <MaintenanceGantt maint={maint} />}
      {activeTab === 'history' && <FailureHistoryTab history={history} />}
      {activeTab === 'spares' && <SparePartsTab spares={spares} />}

      {/* Modal */}
      {modalEquip && <EquipmentModal equip={modalEquip} onClose={() => setModalEquip(null)} />}
    </div>
  );
}
