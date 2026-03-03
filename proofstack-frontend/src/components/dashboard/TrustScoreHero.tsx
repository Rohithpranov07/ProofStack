"use client";

import { memo, useMemo } from "react";
import { getTrustBadge } from "@/types/dashboard";
import type { DashboardEngines, EscalationInfo } from "@/types/dashboard";

interface TrustScoreHeroProps {
  score: number;
  trustBand: string;
  engines: DashboardEngines;
  escalation: EscalationInfo;
}

/* ── colour palette per axis ─────────────────────────────── */
const AXIS_COLORS = [
  { dot: "#1A73E8", label: "#1A73E8" }, // GitHub Activity — blue
  { dot: "#34A853", label: "#34A853" }, // Resume Match — green
  { dot: "#FBBC04", label: "#B8960C" }, // Problem Solving — amber
  { dot: "#EA4335", label: "#EA4335" }, // Product Mindset — red
  { dot: "#A142F4", label: "#A142F4" }, // Digital Footprint — purple
  { dot: "#00ACC1", label: "#00ACC1" }, // Resume Intelligence — teal
];

/* ── icons per axis (Material Symbols names) ─────────────── */
const AXIS_ICONS = [
  "code",            // GitHub Activity
  "assignment_ind",  // Resume Match
  "psychology",      // Problem Solving
  "category",        // Product Mindset
  "fingerprint",     // Digital Footprint
  "article",         // Resume Intelligence
];

function TrustScoreHeroInner({ score, trustBand, engines, escalation }: TrustScoreHeroProps) {
  const badge = getTrustBadge(trustBand);
  const hasEscalation = escalation.escalation_reasons.length > 0;

  const axes = useMemo(() => [
    { label: "GitHub Activity", value: engines.github.normalized_score },
    { label: "Resume Match", value: engines.profile.normalized_score },
    { label: "Problem Solving", value: engines.leetcode.normalized_score },
    { label: "Product Mindset", value: engines.product_mindset.normalized_score },
    { label: "Digital Footprint", value: engines.digital_footprint.normalized_score },
    { label: "Resume Intelligence", value: engines.ats_intelligence?.normalized_score ?? 0 },
  ], [engines]);

  /* ── SVG geometry ─────────────────────────────────────── */
  const cx = 50, cy = 50, maxR = 40;
  const n = axes.length;

  // Build concentric hexagon grid lines at 25%, 50%, 75%, 100%
  const gridLevels = [0.25, 0.5, 0.75, 1.0];

  const hexAtLevel = (level: number) =>
    Array.from({ length: n }, (_, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const r = level * maxR;
      return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
    }).join(" ");

  // Axis spokes (center → outer vertex)
  const spokeEnds = Array.from({ length: n }, (_, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    return { x: cx + maxR * Math.cos(angle), y: cy + maxR * Math.sin(angle) };
  });

  // Data polygon
  const dataPoints = axes.map((a, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    const r = (a.value / 100) * maxR;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  });
  const polyPoints = dataPoints.map((p) => `${p.x},${p.y}`).join(" ");

  // Label positions (pushed slightly outward for readability)
  const labelPositions = axes.map((_, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    const r = maxR + 9;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  });

  return (
    <div className="dash-card p-6 relative overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h2
            className="text-lg font-semibold text-gray-900 dark:text-white"
            style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
          >
            Global Trust Score
          </h2>
          <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">Computed via PST Engine</p>
        </div>
        <span
          className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-sm"
          style={{
            background: badge.bgColor,
            color: badge.color,
            border: `1px solid ${badge.borderColor}`,
          }}
        >
          <span className="material-symbols-outlined text-sm filled">verified</span>
          {badge.label}
        </span>
      </div>

      {/* ─── Radar + Score ─── */}
      <div className="relative flex items-center justify-center" style={{ height: 260 }}>
        {/* SVG radar */}
        <svg viewBox="0 0 100 100" className="w-full h-full max-w-[280px]">
          <defs>
            {/* gradient fill for the data polygon */}
            <linearGradient id="radarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1A73E8" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#A142F4" stopOpacity="0.12" />
            </linearGradient>
            {/* glow filter for data dots */}
            <filter id="dotGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="0.8" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Grid hexagons */}
          {gridLevels.map((lvl) => (
            <polygon
              key={lvl}
              points={hexAtLevel(lvl)}
              fill="none"
              stroke="currentColor"
              className="text-gray-200 dark:text-gray-700"
              strokeWidth="0.3"
            />
          ))}

          {/* Axis spokes */}
          {spokeEnds.map((end, i) => (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={end.x}
              y2={end.y}
              stroke="currentColor"
              className="text-gray-200 dark:text-gray-700"
              strokeWidth="0.3"
            />
          ))}

          {/* Data polygon — gradient fill + coloured stroke */}
          <polygon
            points={polyPoints}
            fill="url(#radarGrad)"
            stroke="#1A73E8"
            strokeWidth="0.8"
            strokeLinejoin="round"
          />

          {/* Data dots — each axis gets its own colour */}
          {dataPoints.map((p, i) => (
            <g key={i} filter="url(#dotGlow)">
              <circle cx={p.x} cy={p.y} r="1.8" fill="white" />
              <circle cx={p.x} cy={p.y} r="1.3" fill={AXIS_COLORS[i].dot} />
            </g>
          ))}

          {/* Axis value labels (percentage) on the spoke */}
          {labelPositions.map((pos, i) => (
            <text
              key={i}
              x={pos.x}
              y={pos.y}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize="3.2"
              fontWeight="600"
              fill={AXIS_COLORS[i].dot}
              style={{ fontFamily: "'Google Sans', sans-serif" }}
            >
              {Math.round(axes[i].value)}
            </text>
          ))}
        </svg>

        {/* Centered score overlay */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <span
              className="text-5xl font-semibold text-gray-900 dark:text-white tracking-tight"
              style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
            >
              {Math.round(score)}
            </span>
            <span className="text-lg text-gray-400 dark:text-gray-500 font-light">/100</span>
          </div>
        </div>
      </div>

      {/* ─── Legend (coloured dots + icons) ─── */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 mt-2">
        {axes.map((a, i) => (
          <div key={a.label} className="flex items-center gap-2 group">
            <span
              className="material-symbols-outlined text-[15px]"
              style={{ color: AXIS_COLORS[i].dot }}
            >
              {AXIS_ICONS[i]}
            </span>
            <span className="text-[11.5px] font-medium text-gray-600 dark:text-gray-400 leading-tight">
              {a.label}
            </span>
            <span
              className="ml-auto text-[11px] font-semibold tabular-nums"
              style={{ color: AXIS_COLORS[i].label }}
            >
              {Math.round(a.value)}
            </span>
          </div>
        ))}
      </div>

      {/* Escalation banner */}
      {hasEscalation && (
        <div className="mt-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-3">
          <div className="flex items-center gap-2 text-[#D93025] text-xs font-bold">
            <span className="material-symbols-outlined text-sm filled">warning</span>
            Score capped due to high-risk anomaly detection.
          </div>
          <ul className="mt-1 text-[11px] text-gray-600 dark:text-gray-400 space-y-0.5">
            {escalation.escalation_reasons.map((r, i) => (
              <li key={i}>• {r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

const TrustScoreHero = memo(TrustScoreHeroInner);
export default TrustScoreHero;
