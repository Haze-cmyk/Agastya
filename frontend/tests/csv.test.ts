import { describe, it, expect } from 'vitest';
import { parseTelemetryCSV } from '../src/lib/csv';

describe('CSV Parser', () => {
  it('parses valid telemetry data with standard decimal dots', () => {
    const csv = `speed_knots,displacement_tonnes,sea_state_beaufort,months_since_drydock,fuel_consumption_rate_t_per_day
18.5,160000,3,12,145.2
14.0,120000,4,6,85.4`;

    const { rows, errors } = parseTelemetryCSV(csv);
    expect(errors).toHaveLength(0);
    expect(rows).toHaveLength(2);
    expect(rows[0].speed_knots).toBe(18.5);
    expect(rows[0].displacement_tonnes).toBe(160000);
    expect(rows[0].fuel_consumption_rate_t_per_day).toBe(145.2);
  });

  it('handles European decimal commas (e.g. 18,5)', () => {
    const csv = `speed,displacement,sea,drydock,fuel
"18,5",160000,3,12,"145,2"
"14,0",120000,2,8,"85,0"`;

    const { rows, errors } = parseTelemetryCSV(csv);
    expect(errors).toHaveLength(0);
    expect(rows).toHaveLength(2);
    expect(rows[0].speed_knots).toBe(18.5);
    expect(rows[0].fuel_consumption_rate_t_per_day).toBe(145.2);
  });

  it('detects missing required columns and returns error', () => {
    const csv = `vessel_name,captain,destination
Voyager,Smith,Rotterdam`;

    const { rows, errors } = parseTelemetryCSV(csv);
    expect(rows).toHaveLength(0);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors[0]).toContain("Missing required columns");
  });

  it('ignores invalid or negative numerical rows', () => {
    const csv = `speed,fuel
-5.0,100.0
15.0,-20.0
18.0,120.0`;

    const { rows, errors } = parseTelemetryCSV(csv);
    expect(rows).toHaveLength(1);
    expect(rows[0].speed_knots).toBe(18.0);
    expect(errors.length).toBe(2);
  });
});
