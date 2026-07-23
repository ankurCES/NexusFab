import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { NetworkReport, DemandPlan } from '../types/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LineChart, Line, CartesianGrid } from 'recharts';

const PLANTS = ['PLT-001', 'PLT-002', 'PLT-003', 'PLT-004', 'PLT-005'];

export default function Network() {
  const [net, setNet] = useState<NetworkReport | null>(null);
  const [demand, setDemand] = useState<DemandPlan | null>(null);
  const [demandPlant, setDemandPlant] = useState(PLANTS[0]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    api.network()
      .then(setNet)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    api.demand(demandPlant, 12).then(setDemand).catch(() => {});
  }, [demandPlant]);

  if (loading) return <div className="flex items-center justify-center min-h-screen text-slate-400 animate-pulse">Loading...</div>;
  if (error) return <div className="p-6 text-red-400">{error}</div>;
  if (!net) return null;

  const utilData = net.plants.map((p) => ({
    name: p.plant_id,
    utilization: Math.round(p.utilization * 100),
    oee: Math.round(p.avg_oee * 100),
    fill: p.plant_id === net.bottleneck ? '#ef4444' : '#3b82f6',
  }));

  const gapData = demand?.capacity_gaps.map((g) => ({
    period: g.period,
    demand: Math.round(g.demand),
    capacity: Math.round(g.capacity),
  })) ?? [];

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Network Overview</h1>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
        <KPI label="Total Capacity" value={`${net.network_capacity_tons.toLocaleString()} t/d`} />
        <KPI label="Avg Utilization" value={`${Math.round(net.avg_utilization * 100)}%`} />
        <KPI label="Avg OEE" value={`${Math.round(net.avg_oee * 100)}%`} />
        <KPI label="Bottleneck" value={net.bottleneck} warn />
        <KPI label="Plants" value={net.plant_count} />
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Utilization chart */}
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Plant Utilization</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={utilData}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
              <Bar dataKey="utilization" name="Utilization %">
                {utilData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Plant table */}
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Plant Status</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 text-left text-xs">
                <th className="pb-2">Plant</th>
                <th className="pb-2">Category</th>
                <th className="pb-2">Capacity</th>
                <th className="pb-2">Util%</th>
                <th className="pb-2">OEE%</th>
                <th className="pb-2 text-right">Available</th>
              </tr>
            </thead>
            <tbody>
              {net.plants.map((p) => (
                <tr key={p.plant_id} className={`border-t border-slate-700 ${p.plant_id === net.bottleneck ? 'text-red-300' : 'text-slate-300'}`}>
                  <td className="py-1.5 font-medium">{p.plant_id}</td>
                  <td>{p.category}</td>
                  <td>{p.capacity_tons} t/d</td>
                  <td>{Math.round(p.utilization * 100)}%</td>
                  <td>{Math.round(p.avg_oee * 100)}%</td>
                  <td className="text-right">{Math.round(p.available_tons)} t/d</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transfers */}
      {net.suggested_transfers.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-yellow-400 mb-3">Suggested Transfers</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {net.suggested_transfers.map((t, i) => (
              <div key={i} className="bg-slate-900 rounded p-3">
                <div className="text-white font-medium text-sm">{t.from} → {t.to}</div>
                <div className="text-xs text-slate-400 mt-1">{t.tons} tons · {t.category}</div>
                <div className="text-xs text-slate-500">${t.transport_cost.toLocaleString()} transport · {t.transport_hours}h</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Demand Planning */}
      <div className="bg-slate-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-white">Demand vs Capacity</h3>
          <select
            value={demandPlant}
            onChange={(e) => setDemandPlant(e.target.value)}
            className="bg-slate-900 text-white text-xs rounded px-2 py-1 border border-slate-700"
          >
            {PLANTS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        {gapData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={gapData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="period" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
              <Line type="monotone" dataKey="demand" stroke="#f59e0b" strokeWidth={2} dot={false} name="Demand" />
              <Line type="monotone" dataKey="capacity" stroke="#22c55e" strokeWidth={2} dot={false} name="Capacity" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-slate-500 text-sm">Loading demand data...</div>
        )}
        {demand && (
          <div className="flex gap-4 mt-2 text-xs text-slate-500">
            <span>{demand.total_forecasts} forecasts</span>
            <span>{demand.total_units.toLocaleString()} units</span>
            <span>{demand.capacity_gaps.filter((g) => g.status === 'shortfall').length} shortfalls</span>
          </div>
        )}
      </div>
    </div>
  );
}

function KPI({ label, value, warn }: { label: string; value: string | number; warn?: boolean }) {
  return (
    <div className="bg-slate-800 rounded-lg p-3">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`text-lg font-bold mt-1 ${warn ? 'text-red-400' : 'text-white'}`}>{value}</div>
    </div>
  );
}
