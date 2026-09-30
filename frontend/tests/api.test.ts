import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, ApiError, API_BASE } from '../src/lib/api';

describe('API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('checks health endpoint successfully', async () => {
    const mockHealth = { status: 'ok', version: '1.0.0', uptime_seconds: 120 };
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealth
    } as Response);

    const res = await api.checkHealth();
    expect(res.status).toBe('ok');
    expect(res.version).toBe('1.0.0');
  });

  it('translates 422 error details into ApiError', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({
        error: 'Validation Error',
        field_errors: ['speed_knots: Speed must be greater than or equal to 0']
      })
    } as Response);

    await expect(api.predictFuel({
      vessel_type: 'Container_14000TEU',
      speed_knots: -5,
      sea_state_beaufort: 3,
      months_since_drydock: 12,
      fuel_type: 'VLSFO'
    })).rejects.toThrow('speed_knots: Speed must be greater than or equal to 0');
  });

  it('triggers cold start callback when fetch fails', async () => {
    const onColdStart = vi.fn();
    vi.spyOn(global, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(api.launchOptimization({
      algorithm: 'QIEA',
      cargo_demand_teu: 50000,
      route_distance_nm: 10000,
      max_delivery_days: 30,
      emission_cap_tco2e: 100000,
      carbon_price_usd_per_tco2e: 80,
      candidate_vessels: ['Container_14000TEU'],
      candidate_fuels: ['VLSFO'],
      origin_port: 'CNSHA',
      destination_port: 'NLRTM',
      allow_shore_power: true,
      generations: 10,
      population_size: 10,
      seed: 42
    }, onColdStart, 2, 10)).rejects.toThrow('Failed to fetch');

    expect(onColdStart).toHaveBeenCalled();
  });
});
