"use client";

import { memo } from "react";
import Link from "next/link";
import type { ProfileEngine } from "@/types/dashboard";

interface ProfileConsistencyCardProps {
  profile: ProfileEngine;
  jobId: string;
}

function confidenceColor(c: number): { bg: string; text: string } {
  if (c >= 90) return { bg: "bg-green-100", text: "text-green-800" };
  if (c >= 70) return { bg: "bg-yellow-100", text: "text-yellow-800" };
  return { bg: "bg-red-100", text: "text-red-800" };
}

function ProfileConsistencyCardInner({ profile, jobId }: ProfileConsistencyCardProps) {
  const items = profile.verification_items ?? [];
  const hasData = profile.has_data !== false && items.length > 0;

  return (
    <div className="dash-card overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-[#DADCE0]/50 flex justify-between items-start">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${hasData ? "bg-[#E8F0FE] text-[#1A73E8]" : "bg-gray-100 text-gray-400"}`}>
            <span className="material-symbols-outlined text-xl">verified_user</span>
          </div>
          <div>
            <h3
              className="text-lg font-medium text-gray-900"
              style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
            >
              Profile Consistency Verification
            </h3>
            <p className="text-xs text-gray-500">Cross-reference of claimed vs digital profile</p>
          </div>
        </div>
        {hasData && (
          <Link
            href={`/dashboard/${jobId}/profile-consistency`}
            className="text-xs font-medium text-[#1A73E8] hover:underline flex items-center gap-1"
          >
            View Details
            <span className="material-symbols-outlined text-sm">open_in_new</span>
          </Link>
        )}
      </div>

      {!hasData ? (
        /* Empty state */
        <div className="px-6 py-12 flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-full bg-gray-50 flex items-center justify-center mb-3">
            <span className="material-symbols-outlined text-2xl text-gray-300">description_off</span>
          </div>
          <p className="text-sm font-medium text-gray-500 mb-1">No Resume Data Provided</p>
          <p className="text-xs text-gray-400 max-w-xs">
            Resume or LinkedIn data was not supplied during analysis. Provide resume content to enable cross-reference verification against the digital profile.
          </p>
        </div>
      ) : (
        /* Table */
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-[#DADCE0]/50">
              <tr>
                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider text-left">
                  Data Point
                </th>
                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider text-left">
                  Source A (Resume)
                </th>
                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider text-left">
                  Source B (Digital)
                </th>
                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider text-left">
                  Confidence
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#DADCE0]/30 text-sm">
              {items.map((item, idx) => {
                const cc = confidenceColor(item.confidence);
                return (
                  <tr key={idx} className="hover:bg-blue-50/30 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{item.data_point}</td>
                    <td className="px-6 py-4 text-gray-600">{item.source_a}</td>
                    <td className="px-6 py-4 text-gray-600">{item.source_b}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cc.bg} ${cc.text}`}
                      >
                        {item.confidence}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const ProfileConsistencyCard = memo(ProfileConsistencyCardInner);
export default ProfileConsistencyCard;
