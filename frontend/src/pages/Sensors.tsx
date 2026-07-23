import { useEffect, useRef, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api/client';
import type {
  EquipmentInfo,
  EquipmentPrediction,
  HealthSummary,
  Plant,
  PlantLine,
  SensorHistory,
  SensorReadings,
} from '../types/api';

const HISTORY_OPTS = [
  { label: '24h', hours: 24 },
  { label: '7d', hours: 168 },
  { label: '30d', hours: 720 },
];

const ALERT_CLS: Record<string, string> = {
  GREEN:  'bg-green-900/40 border border-green-700 text-green-300',
  YELLOW: 'bg-yellow-900/40 border border-yellow-700 text-yellow-300',
  ORANGE: 'bg-orange-900/40 border border-orange-700 text-orange-300',
  RED:    'bg-red-900/40 border border-red-700 text-red-400',
};

const STATUS_DOT: Record<string, string> = {
  normal:  'bg-green-500',
  warning: 'bg-yellow-400',
  alarm:   'bg-red-500',
};

function polar(cx: number, cy: number, r: number, deg: number): [number, number] {
  const rad = (deg * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
}

function Gauge({
  value, setpoint, sigma, unit, label, status,
}: {
  value: number; setpoint: number; sigma: number;
  unit: string; label: string; status: 'normal' | 'warning' | 'alarm';
}) {
  const min = setpoint - 3.5 * sigma;
  const max = setpoint + 3.5 * sigma;
  const pct = Math.max(0, Math.min(1, (value - min) / (max - min)));
  const sweepDeg = -135 + pct * 270;
  const [sx, sy] = polar(60, 60, 45, -135);
  const [tx, ty] = polar(60, 60, 45, 135);
  const [ex, ey] = polar(60, 60, 45, sweepDeg);
  const largeArc = pct > 0.5 ? 1 : 0;
  const color = status === 'alarm' ? '#ef4444' : status === 'warning' ? '#eab308' : '#22c55e';

  return (
    <svg width="120" height="105" viewBox="0 0 120 105">
      <path
        d={`M ${sx} ${sy} A 45 45 0 1 1 ${tx} ${ty}`}
        fill="none" stroke="#334155" strokeWidth="8" strokeLinecap="round"
      />
      <path
        d={`M ${sx} ${sy} A 45 45 0 ${largeArc} 1 ${ex} ${ey}`}
        fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
      />
      <text x="60" y="64" textAnchor="middle" fill="white" fontSize="13" fontWeight="bold">
        {value.toFixed(1)}
      </text>
      <text x="60" y="78" textAnchor="middle" fill="#94a3b8" fontSize="9">{unit}</text>
      <text x="60" y="93" textAnchor="middle" fill="#64748b" fontSize="9">{label}</text>
    </svg>
  );
}

function Sparkline({ data }: { data: { value: number }[] }) {
  if (!data.length) return <div className="h-9 w-full" />;
  return (
    <ResponsiveContainer width="100%" height={36}>
      <LineChart data={data}>
        <Line
          type="monotone" dataKey="value" stroke="#60a5fa"
          dot={false} strokeWidth={1.5} isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

function fmtTs(ts: number, hours: number): string {
  const d = new Date(ts * 1000);
  if (hours <= 24) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return d.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function Sensors() {
  const [plants, setPlants] = useState<Plant[]>([]);
  const [plant, setPlant] = useState('');
  const [lines, setLines] = useState<PlantLine[]>([]);
  const [line, setLine] = useState('');
  const [equipList, setEquipList] = useState<EquipmentInfo[]>([]);
  const [equip, setEquip] = useState('');
  const [readings, setReadings] = useState<SensorReadings | null>(null);
  const [health, setHealth] = useState<HealthSummary | null>(null);
  const [history, setHistory] = useState<SensorHistory | null>(null);
  const [histHours, setHistHours] = useState(24);
  const [activeSensor, setActiveSensor] = useState('');
  const [loading, setLoading] = useState(false);
  const [histLoading, setHistLoading] = useState(false);
  const [error, setError] = useState('');
  const [live, setLive] = useState(false);

  const equipRef = useRef(equip);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => { equipRef.current = equip; }, [equip]);

  // Load plants once
  useEffect(() => {
    api.plants().then(setPlants).catch((e) => setError(e.message));
  }, []);

  // Plant → lines + health
  useEffect(() => {
    if (!plant) { setLines([]); setLine(''); setEquipList([]); setEquip(''); setHealth(null); return; }
    api.plantLines(plant).then((ls) => { setLines(ls); setLine(''); setEquipList([]); setEquip(''); });
    api.healthSummary(plant).then(setHealth).catch(() => {});
  }, [plant]);

  // Line → equipment list
  useEffect(() => {
    if (!plant || !line) { setEquipList([]); setEquip(''); return; }
    api.sensorEquipment(plant, line).then((eq) => { setEquipList(eq); setEquip(''); });
  }, [plant, line]);

  // Equipment → current readings
  useEffect(() => {
    if (!plant || !line || !equip) { setReadings(null); return; }
    setLoading(true);
    setError('');
    api.sensorReadings(plant, line, equip)
      .then((r) => { setReadings(r); setActiveSensor(r.readings[0]?.sensor_type ?? ''); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [plant, line, equip]);

  // Equipment + hours → history
  useEffect(() => {
    if (!equip) { setHistory(null); return; }
    setHistLoading(true);
    api.sensorHistory(equip, histHours)
      .then(setHistory)
      .catch(() => {})
      .finally(() => setHistLoading(false));
  }, [equip, histHours]);

  // SSE live updates per plant
  useEffect(() => {
    if (esRef.current) { esRef.current.close(); esRef.current = null; }
    if (!plant) { setLive(false); return; }

    const es = new EventSource(`/api/sensors/stream/${plant}`);
    esRef.current = es;
    es.onopen = () => setLive(true);
    es.onerror = () => setLive(false);
    es.onmessage = (evt) => {
      const currentEquip = equipRef.current;
      if (!currentEquip) return;
      try {
        const data = JSON.parse(evt.data) as {
          timestamp: number;
          readings: { tag: string; value: number; quality: string }[];
        };
        const relevant = data.readings.filter((r) => r.tag.split('.')[2] === currentEquip);
        if (!relevant.length) return;
        setReadings((prev) => {
          if (!prev) return prev;
          const updated = prev.readings.map((r) => {
            const lr = relevant.find((x) => x.tag === r.tag);
            return lr ? { ...r, value: lr.value, quality: lr.quality } : r;
          });
          return { ...prev, readings: updated, timestamp: data.timestamp };
        });
      } catch { /* ignore parse errors */ }
    };
    return () => { es.close(); esRef.current = null; setLive(false); };
  }, [plant]);

  const activeSeries = history?.series.find((s) => s.sensor_type === activeSensor);
  const chartData = activeSeries?.data.map((pt) => ({
    ts: pt.ts,
    value: pt.value,
    deviation: pt.deviation,
    label: fmtTs(pt.ts, histHours),
  })) ?? [];

  const selectCls = 'bg-slate-800 text-white rounded px-3 py-2 text-sm border border-slate-700';

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <header className="flex flex-wrap items-center gap-3 mb-6">
        <div className="flex-1 min-w-48">
          <h1 className="text-2xl font-bold text-white">Sensor Dashboard</h1>
          <p className="text-sm text-slate-400">
            Live readings · PdM health · Trend analysis
            {live && (
              <span className="ml-2 inline-flex items-center gap-1 text-green-400">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse inline-block" />
                Live
              </span>
            )}
          </p>
        </div>
        <select value={plant} onChange={(e) => setPlant(e.target.value)} className={selectCls}>
          <option value="">Select plant…</option>
          {plants.map((p) => <option key={p.id} value={p.id}>{p.id} — {p.name}</option>)}
        </select>
        <select value={line} onChange={(e) => setLine(e.target.value)} className={selectCls} disabled={!plant}>
          <option value="">Select line…</option>
          {lines.map((l) => <option key={l.name} value={l.name}>{l.name}</option>)}
        </select>
        <select value={equip} onChange={(e) => setEquip(e.target.value)} className={selectCls} disabled={!line}>
          <option value="">Select equipment…</option>
          {equipList.map((e) => <option key={e.name} value={e.name}>{e.name} ({e.type})</option>)}
        </select>
      </header>

      {error && <div className="mb-4 p-3 bg-red-900/40 text-red-300 rounded text-sm">{error}</div>}

      {/* Live readings */}
      {equip && (
        <section className="mb-6">
          <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
            Live Sensor Readings
            {loading && <span className="ml-2 text-slate-500 animate-pulse">Loading…</span>}
          </h2>
          {readings && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {readings.readings.map((r) => {
                const sparkData = (
                  history?.series.find((s) => s.sensor_type === r.sensor_type)?.data ?? []
                ).slice(-12).map((pt) => ({ value: pt.value }));

                return (
                  <button
                    key={r.tag}
                    onClick={() => setActiveSensor(r.sensor_type)}
                    className={`bg-slate-800 rounded-lg p-3 text-left transition-colors hover:bg-slate-700 ${
                      activeSensor === r.sensor_type ? 'ring-2 ring-blue-500' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-400 font-mono">{r.sensor_type}</span>
                      <span className={`w-2 h-2 rounded-full ${STATUS_DOT[r.status]}`} />
                    </div>
                    <div className="flex justify-center my-1">
                      <Gauge
                        value={r.value}
                        setpoint={r.setpoint}
                        sigma={r.sigma}
                        unit={r.unit}
                        label={r.quality}
                        status={r.status}
                      />
                    </div>
                    <Sparkline data={sparkData} />
                    <div className="text-xs text-slate-500 text-center mt-1">
                      SP: {r.setpoint.toFixed(1)} ±{(r.sigma * 2).toFixed(1)}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </section>
      )}

      {/* Equipment health overview */}
      {health && health.equipment.length > 0 && (
        <section className="mb-6">
          <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
            Equipment Health — {health.plant_id}
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {health.equipment.map((eq: EquipmentPrediction) => (
              <div key={eq.equipment_name} className={`rounded-lg p-3 ${ALERT_CLS[eq.alert_level]}`}>
                <div className="font-mono text-xs font-semibold mb-1 truncate">{eq.equipment_name}</div>
                <div className="text-xs opacity-70 mb-2">{eq.line} · {eq.equipment_type}</div>
                <div className="flex items-end justify-between">
                  <div>
                    <div className="text-lg font-bold">{(eq.health_index * 100).toFixed(0)}%</div>
                    <div className="text-xs opacity-70">health</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold">{eq.rul_hours.toFixed(0)}h</div>
                    <div className="text-xs opacity-70">RUL</div>
                  </div>
                </div>
                <div className="mt-2 h-1.5 bg-black/30 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      eq.alert_level === 'RED' ? 'bg-red-400' :
                      eq.alert_level === 'ORANGE' ? 'bg-orange-400' :
                      eq.alert_level === 'YELLOW' ? 'bg-yellow-400' : 'bg-green-400'
                    }`}
                    style={{ width: `${eq.health_index * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Sensor history chart */}
      {equip && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
              Sensor History — {activeSensor || '(select a sensor above)'}
            </h2>
            <div className="flex gap-1">
              {HISTORY_OPTS.map((o) => (
                <button
                  key={o.hours}
                  onClick={() => setHistHours(o.hours)}
                  className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                    histHours === o.hours
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>

          {histLoading ? (
            <div className="bg-slate-800 rounded-lg p-8 text-center text-slate-400 animate-pulse">
              Loading history…
            </div>
          ) : activeSeries ? (
            <div className="bg-slate-800 rounded-lg p-4">
              {/* Main value chart */}
              <div className="mb-1 text-xs text-slate-400">
                {activeSeries.sensor_type} ({activeSeries.unit})
                {' · '}SP {activeSeries.setpoint.toFixed(1)} ±2σ {(activeSeries.sigma * 2).toFixed(1)}
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="label" tick={{ fill: '#64748b', fontSize: 10 }}
                    interval="preserveStartEnd" tickLine={false}
                  />
                  <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} width={55} />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 6 }}
                    labelStyle={{ color: '#94a3b8', fontSize: 11 }}
                    itemStyle={{ color: '#60a5fa', fontSize: 12 }}
                  />
                  {/* Setpoint + sigma bands */}
                  <ReferenceLine y={activeSeries.setpoint} stroke="#475569" strokeDasharray="4 2" />
                  <ReferenceLine y={activeSeries.setpoint + 2 * activeSeries.sigma} stroke="#854d0e" strokeDasharray="3 3" />
                  <ReferenceLine y={activeSeries.setpoint - 2 * activeSeries.sigma} stroke="#854d0e" strokeDasharray="3 3" />
                  <ReferenceLine y={activeSeries.setpoint + 3 * activeSeries.sigma} stroke="#7f1d1d" strokeDasharray="3 3" />
                  <ReferenceLine y={activeSeries.setpoint - 3 * activeSeries.sigma} stroke="#7f1d1d" strokeDasharray="3 3" />
                  {/* Failure event markers */}
                  {history?.failure_events.map((fe, i) => (
                    <ReferenceLine
                      key={i} x={fmtTs(fe.timestamp, histHours)}
                      stroke="#ef4444" strokeWidth={2} label={{ value: '⚠', fill: '#ef4444', fontSize: 12 }}
                    />
                  ))}
                  <Line
                    type="monotone" dataKey="value" stroke="#60a5fa"
                    dot={false} strokeWidth={1.5} isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>

              {/* Anomaly deviation score */}
              <div className="mt-3 border-t border-slate-700 pt-3">
                <div className="text-xs text-slate-500 mb-1">Anomaly deviation (0 = normal, 1 = alarm)</div>
                <ResponsiveContainer width="100%" height={70}>
                  <LineChart data={chartData} margin={{ top: 2, right: 8, left: 0, bottom: 0 }}>
                    <XAxis dataKey="label" hide />
                    <YAxis domain={[0, 1]} tick={{ fill: '#64748b', fontSize: 9 }} tickLine={false} axisLine={false} width={30} ticks={[0, 0.5, 1]} />
                    <ReferenceLine y={0.67} stroke="#eab308" strokeDasharray="3 3" />
                    <ReferenceLine y={1.0} stroke="#ef4444" strokeDasharray="3 3" />
                    <Line
                      type="monotone" dataKey="deviation" stroke="#f97316"
                      dot={false} strokeWidth={1.5} isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            !histLoading && equip && (
              <div className="bg-slate-800 rounded-lg p-8 text-center text-slate-500 text-sm">
                Select a sensor card above to view its history.
              </div>
            )
          )}
        </section>
      )}

      {!plant && (
        <div className="mt-12 text-center text-slate-500">
          <div className="text-4xl mb-3">📡</div>
          <div>Select a plant to begin</div>
        </div>
      )}
    </div>
  );
}
