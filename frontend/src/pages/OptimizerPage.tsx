import React, { useState, useEffect, useRef } from 'react';
import { api, ApiError } from '../lib/api';
import { exportParetoToCSV, exportJsonToFile } from '../lib/csv';
import { FleetOptimizationInput, ParetoSolution, OptimizationJob } from '../types';
import { ParetoFrontChart } from '../charts/ParetoFrontChart';
import { Play, Square, Download, Save, AlertTriangle } from 'lucide-react';

interface OptimizerPageProps {
  isLocalMode: boolean;
  onTriggerColdStart: (attempt: number) => void;
  presetToLoad?: any;
}

const LOCAL_STORAGE_KEY = 'agastya_optimizer_input';

export const OptimizerPage: React.FC<OptimizerPageProps> = ({
  isLocalMode,
  onTriggerColdStart,
  presetToLoad
}) => {
  const [inputs, setInputs] = useState<FleetOptimizationInput>(() => {
    const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {}
    }
    return {
      algorithm: 'QIEA',
      cargo_demand_teu: 50000,
      route_distance_nm: 11500,
      max_delivery_days: 28,
      emission_cap_tco2e: 120000,
      carbon_price_usd_per_tco2e: 85,
      candidate_vessels: ['Container_14000TEU', 'Feeder_2500TEU'],
      candidate_fuels: ['VLSFO', 'LNG', 'Methanol', 'Ammonia'],
      origin_port: 'CNSHA',
      destination_port: 'NLRTM',
      allow_shore_power: true,
      generations: 35,
      population_size: 25,
      seed: 42
    };
  });

  const [activeJob, setActiveJob] = useState<OptimizationJob | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [selectedSolution, setSelectedSolution] = useState<ParetoSolution | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [xMetric, setXMetric] = useState<'operating_cost_usd' | 'fuel_consumption_tonnes'>('operating_cost_usd');

  const pollIntervalRef = useRef<any>(null);
  const workerRef = useRef<Worker | null>(null);

  // Load preset if passed
  useEffect(() => {
    if (presetToLoad) {
      setInputs((prev) => ({
        ...prev,
        cargo_demand_teu: presetToLoad.cargo_demand || prev.cargo_demand_teu,
        route_distance_nm: presetToLoad.route_distance_nm || prev.route_distance_nm,
        max_delivery_days: presetToLoad.max_delivery_days || prev.max_delivery_days,
        emission_cap_tco2e: presetToLoad.emission_cap_tco2e || prev.emission_cap_tco2e,
        carbon_price_usd_per_tco2e: presetToLoad.carbon_price_usd_per_tco2e || prev.carbon_price_usd_per_tco2e,
        candidate_vessels: presetToLoad.candidate_vessels || prev.candidate_vessels,
        candidate_fuels: presetToLoad.candidate_fuels || prev.candidate_fuels,
        origin_port: presetToLoad.origin_port || prev.origin_port,
        destination_port: presetToLoad.destination_port || prev.destination_port,
        preset_id: presetToLoad.preset_id
      }));
    }
  }, [presetToLoad]);

  // Persist inputs to localStorage
  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(inputs));
  }, [inputs]);

  // Clean up polling and worker on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (workerRef.current) workerRef.current.terminate();
    };
  }, []);

  const handleInputChange = (field: keyof FleetOptimizationInput, value: any) => {
    setInputs((prev) => ({ ...prev, [field]: value }));
  };

  const toggleArrayItem = (field: 'candidate_vessels' | 'candidate_fuels', item: string) => {
    setInputs((prev) => {
      const current = prev[field];
      const next = current.includes(item)
        ? current.filter((x) => x !== item)
        : [...current, item];
      return { ...prev, [field]: next.length ? next : [item] };
    });
  };

  const startWorkerOptimization = () => {
    if (workerRef.current) workerRef.current.terminate();

    const worker = new Worker(new URL('../workers/optimizer.worker.ts', import.meta.url), {
      type: 'module'
    });
    workerRef.current = worker;

    const fakeJobId = `job_local_${Date.now()}`;
    setActiveJob({
      job_id: fakeJobId,
      algorithm: inputs.algorithm + ' (Local Worker)',
      status: 'RUNNING',
      progress_percent: 0,
      current_generation: 0,
      total_generations: inputs.generations,
      elapsed_seconds: 0,
      pareto_front: [],
      hypervolume: 0,
      spread_metric: 0
    });

    worker.onmessage = (e) => {
      const msg = e.data;
      if (msg.type === 'PROGRESS') {
        setActiveJob((prev) => (prev ? { ...prev, ...msg } : null));
      } else if (msg.type === 'COMPLETED') {
        setActiveJob((prev) =>
          prev
            ? {
                ...prev,
                status: 'COMPLETED',
                progress_percent: 100,
                pareto_front: msg.pareto_front
              }
            : null
        );
        setIsRunning(false);
        if (msg.pareto_front?.length) setSelectedSolution(msg.pareto_front[0]);
      }
    };

    worker.postMessage({
      type: 'START_OPTIMIZATION',
      payload: inputs
    });
  };

  const handleRunOptimization = async () => {
    if (isRunning) return; // double-click protection
    setIsRunning(true);
    setErrorMessage(null);
    setSelectedSolution(null);

    if (isLocalMode) {
      startWorkerOptimization();
      return;
    }

    try {
      const launch = await api.launchOptimization(inputs, (attempt) => {
        onTriggerColdStart(attempt);
      });

      setActiveJob({
        job_id: launch.job_id,
        algorithm: inputs.algorithm,
        status: 'QUEUED',
        progress_percent: 0,
        current_generation: 0,
        total_generations: inputs.generations,
        elapsed_seconds: 0,
        pareto_front: [],
        hypervolume: 0,
        spread_metric: 0
      });

      // Start Polling
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = setInterval(async () => {
        try {
          const status = await api.getJobStatus(launch.job_id);
          setActiveJob(status);

          if (['COMPLETED', 'FAILED', 'CANCELLED', 'TIMED_OUT'].includes(status.status)) {
            clearInterval(pollIntervalRef.current);
            setIsRunning(false);
            if (status.pareto_front && status.pareto_front.length > 0) {
              setSelectedSolution(status.pareto_front[0]);
            }
          }
        } catch (err: any) {
          clearInterval(pollIntervalRef.current);
          setIsRunning(false);
          setErrorMessage(`Job polling error: ${err.message}`);
        }
      }, 800);
    } catch (err: any) {
      setIsRunning(false);
      const isNetwork = err instanceof ApiError || err.message?.includes('fetch');
      if (isNetwork) {
        setErrorMessage('Backend unreachable. Switched to client-side Web Worker execution.');
        startWorkerOptimization();
      } else {
        setErrorMessage(err.message || 'Failed to launch optimization job.');
      }
    }
  };

  const handleCancel = async () => {
    if (isLocalMode && workerRef.current) {
      workerRef.current.terminate();
      setIsRunning(false);
      setActiveJob((prev) => (prev ? { ...prev, status: 'CANCELLED' } : null));
      return;
    }

    if (activeJob) {
      try {
        await api.cancelJob(activeJob.job_id);
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        setIsRunning(false);
        setActiveJob((prev) => (prev ? { ...prev, status: 'CANCELLED' } : null));
      } catch (err: any) {
        setErrorMessage(`Cancellation failed: ${err.message}`);
      }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Top Banner / Case Study Notice */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-subtle)',
          padding: '10px 16px'
        }}
      >
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-dark-spruce)' }}>
            Green Fleet Multi-Objective Deployment Optimizer
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Simultaneously minimizes annual bunker fuel, operational expenditures, and Well-to-Wake GHG emissions.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => exportParetoToCSV(activeJob?.pareto_front || [])}
            disabled={!activeJob?.pareto_front?.length}
            className="btn btn-secondary"
          >
            <Download size={14} /> Export CSV
          </button>
          <button
            onClick={() => exportJsonToFile(activeJob?.pareto_front || [])}
            disabled={!activeJob?.pareto_front?.length}
            className="btn btn-secondary"
          >
            <Save size={14} /> Export JSON
          </button>
        </div>
      </div>

      {errorMessage && (
        <div
          style={{
            backgroundColor: '#FFECEB',
            border: '1px solid var(--danger)',
            color: 'var(--danger)',
            padding: '10px 14px',
            fontSize: '12px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <AlertTriangle size={15} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Grid: Parameters on Left, Results on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '16px', alignItems: 'start' }}>
        {/* Left Form: Parameter Controls */}
        <div
          style={{
            backgroundColor: 'var(--bg-panel-light)',
            border: '1px solid var(--border-subtle)',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px'
          }}
        >
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-dark-spruce)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
            OPTIMIZATION CONFIGURATION
          </div>

          {/* Solver Selection */}
          <div>
            <label htmlFor="solverSelect">Solver Algorithm</label>
            <select
              id="solverSelect"
              value={inputs.algorithm}
              onChange={(e) => handleInputChange('algorithm', e.target.value)}
              disabled={isRunning}
              style={{ width: '100%' }}
            >
              <option value="QIEA">QIEA (Quantum-Inspired Evolutionary)</option>
              <option value="QI-PSO">QI-PSO (Quantum Delta-Potential Swarm)</option>
              <option value="NSGA-II">NSGA-II (Classical Pareto Genetic)</option>
              <option value="GA">Classical Elitist GA</option>
              <option value="PSO">Classical Kinematic PSO</option>
            </select>
          </div>

          {/* Demand & Route */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label>Cargo Demand</label>
              <input
                type="number"
                value={inputs.cargo_demand_teu}
                onChange={(e) => handleInputChange('cargo_demand_teu', parseFloat(e.target.value) || 0)}
                disabled={isRunning}
                style={{ width: '100%' }}
              />
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>TEU or DWT / year</span>
            </div>
            <div>
              <label>One-Way Distance</label>
              <input
                type="number"
                value={inputs.route_distance_nm}
                onChange={(e) => handleInputChange('route_distance_nm', parseFloat(e.target.value) || 0)}
                disabled={isRunning}
                style={{ width: '100%' }}
              />
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>nautical miles</span>
            </div>
          </div>

          {/* Deadlines & Caps */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label>Max Delivery Days</label>
              <input
                type="number"
                step="0.5"
                value={inputs.max_delivery_days}
                onChange={(e) => handleInputChange('max_delivery_days', parseFloat(e.target.value) || 0)}
                disabled={isRunning}
                style={{ width: '100%' }}
              />
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>days one-way</span>
            </div>
            <div>
              <label>Emission Ceiling</label>
              <input
                type="number"
                value={inputs.emission_cap_tco2e}
                onChange={(e) => handleInputChange('emission_cap_tco2e', parseFloat(e.target.value) || 0)}
                disabled={isRunning}
                style={{ width: '100%' }}
              />
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>tCO2e / year</span>
            </div>
          </div>

          {/* Carbon Price */}
          <div>
            <label>Carbon Price Tax: ${inputs.carbon_price_usd_per_tco2e} / tCO2e</label>
            <input
              type="range"
              min="0"
              max="250"
              step="5"
              value={inputs.carbon_price_usd_per_tco2e}
              onChange={(e) => handleInputChange('carbon_price_usd_per_tco2e', parseFloat(e.target.value))}
              disabled={isRunning}
              style={{ width: '100%' }}
            />
          </div>

          {/* Candidate Vessels */}
          <div>
            <label>Candidate Vessel Types</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '12px' }}>
              {['Container_14000TEU', 'Feeder_2500TEU', 'Capesize_180000DWT', 'Panamax_82000DWT', 'VLCC_300000DWT', 'Aframax_115000DWT'].map((v) => (
                <label key={v} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', textTransform: 'none', fontWeight: 500 }}>
                  <input
                    type="checkbox"
                    checked={inputs.candidate_vessels.includes(v)}
                    onChange={() => toggleArrayItem('candidate_vessels', v)}
                    disabled={isRunning}
                  />
                  <span>{v.replace(/_/g, ' ')}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Candidate Fuels */}
          <div>
            <label>Candidate Fuels</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '12px' }}>
              {['VLSFO', 'LNG', 'Methanol', 'Ammonia', 'Hydrogen'].map((f) => (
                <label key={f} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', textTransform: 'none', fontWeight: 500 }}>
                  <input
                    type="checkbox"
                    checked={inputs.candidate_fuels.includes(f)}
                    onChange={() => toggleArrayItem('candidate_fuels', f)}
                    disabled={isRunning}
                  />
                  <span>{f}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Shore Power Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="checkbox"
              id="shorePowerToggle"
              checked={inputs.allow_shore_power}
              onChange={(e) => handleInputChange('allow_shore_power', e.target.checked)}
              disabled={isRunning}
            />
            <label htmlFor="shorePowerToggle" style={{ margin: 0, textTransform: 'none', fontWeight: 600, cursor: 'pointer' }}>
              Enable Shore Power (Cold Ironing)
            </label>
          </div>

          {/* Generational parameters */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label>Generations</label>
              <input
                type="number"
                min="5"
                max="100"
                value={inputs.generations}
                onChange={(e) => handleInputChange('generations', parseInt(e.target.value) || 20)}
                disabled={isRunning}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label>Population Size</label>
              <input
                type="number"
                min="10"
                max="60"
                value={inputs.population_size}
                onChange={(e) => handleInputChange('population_size', parseInt(e.target.value) || 20)}
                disabled={isRunning}
                style={{ width: '100%' }}
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
            <button
              onClick={handleRunOptimization}
              disabled={isRunning}
              className="btn btn-primary"
              style={{ flex: 1, justifyContent: 'center' }}
            >
              <Play size={14} /> Run Optimizer
            </button>
            {isRunning && (
              <button
                onClick={handleCancel}
                className="btn btn-danger"
                style={{ justifyContent: 'center' }}
                title="Cooperative Cancel"
              >
                <Square size={14} /> Cancel
              </button>
            )}
          </div>
        </div>

        {/* Right Section: Progress, Pareto Frontier, Solution Inspection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Progress Bar & Status */}
          {activeJob && (
            <div
              style={{
                backgroundColor: 'var(--bg-panel-light)',
                border: '1px solid var(--border-subtle)',
                padding: '12px 16px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                <div>
                  Status: <strong>{activeJob.status}</strong> &bull; Gen {activeJob.current_generation} / {activeJob.total_generations}
                </div>
                <div className="num">
                  {activeJob.progress_percent}% ({activeJob.elapsed_seconds}s)
                </div>
              </div>
              <div style={{ height: '6px', backgroundColor: 'var(--bg-input)', border: '1px solid var(--border-subtle)' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${activeJob.progress_percent}%`,
                    backgroundColor: 'var(--color-golden-earth)',
                    transition: 'width 0.2s ease'
                  }}
                />
              </div>

              {activeJob.pareto_front && (
                <div style={{ display: 'flex', gap: '18px', marginTop: '8px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                  <div>HV Indicator: <strong>{activeJob.hypervolume || '0.000'}</strong></div>
                  <div>Spread Metric: <strong>{activeJob.spread_metric || '0.00'}</strong></div>
                  <div>Solutions: <strong>{activeJob.pareto_front.length}</strong></div>
                </div>
              )}
            </div>
          )}

          {/* Pareto Chart */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginBottom: '4px' }}>
              <button
                onClick={() => setXMetric('operating_cost_usd')}
                style={{
                  fontSize: '11px',
                  padding: '2px 8px',
                  background: xMetric === 'operating_cost_usd' ? 'var(--color-dark-spruce)' : 'transparent',
                  color: xMetric === 'operating_cost_usd' ? '#FFFFFF' : 'var(--text-main)',
                  border: '1px solid var(--border-subtle)',
                  cursor: 'pointer'
                }}
              >
                Cost vs GHG
              </button>
              <button
                onClick={() => setXMetric('fuel_consumption_tonnes')}
                style={{
                  fontSize: '11px',
                  padding: '2px 8px',
                  background: xMetric === 'fuel_consumption_tonnes' ? 'var(--color-dark-spruce)' : 'transparent',
                  color: xMetric === 'fuel_consumption_tonnes' ? '#FFFFFF' : 'var(--text-main)',
                  border: '1px solid var(--border-subtle)',
                  cursor: 'pointer'
                }}
              >
                Fuel vs GHG
              </button>
            </div>
            <ParetoFrontChart
              solutions={activeJob?.pareto_front || []}
              selectedSolution={selectedSolution}
              onSelectSolution={setSelectedSolution}
              xMetric={xMetric}
            />
          </div>

          {/* Solution Inspection Card */}
          {selectedSolution && (
            <div
              style={{
                backgroundColor: 'var(--bg-panel-light)',
                border: '2px solid var(--color-dark-spruce)',
                padding: '14px 18px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className={`badge ${selectedSolution.feasible ? 'badge-feasible' : 'badge-infeasible'}`}>
                    {selectedSolution.feasible ? 'FEASIBLE DEPLOYMENT' : 'CONSTRAINT BREACH'}
                  </span>
                  <span style={{ fontSize: '13px', fontWeight: 700 }}>
                    {selectedSolution.vessel_count}x {selectedSolution.vessel_type} ({selectedSolution.fuel_type})
                  </span>
                </div>
                <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                  ID: {selectedSolution.solution_id}
                </div>
              </div>

              {/* Infeasible Violations Notice if present */}
              {!selectedSolution.feasible && selectedSolution.violations && (
                <div style={{ backgroundColor: '#FFECEB', border: '1px solid var(--danger)', padding: '8px 12px', fontSize: '11px', color: 'var(--danger)', marginBottom: '12px' }}>
                  <strong>Violated Constraints:</strong>
                  <ul style={{ marginLeft: '16px', marginTop: '4px' }}>
                    {selectedSolution.violations.map((v, i) => (
                      <li key={i}>{v}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Metrics Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                <div style={{ padding: '8px', backgroundColor: 'var(--bg-panel)' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>ANNUAL FUEL</div>
                  <div style={{ fontSize: '15px', fontWeight: 700 }} className="num">
                    {selectedSolution.fuel_consumption_tonnes.toLocaleString()} t
                  </div>
                </div>
                <div style={{ padding: '8px', backgroundColor: 'var(--bg-panel)' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>ANNUAL OPEX &amp; TAX</div>
                  <div style={{ fontSize: '15px', fontWeight: 700 }} className="num">
                    ${(selectedSolution.operating_cost_usd / 1e6).toFixed(2)}M
                  </div>
                </div>
                <div style={{ padding: '8px', backgroundColor: 'var(--bg-panel)' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>LIFECYCLE WTW GHG</div>
                  <div style={{ fontSize: '15px', fontWeight: 700 }} className="num">
                    {selectedSolution.lifecycle_ghg_tco2e.toLocaleString()} tCO2e
                  </div>
                </div>
                <div style={{ padding: '8px', backgroundColor: 'var(--bg-panel)' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>TRANSIT TIME (ONE-WAY)</div>
                  <div style={{ fontSize: '15px', fontWeight: 700 }} className="num">
                    {selectedSolution.transit_days_oneway} days ({selectedSolution.speed_knots} kn)
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Non-Dominated Solutions Table */}
          {activeJob?.pareto_front && activeJob.pareto_front.length > 0 && (
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Vessel Type</th>
                    <th className="num">Count</th>
                    <th className="num">Speed (kn)</th>
                    <th>Fuel</th>
                    <th>Shore</th>
                    <th className="num">Fuel (t/yr)</th>
                    <th className="num">OPEX ($/yr)</th>
                    <th className="num">GHG (tCO2e)</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {activeJob.pareto_front.map((sol, idx) => {
                    const isSelected = selectedSolution?.solution_id === sol.solution_id;
                    return (
                      <tr
                        key={sol.solution_id || idx}
                        className={isSelected ? 'selected' : ''}
                        onClick={() => setSelectedSolution(sol)}
                        style={{ cursor: 'pointer' }}
                      >
                        <td>{sol.vessel_type}</td>
                        <td className="num">{sol.vessel_count}</td>
                        <td className="num">{sol.speed_knots}</td>
                        <td>{sol.fuel_type}</td>
                        <td>{sol.shore_power_active ? 'Yes' : 'No'}</td>
                        <td className="num">{sol.fuel_consumption_tonnes.toLocaleString()}</td>
                        <td className="num">${(sol.operating_cost_usd / 1e6).toFixed(2)}M</td>
                        <td className="num">{sol.lifecycle_ghg_tco2e.toLocaleString()}</td>
                        <td>
                          <span className={`badge ${sol.feasible ? 'badge-feasible' : 'badge-infeasible'}`}>
                            {sol.feasible ? 'Feasible' : 'Infeasible'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
