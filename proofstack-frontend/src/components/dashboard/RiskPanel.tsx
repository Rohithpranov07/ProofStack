"use client";

import { memo } from "react";
import type { RedFlagEngine } from "@/types/dashboard";

interface RiskPanelProps {
  redflag: RedFlagEngine;
}

function RiskPanelInner({ redflag }: RiskPanelProps) {
  const flagCount = redflag.total_flags;
  const flags = redflag.flags ?? [];

  return (
    <div className="dash-card p-0 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[#DADCE0]/50 flex justify-between items-center bg-gray-50">
        <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
          <span className="material-symbols-outlined text-[#D93025] text-lg filled">
            warning
          </span>
          Risk Signals
        </h3>
        <span className="bg-[#D93025]/10 text-[#D93025] text-xs font-bold px-2 py-0.5 rounded-full">
          {flagCount} Detected
        </span>
      </div>

      {/* Flag list */}
      <div className="divide-y divide-[#DADCE0]/30">
        {flags.length === 0 && (
          <div className="p-4 text-center text-xs text-gray-400">
            No risk signals detected.
          </div>
        )}
        {flags.slice(0, 5).map((flag, idx) => (
          <div key={idx} className="p-4 hover:bg-gray-50 transition-colors">
            <div className="flex justify-between items-start mb-2">
              <span className="font-medium text-sm text-gray-900">{flag.flag}</span>
              <SeverityBadge severity={flag.severity} />
            </div>
            <p className="text-xs text-gray-600 mb-2">{flag.reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const isHigh =
    severity.toLowerCase() === "high" || severity.toLowerCase() === "critical";
  const isMed = severity.toLowerCase() === "medium" || severity.toLowerCase() === "med";

  const bg = isHigh ? "#D93025" : isMed ? "#F9AB00" : "#5F6368";

  return (
    <span
      className="text-[10px] font-bold text-white px-1.5 py-0.5 rounded uppercase"
      style={{ background: bg }}
    >
      {severity.length > 4 ? severity.slice(0, 4) : severity}
    </span>
  );
}

const RiskPanel = memo(RiskPanelInner);
export default RiskPanel;
