"use client";

import React, { useMemo, useState } from "react";

const GRAPH_SIZE = 480;
const CENTER = GRAPH_SIZE / 2;
const PADDING = 8; // 라벨 없으면 0~4, 라벨 있으면 8~20
const OUTER_RADIUS = GRAPH_SIZE / 2 - PADDING;

const AXIS_LABELS = ["STR", "INT", "DEX", "LUK", "VIT", "WIS"];
const AXIS_VALUES = [0.8, 0.34, 1.0, 0.58, 0.76, 0.79];

const toHexPoints = (radius: number) =>
  Array.from({ length: 6 }, (_, i) => {
    const angle = (Math.PI / 3) * i - Math.PI / 2;
    return {
      x: CENTER + radius * Math.cos(angle),
      y: CENTER + radius * Math.sin(angle),
    };
  });

const HexGraph = () => {
  const [pointerPos, setPointerPos] = useState<{ x: number; y: number } | null>(
    null,
  );

  const rings = useMemo(
    () => [1].map((v) => toHexPoints(OUTER_RADIUS * v)),
    [],
  );
  const ringOutside = useMemo(
    () => [1.8, 1.6, 1.4, 1.2].map((v) => toHexPoints(OUTER_RADIUS * v)),
    [],
  );
  const axisEnds = useMemo(() => toHexPoints(OUTER_RADIUS), []);

  const baseDataPoints = useMemo(() => {
    return AXIS_VALUES.map((value, i) => {
      const angle = (Math.PI / 3) * i - Math.PI / 2;
      const radius = OUTER_RADIUS * value;
      return {
        x: CENTER + radius * Math.cos(angle),
        y: CENTER + radius * Math.sin(angle),
      };
    });
  }, []);

  const animatedDataPoints = useMemo(() => {
    if (!pointerPos) return baseDataPoints;

    const maxDistance = 280;
    const maxPull = 28;

    return baseDataPoints.map((point) => {
      const dx = pointerPos.x - point.x;
      const dy = pointerPos.y - point.y;
      const distance = Math.hypot(dx, dy);

      if (!distance || distance > maxDistance) return point;

      // 가까운 점일수록 더 강하게 반응하도록 감쇠 곡선을 적용한다.
      const influence = Math.pow(1 - distance / maxDistance, 2.2);
      const pull = maxPull * influence;

      return {
        x: point.x + (dx / distance) * pull,
        y: point.y + (dy / distance) * pull,
      };
    });
  }, [baseDataPoints, pointerPos]);

  const dataPolygon = useMemo(
    () => animatedDataPoints.map((point) => `${point.x},${point.y}`).join(" "),
    [animatedDataPoints],
  );

  const handlePointerMove = (event: React.MouseEvent<HTMLDivElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    setPointerPos({
      x: ((event.clientX - bounds.left) / bounds.width) * GRAPH_SIZE,
      y: ((event.clientY - bounds.top) / bounds.height) * GRAPH_SIZE,
    });
  };

  return (
    <div
      className="relative"
      style={{ width: GRAPH_SIZE, height: GRAPH_SIZE }}
      onMouseLeave={() => setPointerPos(null)}
      onMouseMove={handlePointerMove}
    >
      <svg
        viewBox={`0 0 ${GRAPH_SIZE} ${GRAPH_SIZE}`}
        className="h-full w-full overflow-visible"
      >
        {ringOutside.map((ring, ringIndex) => {
          // Even: #ffffff, Odd: alternate #1d4ed8 / #dc2626
          let strokeColor = "#ffffff";
          if (ringIndex % 2 === 1) {
            strokeColor =
              Math.floor(ringIndex / 2) % 2 === 0 ? "#1d4ed8" : "#dc2626";
          }
          return (
            <polygon
              key={`ring-${ringIndex}`}
              points={ring.map((p) => `${p.x},${p.y}`).join(" ")}
              fill="none"
              stroke={strokeColor}
              strokeWidth="6"
            />
          );
        })}
        {rings.map((ring, ringIndex) => (
          <polygon
            key={`ring-${ringIndex}`}
            points={ring.map((p) => `${p.x},${p.y}`).join(" ")}
            fill="none"
            stroke="#ffffff"
            strokeWidth="6"
          />
        ))}

        {/* {axisEnds.map((point, i) => (
          <line
            key={`axis-${i}`}
            x1={CENTER}
            y1={CENTER}
            x2={point.x}
            y2={point.y}
            stroke="#ffffff"
            strokeWidth="4"
          />
        ))} */}

        <polygon
          points={dataPolygon}
          //   fill="rgba(220,38,38,0.43)"
          fill="#dc2626"
          stroke="#dc2626"
          strokeWidth="2"
        />
        {animatedDataPoints.map((point, i) => (
          <circle
            key={`point-${i}`}
            cx={point.x}
            cy={point.y}
            r="8.6"
            fill="#dc2626"
            stroke="white"
            strokeWidth="1"
          />
        ))}
      </svg>
    </div>
  );
};

export default HexGraph;
