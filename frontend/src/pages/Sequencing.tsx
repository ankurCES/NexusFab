import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type {
  ChangeoverMatrix,
  ProductionKpis,
  ProductionSchedule,
  SequenceOptimizeResult,
} from '../types/api';

const PLANTS = ['PLT-001', 'PLT-002', 'PLT-003', 'PLT-004', 'PLT-005'];

const PLANT_CATEGORIES: Record<string, string> = {
  'PLT-001': 'WATER',
  'PLT-002': 'CONFECTIONERY',
  'PLT-003': 'DAIRY',
  'PLT-004': 'PET_FOOD',
  'PLT-005': 'PREPARED_FOODS',
};

const CATEGORY_COLORS: Record<string, string> = {
  WATER: '#06b6d4',
  CONFECTIONERY: '#8b5cf6',
  DAIRY: '#3b82f6',
  PET_FOOD: '#f59e0b',
  PREPARED_FOODS: '#10b981',
  UNKNOWN: '#6366f1',
};

const CIP_CONFIG: Record<string, { color: string; label: string }> = {
  allergen:   { color: '#dc2626', label: 'Allergen CIP' },
  deep_clean: { color: '#b91c1c', label: 'Deep Clean' },
  standard:   { color: '#ca8a04', label: 'Standard CIP' },
  rinse:      { color: '#6b7280', label: 'Rinse' },
  none:       { color: '', label: 'None' },
};

// ── Gantt ───────────────────────────────────────────────────────────────────

function Gantt({ schedule }: { schedule: ProductionSchedule }) {
  const t0 = new Date(schedule.start).getTime();
  const span = new Date(schedule.end).getTime() - t0 || 1;

  const pct = (iso: string) => ((new Date(iso).getTime() - t0) / span) * 100;
  const width = (s: string, e: string) =>
    Math.max(((new Date(e).getTime() - new Date(s).getTime()) / span) * 100, 0.3);

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      {/* ponytail: overflow-x scroll instead of drag-pan; add pointer events if UX insufficient */}
      <div className="overflow-x-auto">
        <div className="min-w-[700px]">
          {schedule.lines.map(({ line, blocks }) => (
            <div key={line} className="flex items-center mb-2">
              <div className="w-28 text-xs text-slate-400 shrink-0 truncate pr-2">{line}</div>
              <div className="flex-1 relative h-7 bg-slate-900 rounded overflow-hidden">
                {blocks
                  .filter((b) => b.type === 'changeover' && b.cip_type && b.cip_type !== 'none')
                  .map((b, i) => {
                    const cfg = CIP_CONFIG[b.cip_type!] ?? CIP_CONFIG.rinse;
                    return (
                      <div
                        key={`co-${i}`}
                        className="absolute top-0 bottom-0"
                        style={{
                          left: `${pct(b.start)}%`,
                          width: `${width(b.start, b.end)}%`,
                          background: `repeating-linear-gradient(45deg,${cfg.color},${cfg.color} 3px,transparent 3px,transparent 6px)`,
                          opacity: 0.9,
                        }}
                        title={`${cfg.label}: ${b.from_sku} → ${b.to_sku} (${b.minutes?.toFixed(0)} min)`}
                      />
                    );
                  })}
                {blocks
                  .filter((b) => b.type === 'production')
                  .map((b, i) => {
                    const color = CATEGORY_COLORS[b.category ?? 'UNKNOWN'];
                    const w = width(b.start, b.end);
                    return (
                      <div
                        key={`p-${i}`}
                        className="absolute top-0.5 bottom-0.5 rounded text-[10px] text-white flex items-center px-1 overflow-hidden"
                        style={{ left: `${pct(b.start)}%`, width: `${w}%`, backgroundColor: color }}
                        title={`${b.product} (${b.quantity?.toLocaleString()} units)\n${b.start} → ${b.end}`}
                      >
                        {w > 5 ? b.sku : ''}
                      </div>
                    );
                  })}
              </div>
            </div>
          ))}

          {/* Time axis */}
          <div className="flex mt-1 ml-28 text-[10px] text-slate-500">
            <span>{new Date(schedule.start).toLocaleDateString()}</span>
            <span className="flex-1" />
            <span>+{schedule.days}d</span>
          </div>

          {/* Legend */}
          <div className="flex gap-4 mt-2 ml-28 flex-wrap">
            {Object.entries(CATEGORY_COLORS)
              .filter(([k]) => k !== 'UNKNOWN')
              .map(([cat, color]) => (
                <div key={cat} className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
                  <span className="text-[10px] text-slate-400">{cat.replace('_', ' ')}</span>
                </div>
              ))}
            {Object.entries(CIP_CONFIG)
              .filter(([k]) => k !== 'none')
              .map(([key, cfg]) => (
                <div key={key} className="flex items-center gap-1">
                  <div
                    className="w-3 h-3 rounded"
                    style={{
                      background: `repeating-linear-gradient(45deg,${cfg.color},${cfg.color} 3px,#334155 3px,#334155 6px)`,
                    }}
                  />
                  <span className="text-[10px] text-slate-400">{cfg.label}</span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Sequence optimizer panel ────────────────────────────────────────────────

function SequencePanel({
  result,
  onApply,
  applying,
  applied,
}: {
  result: SequenceOptimizeResult;
  onApply: () => void;
  applying: boolean;
  applied: boolean;
}) {
  const nameOf = Object.fromEntries(result.products.map((p) => [p.sku, p.name]));

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
          Sequence Optimizer
        </h2>
        <button
          onClick={onApply}
          disabled={applying || applied}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs rounded font-medium"
        >
          {applying ? 'Optimizing…' : applied ? '✓ Applied' : 'Apply Optimized'}
        </button>
      </div>

      {/* Metric comparison */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        {[
          { label: 'Changeover', fifo: result.fifo.total_changeover_min, opt: result.optimized.total_changeover_min, unit: 'min' },
          { label: 'Makespan', fifo: result.fifo.makespan, opt: result.optimized.makespan, unit: 'h' },
          { label: 'Late Orders', fifo: result.fifo.late_orders.length, opt: result.optimized.late_orders.length, unit: '' },
        ].map(({ label, fifo, opt, unit }) => (
          <div key={label} className="bg-slate-900 rounded p-2">
            <div className="text-[10px] text-slate-500 uppercase mb-1">{label}</div>
            <div className="text-xs text-slate-400">FIFO: {Number(fifo).toFixed(unit === 'h' ? 1 : 0)}{unit}</div>
            <div className={`text-xs font-semibold ${opt <= fifo ? 'text-green-400' : 'text-red-400'}`}>
              OPT: {Number(opt).toFixed(unit === 'h' ? 1 : 0)}{unit}
            </div>
          </div>
        ))}
      </div>

      {result.changeover_reduction_pct > 0 && (
        <div className="text-xs text-green-400 mb-3">
          ↓ {result.changeover_reduction_min} min ({result.changeover_reduction_pct}%) changeover saved
        </div>
      )}

      {/* Side-by-side sequences */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-[10px] text-slate-500 uppercase mb-1.5">FIFO</div>
          {result.fifo.sequence.map((sku, i) => (
            <div key={sku} className="flex items-center gap-1.5 mb-1">
              <span className="text-[10px] text-slate-600 w-4 shrink-0">{i + 1}.</span>
              <span className="text-xs text-slate-300 truncate" title={nameOf[sku]}>{nameOf[sku] ?? sku}</span>
            </div>
          ))}
        </div>
        <div>
          <div className="text-[10px] text-slate-500 uppercase mb-1.5">Optimized</div>
          {result.optimized.sequence.map((sku, i) => (
            <div key={sku} className="flex items-center gap-1.5 mb-1">
              <span className="text-[10px] text-slate-600 w-4 shrink-0">{i + 1}.</span>
              <span className="text-xs text-green-400 truncate" title={nameOf[sku]}>{nameOf[sku] ?? sku}</span>
            </div>
          ))}
          {result.optimized.allergen_violations > 0 && (
            <div className="text-[10px] text-red-400 mt-1.5">
              ⚠ {result.optimized.allergen_violations} allergen violation{result.optimized.allergen_violations > 1 ? 's' : ''}
            </div>
          )}
          {result.optimized.cip_interval_warning && (
            <div className="text-[10px] text-yellow-400 mt-1">⚠ UHT CIP interval warning</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Changeover matrix heatmap ───────────────────────────────────────────────

function ChangeoverHeatmap({ matrix }: { matrix: ChangeoverMatrix }) {
  const products = matrix.products;
  const maxMin = Math.max(...matrix.matrix.map((e) => e.minutes), 1);

  const getEntry = (fromSku: string, toSku: string) =>
    matrix.matrix.find((e) => e.from_sku === fromSku && e.to_sku === toSku);

  return (
    <div className="bg-slate-800 rounded-lg p-4 overflow-x-auto">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
          Changeover Matrix — {matrix.plant_category.replace('_', ' ')}
        </h2>
        <span className="text-[10px] text-yellow-400">
          {matrix.asymmetric_pairs.length} asymmetric pairs
        </span>
      </div>

      <table className="text-[10px] border-collapse">
        <thead>
          <tr>
            <th className="p-1 text-slate-500 font-normal text-left w-12">↓ / →</th>
            {products.map((p) => (
              <th key={p.sku} className="p-1 text-slate-400 font-normal w-14 text-center" title={p.name}>
                {p.sku}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {products.map((fromP) => (
            <tr key={fromP.sku}>
              <td className="p-1 text-slate-400 font-mono" title={fromP.name}>
                {fromP.sku}
              </td>
              {products.map((toP) => {
                if (fromP.sku === toP.sku) {
                  return (
                    <td key={toP.sku} className="p-1 bg-slate-900 text-center text-slate-600 w-14">
                      —
                    </td>
                  );
                }
                const entry = getEntry(fromP.sku, toP.sku);
                const mins = entry?.minutes ?? 0;
                const alpha = (mins / maxMin) * 0.85;
                return (
                  <td
                    key={toP.sku}
                    className={`p-1 text-center text-white w-14 ${entry?.asymmetric ? 'outline outline-1 outline-yellow-500' : ''}`}
                    style={{ backgroundColor: `rgba(220,38,38,${alpha})` }}
                    title={`${fromP.name} → ${toP.name}: ${mins} min (${entry?.cip_type ?? '—'})${entry?.asymmetric ? ' ⚡ asymmetric' : ''}`}
                  >
                    {mins}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flex gap-4 mt-3 items-center">
        <div className="flex items-center gap-1.5">
          <div
            className="w-16 h-3 rounded"
            style={{ background: 'linear-gradient(to right,rgba(220,38,38,0.05),rgba(220,38,38,0.85))' }}
          />
          <span className="text-[10px] text-slate-400">0 → {Math.round(maxMin)} min</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded outline outline-1 outline-yellow-500" style={{ backgroundColor: 'rgba(220,38,38,0.4)' }} />
          <span className="text-[10px] text-slate-400">Asymmetric (A→B ≠ B→A)</span>
        </div>
      </div>
    </div>
  );
}

// ── KPI cards ───────────────────────────────────────────────────────────────

function KpiCards({ kpis }: { kpis: ProductionKpis }) {
  const n = kpis.lines.length || 1;
  const avgCoPct = kpis.lines.reduce((s, l) => s + l.changeover_pct, 0) / n;
  const totalTarget = kpis.lines.reduce((s, l) => s + l.units_target, 0);
  const avgRft = kpis.lines.reduce((s, l) => s + l.right_first_time, 0) / n;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card label="Plant OEE" value={`${(kpis.plant_oee * 100).toFixed(1)}%`} highlight={kpis.plant_oee > 0.75} />
      <Card label="Changeover Time" value={`${avgCoPct.toFixed(1)}% of available`} />
      <Card
        label="Units vs Target"
        value={`${kpis.total_units.toLocaleString()} / ${totalTarget.toLocaleString()}`}
        highlight={totalTarget > 0 && kpis.total_units >= totalTarget * 0.9}
      />
      <Card label="Right First Time" value={`${(avgRft * 100).toFixed(1)}%`} highlight={avgRft > 0.93} />
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

// ── KPI by line table ────────────────────────────────────────────────────────

function KpiTable({ kpis }: { kpis: ProductionKpis }) {
  return (
    <div className="bg-slate-800 rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-900 text-slate-400 text-xs uppercase">
          <tr>
            <th className="px-4 py-2 text-left">Line</th>
            <th className="px-4 py-2 text-right">OEE</th>
            <th className="px-4 py-2 text-right">Avail</th>
            <th className="px-4 py-2 text-right">Perf</th>
            <th className="px-4 py-2 text-right">Quality</th>
            <th className="px-4 py-2 text-right">CO Time %</th>
            <th className="px-4 py-2 text-right">Units / Target</th>
          </tr>
        </thead>
        <tbody className="text-slate-300">
          {kpis.lines.map((l) => (
            <tr key={l.line} className="border-t border-slate-700">
              <td className="px-4 py-2 font-mono text-xs">{l.line}</td>
              <td className={`px-4 py-2 text-right font-semibold ${l.oee > 0.75 ? 'text-green-400' : l.oee > 0.60 ? 'text-yellow-400' : 'text-red-400'}`}>
                {(l.oee * 100).toFixed(1)}%
              </td>
              <td className="px-4 py-2 text-right">{(l.availability * 100).toFixed(1)}%</td>
              <td className="px-4 py-2 text-right">{(l.performance * 100).toFixed(1)}%</td>
              <td className="px-4 py-2 text-right">{(l.quality * 100).toFixed(1)}%</td>
              <td className="px-4 py-2 text-right">{l.changeover_pct.toFixed(1)}%</td>
              <td className="px-4 py-2 text-right text-xs">
                {l.units_produced.toLocaleString()} / {l.units_target.toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function Sequencing() {
  const [plant, setPlant] = useState('PLT-001');
  const [days, setDays] = useState(7);
  const [schedule, setSchedule] = useState<ProductionSchedule | null>(null);
  const [kpis, setKpis] = useState<ProductionKpis | null>(null);
  const [matrix, setMatrix] = useState<ChangeoverMatrix | null>(null);
  const [seqResult, setSeqResult] = useState<SequenceOptimizeResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [optimizing, setOptimizing] = useState(false);
  const [applied, setApplied] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError('');
    setApplied(false);
    const category = PLANT_CATEGORIES[plant] ?? 'WATER';
    Promise.all([
      api.productionSchedule(plant, days),
      api.productionKpis(plant),
      api.changeoverMatrix(category),
      api.optimizeSequence(plant),
    ])
      .then(([sched, k, mat, seq]) => {
        setSchedule(sched);
        setKpis(k);
        setMatrix(mat);
        setSeqResult(seq);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [plant, days]);

  const handleApply = () => {
    setOptimizing(true);
    api.optimizeSequence(plant)
      .then((r) => { setSeqResult(r); setApplied(true); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setOptimizing(false));
  };

  if (error) return <div className="p-6 text-red-400">{error}</div>;

  return (
    <div className="p-4 lg:p-6 max-w-screen-xl mx-auto">
      {/* Header */}
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Production Sequencing</h1>
          <p className="text-sm text-slate-400">Line schedule, changeover optimization &amp; KPIs</p>
        </div>
        <div className="flex gap-3">
          <div className="flex rounded overflow-hidden border border-slate-700">
            {[1, 7].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 text-xs ${days === d ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
              >
                {d === 1 ? '24h' : '7d'}
              </button>
            ))}
          </div>
          <select
            value={plant}
            onChange={(e) => setPlant(e.target.value)}
            className="bg-slate-800 text-white rounded px-3 py-1.5 text-sm border border-slate-700"
          >
            {PLANTS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
      </header>

      {loading ? (
        <div className="text-slate-400 animate-pulse">Loading production data…</div>
      ) : (
        <>
          {/* KPI summary */}
          {kpis && <KpiCards kpis={kpis} />}

          {/* Gantt */}
          {schedule && (
            <section className="mb-6">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-3">
                Line Schedule
              </h2>
              <Gantt schedule={schedule} />
            </section>
          )}

          {/* Optimizer + Heatmap */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {seqResult && (
              <SequencePanel
                result={seqResult}
                onApply={handleApply}
                applying={optimizing}
                applied={applied}
              />
            )}
            {matrix && <ChangeoverHeatmap matrix={matrix} />}
          </div>

          {/* KPI by line table */}
          {kpis && (
            <section>
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-3">
                OEE by Line
              </h2>
              <KpiTable kpis={kpis} />
            </section>
          )}
        </>
      )}
    </div>
  );
}
