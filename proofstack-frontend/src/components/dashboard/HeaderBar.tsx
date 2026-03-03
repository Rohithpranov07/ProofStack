"use client";

import { useState } from "react";
import { getTrustBadge } from "@/types/dashboard";
import type { DashboardResponse } from "@/types/dashboard";

interface HeaderBarProps {
  data: DashboardResponse;
  onExportPdf: () => void;
  onRerun: () => void;
  onShare: () => Promise<void>;
}

export default function HeaderBar({ data, onExportPdf, onRerun, onShare }: HeaderBarProps) {
  const badge = getTrustBadge(data.trust_band);
  const [shareState, setShareState] = useState<"idle" | "loading" | "copied">("idle");
  const initials = data.username
    .split(/[\s_-]/)
    .map((s) => s[0]?.toUpperCase() ?? "")
    .slice(0, 2)
    .join("");

  return (
    <header className="bg-white border-b border-[#DADCE0] sticky top-0 z-50">
      <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-6">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#1A73E8] text-3xl">
              shield_person
            </span>
            <span
              className="font-bold text-xl text-gray-800 tracking-tight"
              style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
            >
              ProofStack
            </span>
          </div>

          <div className="h-6 w-px bg-[#DADCE0] mx-2" />

          {/* User info */}
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-[#1A73E8]/10 flex items-center justify-center text-[#1A73E8] font-bold text-sm">
              {initials}
            </div>
            <div>
              <h1
                className="font-medium text-sm text-gray-900 leading-tight"
                style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
              >
                {data.username}
              </h1>
              <p className="text-xs text-gray-500 leading-tight">
                {data.role_level.charAt(0).toUpperCase() + data.role_level.slice(1)} Level
                Engineer
              </p>
            </div>
            <span
              className="text-[10px] font-bold px-2 py-0.5 rounded-sm uppercase tracking-wider ml-2"
              style={{
                background: badge.bgColor,
                color: badge.color,
                border: `1px solid ${badge.borderColor}`,
              }}
            >
              {badge.label}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRerun}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-[#1A73E8] hover:bg-[#E8F0FE]/50 rounded-full transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">refresh</span>
            Re-run Analysis
          </button>
          <button
            onClick={async () => {
              setShareState("loading");
              try {
                await onShare();
                setShareState("copied");
                setTimeout(() => setShareState("idle"), 2000);
              } catch {
                setShareState("idle");
              }
            }}
            disabled={shareState === "loading"}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-[#DADCE0] hover:bg-slate-50 rounded-full transition-colors disabled:opacity-60"
          >
            <span className="material-symbols-outlined text-[18px]">
              {shareState === "copied" ? "check_circle" : "share"}
            </span>
            {shareState === "copied" ? "Copied!" : shareState === "loading" ? "Sharing…" : "Share"}
          </button>
          <button
            onClick={onExportPdf}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-[#1A73E8] text-white hover:bg-[#1557b0] rounded-full shadow-sm transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
            Export PDF
          </button>
        </div>
      </div>
    </header>
  );
}
