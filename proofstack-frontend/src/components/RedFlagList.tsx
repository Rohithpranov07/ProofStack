"use client";

import { motion } from "framer-motion";

interface Flag {
  flag: string;
  severity: string;
  reason: string;
}

interface Props {
  redFlags: {
    flags: Flag[];
    risk_level: string;
  };
}

function getSeverityBorder(severity: string): string {
  switch (severity.toUpperCase()) {
    case "HIGH":
      return "border-l-accent-red";
    case "MEDIUM":
      return "border-l-accent-yellow";
    default:
      return "border-l-accent-primary";
  }
}

function getSeverityBadge(severity: string): string {
  switch (severity.toUpperCase()) {
    case "HIGH":
      return "bg-accent-red/10 text-accent-red";
    case "MEDIUM":
      return "bg-accent-yellow/10 text-accent-yellow";
    default:
      return "bg-accent-primary/10 text-accent-primary";
  }
}

function getRiskColor(level: string): string {
  if (level.toUpperCase().includes("HIGH")) return "text-accent-red";
  if (level.toUpperCase().includes("MODERATE")) return "text-accent-yellow";
  return "text-accent-emerald";
}

export default function RedFlagList({ redFlags }: Props) {
  const flags = redFlags.flags ?? [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="rounded-2xl border border-border-subtle bg-bg-card p-8 shadow-md shadow-black/10"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Risk Signals</h2>
        {redFlags.risk_level && (
          <span
            className={`text-xs font-semibold uppercase tracking-wider ${getRiskColor(
              redFlags.risk_level
            )}`}
          >
            {redFlags.risk_level}
          </span>
        )}
      </div>

      {flags.length === 0 ? (
        <div className="mt-6 rounded-lg border border-border-subtle bg-bg-primary px-6 py-8 text-center">
          <p className="text-sm text-text-muted">
            No major systemic red flags detected.
          </p>
        </div>
      ) : (
        <div className="mt-6 flex flex-col gap-3">
          {flags.map((flag, i) => (
            <motion.div
              key={flag.flag}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.5 + i * 0.1 }}
              className={`rounded-lg border-l-4 bg-bg-primary px-5 py-4 ${getSeverityBorder(
                flag.severity
              )}`}
            >
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-text-primary">
                  {flag.flag}
                </span>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getSeverityBadge(
                    flag.severity
                  )}`}
                >
                  {flag.severity}
                </span>
              </div>
              <p className="mt-1.5 text-sm text-text-muted">{flag.reason}</p>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
