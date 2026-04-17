import React from "react";

const Hexagon = () => {
  return (
    <div className="pointer-events-none absolute inset-0 z-0 flex items-center justify-center">
      {/* Hexagon */}
      <svg
        viewBox="0 0 960 820"
        className="pointer-events-none absolute"
        aria-hidden="true"
        style={{
          width: "840px",
          height: "720px",
          maxWidth: "120vw",
          maxHeight: "115vw",
          right: "-100px",
          top: "0px",
          // top: "auto",
          // left: "auto",
          zIndex: 1,
          overflow: "visible",
        }}
      >
        <polygon
          points="480,90 780,246 780,574 480,730 180,574 180,246"
          fill="none"
          stroke="#ffffff"
          strokeWidth="12"
        />
        <polygon
          points="480,118 758,266 758,554 480,702 202,554 202,266"
          fill="none"
          stroke="#1d4ed8"
          strokeWidth="8"
        />
        <polygon
          points="480,142 734,280 734,540 480,678 226,540 226,280"
          fill="none"
          stroke="#ffffff"
          strokeWidth="12"
        />
        <polygon
          points="480,164 710,294 710,526 480,656 250,526 250,294"
          fill="none"
          stroke="#dc2626"
          strokeWidth="8"
        />
        <image
          href="/assets/pictogram.svg"
          x="390"
          y="320"
          width="180"
          height="180"
          preserveAspectRatio="xMidYMid meet"
        />

        {/* 
      {[
        { x: 480, y: 90, color: "#dc2626" },
        { x: 780, y: 246, color: "#1d4ed8" },
        { x: 780, y: 574, color: "#dc2626" },
        { x: 480, y: 730, color: "#1d4ed8" },
        { x: 180, y: 574, color: "#dc2626" },
        { x: 180, y: 246, color: "#1d4ed8" },
      ].map((dot, idx) => (
        <circle key={idx} cx={dot.x} cy={dot.y} r="18" fill={dot.color} />
      ))} */}
      </svg>
    </div>
  );
};

export default Hexagon;
