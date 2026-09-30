export type ConnectionStatus = 'online' | 'waking_up' | 'offline' | 'error';

export interface VesselSpec {
  vessel_type: string;
  category: string;
  name: string;
  capacity_value: number;
  capacity_unit: string;
  displacement_design_tonnes: number;
  displacement_light_tonnes: number;
  design_speed_knots: number;
  min_speed_knots: number;
  max_speed_knots: number;
  engine_mcr_kw: number;
  auxiliary_power_kw: number;
  auxiliary_port_power_kw: number;
  speed_exponent: number;
  base_sfoc_g_per_kwh: number;
  c_hull: number;
}

export interface FuelSpec {
  name: string;
  lhv_mj_per_kg: number;
  density_kg_per_m3: number;
  wtt_ghg_gco2e_per_mj: number;
  ttw_ghg_gco2e_per_mj: number;
  default_price_usd_per_tonne: number;
  methane_slip_fraction: number;
  n2o_slip_fraction: number;
  daily_boil_off_fraction: number;
  pilot_fuel_fraction: number;
  requires_cryo_tanks: boolean;
}

export interface PortSpec {
  port_id: string;
  name: string;
  country: string;
  available_fuels: string[];
  shore_power_available: boolean;
  grid_carbon_intensity_gco2e_per_kwh: number;
  shore_power_tariff_usd_per_kwh: number;
  port_fee_per_call_usd: number;
}

export interface CaseStudy {
  preset_id: string;
  title: string;
  category: string;
  description: string;
  cargo_demand: number;
  demand_unit: string;
  route_distance_nm: number;
  max_delivery_days: number;
  emission_cap_tco2e: number;
  carbon_price_usd_per_tco2e: number;
  candidate_vessels: string[];
  candidate_fuels: string[];
  origin_port: string;
  destination_port: string;
  allow_shore_power: boolean;
}

export interface FuelPredictionInput {
  vessel_type: string;
  speed_knots: number;
  displacement_tonnes?: number;
  sea_state_beaufort: number;
  months_since_drydock: number;
  distance_nm?: number;
  fuel_type: string;
}

export interface FuelPredictionResult {
  vessel_type: string;
  speed_knots: number;
  effective_speed_knots: number;
  displacement_tonnes: number;
  engine_power_kw: number;
  engine_load_fraction: number;
  sfoc_g_per_kwh: number;
  fuel_consumption_rate_t_per_day: number;
  total_fuel_tonnes: number;
  voyage_duration_hours: number;
  weather_added_resistance_factor: number;
  fouling_added_resistance_factor: number;
  lifecycle_ghg_tco2e?: number;
  warnings: string[];
}

export interface ModelMetric {
  rmse: number;
  mae: number;
  mape: number;
  r2: number;
  training_time_ms: number;
}

export interface TrainPredictorResponse {
  sample_count: number;
  vessel_type: string;
  models: Record<string, ModelMetric>;
}

export interface FleetOptimizationInput {
  algorithm: string;
  preset_id?: string;
  cargo_demand_teu: number;
  route_distance_nm: number;
  max_delivery_days: number;
  emission_cap_tco2e: number;
  carbon_price_usd_per_tco2e: number;
  candidate_vessels: string[];
  candidate_fuels: string[];
  origin_port: string;
  destination_port: string;
  allow_shore_power: boolean;
  generations: number;
  population_size: number;
  seed: number;
}

export interface ParetoSolution {
  solution_id?: string;
  vessel_type: string;
  vessel_count: number;
  speed_knots: number;
  fuel_type: string;
  shore_power_active: boolean;
  unit_capacity: number;
  fuel_consumption_tonnes: number;
  operating_cost_usd: number;
  lifecycle_ghg_tco2e: number;
  transit_days_oneway: number;
  annual_fleet_capacity: number;
  feasible: boolean;
  violations: string[];
  metrics?: {
    transit_days: number;
    total_fleet_capacity: number;
    annual_roundtrips: number;
    demand_satisfaction_ratio: number;
  };
}

export interface OptimizationJob {
  job_id: string;
  algorithm: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'TIMED_OUT';
  progress_percent: number;
  current_generation: number;
  total_generations: number;
  elapsed_seconds: number;
  pareto_front: ParetoSolution[];
  hypervolume: number;
  spread_metric: number;
  error_message?: string;
}

export interface ScenarioFuelDetail {
  fuel_name: string;
  annual_fuel_consumed_tonnes: number;
  lhv_mj_per_kg: number;
  wtt_ghg_tco2e: number;
  ttw_ghg_tco2e: number;
  methane_slip_tco2e: number;
  n2o_slip_tco2e: number;
  boil_off_tonnes: number;
  berth_ghg_tco2e: number;
  total_wtw_ghg_tco2e: number;
  fuel_cost_usd: number;
  carbon_tax_usd: number;
  berth_cost_usd: number;
  total_annual_cost_usd: number;
  requires_cryo_tanks: boolean;
}

export interface ScenarioComparison {
  vessel_type: string;
  annual_distance_nm: number;
  cruising_speed_knots: number;
  carbon_price_usd_per_tco2e: number;
  fuels_comparison: Record<string, ScenarioFuelDetail>;
}

export interface BenchmarkData {
  metadata: {
    title: string;
    runs_per_algorithm: number;
    generations: number;
    timestamp: string;
    demand_case: string;
  };
  solution_quality: Record<string, {
    hypervolume_mean: number;
    hypervolume_std: number;
    spacing_mean: number;
    spacing_std: number;
    convergence_generations_mean: number;
    convergence_generations_std: number;
    runtime_sec_mean: number;
    runtime_sec_std: number;
  }>;
  scalability_runtime_seconds: {
    fleet_sizes: number[];
    series: Record<string, number[]>;
  };
  convergence_trajectories: {
    generations: number[];
    curves: Record<string, number[]>;
  };
  prediction_accuracy: Record<string, ModelMetric>;
}
