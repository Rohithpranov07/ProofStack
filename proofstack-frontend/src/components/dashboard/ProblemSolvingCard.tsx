"use client";

import { memo, useMemo } from "react";
import Link from "next/link";
import type { LeetCodeEngine, DifficultyBar } from "@/types/dashboard";

interface ProblemSolvingCardProps {
  leetcode: LeetCodeEngine;
  difficulty: DifficultyBar[];
  jobId: string;
}

/* ── Difficulty tier config ──────────────────────────────── */
const DIFF_META: Record<string, { color: string; bg: string; ring: string; icon: string }> = {
  Easy:   { color: "#1A73E8", bg: "rgba(26,115,232,0.08)",  ring: "rgba(26,115,232,0.25)", icon: "check_circle" },
  Med:    { color: "#F9AB00", bg: "rgba(249,171,0,0.08)",   ring: "rgba(249,171,0,0.25)",  icon: "whatshot" },
  Medium: { color: "#F9AB00", bg: "rgba(249,171,0,0.08)",   ring: "rgba(249,171,0,0.25)",  icon: "whatshot" },
  Hard:   { color: "#D93025", bg: "rgba(217,48,37,0.08)",   ring: "rgba(217,48,37,0.25)",  icon: "local_fire_department" },
};

const DEFAULT_META = { color: "#6B7280", bg: "rgba(107,114,128,0.08)", ring: "rgba(107,114,128,0.25)", icon: "code" };

function ProblemSolvingCardInner({ leetcode, difficulty, jobId }: ProblemSolvingCardProps) {
  const total = leetcode.total_solved;
  const maxVal = Math.max(...difficulty.map((d) => d.value), 1);

  /* percentage ring for the total-solved donut */
  const solvedPct = useMemo(() => {
    // assume ~3000 total leetcode problems as denominator
    const cap = 3200;
    return Math.min((total / cap) * 100, 100);
  }, [total]);

  const circumference = 2 * Math.PI * 36; // r=36
  const strokeDash = (solvedPct / 100) * circumference;

  return (
    <div className="dash-card p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400/20 to-orange-500/10 flex items-center justify-center">
            <span className="material-symbols-outlined text-[18px] text-amber-600">psychology</span>
          </div>
          <div>
            <h3
              className="text-base font-semibold text-gray-900 dark:text-white"
              style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
            >
              Problem Solving
            </h3>
            <p className="text-[10px] font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider mt-0">
              LeetCode &bull; HackerRank
            </p>
          </div>
        </div>
        <Link
          href={`/dashboard/${jobId}/problem-solving`}
          className="text-xs font-medium text-[#1A73E8] hover:underline flex items-center gap-1"
        >
          View Details
          <span className="material-symbols-outlined text-sm">open_in_new</span>
        </Link>
      </div>

      {/* ─── Main layout: Donut left + Difficulty bars right ─── */}
      <div className="flex gap-5 items-center">
        {/* Donut ring */}
        <div className="relative flex-shrink-0" style={{ width: 100, height: 100 }}>
          <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
            {/* background ring */}
            <circle cx="40" cy="40" r="36" fill="none" stroke="#E5E7EB" className="dark:stroke-gray-700" strokeWidth="6" />
            {/* progress ring */}
            <circle
              cx="40" cy="40" r="36"
              fill="none"
              stroke="url(#donutGrad)"
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={`${strokeDash} ${circumference}`}
            />
            <defs>
              <linearGradient id="donutGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#1A73E8" />
                <stop offset="100%" stopColor="#A142F4" />
              </linearGradient>
            </defs>
          </svg>
          {/* center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-xl font-bold text-gray-900 dark:text-white leading-none" style={{ fontFamily: "'Google Sans', sans-serif" }}>
              {total.toLocaleString()}
            </span>
            <span className="text-[9px] font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider mt-0.5">solved</span>
          </div>
        </div>

        {/* Difficulty breakdown bars */}
        <div className="flex-1 space-y-2.5">
          {difficulty.map((d) => {
            const meta = DIFF_META[d.label] ?? DEFAULT_META;
            const pct = (d.value / maxVal) * 100;
            return (
              <div key={d.label}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5">
                    <span
                      className="material-symbols-outlined text-[13px]"
                      style={{ color: meta.color }}
                    >
                      {meta.icon}
                    </span>
                    <span className="text-[11px] font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
                      {d.label}
                    </span>
                  </div>
                  <span
                    className="text-[11px] font-bold tabular-nums"
                    style={{ color: meta.color }}
                  >
                    {d.value.toLocaleString()}
                  </span>
                </div>
                <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: meta.bg }}>
                  <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{
                      width: `${pct}%`,
                      background: `linear-gradient(90deg, ${meta.color}, ${meta.color}cc)`,
                      boxShadow: `0 0 6px ${meta.ring}`,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ─── Footer stats ─── */}
      <div className="mt-5 pt-3 border-t border-gray-100 dark:border-gray-800 grid grid-cols-3 gap-3">
        {/* Rank */}
        <div className="text-center">
          <span className="text-[10px] font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider block">Rank</span>
          <span className="text-sm font-bold text-gray-700 dark:text-gray-300 tabular-nums" style={{ fontFamily: "'Google Sans', sans-serif" }}>
            #{leetcode.ranking.toLocaleString()}
          </span>
        </div>
        {/* Acceptance */}
        <div className="text-center">
          <span className="text-[10px] font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider block">Acceptance</span>
          <span className="text-sm font-bold text-gray-700 dark:text-gray-300 tabular-nums" style={{ fontFamily: "'Google Sans', sans-serif" }}>
            {leetcode.acceptance_rate > 0 ? `${leetcode.acceptance_rate.toFixed(1)}%` : "—"}
          </span>
        </div>
        {/* Archetype */}
        <div className="text-center">
          <span className="text-[10px] font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider block">Type</span>
          <span className="text-sm font-bold text-[#1A73E8] capitalize truncate block" style={{ fontFamily: "'Google Sans', sans-serif" }}>
            {leetcode.archetype?.replace(/_/g, " ") || "—"}
          </span>
        </div>
      </div>
    </div>
  );
}

const ProblemSolvingCard = memo(ProblemSolvingCardInner);
export default ProblemSolvingCard;
