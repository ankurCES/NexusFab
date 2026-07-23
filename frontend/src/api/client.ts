import type {
  DashboardResponse,
  DemandPlan,
  EnergyOptimization,
  EnergyReport,
  FlowGraph,
  InventoryReport,
  KpiTrending,
  MaintenanceSchedule,
  NetworkReport,
  Plant,
  PlantLine,
  PlantOEE,
  ScenarioResult,
  ScenarioSummary,
  ScheduleResponse,
  WorkforceReport,
} from '../types/api';

const BASE = '/api';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  plants: () => get<Plant[]>('/plants'),
  dashboard: (hours = 168) => get<DashboardResponse>(`/metrics/dashboard?duration_hours=${hours}`),
  plantOee: (id: string, hours = 168) => get<PlantOEE>(`/oee/plant/${id}?duration_hours=${hours}`),
  plantLines: (id: string) => get<PlantLine[]>(`/plants/${id}/lines`),
  schedule: (plantId: string, nOrders = 20) =>
    post<ScheduleResponse>('/optimize/schedule', { plant_id: plantId, n_orders: nOrders }),
  maintenance: (plantId: string) => get<MaintenanceSchedule>(`/maintenance/schedule/${plantId}`),
  inventory: (plantId?: string) =>
    plantId ? get<InventoryReport>(`/maintenance/inventory/${plantId}`) : get<InventoryReport>('/maintenance/inventory'),
  network: () => get<NetworkReport>('/network/status'),
  networkFlow: () => get<FlowGraph>('/network/flow'),
  networkBalance: (utilizations: Record<string, number>, failedPlant?: string) =>
    post<NetworkReport>('/network/balance', { utilizations, failed_plant: failedPlant }),
  demand: (plantId: string, weeks = 12) => get<DemandPlan>(`/network/demand/${plantId}?weeks=${weeks}`),
  workforce: (plantId?: string) =>
    plantId ? get<WorkforceReport>(`/workforce/${plantId}`) : get<WorkforceReport>('/workforce'),
  energy: (plantId?: string, days = 30) =>
    plantId ? get<EnergyReport>(`/energy/${plantId}?days=${days}`) : get<EnergyReport>(`/energy?days=${days}`),
  energyOptimize: (plantId?: string, days = 30) =>
    post<EnergyOptimization>('/energy/optimize', { plant_id: plantId ?? null, period_days: days }),
  scenarios: () => get<ScenarioSummary[]>('/scenarios'),
  runScenario: (scenarioId: string) =>
    post<ScenarioResult>('/scenarios/run', { scenario_id: scenarioId }),
  runCustomScenario: (params: Record<string, unknown>) =>
    post<ScenarioResult>('/scenarios/custom', params),
  kpiTrending: (plantId?: string, periods = 6) =>
    post<KpiTrending>('/analytics/kpi', { plant_id: plantId ?? null, periods }),
};
