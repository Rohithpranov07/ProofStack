"use client";

import { motion } from "framer-motion";

interface Props {
  title: string;
  icon: string;
  score: number;
  metrics: Record<string, unknown>;
  explanation: Record<string, unknown>;
  delay?: number;
}

/* ------------------------------------------------------------------ */
/*  Score color helpers                                                */
/* ------------------------------------------------------------------ */

function getScoreColor(score: number): string {
  if (score >= 80) return "text-accent-emerald";
  if (score >= 60) return "text-accent-primary";
  if (score >= 40) return "text-accent-yellow";
  return "text-accent-red";
}

function getScoreBg(score: number): string {
  if (score >= 80) return "bg-accent-emerald/10";
  if (score >= 60) return "bg-accent-primary/10";
  if (score >= 40) return "bg-accent-yellow/10";
  return "bg-accent-red/10";
}

/* ------------------------------------------------------------------ */
/*  Formatting helpers                                                 */
/* ------------------------------------------------------------------ */

function formatKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** True when the value is a simple scalar (string, number, boolean, null) */
function isScalar(value: unknown): boolean {
  return (
    value === null ||
    value === undefined ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  );
}

function formatScalar(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number")
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

/** Summarize an array item (object or scalar) into a readable string */
function summarizeItem(item: unknown): string {
  if (isScalar(item)) return formatScalar(item);
  if (typeof item !== "object" || item === null) return String(item);

  const obj = item as Record<string, unknown>;

  // Red-flag style: { flag, severity, reason }
  if ("flag" in obj && "reason" in obj) {
    const sev = obj.severity ? ` [${String(obj.severity)}]` : "";
    return `${obj.flag}${sev} — ${obj.reason}`;
  }

  // Skill mismatch: { skill, claimed_years, observed_years, issue }
  if ("skill" in obj && "issue" in obj) {
    return `${obj.skill}: ${obj.issue}`;
  }

  // Project mismatch: { project, issue }
  if ("project" in obj && "issue" in obj) {
    return `${obj.project}: ${obj.issue}`;
  }

  // Experience item: { company, start_date, end_date }
  if ("company" in obj) {
    return `${obj.company} (${obj.start_date ?? "?"} → ${obj.end_date ?? "?"})`;
  }

  // Score breakdown component: { value, formula, input }
  if ("value" in obj && "formula" in obj) {
    return `${formatScalar(obj.value)} — ${obj.formula}`;
  }

  // Generic: pick the first 3 scalar values
  const parts = Object.entries(obj)
    .filter(([, v]) => isScalar(v))
    .slice(0, 4)
    .map(([k, v]) => `${formatKey(k)}: ${formatScalar(v)}`);
  return parts.join(", ") || JSON.stringify(obj);
}

/* ------------------------------------------------------------------ */
/*  Classify entries into categories                                   */
/* ------------------------------------------------------------------ */

interface ClassifiedEntries {
  scalars: [string, unknown][];
  arrays: [string, unknown[]][];
  objects: [string, Record<string, unknown>][];
}

function classify(data: Record<string, unknown>): ClassifiedEntries {
  const scalars: [string, unknown][] = [];
  const arrays: [string, unknown[]][] = [];
  const objects: [string, Record<string, unknown>][] = [];

  for (const [key, value] of Object.entries(data)) {
    if (isScalar(value)) {
      scalars.push([key, value]);
    } else if (Array.isArray(value)) {
      arrays.push([key, value]);
    } else if (typeof value === "object" && value !== null) {
      objects.push([key, value as Record<string, unknown>]);
    }
  }

  return { scalars, arrays, objects };
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function EngineDetailCard({
  title,
  icon,
  score,
  metrics,
  explanation,
  delay = 0,
}: Props) {
  const m = classify(metrics);
  const e = classify(explanation);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="rounded-2xl border border-border-subtle bg-bg-card p-6 shadow-md shadow-black/10"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl">{icon}</span>
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
        <div
          className={`flex items-center gap-2 rounded-full px-4 py-1.5 ${getScoreBg(score)}`}
        >
          <span className={`text-lg font-bold tabular-nums ${getScoreColor(score)}`}>
            {score.toFixed(1)}
          </span>
          <span className="text-xs text-text-muted">/100</span>
        </div>
      </div>

      {/* ---- Key Metrics (scalars) ---- */}
      {m.scalars.length > 0 && (
        <div className="mt-5">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-muted">
            Key Metrics
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            {m.scalars.map(([key, value]) => (
              <div
                key={key}
                className="flex items-baseline justify-between rounded-lg bg-bg-primary px-4 py-2.5"
              >
                <span className="text-xs text-text-muted">{formatKey(key)}</span>
                <span className="ml-2 text-sm font-medium text-text-primary">
                  {formatScalar(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ---- Detail Lists (arrays of objects / strings) ---- */}
      {m.arrays.map(([key, arr]) => {
        if (arr.length === 0) return null;
        return (
          <div key={key} className="mt-5">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
              {formatKey(key)} ({arr.length})
            </p>
            <div className="space-y-1.5">
              {arr.map((item, i) => (
                <div
                  key={i}
                  className="rounded-lg bg-bg-primary px-4 py-2.5 text-sm text-text-secondary"
                >
                  {summarizeItem(item)}
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {/* ---- Nested objects (score breakdowns etc.) ---- */}
      {m.objects.map(([key, obj]) => {
        const sub = classify(obj);
        return (
          <div key={key} className="mt-5">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
              {formatKey(key)}
            </p>
            {sub.scalars.length > 0 && (
              <div className="grid gap-2 sm:grid-cols-2">
                {sub.scalars.map(([sk, sv]) => (
                  <div
                    key={sk}
                    className="flex items-baseline justify-between rounded-lg bg-bg-primary px-4 py-2.5"
                  >
                    <span className="text-xs text-text-muted">{formatKey(sk)}</span>
                    <span className="ml-2 text-sm font-medium text-text-primary">
                      {formatScalar(sv)}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {/* Render nested objects (e.g. components breakdown) as list items */}
            {sub.objects.map(([nk, nv]) => (
              <div
                key={nk}
                className="mt-2 rounded-lg bg-bg-primary px-4 py-2.5"
              >
                <span className="text-xs font-medium text-text-muted">
                  {formatKey(nk)}
                </span>
                <p className="mt-0.5 text-sm text-text-secondary">
                  {summarizeItem(nv)}
                </p>
              </div>
            ))}
          </div>
        );
      })}

      {/* ---- Analysis Notes (explanation scalars) ---- */}
      {e.scalars.length > 0 && (
        <div className="mt-5">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-muted">
            Analysis Notes
          </p>
          <div className="space-y-2">
            {e.scalars.map(([key, value]) => (
              <div key={key} className="rounded-lg bg-bg-primary px-4 py-2.5">
                <span className="text-xs text-text-muted">{formatKey(key)}</span>
                <p className="mt-0.5 text-sm text-text-secondary">
                  {formatScalar(value)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ---- Explanation breakdowns (nested objects in explanation) ---- */}
      {e.objects.map(([key, obj]) => {
        const sub = classify(obj);
        return (
          <div key={key} className="mt-5">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
              {formatKey(key)}
            </p>
            <div className="space-y-1.5">
              {sub.scalars.map(([sk, sv]) => (
                <div
                  key={sk}
                  className="flex items-baseline justify-between rounded-lg bg-bg-primary px-4 py-2.5"
                >
                  <span className="text-xs text-text-muted">{formatKey(sk)}</span>
                  <span className="ml-2 text-sm font-medium text-text-primary">
                    {formatScalar(sv)}
                  </span>
                </div>
              ))}
              {sub.objects.map(([nk, nv]) => (
                <div
                  key={nk}
                  className="rounded-lg bg-bg-primary px-4 py-2.5"
                >
                  <span className="text-xs font-medium text-text-muted">
                    {formatKey(nk)}
                  </span>
                  <p className="mt-0.5 text-sm text-text-secondary">
                    {summarizeItem(nv)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </motion.div>
  );
}
