"use client";

import Link from "next/link";
import { useState } from "react";
import { getDashboardPdfUrl, createShareLink } from "@/lib/api";

interface DetailLayoutProps {
  jobId: string;
  title: string;
  badgeLabel?: string;
  badgeColor?: string;
  children: React.ReactNode;
}

export default function DetailLayout({ jobId, title, badgeLabel, badgeColor, children }: DetailLayoutProps) {
  const [shareState, setShareState] = useState<"idle" | "loading" | "copied">("idle");

  const handleExportPdf = () => {
    window.open(getDashboardPdfUrl(jobId), "_blank");
  };

  const handleShare = async () => {
    setShareState("loading");
    try {
      const { share_url } = await createShareLink(jobId);
      const fullUrl = `${window.location.origin}${share_url}`;
      if (navigator.share) {
        await navigator.share({ title: `ProofStack — ${title}`, url: fullUrl });
        setShareState("idle");
      } else {
        await navigator.clipboard.writeText(fullUrl);
        setShareState("copied");
        setTimeout(() => setShareState("idle"), 2000);
      }
    } catch {
      // Fallback: copy current page URL
      await navigator.clipboard.writeText(window.location.href);
      setShareState("copied");
      setTimeout(() => setShareState("idle"), 2000);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA]" style={{ backgroundImage: "radial-gradient(#e0e0e0 1px, transparent 1px)", backgroundSize: "24px 24px" }}>
      {/* Header nav */}
      <header className="sticky top-0 z-50 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 md:px-10 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href={`/dashboard/${jobId}`}
              className="group flex items-center gap-2 text-[#1A73E8] text-sm font-semibold px-3 py-1.5 -ml-3 rounded-xl transition-all duration-200 ease-out hover:bg-blue-50/70 active:scale-[0.96] active:bg-blue-100/60"
            >
              <span className="material-symbols-outlined text-[20px] transition-transform duration-200 ease-out group-hover:-translate-x-0.5">arrow_back</span>
              <span className="relative">
                Back to Dashboard
                <span className="absolute left-0 -bottom-0.5 h-[1.5px] w-0 bg-[#1A73E8]/60 rounded-full transition-all duration-200 ease-out group-hover:w-full" />
              </span>
            </Link>
            <div className="h-6 w-px bg-slate-300 mx-1" />
            <div className="flex items-baseline gap-1.5">
              <span className="text-sm text-slate-500 font-medium">Analysis Report:</span>
              <span className="text-sm font-semibold text-slate-900">{title}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {badgeLabel && (
              <span
                className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider"
                style={{
                  backgroundColor: badgeColor ? `${badgeColor}15` : "#e8f5e9",
                  color: badgeColor || "#2e7d32",
                  border: `1px solid ${badgeColor ? `${badgeColor}30` : "#c8e6c9"}`,
                }}
              >
                {badgeLabel}
              </span>
            )}
            <button
              onClick={handleShare}
              disabled={shareState === "loading"}
              className="h-9 px-4 rounded-lg bg-white border border-slate-200 text-sm font-semibold text-slate-700 flex items-center gap-1.5 hover:bg-slate-50 transition-colors disabled:opacity-60"
            >
              <span className="material-symbols-outlined text-lg">
                {shareState === "copied" ? "check_circle" : "share"}
              </span>
              {shareState === "copied" ? "Copied!" : shareState === "loading" ? "Sharing…" : "Share"}
            </button>
            <button
              onClick={handleExportPdf}
              className="h-9 px-4 rounded-lg bg-[#1A73E8] text-white text-sm font-semibold flex items-center gap-1.5 shadow-sm hover:bg-[#1557b0] transition-colors"
            >
              <span className="material-symbols-outlined text-lg">picture_as_pdf</span>
              Export PDF
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 md:px-10 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-8 mt-12">
        <div className="max-w-7xl mx-auto px-6 md:px-10 flex items-center justify-between">
          <p className="text-xs text-slate-400">
            &copy; {new Date().getFullYear()} ProofStack Intelligence
          </p>
          <p className="text-xs text-slate-400">
            All data sourced from publicly available profiles.
          </p>
        </div>
      </footer>
    </div>
  );
}
