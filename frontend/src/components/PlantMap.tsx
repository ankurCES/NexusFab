import type { PlantDashboard } from '../types/api';

function oeeColor(val: number): string {
  if (val >= 0.75) return 'bg-green-500';
  if (val >= 0.60) return 'bg-yellow-500';
  return 'bg-red-500';
}

function categoryIcon(cat: string): string {
  switch (cat) {
    case 'WATER': return '💧';
    case 'DAIRY': return '🥛';
    case 'PET_FOOD': return '🐾';
    case 'CONFECTIONERY': return '🍫';
    case 'COFFEE': return '☕';
    case 'PREPARED_FOODS': return '🍽️';
    default: return '🏭';
  }
}

interface Props {
  plants: PlantDashboard[];
  onSelect: (plantId: string) => void;
  selectedId?: string;
}

export default function PlantMap({ plants, onSelect, selectedId }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
      {plants.map((p) => (
        <button
          key={p.plant_id}
          onClick={() => onSelect(p.plant_id)}
          className={`rounded-lg p-4 text-left transition-all cursor-pointer
            ${selectedId === p.plant_id
              ? 'bg-slate-700 ring-2 ring-blue-500'
              : 'bg-slate-800 hover:bg-slate-700'}`}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">{categoryIcon(p.category)}</span>
            <span className="font-semibold text-sm text-white truncate">{p.plant_name}</span>
          </div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`w-2.5 h-2.5 rounded-full ${oeeColor(p.oee)}`} />
            <span className="text-lg font-bold text-white">{Math.round(p.oee * 100)}%</span>
            <span className="text-xs text-slate-400">OEE</span>
          </div>
          <div className="text-xs text-slate-400">
            {p.total_lines} lines · {p.location}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {p.total_units.toLocaleString()} units · {p.total_failures} failures
          </div>
        </button>
      ))}
    </div>
  );
}
