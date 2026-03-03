"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

interface Props {
  pstScore: number;
  trustLevel: string;
}

function getScoreColor(score: number): string {
  if (score >= 85) return "#10b981";
  if (score >= 70) return "#3b82f6";
  if (score >= 50) return "#f59e0b";
  return "#ef4444";
}

function getScoreClass(score: number): string {
  if (score >= 85) return "text-accent-emerald";
  if (score >= 70) return "text-accent-primary";
  if (score >= 50) return "text-accent-yellow";
  return "text-accent-red";
}

function getGlowClass(score: number): string {
  if (score >= 85) return "shadow-accent-emerald/20";
  if (score >= 70) return "shadow-accent-primary/20";
  if (score >= 50) return "shadow-accent-yellow/20";
  return "shadow-accent-red/20";
}

export default function TrustScoreCard({ pstScore, trustLevel }: Props) {
  const [displayed, setDisplayed] = useState(0);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    const duration = 1200; // ms
    const start = performance.now();
    const target = pstScore;

    const tick = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayed(Math.round(eased * target * 100) / 100);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      }
    };

    frameRef.current = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(frameRef.current);
  }, [pstScore]);

  const color = getScoreColor(pstScore);
  const scoreClass = getScoreClass(pstScore);
  const glowClass = getGlowClass(pstScore);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={`flex flex-col items-center rounded-2xl border border-border-subtle bg-bg-card p-12 shadow-md shadow-black/10 ${glowClass}`}
    >
      {/* Score number */}
      <div className="relative">
        {/* Subtle glow backdrop */}
        <div
          className="absolute inset-0 blur-3xl opacity-20"
          style={{ backgroundColor: color }}
        />
        <span
          className={`relative text-8xl font-bold tabular-nums tracking-tight ${scoreClass}`}
          style={{ textShadow: `0 0 20px ${color}66` }}
        >
          {displayed.toFixed(1)}
        </span>
      </div>

      {/* Label */}
      <p className="mt-4 text-sm font-medium tracking-widest uppercase text-text-muted">
        ProofStack Trust Score
      </p>

      {/* Trust level badge */}
      <div
        className="mt-5 rounded-full px-5 py-1.5 text-sm font-semibold"
        style={{
          backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
          color,
        }}
      >
        {trustLevel}
      </div>
    </motion.div>
  );
}
