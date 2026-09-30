import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { BenchmarkData } from '../types';
import { ConvergenceChart } from '../charts/ConvergenceChart';
import { Play } from 'lucide-react';

interface BenchmarksPageProps {
  isLocalMode: boolean;
}

export const BenchmarksPage: React.FC<BenchmarksPageProps> = ({ isLocalMode }) => {
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLiveRunning, setIsLiveRunning] = useState(false);
  const [liveRuns, setLiveRuns] = useState(3);
  const [liveResults, setLiveResults] = useState<any>(null);

  useEffect(() => {
    const loadBenchmarks = async () => {
      setIsLoading(true);
      try {
        const data = await api.getPrecomputedBenchmarks();
        setBenchmarkData(data);
      } catch (err) {
        console.error('Failed to load precomputed benchmarks:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadBenchmarks();
  }, []);

  const handleRunLive = async () => {
    setIsLiveRunning(true);
    setLiveResults(null);
    try {
      const res = await api.runLiveBenchmark(['QIEA', 'QI-PSO', 'NSGA-II'], liveRuns, 20, 101);
      setLiveResults(res);
    } catch (err: any) {
      alert(`Live benchmark error: ${err.message}`);
    } finally {
      setIsLiveRunning(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Banner */}
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
            Algorithm Benchmarks &amp; Statistical Rigor
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Comparative statistical evaluation over 30 independent runs with fixed random seeds. {isLoading && 'Loading benchmarks...'}
          </p>
        </div>

        {/* Live Re-Run Trigger */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
            <span>Runs:</span>
            <select
              value={liveRuns}
              onChange={(e) => setLiveRuns(parseInt(e.target.value))}
              disabled={isLiveRunning || isLocalMode}
              style={{ padding: '2px 6px' }}
            >
              <option value="1">1 run</option>
              <option value="3">3 runs</option>
              <option value="5">5 runs</option>
            </select>
          </div>
          <button
            onClick={handleRunLive}
            disabled={isLiveRunning || isLocalMode}
            className="btn btn-primary"
          >
            <Play size={13} /> {isLiveRunning ? 'Running Live Evaluation...' : 'Re-Run Live Benchmark'}
          </button>
        </div>
      </div>

      {/* Statistical Summary Table */}
      {benchmarkData && (
        <div style={{ backgroundColor: 'var(--bg-panel-light)', border: '1px solid var(--border-subtle)', padding: '16px' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-dark-spruce)', marginBottom: '12px' }}>
            Multi-Objective Frontier Quality Metrics (N = 30 independent runs &bull; Mean &plusmn; Standard Deviation)
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Algorithm Architecture</th>
                <th className="num">Hypervolume Indicator</th>
                <th className="num">Spread / Spacing (S)</th>
                <th className="num">Convergence Speed (Gen)</th>
                <th className="num">Runtime (seconds)</th>
                <th>Classification</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(benchmarkData.solution_quality).map(([algo, metrics]) => {
                const isQIEA = algo === 'QIEA';
                const isQIPSO = algo === 'QI-PSO';
                return (
                  <tr key={algo} style={{ fontWeight: isQIEA || isQIPSO ? 700 : 400, backgroundColor: isQIEA ? 'rgba(153, 98, 30, 0.12)' : 'transparent' }}>
                    <td>{algo}</td>
                    <td className="num">{metrics.hypervolume_mean.toFixed(3)} &plusmn; {metrics.hypervolume_std.toFixed(3)}</td>
                    <td className="num">{metrics.spacing_mean.toFixed(3)} &plusmn; {metrics.spacing_std.toFixed(3)}</td>
                    <td className="num">{metrics.convergence_generations_mean.toFixed(1)} &plusmn; {metrics.convergence_generations_std.toFixed(1)}</td>
                    <td className="num">{metrics.runtime_sec_mean.toFixed(2)}s &plusmn; {metrics.runtime_sec_std.toFixed(2)}s</td>
                    <td>
                      {isQIEA ? (
                        <span className="badge badge-feasible">Quantum Superposition</span>
                      ) : isQIPSO ? (
                        <span className="badge badge-feasible">Delta-Potential Well</span>
                      ) : (
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Classical Baseline</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Live Re-Run Results if executed */}
      {liveResults && (
        <div style={{ backgroundColor: 'var(--bg-panel-light)', border: '2px solid var(--color-golden-earth)', padding: '16px' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-dark-spruce)', marginBottom: '10px' }}>
            Live Benchmark Execution Output ({liveResults.runs} runs &bull; Seed {liveResults.seed})
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Algorithm</th>
                <th className="num">Hypervolume (Mean &plusmn; Std)</th>
                <th className="num">Spacing Metric</th>
                <th className="num">Execution Time</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(liveResults.results).map(([algo, res]: [string, any]) => (
                <tr key={algo}>
                  <td><strong>{algo}</strong></td>
                  <td className="num">{res.hypervolume_mean} &plusmn; {res.hypervolume_std}</td>
                  <td className="num">{res.spacing_mean} &plusmn; {res.spacing_std}</td>
                  <td className="num">{res.runtime_sec_mean}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {benchmarkData?.convergence_trajectories && (
          <ConvergenceChart
            generations={benchmarkData.convergence_trajectories.generations}
            curves={benchmarkData.convergence_trajectories.curves}
          />
        )}

        {/* Scalability Table / Card */}
        {benchmarkData?.scalability_runtime_seconds && (
          <div style={{ backgroundColor: 'var(--bg-panel-light)', border: '1px solid var(--border-subtle)', padding: '12px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px', textTransform: 'uppercase' }}>
              Scalability: Optimization Execution Time vs Fleet Size (Seconds)
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Algorithm</th>
                  <th className="num">5 Vessels</th>
                  <th className="num">15 Vessels</th>
                  <th className="num">30 Vessels</th>
                  <th className="num">60 Vessels</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(benchmarkData.scalability_runtime_seconds.series).map(([algo, times]) => (
                  <tr key={algo}>
                    <td><strong>{algo}</strong></td>
                    {times.map((t, idx) => (
                      <td key={idx} className="num">{t.toFixed(2)}s</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Rigor & Limitations Footnote */}
      <div style={{ backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-subtle)', padding: '12px 16px', fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
        <strong>Benchmarking Methodology:</strong> All runs initialized with deterministic seeds.
        Hypervolume is computed with reference multiplier 1.1 across normalized objectives [Fuel, Cost, GHG].
        QIEA demonstrates superior exploration-exploitation balance via rotation gates without premature convergence;
        classical NSGA-II maintains high diversity but requires more objective evaluations.
      </div>
    </div>
  );
};
