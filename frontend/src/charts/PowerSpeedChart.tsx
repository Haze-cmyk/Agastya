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
  const width = 580;
  const height = 270;
  const padding = { top: 32, right: 35, bottom: 48, left: 65 };
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
  const currentPower = Math.min(
    engineMcrKw * 1.08,
    cHull * Math.pow(displacementRatio, 2 / 3) * Math.pow(currentClampedSpeed, speedExponent)
  );
  const currentX = getX(currentSpeed);
  const currentY = getY(currentPower);

  const mcrMw = (engineMcrKw / 1000).toFixed(0);
  const mcrKwFormatted = Math.round(engineMcrKw).toLocaleString();

  // Clamp zone x bounds
  const xMinSpeed = getX(minSpeed);
  const xMaxSpeed = getX(maxSpeed);
  const midY = padding.top + plotHeight / 2;

  // Operating point tooltip positioning
  const isNearTop = currentY < padding.top + 45;
  const tooltipYOffset = isNearTop ? 22 : -22;

  return (
    <div style={{ backgroundColor: 'var(--bg-panel-light)', border: '1px solid var(--border-subtle)', padding: '14px' }}>
      {/* Top Header & Engineering Legend Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '0.4px', textTransform: 'uppercase' }}>
          Propulsion Power Curve &amp; Hydrodynamic Clamping ({speedExponent.toFixed(2)} Exponent)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
          <span style={{ backgroundColor: 'rgba(146, 20, 12, 0.12)', color: 'var(--oxblood)', padding: '2px 7px', borderRadius: '2px', fontWeight: 700 }}>
            Clamp: &lt;{minSpeed}kn
          </span>
          <span style={{ backgroundColor: 'var(--shadow-grey)', color: 'var(--floral-white)', padding: '2px 7px', borderRadius: '2px', fontWeight: 700 }}>
            MCR: {mcrMw} MW
          </span>
          <span style={{ backgroundColor: 'rgba(146, 20, 12, 0.12)', color: 'var(--oxblood)', padding: '2px 7px', borderRadius: '2px', fontWeight: 700 }}>
            Ceiling: &gt;{maxSpeed}kn
          </span>
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
        {/* Shaded low speed zone (< minSpeed) */}
        <rect
          x={padding.left}
          y={padding.top}
          width={xMinSpeed - padding.left}
          height={plotHeight}
          fill="rgba(146, 20, 12, 0.07)"
        />
        {/* Maneuver clamp label positioned cleanly in the vertical center of the zone, completely away from MCR line and curve */}
        <text
          x={(padding.left + xMinSpeed) / 2}
          y={midY - 4}
          textAnchor="middle"
          fontSize="9"
          fill="var(--oxblood)"
          fontWeight="800"
          letterSpacing="0.4px"
        >
          MANEUVER CLAMP
        </text>
        <text
          x={(padding.left + xMinSpeed) / 2}
          y={midY + 10}
          textAnchor="middle"
          fontSize="8"
          fill="var(--oxblood)"
          fontWeight="600"
        >
          (&lt;{minSpeed}kn)
        </text>

        {/* Shaded high speed zone (> maxSpeed) */}
        <rect
          x={xMaxSpeed}
          y={padding.top}
          width={width - padding.right - xMaxSpeed}
          height={plotHeight}
          fill="rgba(146, 20, 12, 0.08)"
        />
        {/* MCR Exceeded label positioned cleanly in the vertical center of the zone, 70px below the ceiling curve */}
        <text
          x={(xMaxSpeed + width - padding.right) / 2}
          y={midY - 4}
          textAnchor="middle"
          fontSize="9"
          fill="var(--oxblood)"
          fontWeight="800"
          letterSpacing="0.4px"
        >
          MCR EXCEEDED
        </text>
        <text
          x={(xMaxSpeed + width - padding.right) / 2}
          y={midY + 10}
          textAnchor="middle"
          fontSize="8"
          fill="var(--oxblood)"
          fontWeight="600"
        >
          (&gt;{maxSpeed}kn)
        </text>

        {/* Horizontal grid lines */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((pct, i) => {
          const yPos = padding.top + (1 - pct) * plotHeight;
          const powerKw = pct * maxPower;
          return (
            <g key={i}>
              <line
                x1={padding.left}
                y1={yPos}
                x2={width - padding.right}
                y2={yPos}
                stroke="rgba(30, 30, 36, 0.10)"
                strokeDasharray="2,2"
              />
              <text
                x={padding.left - 6}
                y={yPos + 4}
                textAnchor="end"
                fontSize="9"
                fill="var(--shadow-grey)"
                fontFamily="var(--font-mono)"
              >
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
          stroke="var(--shadow-grey)"
          strokeWidth="1.4"
          strokeDasharray="4,4"
        />

        {/* Rated MCR Badge - positioned centered at 13.5 knots where power is only ~10k and space is completely clear */}
        <g transform={`translate(${getX(13.5)}, ${getY(engineMcrKw)})`}>
          <rect
            x={-68}
            y={-15}
            width={136}
            height={14}
            rx={2}
            fill="var(--shadow-grey)"
          />
          <text
            x={0}
            y={-5}
            textAnchor="middle"
            fontSize="9"
            fontWeight="700"
            fill="var(--floral-white)"
            fontFamily="var(--font-mono)"
          >
            Rated MCR: {mcrMw} MW ({mcrKwFormatted} kW)
          </text>
        </g>

        {/* Power curve polyline */}
        <polyline
          fill="none"
          stroke="var(--shadow-grey)"
          strokeWidth="2.5"
          points={pointsString}
        />

        {/* Design speed line */}
        <line
          x1={getX(designSpeed)}
          y1={padding.top}
          x2={getX(designSpeed)}
          y2={height - padding.bottom}
          stroke="var(--border-subtle)"
          strokeWidth="1.2"
          strokeDasharray="3,3"
        />
        <text
          x={getX(designSpeed)}
          y={height - padding.bottom - 8}
          textAnchor="middle"
          fontSize="9"
          fontWeight="700"
          fill="var(--text-muted)"
        >
          Design: {designSpeed}kn
        </text>

        {/* Current Operating Point & Tooltip Badge */}
        <g transform={`translate(${currentX}, ${currentY})`}>
          {/* Operating Point Tooltip Tag */}
          <rect
            x={-52}
            y={tooltipYOffset - 8}
            width={104}
            height={16}
            rx={2}
            fill="var(--oxblood)"
          />
          <text
            x={0}
            y={tooltipYOffset + 4}
            textAnchor="middle"
            fontSize="9"
            fontWeight="700"
            fill="#FFFFFF"
            fontFamily="var(--font-mono)"
          >
            {currentSpeed.toFixed(1)}kn &bull; {(currentPower / 1000).toFixed(1)} MW
          </text>
          {/* Center Point */}
          <circle
            cx={0}
            cy={0}
            r={6.5}
            fill="var(--oxblood)"
            stroke="#FFFFFF"
            strokeWidth="2.5"
          />
        </g>

        {/* Axes */}
        <line
          x1={padding.left}
          y1={height - padding.bottom}
          x2={width - padding.right}
          y2={height - padding.bottom}
          stroke="var(--shadow-grey)"
          strokeWidth="1.5"
        />
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={height - padding.bottom}
          stroke="var(--shadow-grey)"
          strokeWidth="1.5"
        />

        {/* Axis labels */}
        <text
          x={width / 2}
          y={height - 10}
          textAnchor="middle"
          fontSize="11"
          fontWeight="600"
          fill="var(--shadow-grey)"
        >
          Speed Through Water (knots)
        </text>
        <text
          transform="rotate(-90)"
          x={-(height / 2)}
          y={16}
          textAnchor="middle"
          fontSize="11"
          fontWeight="600"
          fill="var(--shadow-grey)"
        >
          Propulsion Power (kW)
        </text>

        {/* Speed ticks */}
        {[8, 12, 16, 20, 24].map((spd) => (
          <text
            key={spd}
            x={getX(spd)}
            y={height - padding.bottom + 16}
            textAnchor="middle"
            fontSize="9"
            fill="var(--shadow-grey)"
            fontFamily="var(--font-mono)"
          >
            {spd}kn
          </text>
        ))}
      </svg>
    </div>
  );
};
