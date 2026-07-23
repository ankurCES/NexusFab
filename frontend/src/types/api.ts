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
  pallets: number;
  transport_cost: number;
  transport_hours: number;
  cost_per_ton: number;
  cost_per_pallet: number;
}

export interface FlowNode {
  id: string;
  name: string;
  lat: number;
  lon: number;
  category: string;
  capacity_tons: number;
  utilization: number;
  status: 'normal' | 'overloaded' | 'underloaded';
}

export interface FlowEdge {
  source: string;
  target: string;
  flow_tons: number;
  cost: number;
  lead_time_hours: number;
  pallets: number;
  active: boolean;
}

export interface FlowGraph {
  nodes: FlowNode[];
  edges: FlowEdge[];
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
  flow_graph: FlowGraph;
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

// Scenarios
export interface ScenarioSummary {
  id: string;
  name: string;
  description: string;
  plant_id: string;
}

export interface ScenarioImpact {
  forced_failure: boolean;
  failure_downtime_minutes: number;
  demand_multiplier: number;
  capacity_gap_units: number;
  cip_extra_minutes: number;
  energy_rate_multiplier: number;
  workforce_availability: number;
}

export interface ScenarioResult {
  scenario: { id: string; name: string; description: string; plant_id: string };
  impact: ScenarioImpact;
  duration_hours: number;
  seed: number;
  plant_oee: number;
  total_units: number;
  total_failures: number;
  lines: { name: string; oee: number; availability: number; performance: number; quality: number }[];
}

// Energy Optimization
export interface EnergyScheduleSlot {
  equipment_type: string;
  plant_id: string;
  line: string;
  original_period: string;
  optimized_period: string;
  hours: number;
  kwh: number;
  baseline_cost: number;
  optimized_cost: number;
  savings: number;
}

export interface EnergyOptimization {
  plant_id: string;
  period_days: number;
  baseline_cost: number;
  optimized_cost: number;
  total_savings: number;
  savings_pct: number;
  total_kwh: number;
  kwh_by_line: Record<string, number>;
  tariff_schedule: { start: number; end: number; period: string; rate_multiplier: number }[];
  slots: EnergyScheduleSlot[];
}

// Analytics KPI
export interface KpiPeriod {
  period: number;
  oee: number;
  otif: number;
  waste_pct: number;
  total_units: number;
  failures: number;
  energy_kwh: number;
  energy_cost: number;
  energy_co2_kg: number;
  kwh_per_ton: number;
}

export interface KpiTrending {
  plant_id: string;
  periods: number;
  period_hours: number;
  trending: KpiPeriod[];
}

// Compliance & HACCP
export interface CcpStatus {
  id: string;
  name: string;
  parameter: string;
  unit: string;
  current_value: number;
  lower_limit: number;
  upper_limit: number;
  critical_lower: number;
  critical_upper: number;
  status: 'PASS' | 'WARN' | 'FAIL';
  compliance_rate_30d: number;
  last_checked: string;
}

export interface CcpReport {
  plant_id: string;
  ccps: CcpStatus[];
}

export interface AllergenProduct {
  sku: string;
  name: string;
  allergen_status: Record<string, 'CONTAINS' | 'MAY_CONTAIN' | 'FREE'>;
  is_current_production: boolean;
  next_changeover_cip_class: string | null;
}

export interface AllergenMatrix {
  plant_id: string;
  allergens: string[];
  products: AllergenProduct[];
}

export interface CipEvent {
  id: string;
  line: string;
  line_type: string;
  type: string;
  status: 'completed' | 'in_progress' | 'upcoming' | 'overdue';
  scheduled_start: string;
  actual_start: string | null;
  duration_minutes: number;
  is_uht_aseptic: boolean;
  hard_deadline: string | null;
}

export interface CipSchedule {
  plant_id: string;
  events: CipEvent[];
}

export interface ComplianceScore {
  plant_id: string;
  score: number;
  food_safety_score: number;
  allergen_score: number;
  documentation_score: number;
  trend: { date: string; score: number }[];
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

// Production scheduling & sequencing
export interface ScheduleBlock {
  type: 'production' | 'changeover';
  start: string;
  end: string;
  sku?: string;
  product?: string;
  category?: string;
  quantity?: number;
  order_id?: string;
  cip_type?: string;
  from_sku?: string;
  to_sku?: string;
  minutes?: number;
}

export interface LineSchedule {
  line: string;
  blocks: ScheduleBlock[];
}

export interface ProductionSchedule {
  plant_id: string;
  days: number;
  start: string;
  end: string;
  horizon_hours: number;
  total_changeover_minutes: number;
  lines: LineSchedule[];
}

export interface SequenceSolution {
  sequence: string[];
  total_changeover_min: number;
  effective_changeover_min: number;
  smed_savings_min: number;
  makespan: number;
  late_orders: string[];
  allergen_violations: number;
  cip_interval_warning: boolean;
  solver_status: string;
}

export interface SequenceOptimizeResult {
  plant_id: string;
  line_id: string;
  products: { sku: string; name: string }[];
  fifo: SequenceSolution;
  optimized: SequenceSolution;
  changeover_reduction_min: number;
  changeover_reduction_pct: number;
}

export interface ChangeoverEntry {
  from_sku: string;
  to_sku: string;
  minutes: number;
  cip_type: string;
  asymmetric: boolean;
}

export interface ChangeoverMatrix {
  plant_category: string;
  products: { sku: string; name: string; allergen_tier: number }[];
  matrix: ChangeoverEntry[];
  asymmetric_pairs: { from_sku: string; to_sku: string; a_to_b: number; b_to_a: number }[];
}

export interface LineKpi {
  line: string;
  oee: number;
  availability: number;
  performance: number;
  quality: number;
  right_first_time: number;
  changeover_pct: number;
  units_produced: number;
  units_target: number;
}

export interface ProductionKpis {
  plant_id: string;
  plant_name: string;
  duration_hours: number;
  plant_oee: number;
  total_units: number;
  lines: LineKpi[];
}

// Network Enhanced
export interface NetworkFlow {
  route: string;
  from_plant: string;
  to_plant: string;
  volume_tons: number;
  cost_usd: number;
  transit_hours: number;
  cold_chain: boolean;
  cost_per_pallet: number;
  active: boolean;
}

export interface NetworkFlowsResponse {
  flows: NetworkFlow[];
  total_monthly_cost_usd: number;
  active_routes: number;
}

export interface PlantLineCapacity {
  name: string;
  speed_upm: number;
  pct: number;
}

export interface PlantSummaryDetail {
  utilization: number;
  oee: number;
  target_oee: number;
  capacity_tons: number;
  available_tons: number;
  lines: PlantLineCapacity[];
}

export interface ProductInfo {
  sku: string;
  name: string;
  category: string;
  home_plant: string;
}

export interface AllocationCell {
  volume: number;
  pct: number;
}

export interface AllocationResponse {
  products: ProductInfo[];
  plants: string[];
  allocation: Record<string, Record<string, AllocationCell>>;
  plant_summary: Record<string, PlantSummaryDetail>;
}

export interface AllocationPlan {
  status: string;
  objective_usd: number;
  greedy_usd: number;
  savings_pct: number;
  gap_pct: number;
  solve_time_sec: number;
  cost_breakdown: { production: number; inventory: number; overtime: number };
  line_utilization: Record<string, number>;
  transport: TransferOption[];
  allocation_by_plant: Record<string, Record<string, AllocationCell>>;
}

// Predictive Maintenance
export interface EquipmentPrediction {
  equipment_name: string;
  equipment_type: string;
  rul_hours: number;
  health_index: number;
  anomaly_score: number;
  alert_level: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED';
  confidence: number;
  top_features: string[];
  line: string;
}

export interface PlantPredictions {
  plant_id: string;
  equipment: EquipmentPrediction[];
  summary: { RED: number; ORANGE: number; YELLOW: number; GREEN: number };
}

export interface FailureEvent {
  date: string;
  equipment: string;
  equipment_type: string;
  line: string;
  failure_mode: string;
  severity: 'minor' | 'major' | 'critical';
  mttr_hours: number;
  cost: number;
}

export interface FailureHistory {
  plant_id: string;
  days: number;
  total_events: number;
  events: FailureEvent[];
  by_week: { week: string; failures: number }[];
}

export interface SparePartDetail {
  part: string;
  equipment_type: string;
  unit_cost: number;
  on_hand: number;
  reorder_point: number;
  lead_time_days: number;
  abc_class: string;
  xyz_class: string;
  abc_xyz: string;
  policy: string;
  annual_demand: number;
  safety_stock: number;
  eoq: number;
  stockout_risk: number;
  needs_reorder: boolean;
  annual_cost: number;
  days_to_stockout: number;
}

export interface SparesStatusReport {
  plant_id: string;
  total_parts: number;
  inventory_value: number;
  needs_reorder: number;
  high_risk: number;
  by_abc: Record<string, number>;
  parts: SparePartDetail[];
}

// Sensors & live PdM
export interface EquipmentInfo {
  name: string;
  type: string;
}

export interface SensorReading {
  tag: string;
  sensor_type: string;
  value: number;
  unit: string;
  setpoint: number;
  sigma: number;
  quality: string;
  status: 'normal' | 'warning' | 'alarm';
}

export interface SensorReadings {
  plant_id: string;
  line_id: string;
  equipment_id: string;
  equipment_type: string;
  timestamp: number;
  readings: SensorReading[];
}

export interface SensorDataPoint {
  ts: number;
  value: number;
  quality: string;
  deviation: number;
}

export interface SensorSeries {
  tag: string;
  sensor_type: string;
  unit: string;
  setpoint: number;
  sigma: number;
  data: SensorDataPoint[];
}

export interface SensorHistory {
  equipment_id: string;
  equipment_type: string;
  hours: number;
  series: SensorSeries[];
  failure_events: { timestamp: number; tag: string; type: string }[];
}

export interface HealthSummary {
  plant_id: string;
  equipment: EquipmentPrediction[];
}
