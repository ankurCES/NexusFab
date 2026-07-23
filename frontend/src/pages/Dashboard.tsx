import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { DashboardResponse } from '../types/api';
import PlantMap from '../components/PlantMap';
import OEEGauge from '../components/OEEGauge';

export default function Dashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.dashboard(168)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading />;
  if (error) return <Error msg={error} />;
  if (!data) return null;

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">NexusFab Dashboard</h1>
          <p className="text-sm text-slate-400">
            {data.plant_count} plants &middot; Network OEE
          </p>
        </div>
        <OEEGauge value={data.network_oee} label="Network OEE" size={140} />
      </header>

      <section className="mb-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
          Plant Network
        </h2>
        <PlantMap
          plants={data.plants}
          onSelect={(id) => navigate(`/plant/${id}`)}
        />
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
          Plant OEE Overview
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {data.plants.map((p) => (
            <button
              key={p.plant_id}
              onClick={() => navigate(`/plant/${p.plant_id}`)}
              className="bg-slate-800 rounded-lg p-3 cursor-pointer hover:bg-slate-700 transition-colors"
            >
              <OEEGauge value={p.oee} label={p.plant_name} size={110} />
              <div className="mt-2 text-xs text-slate-500">
                Target: {Math.round(p.target_oee * 100)}%
              </div>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-slate-400 animate-pulse">Loading dashboard...</div>
    </div>
  );
}

function Error({ msg }: { msg: string }) {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 max-w-md">
        <p className="text-red-400 font-semibold">Failed to load</p>
        <p className="text-red-300 text-sm mt-1">{msg}</p>
        <p className="text-red-400/60 text-xs mt-2">
          Is the backend running on localhost:8000?
        </p>
      </div>
    </div>
  );
}
