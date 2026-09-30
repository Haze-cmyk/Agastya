import { ParetoSolution } from '../types';

export function exportParetoToCSV(solutions: ParetoSolution[], filename = 'agastya_pareto_front.csv'): void {
  if (!solutions || solutions.length === 0) return;

  const headers = [
    'Solution_ID',
    'Vessel_Type',
    'Vessel_Count',
    'Speed_Knots',
    'Fuel_Type',
    'Shore_Power',
    'Annual_Fuel_Tonnes',
    'Annual_Operating_Cost_USD',
    'Annual_Lifecycle_GHG_tCO2e',
    'Transit_Days_Oneway',
    'Annual_Fleet_Capacity',
    'Feasible',
    'Violations'
  ];

  const rows = solutions.map((s, idx) => [
    s.solution_id || `sol_${idx + 1}`,
    s.vessel_type,
    s.vessel_count,
    s.speed_knots.toFixed(2),
    s.fuel_type,
    s.shore_power_active ? 'YES' : 'NO',
    s.fuel_consumption_tonnes.toFixed(1),
    s.operating_cost_usd.toFixed(0),
    s.lifecycle_ghg_tco2e.toFixed(1),
    s.transit_days_oneway.toFixed(1),
    s.annual_fleet_capacity.toFixed(0),
    s.feasible ? 'TRUE' : 'FALSE',
    `"${(s.violations || []).join('; ')}"`
  ]);

  const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  downloadBlob(csvContent, filename, 'text/csv;charset=utf-8;');
}

export function exportJsonToFile(data: any, filename = 'agastya_data.json'): void {
  const jsonContent = JSON.stringify(data, null, 2);
  downloadBlob(jsonContent, filename, 'application/json');
}

function downloadBlob(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export interface ParsedTelemetryRow {
  speed_knots: number;
  displacement_tonnes: number;
  sea_state_beaufort: number;
  months_since_drydock: number;
  fuel_consumption_rate_t_per_day: number;
}

function splitCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim().replace(/^"|"$/g, ''));
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim().replace(/^"|"$/g, ''));
  return result;
}

export function parseTelemetryCSV(csvText: string): { rows: ParsedTelemetryRow[]; errors: string[] } {
  const lines = csvText.split(/\r?\n/).filter(line => line.trim().length > 0);
  const errors: string[] = [];
  const rows: ParsedTelemetryRow[] = [];

  if (lines.length < 2) {
    return { rows: [], errors: ['CSV contains no data rows.'] };
  }

  const rawHeaders = splitCSVLine(lines[0]).map(h => h.trim().toLowerCase());

  const getExactOrIncludes = (aliases: string[]) => {
    // First try exact matches
    const exact = rawHeaders.findIndex(h => aliases.includes(h));
    if (exact !== -1) return exact;
    // Then partial
    return rawHeaders.findIndex(h => aliases.some(a => h.includes(a)));
  };

  const speedIdx = getExactOrIncludes(['speed_knots', 'speed', 'sog', 'knots']);
  const dispIdx = getExactOrIncludes(['displacement_tonnes', 'displacement', 'disp', 'draft', 'weight']);
  const seaIdx = getExactOrIncludes(['sea_state_beaufort', 'sea_state', 'beaufort', 'sea', 'wave']);
  const foulIdx = getExactOrIncludes(['months_since_drydock', 'drydock', 'fouling']);
  const fuelIdx = getExactOrIncludes(['fuel_consumption_rate_t_per_day', 'fuel_consumption', 'fuel_rate', 'fuel']);

  if (speedIdx === -1 || fuelIdx === -1) {
    errors.push("Missing required columns: CSV must contain 'speed' and 'fuel' columns.");
    return { rows: [], errors };
  }

  for (let i = 1; i < lines.length; i++) {
    const rawCols = splitCSVLine(lines[i]);
    if (rawCols.length < rawHeaders.length) continue;

    const parseNum = (val: string, fallback = 0): number => {
      if (!val) return fallback;
      const normalized = val.replace(',', '.');
      const num = parseFloat(normalized);
      return isNaN(num) ? fallback : num;
    };

    const speed = parseNum(rawCols[speedIdx]);
    const fuel = parseNum(rawCols[fuelIdx]);
    const disp = dispIdx !== -1 ? parseNum(rawCols[dispIdx], 100000) : 100000;
    const sea = seaIdx !== -1 ? Math.round(parseNum(rawCols[seaIdx], 3)) : 3;
    const foul = foulIdx !== -1 ? Math.round(parseNum(rawCols[foulIdx], 12)) : 12;

    if (speed <= 0 || fuel <= 0) {
      errors.push(`Row ${i + 1}: Non-positive speed or fuel ignored.`);
      continue;
    }

    rows.push({
      speed_knots: speed,
      displacement_tonnes: disp,
      sea_state_beaufort: Math.min(12, Math.max(0, sea)),
      months_since_drydock: Math.max(0, foul),
      fuel_consumption_rate_t_per_day: fuel
    });
  }

  return { rows, errors };
}
