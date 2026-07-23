export interface Plant {
  id: string;
  name: string;
  location: string;
  category: string;
  capacity_tons_per_day: number;
  line_count: number;
  lat: number;
  lon: number;
}

export interface PlantDashboard {
  plant_id: string;
  plant_name: string;
  category: string;
  location: string;
  oee: number;
  starting_oee: number;
  target_oee: number;
  total_lines: number;
  total_units: number;
  total_failures: number;
  worst_line: string | null;
  worst_oee: number | null;
  best_line: string | null;
  best_oee: number | null;
}

export interface DashboardResponse {
  network_oee: number;
  plant_count: number;
  plants: PlantDashboard[];
}

export interface PlantOEE {
  plant_id: string;
  plant_name: string;
  plant_oee: number;
  lines: LineOEE[];
  total_units: number;
  total_failures: number;
}

export interface LineOEE {
  name: string;
  oee: number;
  availability: number;
  performance: number;
  quality: number;
  units_produced: number;
  failures: number;
  downtime_minutes: number;
}

export interface ScheduleRun {
  order_id: string;
  line: string;
  sku: string;
  product: string;
  start: string;
  end: string;
  quantity: number;
  changeover_min: number;
  position: number;
}

export interface ScheduleResponse {
  plant_id: string;
  horizon_hours: number;
  total_runs: number;
  total_changeover_minutes: number;
  naive_changeover_minutes: number;
  improvement_pct: number;
  unscheduled_orders: string[];
  schedule: ScheduleRun[];
}

export interface PlantLine {
  name: string;
  line_type: string;
  speed_units_per_min: number;
  equipment_count: number;
}

// Maintenance
export interface MaintenanceAction {
  equipment: string;
  type: string;
  plant_id: string;
  line: string;
  action: string;
  scheduled: string;
  duration_hours: number;
  cost: number;
  priority: number;
  failure_prob: number;
  days_until_due: number;
}

export interface MaintenanceSchedule {
  plant_id: string;
  horizon_days: number;
  total_actions: number;
  total_cost: number;
  total_hours: number;
  by_priority: Record<number, number>;
  actions: MaintenanceAction[];
}

// Spare Parts
export interface SparePartStatus {
  part: string;
  equipment_type: string;
  unit_cost: number;
  on_hand: number;
  reorder_point: number;
  lead_time_days: number;
  abc_class: string;
  annual_demand: number;
  safety_stock: number;
  eoq: number;
  stockout_risk: number;
  needs_reorder: boolean;
  annual_cost: number;
}

export interface InventoryReport {
  plant_id: string;
  total_parts: number;
  inventory_value: number;
  needs_reorder: number;
  high_risk: number;
  by_abc: Record<string, number>;
  parts: SparePartStatus[];
}

// Network
export interface PlantCapacity {
  plant_id: string;
  name: string;
  category: string;
  capacity_tons: number;
  utilization: number;
  available_tons: number;
  lines: number;
  equipment: number;
  avg_oee: number;
}

export interface TransferOption {
  from: string;
  to: string;
  category: string;
  tons: number;
  transport_cost: number;
  transport_hours: number;
  cost_per_ton: number;
}

export interface NetworkReport {
  timestamp: string;
  network_capacity_tons: number;
  avg_utilization: number;
  avg_oee: number;
  bottleneck: string;
  plant_count: number;
  plants: PlantCapacity[];
  suggested_transfers: TransferOption[];
}

// Demand
export interface DemandForecast {
  sku: string;
  product: string;
  plant_id: string;
  period_start: string;
  period_end: string;
  forecast_units: number;
  lower_bound: number;
  upper_bound: number;
  seasonal_factor: number;
  trend_factor: number;
}

export interface CapacityGap {
  plant_id: string;
  plant: string;
  period: string;
  demand: number;
  capacity: number;
  gap: number;
  gap_pct: number;
  status: string;
}

export interface DemandPlan {
  horizon_weeks: number;
  total_forecasts: number;
  total_units: number;
  by_plant: Record<string, number>;
  capacity_gaps: CapacityGap[];
  forecasts: DemandForecast[];
}

// Workforce
export interface OperatorProfile {
  id: string;
  name: string;
  plant_id: string;
  shift: number;
  skills: Record<string, number>;
  skill_score: number;
  experience_years: number;
  cert_expires: string | null;
}

export interface ShiftCoverage {
  plant_id: string;
  shift: number;
  required: number;
  available: number;
  coverage_pct: number;
  avg_skill: number;
  gaps: string[];
}

export interface TrainingGap {
  operator: string;
  name: string;
  skill: string;
  current: number;
  required: number;
  priority: string;
}

export interface WorkforceReport {
  plant_id: string;
  total_operators: number;
  avg_skill_score: number;
  shift_coverage: ShiftCoverage[];
  training_gaps_count: number;
  training_gaps: TrainingGap[];
  operators: OperatorProfile[];
}

// Energy
export interface EquipmentEnergy {
  equipment: string;
  type: string;
  plant_id: string;
  line: string;
  kwh_per_hour: number;
  running_hours: number;
  total_kwh: number;
  cost: number;
  co2_kg: number;
}

export interface SavingsOpportunity {
  description: string;
  plant_id: string;
  equipment_type: string;
  annual_kwh_savings: number;
  annual_cost_savings: number;
  annual_co2_savings_kg: number;
  implementation_cost: number;
  payback_months: number;
  priority: string;
}

export interface EnergyReport {
  plant_id: string;
  period_days: number;
  total_kwh: number;
  total_cost: number;
  total_co2_kg: number;
  kwh_per_ton: number;
  by_equipment_type: Record<string, number>;
  savings_opportunities: SavingsOpportunity[];
  equipment_detail: EquipmentEnergy[];
}
