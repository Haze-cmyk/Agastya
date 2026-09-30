import React from 'react';
import { ScenarioFuelDetail } from '../types';

interface FuelComparisonChartProps {
  fuelsData: Record<string, ScenarioFuelDetail>;
}

export const FuelComparisonChart: React.FC<FuelComparisonChartProps> = ({ fuelsData }) => {
  const fuels = Object.keys(fuelsData);
  if (fuels.length === 0) return null;

  const width = 560;
  const height = 260;
  const padding = { top: 30, right: 20, bottom: 40, left: 60 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const maxGHG = Math.max(...Object.values(fuelsData).map(f => f.total_wtw_ghg_tco2e)) * 1.15;
  const barWidth = Math.min(42, (plotWidth / fuels.length) * 0.65);
  const gap = plotWidth / fuels.length;

  return (
    <div style={{ backgroundColor: 'var(--bg-panel-light)', border: '1px solid var(--border-subtle)', padding: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-main)', textTransform: 'uppercase' }}>
          Well-to-Wake Lifecycle GHG Breakdown (tCO2e / year)
        </div>
        <div style={{ display: 'flex', gap: '14px', fontSize: '11px', fontWeight: 600 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '10px', height: '10px', backgroundColor: 'var(--color-dark-spruce)', display: 'inline-block' }} />
            TTW Combustion
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '10px', height: '10px', backgroundColor: 'var(--color-muted-teal)', display: 'inline-block' }} />
            WTT Upstream
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '10px', height: '10px', backgroundColor: 'var(--color-toasted-almond)', display: 'inline-block' }} />
            Slip / Venting
          </span>
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
        {/* Horizontal grid lines */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((pct, i) => {
          const y = padding.top + (1 - pct) * plotHeight;
          const val = pct * maxGHG;
          return (
            <g key={i}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="rgba(115, 158, 130, 0.2)" strokeDasharray="2,2" />
              <text x={padding.left - 6} y={y + 4} textAnchor="end" fontSize="9" fill="var(--color-dark-spruce)" fontFamily="var(--font-mono)">
                {(val / 1000).toFixed(0)}k
              </text>
            </g>
          );
        })}

        {/* Stacked bars */}
        {fuels.map((fuelKey, idx) => {
          const data = fuelsData[fuelKey];
          const x = padding.left + idx * gap + (gap - barWidth) / 2;

          const hTTW = (data.ttw_ghg_tco2e / maxGHG) * plotHeight;
          const hWTT = (data.wtt_ghg_tco2e / maxGHG) * plotHeight;
          const slipVal = (data.methane_slip_tco2e || 0) + (data.n2o_slip_tco2e || 0);
          const hSlip = (slipVal / maxGHG) * plotHeight;

          const yTTW = height - padding.bottom - hTTW;
          const yWTT = yTTW - hWTT;
          const ySlip = yWTT - hSlip;

          return (
            <g key={fuelKey}>
              {/* TTW direct combustion */}
              {hTTW > 0 && (
                <rect x={x} y={yTTW} width={barWidth} height={hTTW} fill="var(--color-dark-spruce)" />
              )}
              {/* WTT upstream */}
              {hWTT > 0 && (
                <rect x={x} y={yWTT} width={barWidth} height={hWTT} fill="var(--color-muted-teal)" />
              )}
              {/* Methane / N2O slip */}
              {hSlip > 0 && (
                <rect x={x} y={ySlip} width={barWidth} height={hSlip} fill="var(--color-toasted-almond)" />
              )}

              {/* Total label above bar */}
              <text
                x={x + barWidth / 2}
                y={ySlip - 4}
                textAnchor="middle"
                fontSize="9"
                fontWeight="700"
                fill="var(--color-dark-spruce)"
                fontFamily="var(--font-mono)"
              >
                {(data.total_wtw_ghg_tco2e / 1000).toFixed(0)}k
              </text>

              {/* Fuel label below axis */}
              <text
                x={x + barWidth / 2}
                y={height - padding.bottom + 14}
                textAnchor="middle"
                fontSize="10"
                fontWeight="600"
                fill="var(--color-dark-spruce)"
              >
                {fuelKey}
              </text>
            </g>
          );
        })}

        {/* Baseline axis */}
        <line x1={padding.left} y1={height - padding.bottom} x2={width - padding.right} y2={height - padding.bottom} stroke="var(--color-dark-spruce)" strokeWidth="1.2" />
      </svg>
    </div>
  );
};
