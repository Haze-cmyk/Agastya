/* eslint-disable no-restricted-globals */
/**
 * Agastya Client-Side Web Worker Offline Optimization Fallback
 * Runs when the remote backend is waking up or completely unreachable.
 */

interface WorkerTaskMessage {
  type: 'START_OPTIMIZATION';
  payload: {
    cargo_demand_teu: number;
    route_distance_nm: number;
    max_delivery_days: number;
    emission_cap_tco2e: number;
    carbon_price_usd_per_tco2e: number;
    candidate_vessels: string[];
    candidate_fuels: string[];
    generations?: number;
    population_size?: number;
    seed?: number;
  };
}

const LOCAL_VESSELS: Record<string, { capacity: number; disp: number; v_min: number; v_max: number; mcr: number; exp: number; sfoc: number; c_hull: number }> = {
  Container_14000TEU: { capacity: 14000, disp: 165000, v_min: 10.0, v_max: 23.5, mcr: 58000, exp: 3.35, sfoc: 166.0, c_hull: 1.813 },
  Feeder_2500TEU: { capacity: 2500, disp: 38000, v_min: 8.0, v_max: 19.5, mcr: 16500, exp: 3.25, sfoc: 172.0, c_hull: 1.242 },
  Capesize_180000DWT: { capacity: 180000, disp: 208000, v_min: 7.5, v_max: 15.8, mcr: 18500, exp: 2.92, sfoc: 162.0, c_hull: 7.095 },
  Panamax_82000DWT: { capacity: 82000, disp: 96000, v_min: 7.0, v_max: 15.2, mcr: 9800, exp: 2.88, sfoc: 164.0, c_hull: 4.278 },
  VLCC_300000DWT: { capacity: 300000, disp: 352000, v_min: 8.0, v_max: 16.5, mcr: 27500, exp: 3.05, sfoc: 160.0, c_hull: 6.006 },
  Aframax_115000DWT: { capacity: 115000, disp: 136000, v_min: 7.5, v_max: 16.0, mcr: 13200, exp: 2.98, sfoc: 165.0, c_hull: 3.915 }
};

const LOCAL_FUELS: Record<string, { lhv: number; wtt: number; ttw: number; price: number; slip: number }> = {
  HFO: { lhv: 40.2, wtt: 13.5, ttw: 77.4, price: 550, slip: 0 },
  VLSFO: { lhv: 41.0, wtt: 14.1, ttw: 76.5, price: 620, slip: 0 },
  MGO: { lhv: 42.7, wtt: 15.0, ttw: 74.5, price: 850, slip: 0 },
  LNG: { lhv: 48.0, wtt: 18.5, ttw: 56.1, price: 700, slip: 0.022 },
  Methanol: { lhv: 19.9, wtt: 25.0, ttw: 30.0, price: 650, slip: 0 },
  Ammonia: { lhv: 18.6, wtt: 15.0, ttw: 0.0, price: 800, slip: 0.0004 },
  Hydrogen: { lhv: 120.0, wtt: 20.0, ttw: 0.0, price: 3500, slip: 0 }
};

function evaluateCandidateLocally(cand: any, spec: any) {
  const vSpec = LOCAL_VESSELS[cand.vessel_type] || LOCAL_VESSELS['Container_14000TEU'];
  const fSpec = LOCAL_FUELS[cand.fuel_type] || LOCAL_FUELS['VLSFO'];

  const speed = Math.max(vSpec.v_min, Math.min(vSpec.v_max, cand.speed_knots));
  const pCalm = vSpec.c_hull * Math.pow(speed, vSpec.exp);
  const weather = 1.0 + 0.0085 * (3 * 3);
  const power = Math.min(vSpec.mcr * 1.05, pCalm * weather * 1.05);

  const load = power / vSpec.mcr;
  const sfoc = vSpec.sfoc * (1.0 + 0.35 * Math.pow(load - 0.75, 2));

  const transitHours = spec.route_distance_nm / speed;
  const onewayFuelT = (power * sfoc * transitHours) / 1_000_000;

  const roundtripDays = (transitHours * 2 + 48) / 24;
  const roundtripsYear = Math.max(1, 350 / roundtripDays);
  const totalFleetTrips = roundtripsYear * cand.vessel_count;

  const annualFuelTonnes = onewayFuelT * 2 * totalFleetTrips;
  const fuelEnergyMJ = annualFuelTonnes * 1000 * fSpec.lhv;
  const wtwGHG = (fuelEnergyMJ * (fSpec.wtt + fSpec.ttw)) / 1_000_000;

  const fuelCost = annualFuelTonnes * fSpec.price;
  const carbonTax = wtwGHG * spec.carbon_price_usd_per_tco2e;
  const opex = cand.vessel_count * 350 * 10000;
  const totalCost = fuelCost + carbonTax + opex;

  const annualCapacity = cand.vessel_count * vSpec.capacity * roundtripsYear;
  const transitDays = transitHours / 24;

  const violations: string[] = [];
  if (annualCapacity < spec.cargo_demand_teu) {
    violations.push(`Capacity shortfall: ${Math.round(annualCapacity).toLocaleString()} vs required ${Math.round(spec.cargo_demand_teu).toLocaleString()}`);
  }
  if (transitDays > spec.max_delivery_days) {
    violations.push(`Transit delay: ${transitDays.toFixed(1)}d exceeds deadline ${spec.max_delivery_days}d`);
  }
  if (spec.emission_cap_tco2e > 0 && wtwGHG > spec.emission_cap_tco2e) {
    violations.push(`Emission cap exceeded: ${Math.round(wtwGHG).toLocaleString()} vs cap ${Math.round(spec.emission_cap_tco2e).toLocaleString()}`);
  }

  return {
    solution_id: `sol_local_${Math.random().toString(36).substring(2, 7)}`,
    vessel_type: cand.vessel_type,
    vessel_count: cand.vessel_count,
    speed_knots: speed,
    fuel_type: cand.fuel_type,
    shore_power_active: cand.shore_power_active,
    unit_capacity: vSpec.capacity,
    fuel_consumption_tonnes: Math.round(annualFuelTonnes),
    operating_cost_usd: Math.round(totalCost),
    lifecycle_ghg_tco2e: Math.round(wtwGHG),
    transit_days_oneway: Number(transitDays.toFixed(1)),
    annual_fleet_capacity: Math.round(annualCapacity),
    feasible: violations.length === 0,
    violations,
    metrics: {
      transit_days: Number(transitDays.toFixed(1)),
      total_fleet_capacity: Math.round(annualCapacity),
      annual_roundtrips: Math.round(totalFleetTrips),
      demand_satisfaction_ratio: Number((annualCapacity / Math.max(1, spec.cargo_demand_teu)).toFixed(2))
    }
  };
}

function dominates(a: any, b: any): boolean {
  return (
    a.fuel_consumption_tonnes <= b.fuel_consumption_tonnes &&
    a.operating_cost_usd <= b.operating_cost_usd &&
    a.lifecycle_ghg_tco2e <= b.lifecycle_ghg_tco2e &&
    (a.fuel_consumption_tonnes < b.fuel_consumption_tonnes ||
      a.operating_cost_usd < b.operating_cost_usd ||
      a.lifecycle_ghg_tco2e < b.lifecycle_ghg_tco2e)
  );
}

self.onmessage = (e: MessageEvent<WorkerTaskMessage>) => {
  if (e.data.type === 'START_OPTIMIZATION') {
    const spec = e.data.payload;
    const generations = spec.generations || 15;
    const popSize = spec.population_size || 20;
    const vessels = spec.candidate_vessels.length ? spec.candidate_vessels : ['Container_14000TEU'];
    const fuels = spec.candidate_fuels.length ? spec.candidate_fuels : ['VLSFO', 'LNG'];

    let archive: any[] = [];

    for (let gen = 1; gen <= generations; gen++) {
      const currentGenSols = [];
      for (let i = 0; i < popSize; i++) {
        const vType = vessels[Math.floor(Math.random() * vessels.length)];
        const vSpec = LOCAL_VESSELS[vType] || LOCAL_VESSELS['Container_14000TEU'];
        const vCount = Math.floor(Math.random() * 12) + 1;
        const speed = vSpec.v_min + Math.random() * (vSpec.v_max - vSpec.v_min);
        const fuel = fuels[Math.floor(Math.random() * fuels.length)];

        const cand = {
          vessel_type: vType,
          vessel_count: vCount,
          speed_knots: Number(speed.toFixed(1)),
          fuel_type: fuel,
          shore_power_active: Math.random() > 0.5
        };

        const evaluated = evaluateCandidateLocally(cand, spec);
        currentGenSols.push(evaluated);
      }

      // Update non-dominated archive
      const combined = [...archive, ...currentGenSols];
      const nonDom = combined.filter((candA, idxA) => {
        return !combined.some((candB, idxB) => idxA !== idxB && dominates(candB, candA));
      });

      // Dedup
      const unique = Array.from(new Map(nonDom.map(s => [`${s.vessel_type}_${s.vessel_count}_${s.speed_knots}_${s.fuel_type}`, s])).values());
      archive = unique.slice(0, 30);

      const progress = Math.min(100, Math.round((gen / generations) * 100));
      self.postMessage({
        type: 'PROGRESS',
        progress_percent: progress,
        current_generation: gen,
        total_generations: generations,
        pareto_front: archive
      });
    }

    self.postMessage({
      type: 'COMPLETED',
      pareto_front: archive
    });
  }
};
