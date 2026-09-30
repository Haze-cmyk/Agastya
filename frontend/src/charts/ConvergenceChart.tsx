import React from 'react';

interface ConvergenceChartProps {
  generations: number[];
  curves: Record<string, number[]>;
}

export const ConvergenceChart: React.FC<ConvergenceChartProps> = ({ generations, curves }) => {
  const width = 560;
  const height = 240;
  const padding = { top: 25, right: 30, bottom: 40, left: 55 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const maxGen = Math.max(...generations, 25);
  const getX = (g: number) => padding.left + ((g - 1) / (maxGen - 1)) * plotWidth;
  const getY = (hv: number) => height - padding.bottom - (hv / 1.0) * plotHeight;

  // Strictly palette colors
  const colorMap: Record<string, string> = {
    QIEA: 'var(--oxblood, #92140c)',
    'QI-PSO': 'var(--shadow-grey, #1e1e24)',
    'NSGA-II': 'var(--color-muted-teal, #4E5360)',
    GA: '#7D7A84',
    PSO: '#C26747'
  };

  return (
    <div style={{ backgroundColor: 'var(--bg-panel-light)', border: '1px solid var(--border-subtle)', padding: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-main)', textTransform: 'uppercase' }}>
          Hypervolume Indicator Convergence Trajectory
        </div>
        <div style={{ display: 'flex', gap: '10px', fontSize: '11px', fontWeight: 600 }}>
          {Object.keys(curves).map((algo) => (
            <span key={algo} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '12px', height: '3px', backgroundColor: colorMap[algo] || 'var(--color-dark-spruce)' }} />
              {algo}
            </span>
          ))}
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
        {/* Y Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((val) => {
          const y = getY(val);
          return (
            <g key={val}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="rgba(115, 158, 130, 0.2)" strokeDasharray="2,2" />
              <text x={padding.left - 6} y={y + 3} textAnchor="end" fontSize="9" fill="var(--color-dark-spruce)" fontFamily="var(--font-mono)">
                {val.toFixed(2)}
              </text>
            </g>
          );
        })}

        {/* Polylines for each algorithm */}
        {Object.entries(curves).map(([algo, points]) => {
          const pointsStr = points.map((hv, i) => `${getX(generations[i]).toFixed(1)},${getY(hv).toFixed(1)}`).join(' ');
          const strokeColor = colorMap[algo] || 'var(--color-dark-spruce)';
          const strokeWidth = algo === 'QIEA' || algo === 'QI-PSO' ? 2.5 : 1.5;

          return (
            <g key={algo}>
              <polyline fill="none" stroke={strokeColor} strokeWidth={strokeWidth} points={pointsStr} />
              {/* Endpoint marker */}
              {points.length > 0 && (
                <circle
                  cx={getX(generations[points.length - 1])}
                  cy={getY(points[points.length - 1])}
                  r={3.5}
                  fill={strokeColor}
                />
              )}
            </g>
          );
        })}

        {/* Axes */}
        <line x1={padding.left} y1={height - padding.bottom} x2={width - padding.right} y2={height - padding.bottom} stroke="var(--color-dark-spruce)" strokeWidth="1.2" />
        <line x1={padding.left} y1={padding.top} x2={padding.left} y2={height - padding.bottom} stroke="var(--color-dark-spruce)" strokeWidth="1.2" />

        {/* Axis Labels */}
        <text x={width / 2} y={height - 8} textAnchor="middle" fontSize="11" fontWeight="600" fill="var(--color-dark-spruce)">
          Optimization Generations
        </text>
        <text transform="rotate(-90)" x={-(height / 2)} y={16} textAnchor="middle" fontSize="11" fontWeight="600" fill="var(--color-dark-spruce)">
          Normalized Hypervolume
        </text>

        {/* X Ticks */}
        {[1, 5, 10, 15, 20, 25].map((g) => (
          <text key={g} x={getX(g)} y={height - padding.bottom + 14} textAnchor="middle" fontSize="9" fill="var(--color-dark-spruce)" fontFamily="var(--font-mono)">
            {g}
          </text>
        ))}
      </svg>
    </div>
  );
};
