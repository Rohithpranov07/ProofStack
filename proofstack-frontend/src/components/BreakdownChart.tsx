"use client";

import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface Props {
  componentScores: {
    github_score: number;
    profile_score: number;
    leetcode_score: number;
    redflag_severity: number;
  };
}

function getBarColor(value: number): string {
  if (value >= 80) return "var(--accent-emerald)";
  if (value >= 60) return "var(--accent-primary)";
  if (value >= 40) return "var(--accent-yellow)";
  return "var(--accent-red)";
}

export default function BreakdownChart({ componentScores }: Props) {
  const data = [
    { name: "GitHub", value: Math.round(componentScores.github_score * 10) / 10 },
    { name: "Profile", value: Math.round(componentScores.profile_score * 10) / 10 },
    { name: "LeetCode", value: Math.round(componentScores.leetcode_score * 10) / 10 },
    {
      name: "Red Flags",
      value: Math.round((100 - componentScores.redflag_severity) * 10) / 10,
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="rounded-2xl border border-border-subtle bg-bg-card p-8 shadow-md shadow-black/10"
    >
      <h2 className="text-lg font-semibold">Signal Breakdown</h2>
      <p className="mt-1 text-sm text-text-secondary">
        Individual engine scores across all verification signals
      </p>

      <div className="mt-8 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barSize={48}>
            <XAxis
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "var(--text-muted)", fontSize: 13 }}
            />
            <YAxis
              domain={[0, 100]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "var(--text-muted)", fontSize: 12 }}
              width={36}
            />
            <Tooltip
              cursor={{ fill: "var(--border-subtle)" }}
              contentStyle={{
                backgroundColor: "var(--bg-primary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 8,
                fontSize: 13,
                color: "var(--text-primary)",
              }}
              formatter={(value) => [`${value}`, "Score"]}
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={index} fill={getBarColor(entry.value)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
