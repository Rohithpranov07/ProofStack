"use client";

import { memo } from "react";
import type { DashboardRecommendation } from "@/types/dashboard";

interface FinalRecommendationCardProps {
  recommendation: DashboardRecommendation;
  username: string;
}

function FinalRecommendationCardInner({ recommendation, username }: FinalRecommendationCardProps) {
  return (
    <div className="dash-card-elevated p-6 relative overflow-hidden">
      {/* Left accent bar */}
      <div className="absolute top-0 left-0 w-1 h-full bg-[#1A73E8]" />

      <div className="flex items-start gap-4 pl-4">
        <span className="material-symbols-outlined text-[#1A73E8] text-3xl mt-0.5">recommend</span>
        <div className="flex-1 min-w-0">
          <h3
            className="text-lg font-bold text-gray-900 mb-2"
            style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
          >
            Final Recommendation
          </h3>
          <p className="text-sm text-gray-600 leading-relaxed max-w-2xl mb-4">
            <strong>{username}</strong> — {recommendation.summary}
          </p>

          {/* Strengths */}
          {recommendation.strengths.length > 0 && (
            <div className="mb-3">
              <span className="text-xs font-bold text-[#1E8E3E] uppercase tracking-wider">
                Strengths
              </span>
              <ul className="mt-1 space-y-0.5">
                {recommendation.strengths.map((s, i) => (
                  <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                    <span className="material-symbols-outlined text-[#1E8E3E] text-xs mt-0.5 filled">
                      check_circle
                    </span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Concerns */}
          {recommendation.concerns.length > 0 && (
            <div className="mb-4">
              <span className="text-xs font-bold text-[#F9AB00] uppercase tracking-wider">
                Concerns
              </span>
              <ul className="mt-1 space-y-0.5">
                {recommendation.concerns.map((c, i) => (
                  <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                    <span className="material-symbols-outlined text-[#F9AB00] text-xs mt-0.5 filled">
                      info
                    </span>
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            <button className="px-5 py-2.5 rounded-lg border border-[#DADCE0] text-gray-700 text-sm font-medium hover:bg-gray-50 transition-colors">
              Flag for Review
            </button>
            <button className="px-5 py-2.5 rounded-lg bg-[#1A73E8] text-white text-sm font-medium shadow-md hover:bg-[#1557b0] hover:-translate-y-0.5 transition-all">
              Proceed to Interview
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const FinalRecommendationCard = memo(FinalRecommendationCardInner);
export default FinalRecommendationCard;
