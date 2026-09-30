import React, { useState, useRef } from 'react';
import { ParetoSolution } from '../types';
import { Download } from 'lucide-react';

interface ParetoFrontChartProps {
  solutions: ParetoSolution[];
  selectedSolution?: ParetoSolution | null;
  onSelectSolution?: (sol: ParetoSolution) => void;
  xMetric?: 'operating_cost_usd' | 'fuel_consumption_tonnes';
}

export const ParetoFrontChart: React.FC<ParetoFrontChartProps> = ({
  solutions,
  selectedSolution,
  onSelectSolution,
  xMetric = 'operating_cost_usd'
}) => {
  const [hoveredSolution, setHoveredSolution] = useState<ParetoSolution | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  if (!solutions || solutions.length === 0) {
    return (
      <div
        style={{
          height: '280px',
          backgroundColor: 'var(--bg-panel-light)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          fontSize: '13px'
        }}
      >
        No Pareto front computed yet. Configure parameters and run optimization.
      </div>
    );
  }

  const padding = { top: 30, right: 30, bottom: 45, left: 65 };
  const width = 560;
  const height = 300;
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const xValues = solutions.map(s => xMetric === 'operating_cost_usd' ? s.operating_cost_usd : s.fuel_consumption_tonnes);
  const yValues = solutions.map(s => s.lifecycle_ghg_tco2e);

  const minX = Math.min(...xValues) * 0.95;
  const maxX = Math.max(...xValues) * 1.05;
  const minY = Math.min(...yValues) * 0.95;
  const maxY = Math.max(...yValues) * 1.05;

  const getX = (val: number) => padding.left + ((val - minX) / Math.max(1, maxX - minX)) * plotWidth;
  const getY = (val: number) => height - padding.bottom - ((val - minY) / Math.max(1, maxY - minY)) * plotHeight;

  const handleExportPNG = () => {
    if (!svgRef.current) return;
    const svgElement = svgRef.current;
    const svgString = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement('canvas');
    canvas.width = width * 2;
    canvas.height = height * 2;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      ctx.fillStyle = '#EDF9AB';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      const pngUrl = canvas.toDataURL('image/png');
      const a = document.createElement('a');
      a.download = `agastya_pareto_chart.png`;
      a.href = pngUrl;
      a.click();
    };
    img.src = url;
  };

  const xLabel = xMetric === 'operating_cost_usd' ? 'Annual Operating Cost ($ / year)' : 'Annual Fuel Consumption (tonnes / year)';
  const yLabel = 'Lifecycle WTW GHG (tCO2e / year)';

  return (
    <div style={{ backgroundColor: 'var(--bg-panel-light)', border: '1px solid var(--border-subtle)', padding: '12px', position: 'relative' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-main)', textTransform: 'uppercase' }}>
          Pareto Non-Dominated Frontier ({solutions.length} trade-off points)
        </div>
        <button
          onClick={handleExportPNG}
          className="btn btn-secondary"
          style={{ padding: '3px 8px', fontSize: '11px' }}
          title="Export Chart as PNG"
        >
          <Download size={12} /> PNG Export
        </button>
      </div>

      <svg ref={svgRef} viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}>
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
          const yPos = padding.top + pct * plotHeight;
          const xPos = padding.left + pct * plotWidth;
          const yVal = maxY - pct * (maxY - minY);
          const xVal = minX + pct * (maxX - minX);

          return (
            <g key={i}>
              <line x1={padding.left} y1={yPos} x2={width - padding.right} y2={yPos} stroke="rgba(115, 158, 130, 0.25)" strokeDasharray="2,2" />
              <line x1={xPos} y1={padding.top} x2={xPos} y2={height - padding.bottom} stroke="rgba(115, 158, 130, 0.25)" strokeDasharray="2,2" />
              <text x={padding.left - 8} y={yPos + 4} textAnchor="end" fontSize="10" fill="var(--color-dark-spruce)" fontFamily="var(--font-mono)">
                {yVal >= 1000 ? `${(yVal / 1000).toFixed(0)}k` : yVal.toFixed(0)}
              </text>
              <text x={xPos} y={height - padding.bottom + 16} textAnchor="middle" fontSize="10" fill="var(--color-dark-spruce)" fontFamily="var(--font-mono)">
                {xVal >= 1000000 ? `${(xVal / 1000000).toFixed(1)}M` : xVal >= 1000 ? `${(xVal / 1000).toFixed(0)}k` : xVal.toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Axes */}
        <line x1={padding.left} y1={height - padding.bottom} x2={width - padding.right} y2={height - padding.bottom} stroke="var(--color-dark-spruce)" strokeWidth="1.5" />
        <line x1={padding.left} y1={padding.top} x2={padding.left} y2={height - padding.bottom} stroke="var(--color-dark-spruce)" strokeWidth="1.5" />

        {/* Axis Labels */}
        <text x={width / 2} y={height - 6} textAnchor="middle" fontSize="11" fontWeight="600" fill="var(--color-dark-spruce)">
          {xLabel}
        </text>
        <text transform={`rotate(-90)`} x={-(height / 2)} y={16} textAnchor="middle" fontSize="11" fontWeight="600" fill="var(--color-dark-spruce)">
          {yLabel}
        </text>

        {/* Pareto Points */}
        {solutions.map((sol, idx) => {
          const xVal = xMetric === 'operating_cost_usd' ? sol.operating_cost_usd : sol.fuel_consumption_tonnes;
          const cx = getX(xVal);
          const cy = getY(sol.lifecycle_ghg_tco2e);
          const isSelected = selectedSolution?.solution_id === sol.solution_id;
          const isHovered = hoveredSolution?.solution_id === sol.solution_id;

          const pointFill = sol.feasible ? (isSelected ? 'var(--color-golden-earth)' : 'var(--color-dark-spruce)') : '#99231E';

          return (
            <g
              key={sol.solution_id || idx}
              style={{ cursor: 'pointer' }}
              onClick={() => onSelectSolution && onSelectSolution(sol)}
              onMouseEnter={() => setHoveredSolution(sol)}
              onMouseLeave={() => setHoveredSolution(null)}
            >
              <circle
                cx={cx}
                cy={cy}
                r={isSelected ? 7 : isHovered ? 6 : 4.5}
                fill={pointFill}
                stroke={isSelected || isHovered ? '#FFFFFF' : 'var(--color-muted-teal)'}
                strokeWidth={isSelected ? 2.5 : 1}
              />
            </g>
          );
        })}
      </svg>

      {/* Tooltip */}
      {hoveredSolution && (
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            right: '16px',
            backgroundColor: 'var(--color-dark-spruce)',
            color: 'var(--color-lime-cream)',
            padding: '8px 12px',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            borderRadius: '2px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
            zIndex: 10,
            pointerEvents: 'none'
          }}
        >
          <div><strong>{hoveredSolution.vessel_count}x {hoveredSolution.vessel_type}</strong> ({hoveredSolution.fuel_type})</div>
          <div>Speed: {hoveredSolution.speed_knots} kn &bull; Shore: {hoveredSolution.shore_power_active ? 'Yes' : 'No'}</div>
          <div>Cost: ${(hoveredSolution.operating_cost_usd / 1e6).toFixed(2)}M / yr</div>
          <div>Fuel: {hoveredSolution.fuel_consumption_tonnes.toLocaleString()} t / yr</div>
          <div>GHG: {hoveredSolution.lifecycle_ghg_tco2e.toLocaleString()} tCO2e / yr</div>
          <div>Status: {hoveredSolution.feasible ? 'FEASIBLE' : 'INFEASIBLE'}</div>
        </div>
      )}
    </div>
  );
};
