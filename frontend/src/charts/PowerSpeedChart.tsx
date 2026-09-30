import React from 'react';

interface PowerSpeedChartProps {
  currentSpeed: number;
  minSpeed: number;
  maxSpeed: number;
  designSpeed: number;
  engineMcrKw: number;
  speedExponent: number;
  cHull: number;
  displacementRatio?: number;
}

export const PowerSpeedChart: React.FC<PowerSpeedChartProps> = ({
  currentSpeed,
  minSpeed,
  maxSpeed,
  designSpeed,
  engineMcrKw,
  speedExponent,
  cHull,
  displacementRatio = 1.0
}) => {
  const width = 520;
  const height = 240;
  const padding = { top: 20, right: 30, bottom: 40, left: 60 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  // Generate curve from 6.0 to 25.0 knots
  const speeds: number[] = [];
  for (let s = 6.0; s <= 25.0; s += 0.5) {
    speeds.push(s);
  }

  const powers = speeds.map((v) => {
    const clampedV = Math.max(minSpeed, Math.min(maxSpeed, v));
    const p = cHull * Math.pow(displacementRatio, 2 / 3) * Math.pow(clampedV, speedExponent);
    return Math.min(engineMcrKw * 1.08, p);
  });

  const maxPower = engineMcrKw * 1.15;
  const getX = (v: number) => padding.left + ((v - 6.0) / (25.0 - 6.0)) * plotWidth;
  const getY = (p: number) => height - padding.bottom - (p / maxPower) * plotHeight;

  // Polyline points
  const pointsString = speeds.map((v, i) => `${getX(v).toFixed(1)},${getY(powers[i]).toFixed(1)}`).join(' ');

  // Current operating point
  const currentClampedSpeed = Math.max(minSpeed, Math.min(maxSpeed, currentSpeed));
  const currentPower = Math.min(engineMcrKw * 1.08, cHull * Math.pow(displacementRatio, 2 / 3) * Math.pow(currentClampedSpeed, speedExponent));
  const currentX = getX(currentSpeed);
  const currentY = getY(currentPower);

  return (
    <div style={{ backgroundColor: 'var(--bg-panel-light)', border: '1px solid var(--border-subtle)', padding: '12px' }}>
      <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px', textTransform: 'uppercase' }}>
        Propulsion Power Curve &amp; Hydrodynamic Clamping ({speedExponent.toFixed(2)} exponent)
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
        {/* Shaded invalid low speed zone */}
        <rect
          x={padding.left}
          y={padding.top}
          width={getX(minSpeed) - padding.left}
          height={plotHeight}
          fill="rgba(153, 98, 30, 0.12)"
        />
        <text x={padding.left + 6} y={padding.top + 14} fontSize="9" fill="var(--color-golden-earth)" fontWeight="700">
          MANEUVER CLAMP (&lt;{minSpeed}kn)
        </text>

        {/* Shaded invalid high speed zone */}
        <rect
          x={getX(maxSpeed)}
          y={padding.top}
          width={width - padding.right - getX(maxSpeed)}
          height={plotHeight}
          fill="rgba(153, 35, 30, 0.12)"
        />
        <text x={getX(maxSpeed) + 6} y={padding.top + 14} fontSize="9" fill="var(--danger)" fontWeight="700">
          MCR EXCEEDED (&gt;{maxSpeed}kn)
        </text>

        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((pct, i) => {
          const yPos = padding.top + (1 - pct) * plotHeight;
          const powerKw = pct * maxPower;
          return (
            <g key={i}>
              <line x1={padding.left} y1={yPos} x2={width - padding.right} y2={yPos} stroke="rgba(115, 158, 130, 0.2)" strokeDasharray="2,2" />
              <text x={padding.left - 6} y={yPos + 4} textAnchor="end" fontSize="9" fill="var(--color-dark-spruce)" fontFamily="var(--font-mono)">
                {(powerKw / 1000).toFixed(0)}k
              </text>
            </g>
          );
        })}

        {/* MCR threshold dashed line */}
        <line
          x1={padding.left}
          y1={getY(engineMcrKw)}
          x2={width - padding.right}
          y2={getY(engineMcrKw)}
          stroke="var(--color-dark-spruce)"
          strokeWidth="1.2"
          strokeDasharray="4,4"
        />
        <text x={width - padding.right - 4} y={getY(engineMcrKw) - 4} textAnchor="end" fontSize="9" fontWeight="700" fill="var(--color-dark-spruce)">
          Rated MCR: {(engineMcrKw / 1000).toFixed(0)} kW
        </text>

        {/* Power curve polyline */}
        <polyline fill="none" stroke="var(--color-dark-spruce)" strokeWidth="2.5" points={pointsString} />

        {/* Design speed line */}
        <line x1={getX(designSpeed)} y1={padding.top} x2={getX(designSpeed)} y2={height - padding.bottom} stroke="var(--color-muted-teal)" strokeWidth="1" strokeDasharray="3,3" />
        <text x={getX(designSpeed)} y={height - padding.bottom - 4} textAnchor="middle" fontSize="9" fill="var(--color-muted-teal)">
          Design: {designSpeed}kn
        </text>

        {/* Current Operating point */}
        <circle cx={currentX} cy={currentY} r={6} fill="var(--color-golden-earth)" stroke="#FFFFFF" strokeWidth="2" />

        {/* Axes */}
        <line x1={padding.left} y1={height - padding.bottom} x2={width - padding.right} y2={height - padding.bottom} stroke="var(--color-dark-spruce)" strokeWidth="1.2" />
        <line x1={padding.left} y1={padding.top} x2={padding.left} y2={height - padding.bottom} stroke="var(--color-dark-spruce)" strokeWidth="1.2" />

        {/* Axis labels */}
        <text x={width / 2} y={height - 8} textAnchor="middle" fontSize="11" fontWeight="600" fill="var(--color-dark-spruce)">
          Speed Through Water (knots)
        </text>
        <text transform="rotate(-90)" x={-(height / 2)} y={16} textAnchor="middle" fontSize="11" fontWeight="600" fill="var(--color-dark-spruce)">
          Propulsion Power (kW)
        </text>

        {/* Speed ticks */}
        {[8, 12, 16, 20, 24].map((spd) => (
          <text key={spd} x={getX(spd)} y={height - padding.bottom + 14} textAnchor="middle" fontSize="9" fill="var(--color-dark-spruce)" fontFamily="var(--font-mono)">
            {spd}kn
          </text>
        ))}
      </svg>
    </div>
  );
};
