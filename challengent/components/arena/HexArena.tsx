"use client";

import { cn } from "@/lib/utils";
import { getRankEmoji } from "@/lib/utils";
import { AgentSlot, ChallengeInfo } from "@/lib/types";
import { LiveDot } from "@/components/ui/LiveDot";

interface HexArenaProps {
  size?: number;
  agents?: AgentSlot[];
  challenge?: ChallengeInfo;
  animated?: boolean;
  className?: string;
  compact?: boolean;
}

// Hexagon math
const HEX_POINTS = (cx: number, cy: number, r: number) => {
  const pts: [number, number][] = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 2;
    pts.push([cx + r * Math.cos(angle), cy + r * Math.sin(angle)]);
  }
  return pts;
};

const POSITION_ANGLES: Record<string, number> = {
  top: -Math.PI / 2,
  tr: -Math.PI / 6,
  br: Math.PI / 6,
  bottom: Math.PI / 2,
  bl: (5 * Math.PI) / 6,
  tl: (-5 * Math.PI) / 6,
};

export function HexArena({
  size = 520,
  agents = [],
  challenge,
  animated = true,
  className,
  compact = false,
}: HexArenaProps) {
  const cx = size / 2;
  const cy = size / 2;
  const hexR = size * 0.35;
  const dotR = size * 0.22;
  const cardR = size * 0.48;

  const hexPoints = HEX_POINTS(cx, cy, hexR);
  const hexPath = hexPoints.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ") + "Z";

  // Pattern dots for floor
  const patternId = `hex-dots-${size}`;

  return (
    <div className={cn("relative", className)} style={{ width: size, height: size }}>
      <svg
        viewBox={`0 0 ${size} ${size}`}
        width={size}
        height={size}
        className="overflow-visible"
      >
        <defs>
          <pattern id={patternId} x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
            <circle cx="10" cy="10" r="1" fill="rgba(0,0,0,0.08)" />
          </pattern>
        </defs>

        {/* Hexagon floor */}
        <path d={hexPath} fill="#ebebE5" stroke="none" />
        <path d={hexPath} fill={`url(#${patternId})`} />

        {/* Edge ropes - alternating red/blue, 3 lines each */}
        {hexPoints.map((pt, i) => {
          const next = hexPoints[(i + 1) % 6];
          const isRed = i % 2 === 0;
          const color = isRed ? "#dc2626" : "#1d4ed8";
          const dx = (next[1] - pt[1]) * 0.01;
          const dy = -(next[0] - pt[0]) * 0.01;
          return (
            <g key={`rope-${i}`}>
              <line x1={pt[0]} y1={pt[1]} x2={next[0]} y2={next[1]} stroke={color} strokeWidth="3" strokeOpacity="0.8" />
              <line x1={pt[0] + dx} y1={pt[1] + dy} x2={next[0] + dx} y2={next[1] + dy} stroke={color} strokeWidth="2" strokeOpacity="0.5" />
              <line x1={pt[0] - dx} y1={pt[1] - dy} x2={next[0] - dx} y2={next[1] - dy} stroke={color} strokeWidth="1" strokeOpacity="0.3" />
            </g>
          );
        })}

        {/* Corner posts */}
        {hexPoints.map((pt, i) => (
          <circle
            key={`post-${i}`}
            cx={pt[0]}
            cy={pt[1]}
            r={6}
            fill={i % 2 === 0 ? "#dc2626" : "#1d4ed8"}
            stroke="white"
            strokeWidth="2"
          />
        ))}

        {/* Inner dashed ring */}
        <circle
          cx={cx}
          cy={cy}
          r={dotR}
          fill="none"
          stroke="rgba(0,0,0,0.1)"
          strokeWidth="1"
          strokeDasharray="6 4"
        />

        {/* Agent dots on inner ring + VS lines */}
        {agents.map((agent) => {
          const angle = POSITION_ANGLES[agent.position];
          const x = cx + dotR * Math.cos(angle);
          const y = cy + dotR * Math.sin(angle);
          const isTop3 = agent.rank <= 3;
          const dotColor = agent.rank <= 2 ? "#dc2626" : agent.rank <= 4 ? "#1d4ed8" : "#059669";

          return (
            <g key={`dot-${agent.position}`}>
              {/* VS line from center to dot */}
              <line
                x1={cx}
                y1={cy}
                x2={x}
                y2={y}
                stroke="rgba(0,0,0,0.06)"
                strokeWidth="1"
                strokeDasharray="4 3"
              />
              {/* Agent dot */}
              <circle
                cx={x}
                cy={y}
                r={isTop3 ? 8 : 6}
                fill={dotColor}
                stroke="white"
                strokeWidth="2"
                className={animated ? "transition-all duration-700" : ""}
              />
            </g>
          );
        })}

        {/* Center circle */}
        <circle
          cx={cx}
          cy={cy}
          r={size * 0.12}
          fill="white"
          stroke="rgba(0,0,0,0.08)"
          strokeWidth="1.5"
        />

        {/* Center text */}
        {challenge && (
          <>
            <text
              x={cx}
              y={cy - (compact ? 8 : 12)}
              textAnchor="middle"
              className="font-label"
              fontSize={compact ? 9 : 11}
              fill="#111"
              fontWeight="600"
            >
              {challenge.title.length > 12
                ? challenge.title.slice(0, 12) + "..."
                : challenge.title}
            </text>
            <text
              x={cx}
              y={cy + (compact ? 6 : 8)}
              textAnchor="middle"
              className="font-title"
              fontSize={compact ? 16 : 20}
              fill="#dc2626"
            >
              {challenge.bounty} NEAR
            </text>
          </>
        )}
      </svg>

      {/* LIVE indicator */}
      {challenge?.isLive && (
        <div className="absolute" style={{ top: cy - size * 0.12 - 22, left: cx - 20 }}>
          <LiveDot />
        </div>
      )}

      {/* Agent slot cards (outside hex) */}
      {!compact &&
        agents.map((agent) => {
          const angle = POSITION_ANGLES[agent.position];
          const x = cx + cardR * Math.cos(angle);
          const y = cy + cardR * Math.sin(angle);

          return (
            <div
              key={`card-${agent.position}`}
              className={cn(
                "absolute bg-white border border-border rounded-md px-3 py-2 shadow-sm",
                "transition-all duration-700 -translate-x-1/2 -translate-y-1/2",
                animated && "hover:scale-105"
              )}
              style={{ left: x, top: y, minWidth: 120 }}
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">{getRankEmoji(agent.rank)}</span>
                <div>
                  <div className="font-label text-xs font-semibold uppercase tracking-wider truncate max-w-[80px]">
                    {agent.name}
                  </div>
                  <div className="font-title text-red text-lg leading-none">
                    {agent.score.toFixed(1)}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
    </div>
  );
}
