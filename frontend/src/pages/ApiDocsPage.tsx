import React, { useState, useEffect } from 'react';
import { api, API_BASE } from '../lib/api';
import { RefreshCw } from 'lucide-react';

export const ApiDocsPage: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [version, setVersion] = useState<any>(null);
  const [isPinging, setIsPinging] = useState(false);

  const runPing = async () => {
    setIsPinging(true);
    try {
      const h = await api.checkHealth();
      const v = await api.checkVersion();
      setHealth(h);
      setVersion(v);
    } catch (err: any) {
      setHealth({ status: 'unreachable', error: err.message });
    } finally {
      setIsPinging(false);
    }
  };

  useEffect(() => {
    runPing();
  }, []);

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
            System Diagnostics &amp; REST API Integration
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Endpoints for automated fleet routing, fuel consumption forecasting, and optimization background workers.
          </p>
        </div>
        <button onClick={runPing} disabled={isPinging} className="btn btn-secondary">
          <RefreshCw size={13} className={isPinging ? 'animate-spin' : ''} /> Ping Server
        </button>
      </div>

      {/* Live Health State */}
      <div style={{ backgroundColor: 'var(--bg-panel-light)', border: '1px solid var(--border-subtle)', padding: '16px' }}>
        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-dark-spruce)', marginBottom: '10px' }}>
          Backend Service Health
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
          <div style={{ padding: '10px', backgroundColor: 'var(--bg-panel)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>SERVICE STATUS</div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: health?.status === 'ok' ? 'var(--color-dark-spruce)' : 'var(--danger)' }}>
              {health?.status ? health.status.toUpperCase() : 'UNKNOWN'}
            </div>
          </div>
          <div style={{ padding: '10px', backgroundColor: 'var(--bg-panel)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>API VERSION</div>
            <div style={{ fontSize: '16px', fontWeight: 700 }} className="num">
              {version?.version || '1.0.0'}
            </div>
          </div>
          <div style={{ padding: '10px', backgroundColor: 'var(--bg-panel)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>SERVER UPTIME</div>
            <div style={{ fontSize: '16px', fontWeight: 700 }} className="num">
              {health?.uptime_seconds ? `${health.uptime_seconds}s` : '—'}
            </div>
          </div>
          <div style={{ padding: '10px', backgroundColor: 'var(--bg-panel)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>BASE ENDPOINT</div>
            <div style={{ fontSize: '12px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              {API_BASE}
            </div>
          </div>
        </div>
      </div>

      {/* API Reference & cURL Examples */}
      <div style={{ backgroundColor: 'var(--bg-panel-light)', border: '1px solid var(--border-subtle)', padding: '16px' }}>
        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-dark-spruce)', marginBottom: '12px' }}>
          HTTP Endpoints &amp; Command-Line Examples
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '12px' }}>
          <div>
            <div style={{ fontWeight: 700, color: 'var(--color-golden-earth)', marginBottom: '4px' }}>
              1. Single Vessel Fuel Prediction (POST /api/predict)
            </div>
            <pre style={{ backgroundColor: 'var(--color-dark-spruce)', color: 'var(--color-lime-cream)', padding: '10px', overflowX: 'auto', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
{`curl -X POST "${API_BASE}/api/predict" \\
  -H "Content-Type: application/json" \\
  -d '{"vessel_type": "Container_14000TEU", "speed_knots": 18.0, "sea_state_beaufort": 3}'`}
            </pre>
          </div>

          <div>
            <div style={{ fontWeight: 700, color: 'var(--color-golden-earth)', marginBottom: '4px' }}>
              2. Launch Asynchronous Fleet Optimization (POST /api/optimize)
            </div>
            <pre style={{ backgroundColor: 'var(--color-dark-spruce)', color: 'var(--color-lime-cream)', padding: '10px', overflowX: 'auto', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
{`curl -X POST "${API_BASE}/api/optimize" \\
  -H "Content-Type: application/json" \\
  -d '{"algorithm": "QIEA", "cargo_demand_teu": 50000, "route_distance_nm": 11500, "generations": 30}'`}
            </pre>
          </div>

          <div>
            <div style={{ fontWeight: 700, color: 'var(--color-golden-earth)', marginBottom: '4px' }}>
              3. Poll Background Optimization Job (GET /api/jobs/{'{id}'})
            </div>
            <pre style={{ backgroundColor: 'var(--color-dark-spruce)', color: 'var(--color-lime-cream)', padding: '10px', overflowX: 'auto', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
{`curl -X GET "${API_BASE}/api/jobs/job_948f2b71"`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
