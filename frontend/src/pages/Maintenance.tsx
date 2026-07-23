import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { MaintenanceSchedule, InventoryReport } from '../types/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const PLANTS = ['PLT-001', 'PLT-002', 'PLT-003', 'PLT-004', 'PLT-005'];
const PRIORITY_COLORS: Record<number, string> = { 1: '#ef4444', 2: '#f59e0b', 3: '#3b82f6', 4: '#6b7280' };

export default function Maintenance() {
  const [plantId, setPlantId] = useState(PLANTS[0]);
  const [maint, setMaint] = useState<MaintenanceSchedule | null>(null);
  const [inv, setInv] = useState<InventoryReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    Promise.all([api.maintenance(plantId), api.inventory(plantId)])
      .then(([m, i]) => { setMaint(m); setInv(i); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [plantId]);

  if (loading) return <div className="flex items-center justify-center min-h-screen text-slate-400 animate-pulse">Loading...</div>;
  if (error) return <div className="p-6 text-red-400">{error}</div>;
  if (!maint || !inv) return null;

  const priorityData = Object.entries(maint.by_priority).map(([p, count]) => ({
    name: `P${p}`, count, fill: PRIORITY_COLORS[Number(p)] ?? '#6b7280',
  }));

  const reorderParts = inv.parts.filter((p) => p.needs_reorder);

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Maintenance & Inventory</h1>
        <select
          value={plantId}
          onChange={(e) => setPlantId(e.target.value)}
          className="bg-slate-800 text-white text-sm rounded px-3 py-1.5 border border-slate-700"
        >
          {PLANTS.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <KPI label="Actions" value={maint.total_actions} />
        <KPI label="Est. Cost" value={`$${maint.total_cost.toLocaleString()}`} />
        <KPI label="Parts to Reorder" value={inv.needs_reorder} warn={inv.needs_reorder > 0} />
        <KPI label="Inventory Value" value={`$${inv.inventory_value.toLocaleString()}`} />
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Priority chart */}
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Actions by Priority</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={priorityData}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
              <Bar dataKey="count">
                {priorityData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* ABC distribution */}
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-3">ABC Classification</h3>
          <div className="flex gap-4 mt-6">
            {Object.entries(inv.by_abc).map(([cls, count]) => (
              <div key={cls} className="flex-1 text-center">
                <div className="text-3xl font-bold text-white">{count}</div>
                <div className="text-sm text-slate-400">Class {cls}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 text-xs text-slate-500">
            {inv.total_parts} total parts · {inv.high_risk} high stockout risk
          </div>
        </div>
      </div>

      {/* Upcoming actions table */}
      <div className="bg-slate-800 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-semibold text-white mb-3">Upcoming Maintenance ({maint.total_actions})</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 text-left text-xs">
                <th className="pb-2">Equipment</th>
                <th className="pb-2">Line</th>
                <th className="pb-2">Action</th>
                <th className="pb-2">Due</th>
                <th className="pb-2">Pri</th>
                <th className="pb-2">Fail%</th>
                <th className="pb-2 text-right">Cost</th>
              </tr>
            </thead>
            <tbody>
              {maint.actions.slice(0, 20).map((a, i) => (
                <tr key={i} className="border-t border-slate-700 text-slate-300">
                  <td className="py-1.5">{a.equipment}</td>
                  <td>{a.line}</td>
                  <td>{a.action}</td>
                  <td>{a.days_until_due}d</td>
                  <td>
                    <span className="inline-block w-5 h-5 rounded text-center text-xs leading-5 text-white"
                      style={{ background: PRIORITY_COLORS[a.priority] ?? '#6b7280' }}>
                      {a.priority}
                    </span>
                  </td>
                  <td>{Math.round(a.failure_prob * 100)}%</td>
                  <td className="text-right">${a.cost}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {maint.total_actions > 20 && (
            <div className="text-xs text-slate-500 mt-2">Showing 20 of {maint.total_actions}</div>
          )}
        </div>
      </div>

      {/* Reorder alerts */}
      {reorderParts.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-400 mb-3">⚠ Reorder Required ({reorderParts.length})</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 text-left text-xs">
                  <th className="pb-2">Part</th>
                  <th className="pb-2">ABC</th>
                  <th className="pb-2">On Hand</th>
                  <th className="pb-2">Reorder Pt</th>
                  <th className="pb-2">EOQ</th>
                  <th className="pb-2">Stockout Risk</th>
                  <th className="pb-2 text-right">Unit Cost</th>
                </tr>
              </thead>
              <tbody>
                {reorderParts.map((p, i) => (
                  <tr key={i} className="border-t border-slate-700 text-slate-300">
                    <td className="py-1.5">{p.part}</td>
                    <td><span className={`font-bold ${p.abc_class === 'A' ? 'text-red-400' : p.abc_class === 'B' ? 'text-yellow-400' : 'text-slate-400'}`}>{p.abc_class}</span></td>
                    <td>{p.on_hand}</td>
                    <td>{p.reorder_point}</td>
                    <td>{p.eoq}</td>
                    <td className={p.stockout_risk > 0.5 ? 'text-red-400' : 'text-yellow-400'}>{Math.round(p.stockout_risk * 100)}%</td>
                    <td className="text-right">${p.unit_cost}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
      <div className={`text-xl font-bold mt-1 ${warn ? 'text-yellow-400' : 'text-white'}`}>{value}</div>
    </div>
  );
}
