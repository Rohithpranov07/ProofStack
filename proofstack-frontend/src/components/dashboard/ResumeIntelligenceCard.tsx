"use client";

import { memo } from "react";
import Link from "next/link";
import type { ATSIntelligenceEngine } from "@/types/dashboard";

interface ResumeIntelligenceCardProps {
  ats: ATSIntelligenceEngine;
  jobId: string;
}

const METRICS: { key: keyof ATSIntelligenceEngine; label: string; format?: "score" | "label" }[] = [
  { key: "structure_score", label: "Structure Quality", format: "score" },
  { key: "skill_authenticity_score", label: "Skill Authenticity", format: "score" },
  { key: "role_alignment_score", label: "Role Alignment", format: "score" },
  { key: "career_consistency_score", label: "Career Consistency", format: "score" },
  { key: "recruiter_readability", label: "Readability", format: "label" },
  { key: "keyword_stuffing_risk", label: "Keyword Stuffing Risk", format: "label" },
];

function riskColor(risk: string): string {
  switch (risk) {
    case "none":
    case "low":
      return "text-green-600";
    case "moderate":
      return "text-amber-600";
    case "high":
    case "critical":
      return "text-red-600";
    default:
      return "text-gray-600";
  }
}

function readabilityColor(label: string): string {
  switch (label) {
    case "Excellent":
      return "text-green-600";
    case "Good":
      return "text-blue-600";
    case "Dense":
      return "text-amber-600";
    case "Overloaded":
      return "text-red-600";
    default:
      return "text-gray-600";
  }
}

function ResumeIntelligenceCardInner({ ats, jobId }: ResumeIntelligenceCardProps) {
  const hasData = ats.has_data !== false;

  return (
    <div className="dash-card p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-2 rounded-lg ${hasData ? "bg-teal-50 text-teal-700" : "bg-gray-50 text-gray-400"}`}>
          <span className="material-symbols-outlined text-xl">description</span>
        </div>
        <div className="flex-1 min-w-0">
          <h3
            className="text-base font-medium text-gray-900 truncate"
            style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
          >
            Resume Intelligence
          </h3>
        </div>
        {hasData && (
          <Link
            href={`/dashboard/${jobId}/resume-intelligence`}
            className="text-xs font-medium text-[#1A73E8] hover:underline flex items-center gap-1 shrink-0"
          >
            Details
            <span className="material-symbols-outlined text-sm">open_in_new</span>
          </Link>
        )}
      </div>

      {!hasData ? (
        /* Empty state */
        <div className="py-8 flex flex-col items-center text-center">
          <div className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center mb-3">
            <span className="material-symbols-outlined text-xl text-gray-300">description</span>
          </div>
          <p className="text-sm font-medium text-gray-500 mb-1">No Resume Provided</p>
          <p className="text-xs text-gray-400 max-w-[220px]">
            Resume intelligence analysis was not included because no resume was uploaded during the analysis wizard.
          </p>
        </div>
      ) : (
        /* Key-value rows */
        <div className="space-y-0">
          {METRICS.map(({ key, label, format }) => {
            const raw = ats[key];
            let display: string;
            let colorClass = "text-gray-900";

            if (format === "score" && typeof raw === "number") {
              display = raw.toFixed(1);
            } else if (format === "label" && typeof raw === "string") {
              display = raw.charAt(0).toUpperCase() + raw.slice(1);
              if (key === "keyword_stuffing_risk") {
                colorClass = riskColor(raw);
              } else if (key === "recruiter_readability") {
                colorClass = readabilityColor(raw);
              }
            } else if (typeof raw === "number") {
              display = raw.toFixed(1);
            } else {
              display = String(raw ?? "—");
            }

            return (
              <div
                key={key}
                className="py-2 border-b border-dashed border-[#DADCE0]/50 flex justify-between items-center last:border-b-0"
              >
                <span className="text-xs text-gray-500">{label}</span>
                <span className={`text-sm font-mono ${colorClass}`}>
                  {display}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

const ResumeIntelligenceCard = memo(ResumeIntelligenceCardInner);
export default ResumeIntelligenceCard;
