import {
  FuelPredictionInput,
  FuelPredictionResult,
  TrainPredictorResponse,
  FleetOptimizationInput,
  OptimizationJob,
  ScenarioComparison,
  BenchmarkData,
  VesselSpec,
  FuelSpec,
  PortSpec,
  CaseStudy
} from '../types';

function resolveApiBase(): string {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim() !== '') {
    return envUrl.trim().replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined' && window.location) {
    const host = window.location.hostname;
    if (host !== 'localhost' && host !== '127.0.0.1') {
      return 'https://agastya-production-b60f.up.railway.app';
    }
  }
  return 'http://localhost:8000';
}

export const API_BASE = resolveApiBase();

export class ApiError extends Error {
  statusCode: number;
  details?: any;

  constructor(message: string, statusCode: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

async function requestWithRetry<T>(
  url: string,
  options: RequestInit = {},
  retries = 3,
  backoffMs = 1500,
  onColdStart?: (attempt: number) => void
): Promise<T> {
  let lastError: any = null;

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 20000);

      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {})
        }
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData: any = {};
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: response.statusText };
        }

        const msg = errorData.detail || errorData.message || (errorData.field_errors ? errorData.field_errors.join(', ') : `HTTP ${response.status}`);
        throw new ApiError(msg, response.status, errorData);
      }

      return (await response.json()) as T;
    } catch (err: any) {
      lastError = err;

      // Check if server is waking up (Failed to fetch or 502/503/504)
      const isNetworkError = err.name === 'TypeError' || err.name === 'AbortError' || err.message?.includes('Failed to fetch');
      const isColdStart = isNetworkError || (err.statusCode && [502, 503, 504].includes(err.statusCode));

      if (isColdStart && attempt < retries) {
        if (onColdStart) {
          onColdStart(attempt);
        }
        await new Promise((resolve) => setTimeout(resolve, backoffMs * attempt));
        continue;
      }

      throw err;
    }
  }

  throw lastError;
}

export const api = {
  async checkHealth(): Promise<{ status: string; version: string; uptime_seconds: number }> {
    return requestWithRetry<{ status: string; version: string; uptime_seconds: number }>(
      `${API_BASE}/health`,
      { method: 'GET' },
      2,
      1000
    );
  },

  async checkVersion(): Promise<{ name: string; version: string; min_client_version: string }> {
    return requestWithRetry<{ name: string; version: string; min_client_version: string }>(
      `${API_BASE}/api/version`,
      { method: 'GET' }
    );
  },

  async fetchVessels(): Promise<Record<string, VesselSpec>> {
    return requestWithRetry<Record<string, VesselSpec>>(`${API_BASE}/api/data/vessels`, { method: 'GET' });
  },

  async fetchFuels(): Promise<Record<string, FuelSpec>> {
    return requestWithRetry<Record<string, FuelSpec>>(`${API_BASE}/api/data/fuels`, { method: 'GET' });
  },

  async fetchPorts(): Promise<Record<string, PortSpec>> {
    return requestWithRetry<Record<string, PortSpec>>(`${API_BASE}/api/data/ports`, { method: 'GET' });
  },

  async fetchCaseStudies(): Promise<Record<string, CaseStudy>> {
    return requestWithRetry<Record<string, CaseStudy>>(`${API_BASE}/api/data/case-studies`, { method: 'GET' });
  },

  async predictFuel(input: FuelPredictionInput): Promise<FuelPredictionResult> {
    return requestWithRetry<FuelPredictionResult>(`${API_BASE}/api/predict`, {
      method: 'POST',
      body: JSON.stringify(input)
    });
  },

  async trainPredictor(sampleCount = 300, vesselType = 'Container_14000TEU', seed = 42): Promise<TrainPredictorResponse> {
    return requestWithRetry<TrainPredictorResponse>(`${API_BASE}/api/predict/train`, {
      method: 'POST',
      body: JSON.stringify({ sample_count: sampleCount, vessel_type: vesselType, seed })
    });
  },

  async launchOptimization(
    input: FleetOptimizationInput,
    onColdStart?: (attempt: number) => void,
    retries = 3,
    backoffMs = 2000
  ): Promise<{ job_id: string; status: string; message: string }> {
    return requestWithRetry<{ job_id: string; status: string; message: string }>(
      `${API_BASE}/api/optimize`,
      {
        method: 'POST',
        body: JSON.stringify(input)
      },
      retries,
      backoffMs,
      onColdStart
    );
  },

  async getJobStatus(jobId: string): Promise<OptimizationJob> {
    return requestWithRetry<OptimizationJob>(`${API_BASE}/api/jobs/${jobId}`, { method: 'GET' });
  },

  async cancelJob(jobId: string): Promise<{ job_id: string; status: string }> {
    return requestWithRetry<{ job_id: string; status: string }>(`${API_BASE}/api/jobs/${jobId}/cancel`, {
      method: 'POST'
    });
  },

  async compareScenarios(params: {
    vessel_type: string;
    annual_distance_nm: number;
    cruising_speed_knots: number;
    carbon_price_usd_per_tco2e: number;
    fuel_price_adjustments?: Record<string, number>;
  }): Promise<ScenarioComparison> {
    return requestWithRetry<ScenarioComparison>(`${API_BASE}/api/scenarios/compare`, {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  async getPrecomputedBenchmarks(): Promise<BenchmarkData> {
    return requestWithRetry<BenchmarkData>(`${API_BASE}/api/benchmark/precomputed`, { method: 'GET' });
  },

  async runLiveBenchmark(algorithms: string[], runs = 3, generations = 20, seed = 42): Promise<any> {
    return requestWithRetry<any>(`${API_BASE}/api/benchmark/run`, {
      method: 'POST',
      body: JSON.stringify({ algorithms, runs, generations, seed })
    });
  }
};
