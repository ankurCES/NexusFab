import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type {
  AllocationPlan,
  AllocationResponse,
  NetworkFlowsResponse,
  NetworkReport,
} from '../types/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LineChart, Line, CartesianGrid } from 'recharts';

// Geographic positions for continental US map (viewBox 0 0 1000 600)
// Derived from lat/lon: x=(lon+125)/59*1000, y=(49-lat)/25*600
const GEO: Record<string, { cx: number; cy: number; city: string }> = {
  'PLT-001': { cx: 473, cy: 390, city: 'Arlington TX' },
  'PLT-002': { cx: 618, cy: 152, city: 'Burlington WI' },
  'PLT-003': { cx: 68,  cy: 273, city: 'Modesto CA' },
  'PLT-004': { cx: 339, cy: 222, city: 'Denver CO' },
  'PLT-005': { cx: 736, cy: 334, city: 'Gaffney SC' },
};

const CATEGORY_COLORS: Record<string, string> = {
  WATER: '#3b82f6',
  CONFECTIONERY: '#a855f7',
  DAIRY: '#22c55e',
  PET_FOOD: '#f59e0b',
  PREPARED_FOODS: '#ef4444',
};

const PLANTS = ['PLT-001', 'PLT-002', 'PLT-003', 'PLT-004', 'PLT-005'];

function routeColor(costPerPallet: number): string {
  if (costPerPallet <= 200) return '#22c55e';
  if (costPerPallet <= 350) return '#f59e0b';
  return '#ef4444';
}

export default function Network() {
  const [net, setNet] = useState<NetworkReport | null>(null);
  const [flows, setFlows] = useState<NetworkFlowsResponse | null>(null);
  const [alloc, setAlloc] = useState<AllocationResponse | null>(null);
  const [milp, setMilp] = useState<AllocationPlan | null>(null);
  const [milpLoading, setMilpLoading] = useState(false);
  const [showOptimized, setShowOptimized] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [demandPlant, setDemandPlant] = useState(PLANTS[0]);
  const [demand, setDemand] = useState<{ capacity_gaps: { period: string; demand: number; capacity: number }[] } | null>(null);
  const [allocCategory, setAllocCategory] = useState('WATER');

  useEffect(() => {
    setLoading(true);
    Promise.all([api.network(), api.networkFlows(), api.networkAllocation()])
      .then(([n, f, a]) => { setNet(n); setFlows(f); setAlloc(a); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    api.demand(demandPlant, 12).then(setDemand).catch(() => {});
  }, [demandPlant]);

  if (loading) return <div className="flex items-center justify-center min-h-screen text-slate-400 animate-pulse">Loading...</div>;
  if (error) return <div className="p-6 text-red-400">{error}</div>;
  if (!net) return null;

  const handleOptimize = () => {
    if (milp) { setShowOptimized(!showOptimized); return; }
    setMilpLoading(true);
    api.networkOptimize()
      .then((plan) => { setMilp(plan); setShowOptimized(true); })
      .catch(() => {})
      .finally(() => setMilpLoading(false));
  };

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

  const allocProducts = alloc?.products.filter((p) => p.category === allocCategory) ?? [];
  const activeAlloc = showOptimized && milp
    ? milp.allocation_by_plant
    : alloc?.allocation ?? {};

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

      {/* Geographic Network Map */}
      <div className="bg-slate-800 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-semibold text-white mb-1">Geographic Network Map</h3>
        <div className="flex gap-4 text-xs text-slate-500 mb-3">
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-green-500 inline-block" /> cheap ≤$200/t</span>
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-amber-400 inline-block" /> mid $200–350</span>
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-red-500 inline-block" /> expensive &gt;$350</span>
        </div>
        <GeoMap net={net} flows={flows} />
      </div>

      {/* Plant Capacity Cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mb-6">
        {net.plants.map((p) => {
          const summary = alloc?.plant_summary[p.plant_id];
          return (
            <CapacityCard
              key={p.plant_id}
              plantId={p.plant_id}
              utilization={p.utilization}
              oee={p.avg_oee}
              targetOee={summary?.target_oee ?? 78}
              capacityTons={p.capacity_tons}
              availableTons={p.available_tons}
              lines={summary?.lines ?? []}
              isBottleneck={p.plant_id === net.bottleneck}
            />
          );
        })}
      </div>

      {/* Allocation Table */}
      <div className="bg-slate-800 rounded-lg p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h3 className="text-sm font-semibold text-white">Allocation by Product</h3>
          <div className="flex items-center gap-2">
            <select
              value={allocCategory}
              onChange={(e) => setAllocCategory(e.target.value)}
              className="bg-slate-900 text-white text-xs rounded px-2 py-1 border border-slate-700"
            >
              {['WATER', 'CONFECTIONERY', 'DAIRY', 'PET_FOOD', 'PREPARED_FOODS'].map((c) => (
                <option key={c} value={c}>{c.replace('_', ' ')}</option>
              ))}
            </select>
            <button
              onClick={handleOptimize}
              disabled={milpLoading}
              className={`text-xs px-3 py-1 rounded border transition-colors ${
                showOptimized
                  ? 'bg-green-600 border-green-500 text-white'
                  : 'bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600'
              } disabled:opacity-50`}
            >
              {milpLoading ? 'Running MILP…' : showOptimized ? 'MILP Optimized' : 'Show Optimized'}
            </button>
          </div>
        </div>
        {milp && showOptimized && (
          <div className="flex gap-4 text-xs mb-3 bg-slate-900 rounded p-2">
            <span className="text-green-400 font-semibold">Savings: {milp.savings_pct}%</span>
            <span className="text-slate-400">MILP: ${milp.objective_usd.toLocaleString()}</span>
            <span className="text-slate-400">Greedy: ${milp.greedy_usd.toLocaleString()}</span>
            <span className="text-slate-500">Status: {milp.status}</span>
          </div>
        )}
        <AllocationTable
          products={allocProducts}
          plants={PLANTS}
          allocation={activeAlloc}
          plantSummary={alloc?.plant_summary ?? {}}
        />
      </div>

      {/* Transport Cost Summary */}
      {flows && (
        <div className="bg-slate-800 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white">Transport Cost Summary</h3>
            <div className="text-xs text-slate-400">
              Monthly est: <span className="text-white font-semibold">${flows.total_monthly_cost_usd.toLocaleString()}</span>
              <span className="ml-3 text-slate-500">{flows.active_routes} active routes</span>
            </div>
          </div>
          <FlowTable flows={flows.flows} />
        </div>
      )}

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

        {/* Demand chart */}
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
            <ResponsiveContainer width="100%" height={195}>
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
            <div className="text-slate-500 text-sm mt-4">Loading demand data...</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────

function KPI({ label, value, warn }: { label: string; value: string | number; warn?: boolean }) {
  return (
    <div className="bg-slate-800 rounded-lg p-3">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`text-lg font-bold mt-1 ${warn ? 'text-red-400' : 'text-white'}`}>{value}</div>
    </div>
  );
}

function GeoMap({
  net,
  flows,
}: {
  net: NetworkReport;
  flows: NetworkFlowsResponse | null;
}) {
  const W = 1000, H = 600, R = 28;
  const plantsById = Object.fromEntries(net.plants.map((p) => [p.plant_id, p]));

  const pairs: [string, string][] = [];
  const plantIds = net.plants.map((p) => p.plant_id);
  for (let i = 0; i < plantIds.length; i++) {
    for (let j = i + 1; j < plantIds.length; j++) {
      pairs.push([plantIds[i], plantIds[j]]);
    }
  }

  const flowMap: Record<string, (typeof flows)['flows'][0]> = {};
  if (flows) {
    for (const f of flows.flows) {
      flowMap[`${f.from_plant}|${f.to_plant}`] = f;
      flowMap[`${f.to_plant}|${f.from_plant}`] = f;
    }
  }

  return (
    <div className="relative">
      <style>{`
        @keyframes flowDash {
          from { stroke-dashoffset: 24; }
          to { stroke-dashoffset: 0; }
        }
        .flow-active { animation: flowDash 1.8s linear infinite; }
      `}</style>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 380, background: '#0f172a', borderRadius: 8 }}>
        {/* Faint US region outlines */}
        <rect x={0} y={0} width={W} height={H} rx={8} fill="#0f172a" />
        <text x={500} y={580} textAnchor="middle" fill="#1e293b" fontSize={11}>Continental United States</text>

        {/* Routes */}
        {pairs.map(([p1, p2]) => {
          const g1 = GEO[p1], g2 = GEO[p2];
          if (!g1 || !g2) return null;
          const flow = flowMap[`${p1}|${p2}`];
          const active = flow?.active ?? false;
          const color = flow ? routeColor(flow.cost_per_pallet) : '#334155';
          const vol = flow?.volume_tons ?? 0;
          const sw = active ? Math.max(2, Math.min(7, vol / 15)) : 1;
          return (
            <line
              key={`${p1}-${p2}`}
              x1={g1.cx} y1={g1.cy} x2={g2.cx} y2={g2.cy}
              stroke={color}
              strokeWidth={sw}
              strokeDasharray={active ? '12 6' : '4 4'}
              opacity={active ? 0.85 : 0.25}
              className={active ? 'flow-active' : undefined}
            />
          );
        })}

        {/* Plant nodes */}
        {net.plants.map((p) => {
          const geo = GEO[p.plant_id];
          if (!geo) return null;
          const util = p.utilization;
          const fill = util > 0.80 ? '#ef4444' : util < 0.60 ? '#22c55e' : '#3b82f6';
          const catColor = CATEGORY_COLORS[p.category] ?? '#94a3b8';
          return (
            <g key={p.plant_id}>
              {/* Outer ring = category color */}
              <circle cx={geo.cx} cy={geo.cy} r={R + 4} fill="none" stroke={catColor} strokeWidth={2} opacity={0.5} />
              <circle cx={geo.cx} cy={geo.cy} r={R} fill={fill} opacity={0.9} stroke="#1e293b" strokeWidth={2} />
              {/* Utilization arc */}
              <text x={geo.cx} y={geo.cy - 6} textAnchor="middle" fill="white" fontSize={9} fontWeight="bold">
                {p.plant_id.replace('PLT-00', 'P')}
              </text>
              <text x={geo.cx} y={geo.cy + 7} textAnchor="middle" fill="white" fontSize={9}>
                {Math.round(util * 100)}%
              </text>
              <text x={geo.cx} y={geo.cy + R + 14} textAnchor="middle" fill="#94a3b8" fontSize={9}>
                {geo.city}
              </text>
            </g>
          );
        })}

        {/* Legend */}
        <g transform="translate(820, 20)">
          <rect x={-4} y={-4} width={156} height={68} rx={4} fill="#1e293b" opacity={0.8} />
          <text x={0} y={10} fill="#94a3b8" fontSize={9} fontWeight="bold">UTILIZATION</text>
          {[['#22c55e', 'Under 60%'], ['#3b82f6', '60–80%'], ['#ef4444', 'Over 80%']].map(([c, label], i) => (
            <g key={i} transform={`translate(0, ${18 + i * 14})`}>
              <circle cx={5} cy={4} r={4} fill={c} opacity={0.85} />
              <text x={14} y={8} fill="#94a3b8" fontSize={9}>{label}</text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}

function CapacityCard({
  plantId,
  utilization,
  oee,
  targetOee,
  capacityTons,
  availableTons,
  lines,
  isBottleneck,
}: {
  plantId: string;
  utilization: number;
  oee: number;
  targetOee: number;
  capacityTons: number;
  availableTons: number;
  lines: { name: string; pct: number }[];
  isBottleneck: boolean;
}) {
  const util = Math.round(utilization * 100);
  const oeePct = Math.round(oee * 100);
  const oeeAlert = oeePct < targetOee;
  const utilAlert = utilization > 0.80;

  return (
    <div className={`bg-slate-900 rounded-lg p-3 border ${isBottleneck ? 'border-red-500/50' : 'border-slate-700'}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-white font-semibold text-sm">{plantId}</span>
        <div className="flex gap-1">
          {isBottleneck && <span className="text-xs bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded">BOTTLENECK</span>}
          {oeeAlert && <span className="text-xs bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">OEE↓</span>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-1 text-xs mb-3">
        <div>
          <div className="text-slate-400">Utilization</div>
          <div className={`font-bold ${utilAlert ? 'text-red-400' : 'text-white'}`}>{util}%</div>
        </div>
        <div>
          <div className="text-slate-400">OEE</div>
          <div className={`font-bold ${oeeAlert ? 'text-amber-400' : 'text-white'}`}>{oeePct}%</div>
        </div>
        <div>
          <div className="text-slate-400">Active Lines</div>
          <div className="text-white font-bold">{lines.length}</div>
        </div>
        <div>
          <div className="text-slate-400">Available</div>
          <div className="text-white font-bold">{availableTons.toFixed(0)} t/d</div>
        </div>
      </div>

      {/* Mini bar chart: capacity by line */}
      <div className="space-y-1">
        <div className="text-xs text-slate-500 mb-1">Line capacity</div>
        {lines.map((l) => (
          <div key={l.name} className="flex items-center gap-1">
            <div className="text-slate-500 text-xs w-16 truncate">{l.name.split('-').slice(-1)[0]}</div>
            <div className="flex-1 bg-slate-700 rounded-full h-1.5">
              <div
                className="h-1.5 rounded-full bg-blue-500"
                style={{ width: `${Math.round(l.pct * utilization)}%` }}
              />
            </div>
            <div className="text-slate-500 text-xs w-6 text-right">{Math.round(l.pct)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AllocationTable({
  products,
  plants,
  allocation,
  plantSummary,
}: {
  products: { sku: string; name: string; category: string }[];
  plants: string[];
  allocation: Record<string, Record<string, { volume: number; pct: number }>>;
  plantSummary: Record<string, { utilization: number; oee: number; target_oee: number }>;
}) {
  if (products.length === 0) return <div className="text-slate-500 text-sm">No products in this category.</div>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left">
            <th className="pb-2 pr-3 text-slate-400 font-medium">Product</th>
            {plants.map((pl) => {
              const s = plantSummary[pl];
              const over = s && s.utilization > 80;
              const under = s && s.utilization < 60;
              return (
                <th key={pl} className={`pb-2 px-2 text-center font-medium ${over ? 'text-red-400' : under ? 'text-green-400' : 'text-slate-400'}`}>
                  {pl.replace('PLT-00', 'P')}
                  {over && <span className="ml-1 text-red-500">↑</span>}
                  {under && <span className="ml-1 text-green-500">↓</span>}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {products.map((p) => {
            const row = allocation[p.sku] ?? {};
            return (
              <tr key={p.sku} className="border-t border-slate-700">
                <td className="py-1.5 pr-3 text-slate-300 max-w-[140px]">
                  <div className="truncate">{p.name}</div>
                  <div className="text-slate-500">{p.sku}</div>
                </td>
                {plants.map((pl) => {
                  const cell = row[pl];
                  const vol = cell?.volume ?? 0;
                  const pct = cell?.pct ?? 0;
                  if (vol === 0) return <td key={pl} className="py-1.5 px-2 text-center text-slate-600">—</td>;
                  const highlight = pct > 100 ? 'text-red-300' : pct < 50 ? 'text-amber-300' : 'text-slate-200';
                  return (
                    <td key={pl} className={`py-1.5 px-2 text-center ${highlight}`}>
                      <div className="font-medium">{vol.toLocaleString()}</div>
                      <div className="text-slate-500">{pct.toFixed(0)}%</div>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function FlowTable({ flows }: { flows: NetworkFlowsResponse['flows'] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-slate-400 text-left text-xs">
            <th className="pb-2">Route</th>
            <th className="pb-2 text-right">Volume (t)</th>
            <th className="pb-2 text-right">Cost/Pallet</th>
            <th className="pb-2 text-right">Transit (h)</th>
            <th className="pb-2 text-center">Cold Chain</th>
            <th className="pb-2 text-center">Status</th>
          </tr>
        </thead>
        <tbody>
          {flows.map((f) => (
            <tr key={f.route} className={`border-t border-slate-700 ${f.active ? 'text-slate-200' : 'text-slate-500'}`}>
              <td className="py-1.5 font-mono">{f.route}</td>
              <td className="py-1.5 text-right">{f.volume_tons > 0 ? f.volume_tons : '—'}</td>
              <td className="py-1.5 text-right" style={{ color: routeColor(f.cost_per_pallet) }}>
                ${f.cost_per_pallet.toLocaleString()}
              </td>
              <td className="py-1.5 text-right">{f.transit_hours}h</td>
              <td className="py-1.5 text-center">
                {f.cold_chain ? <span className="text-blue-400">❄</span> : <span className="text-slate-600">—</span>}
              </td>
              <td className="py-1.5 text-center">
                {f.active
                  ? <span className="text-xs bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">active</span>
                  : <span className="text-xs bg-slate-700 text-slate-500 px-1.5 py-0.5 rounded">potential</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
