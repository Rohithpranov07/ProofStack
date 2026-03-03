"use client";

import { memo } from "react";
import Link from "next/link";
import type { ProductMindsetEngine } from "@/types/dashboard";

interface ProductMindsetCardProps {
  product: ProductMindsetEngine;
  jobId: string;
}

const INDICATORS = [
  { key: "problem_detection", label: "Problem Statement Detection" },
  { key: "impact_metrics", label: "Impact Metrics Clarity" },
  { key: "deployment_evidence", label: "Deployment Evidence" },
  { key: "originality", label: "Originality Score" },
  { key: "maintenance_recency", label: "Maintenance Recency" },
] as const;

function ProductMindsetCardInner({ product, jobId }: ProductMindsetCardProps) {
  const hasData = product.has_data !== false;

  return (
    <div className="dash-card p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-2 rounded-lg ${hasData ? "bg-purple-50 text-purple-700" : "bg-gray-50 text-gray-400"}`}>
          <span className="material-symbols-outlined text-xl">psychology</span>
        </div>
        <div className="flex-1 min-w-0">
          <h3
            className="text-base font-medium text-gray-900 truncate"
            style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
          >
            Product Mindset
          </h3>
        </div>
        {hasData && (
          <Link
            href={`/dashboard/${jobId}/product-mindset`}
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
            <span className="material-symbols-outlined text-xl text-gray-300">psychology_alt</span>
          </div>
          <p className="text-sm font-medium text-gray-500 mb-1">Engine Not Available</p>
          <p className="text-xs text-gray-400 max-w-[220px]">
            Product mindset analysis was not included in this run. Additional project data is needed to evaluate this dimension.
          </p>
        </div>
      ) : (
        /* Progress bars */
        <div className="space-y-3">
          {INDICATORS.map(({ key, label }) => {
            const value = (product[key] as number) ?? 0;
            const pct = Math.min(value * 100, 100);
            return (
              <div key={key}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-gray-600">{label}</span>
                  <span className="text-xs font-bold text-gray-900">{pct.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-1.5">
                  <div
                    className="h-1.5 rounded-full transition-all duration-500"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: pct >= 80 ? "#7C3AED" : "#A78BFA",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

const ProductMindsetCard = memo(ProductMindsetCardInner);
export default ProductMindsetCard;
