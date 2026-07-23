import type {
  AllergenMatrix,
  AllocationPlan,
  AllocationResponse,
  CcpReport,
  ChangeoverMatrix,
  CipSchedule,
  ComplianceScore,
  DashboardResponse,
  DemandPlan,
  EquipmentInfo,
  EnergyOptimization,
  EnergyReport,
  FailureHistory,
  FlowGraph,
  HealthSummary,
  InventoryReport,
  KpiTrending,
  MaintenanceSchedule,
  NetworkFlowsResponse,
  NetworkReport,
  Plant,
  PlantLine,
  PlantOEE,
  PlantPredictions,
  ProductionKpis,
  ProductionSchedule,
  ScenarioResult,
  ScenarioSummary,
  ScheduleResponse,
  SensorHistory,
  SensorReadings,
  SequenceOptimizeResult,
  SparesStatusReport,
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
  complianceCcps: (plantId: string) => get<CcpReport>(`/compliance/${plantId}/ccps`),
  complianceAllergens: (plantId: string) => get<AllergenMatrix>(`/compliance/${plantId}/allergens`),
  complianceCip: (plantId: string) => get<CipSchedule>(`/compliance/${plantId}/cip-schedule`),
  complianceScore: (plantId: string) => get<ComplianceScore>(`/compliance/${plantId}/score`),
  productionSchedule: (plantId: string, days = 7) =>
    get<ProductionSchedule>(`/production/schedule/${plantId}?days=${days}`),
  optimizeSequence: (plantId: string, lineId = '') =>
    post<SequenceOptimizeResult>('/production/optimize-sequence', { plant_id: plantId, line_id: lineId }),
  changeoverMatrix: (category: string) =>
    get<ChangeoverMatrix>(`/production/changeover-matrix/${category}`),
  productionKpis: (plantId: string) =>
    get<ProductionKpis>(`/production/kpis/${plantId}`),
  networkFlows: () => get<NetworkFlowsResponse>('/network/flows'),
  networkAllocation: () => get<AllocationResponse>('/network/allocation'),
  networkOptimize: () => get<AllocationPlan>('/network/optimize'),
  maintenancePredictions: (plantId: string) => get<PlantPredictions>(`/maintenance/predictions/${plantId}`),
  maintenanceHistory: (plantId: string, days = 90) => get<FailureHistory>(`/maintenance/history/${plantId}?days=${days}`),
  sparesStatus: (plantId: string) => get<SparesStatusReport>(`/spares/status/${plantId}`),
  sensorEquipment: (plantId: string, lineId: string) =>
    get<EquipmentInfo[]>(`/sensors/${plantId}/${lineId}/equipment`),
  sensorReadings: (plantId: string, lineId: string, equipmentId: string) =>
    get<SensorReadings>(`/sensors/${plantId}/${lineId}/${equipmentId}`),
  sensorHistory: (equipmentId: string, hours = 24) =>
    get<SensorHistory>(`/sensors/${equipmentId}/history?hours=${hours}`),
  healthSummary: (plantId: string) => get<HealthSummary>(`/maintenance/health/${plantId}`),
};
