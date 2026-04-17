"use client";

import { useMemo } from "react";

const DEFAULT_SIZE = 280;
const DEFAULT_COLORS = [
  "#dc2626",
  "#1d4ed8",
  "#059669",
  "#7c3aed",
  "#f59e0b",
  "#0891b2",
];

export type RadarSeries = {
  id: string;
  label: string;
  values: number[];
  color?: string;
};

type AgentRadarGraphProps = {
  size?: number;
  axisLabels: string[];
  series: RadarSeries[];
};

const toPolygonPoints = (count: number, center: number, radius: number) =>
  Array.from({ length: count }, (_, i) => {
    const angle = (Math.PI * 2 * i) / count - Math.PI / 2;
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
    };
  });

export default function AgentRadarGraph({
  size = DEFAULT_SIZE,
  axisLabels,
  series,
}: AgentRadarGraphProps) {
  const center = size / 2;
  const padding = 14;
  const outerRadius = size / 2 - padding;
  const axisCount = axisLabels.length;

  const rings = useMemo(
    () =>
      [1, 0.8, 0.6, 0.4, 0.2].map((v) =>
        toPolygonPoints(axisCount, center, outerRadius * v),
      ),
    [axisCount, center, outerRadius],
  );

  const axisEnds = useMemo(
    () => toPolygonPoints(axisCount, center, outerRadius),
    [axisCount, center, outerRadius],
  );

  const normalizedSeries = useMemo(() => {
    return series.map((item, index) => {
      const safeValues = axisLabels.map((_, valueIndex) => {
        const raw = item.values[valueIndex] ?? 0;
        return Math.max(0, Math.min(1, raw));
      });

      const points = safeValues.map((value, i) => {
        const angle = (Math.PI * 2 * i) / axisCount - Math.PI / 2;
        const radius = outerRadius * value;
        return {
          x: center + radius * Math.cos(angle),
          y: center + radius * Math.sin(angle),
        };
      });

      return {
        ...item,
        color: item.color ?? DEFAULT_COLORS[index % DEFAULT_COLORS.length],
        points,
      };
    });
  }, [axisCount, axisLabels, center, outerRadius, series]);

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-auto">
        {rings.map((ring, ringIndex) => (
          <polygon
            key={`ring-${ringIndex}`}
            points={ring.map((p) => `${p.x},${p.y}`).join(" ")}
            fill="none"
            stroke={ringIndex % 2 === 0 ? "#ffffff" : "rgba(0,0,0,0.1)"}
            strokeWidth={ringIndex === 0 ? "1" : "1"}
          />
        ))}

        {axisEnds.map((point, i) => (
          <line
            key={`axis-${i}`}
            x1={center}
            y1={center}
            x2={point.x}
            y2={point.y}
            stroke="rgba(0,0,0,0.1)"
            strokeWidth="1"
            strokeDasharray="4 3"
          />
        ))}

        {normalizedSeries.map((item) => (
          <g key={item.id}>
            <polygon
              points={item.points.map((p) => `${p.x},${p.y}`).join(" ")}
              fill={item.color}
              fillOpacity="0.2"
              stroke={item.color}
              strokeWidth="1"
            />
            {item.points.map((point, idx) => (
              <circle
                key={`${item.id}-${idx}`}
                cx={point.x}
                cy={point.y}
                r="2.5"
                fill={item.color}
              />
            ))}
          </g>
        ))}

        {axisEnds.map((point, i) => (
          <text
            key={`axis-label-${i}`}
            x={point.x}
            y={point.y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="font-label fill-ink-2"
            fontSize="6"
          >
            {axisLabels[i]}
          </text>
        ))}
      </svg>

      <div className="mt-4 flex flex-wrap gap-2">
        {normalizedSeries.map((item) => (
          <div
            key={`legend-${item.id}`}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-white px-3 py-1 text-xs text-ink-2"
          >
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
