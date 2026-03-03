"use client";
import { useParams, useRouter } from "next/navigation";
import { useState, useEffect, useCallback } from "react";

interface StepInfo {
  title: string;
  description: string;
  progressDescription: string;
}

const STEPS: StepInfo[] = [
  { title: "Fetching public profiles", description: "Retrieving data from GitHub REST v3, LeetCode GraphQL, and LinkedIn HTTP.", progressDescription: "Retrieved data from GitHub, LeetCode, and LinkedIn APIs." },
  { title: "Resume parsing & entity extraction", description: "Extracting skills, projects, and experience timeline from resume.", progressDescription: "Extracted skills and identified major projects from resume." },
  { title: "Cross-verifying claims (Engines 1–4)", description: "Running GitHub Authenticity, Profile Consistency, LeetCode Pattern, and Red Flag engines.", progressDescription: "Commit entropy, skill mapping, and red flag detection complete." },
  { title: "Calculating ProofStack Trust Score", description: "Aggregating engine outputs with role-weighted PST formula.", progressDescription: "PST score computed with deterministic weighting." },
  { title: "Final Report & Narrative", description: "Generating executive summary and shareable dashboard link.", progressDescription: "Dashboard ready — redirecting..." },
];

export default function AnalysisProgressPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;
  const [currentStep, setCurrentStep] = useState(0);
  const [status, setStatus] = useState("PENDING");
  const [progressPercent, setProgressPercent] = useState(0);
  const [pendingCount, setPendingCount] = useState(0);
  const [retrying, setRetrying] = useState(false);
  const [stale, setStale] = useState(false);

  const handleRetry = useCallback(async () => {
    setRetrying(true);
    setStale(false);
    setPendingCount(0);
    try {
      const res = await fetch(`http://localhost:8000/jobs/${jobId}/retry`, {
        method: "POST",
        headers: { "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "proofstack-demo-2025" },
      });
      if (!res.ok) {
        // Retry not available for this job, redirect to wizard
        router.push("/analyze/review");
        return;
      }
    } catch {
      router.push("/analyze/review");
      return;
    }
    setRetrying(false);
  }, [jobId, router]);

  const poll = useCallback(async () => {
    try {
      const res = await fetch(`http://localhost:8000/jobs/${jobId}`, {
        headers: { "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "proofstack-demo-2025" },
      });
      const data = await res.json();
      setStatus(data.status);
      if (data.status === "COMPLETED") {
        setCurrentStep(5);
        setProgressPercent(100);
        setTimeout(() => router.push(`/dashboard/${jobId}`), 1500);
      } else if (data.status === "FAILED") {
        setCurrentStep(-1);
        setProgressPercent(100);
      } else if (data.status === "RUNNING") {
        setPendingCount(0);
        setStale(false);
        setCurrentStep((prev) => {
          const next = Math.min(prev + 1, 4);
          setProgressPercent(Math.min((next / 5) * 100 + 15, 95));
          return next;
        });
      } else {
        // PENDING
        setCurrentStep(0);
        setProgressPercent(5);
        setPendingCount((prev) => {
          const next = prev + 1;
          // If PENDING for 10+ polls (30+ seconds), mark as stale
          if (next >= 10) setStale(true);
          return next;
        });
      }
    } catch {
      // network error, keep polling
    }
  }, [jobId, router]);

  useEffect(() => {
    poll();
    const interval = setInterval(poll, 3000);
    return () => clearInterval(interval);
  }, [poll]);

  const getStepStatus = (stepIdx: number) => {
    if (status === "COMPLETED") return "done";
    if (stepIdx < currentStep) return "done";
    if (stepIdx === currentStep) return "active";
    return "pending";
  };

  return (
<div className="bg-white dark:bg-[#0f172a] min-h-screen flex flex-col transition-colors duration-200" style={{fontFamily: "'Roboto', sans-serif"}}>
{/* Nav */}
<nav className="border-b border-[#e5e7eb] dark:border-[#334155] bg-white dark:bg-[#0f172a] sticky top-0 z-10">
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div className="flex justify-between h-16">
      <div className="flex items-center">
        <div className="flex-shrink-0 flex items-center">
          <span className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">ProofStack</span>
        </div>
      </div>
      <div className="flex items-center space-x-8">
        <a className="text-sm font-medium text-[#1a73e8] dark:text-[#8ab4f8]" href="#">Analyze</a>
        <a className="text-sm font-medium text-[#5f6368] dark:text-[#94a3b8] hover:text-gray-900 dark:hover:text-white transition-colors" href="#">About</a>
        <button className="p-2 text-[#5f6368] dark:text-[#94a3b8] rounded-full hover:bg-gray-100 dark:hover:bg-gray-800">
          <span className="material-icons text-xl">dark_mode</span>
        </button>
      </div>
    </div>
  </div>
</nav>

{/* Main */}
<main className="flex-grow flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
  {/* Dot pattern bg */}
  <div className="absolute inset-0 pointer-events-none opacity-50 dark:opacity-20 z-0">
    <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] dark:bg-[radial-gradient(#334155_1px,transparent_1px)] [background-size:20px_20px]"></div>
  </div>

  <div className="w-full max-w-2xl relative z-10">
    <div className="text-center mb-10">
      <h1 className="text-3xl font-normal text-[#202124] dark:text-white mb-2">Analyzing Candidate Profile</h1>
      <p className="text-[#5f6368] dark:text-[#94a3b8]">Please wait while we verify data across multiple platforms.</p>
    </div>

    <div className="bg-white dark:bg-[#1e293b] shadow-[0_1px_2px_0_rgba(60,64,67,0.3),0_1px_3px_1px_rgba(60,64,67,0.15)] dark:shadow-none dark:border dark:border-[#334155] rounded-xl overflow-hidden">
      {/* Top progress bar */}
      <div className="w-full bg-gray-100 dark:bg-gray-700 h-1">
        <div className="bg-[#1a73e8] h-1 rounded-r-full transition-all duration-1000 ease-out" style={{width: `${progressPercent}%`}}></div>
      </div>

      <div className="p-6 sm:p-8">
        {STEPS.map((step, i) => {
          const stepStatus = getStepStatus(i);
          return (
          <div key={i} className={`flex items-start ${i < STEPS.length - 1 ? 'mb-8' : ''} ${stepStatus === 'pending' ? 'opacity-50' : ''} ${stepStatus === 'active' ? 'relative' : ''}`}>
            {/* Connector line for active step */}
            {stepStatus === 'active' && i < STEPS.length - 1 && (
            <div className="absolute left-4 top-8 bottom-[-32px] w-0.5 bg-gray-100 dark:bg-gray-700 -z-10"></div>
            )}
            <div className="flex-shrink-0 mr-4">
              {stepStatus === 'done' ? (
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[#1e8e3e]/10 dark:bg-[#81c995]/20 text-[#1e8e3e] dark:text-[#81c995]">
                <span className="material-icons text-sm">check</span>
              </div>
              ) : stepStatus === 'active' ? (
              <div className="relative flex items-center justify-center w-8 h-8">
                <span className="absolute w-full h-full rounded-full border-2 border-[#1a73e8] border-t-transparent animate-spin"></span>
                <div className="w-2.5 h-2.5 bg-[#1a73e8] rounded-full"></div>
              </div>
              ) : (
              <div className="flex items-center justify-center w-8 h-8 rounded-full border border-[#e5e7eb] dark:border-[#334155] bg-white dark:bg-[#0f172a]">
                <span className="text-xs text-[#5f6368] dark:text-[#94a3b8]">{i + 1}</span>
              </div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-center mb-1">
                <h3 className={`text-sm font-medium ${stepStatus === 'active' ? 'text-[#1a73e8] dark:text-[#8ab4f8]' : 'text-[#202124] dark:text-white'}`}>
                  {step.title}
                </h3>
                {stepStatus === 'done' && (
                <span className="text-xs text-[#5f6368] dark:text-[#94a3b8]">Done</span>
                )}
                {stepStatus === 'active' && (
                <span className="text-xs font-medium text-[#1a73e8] dark:text-[#8ab4f8] animate-pulse">Processing...</span>
                )}
              </div>
              {/* Sub-progress bar for active step */}
              {stepStatus === 'active' && (
              <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-1.5 mb-2 overflow-hidden">
                <div className="bg-[#1a73e8] h-1.5 rounded-full w-2/3 relative overflow-hidden">
                  <div className="absolute inset-0 bg-white/30 w-full h-full animate-[shimmer_1.5s_infinite] -translate-x-full"></div>
                </div>
              </div>
              )}
              <p className="text-xs text-[#5f6368] dark:text-[#94a3b8]">
                {stepStatus === 'done' ? step.progressDescription : step.description}
              </p>
            </div>
          </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="bg-[#f8f9fa] dark:bg-gray-800/50 px-6 py-4 flex justify-between items-center border-t border-[#e5e7eb] dark:border-[#334155]">
        <span className="text-xs text-[#5f6368] dark:text-[#94a3b8] flex items-center gap-1">
          <span className="material-icons text-sm">info</span>
          {status === "COMPLETED" ? "Analysis complete! Redirecting..." : status === "FAILED" ? "Analysis failed." : stale ? "Job appears stuck." : "Estimated time remaining: ~45 seconds"}
        </span>
        <div className="flex items-center gap-3">
          {(stale || status === "FAILED") && (
          <button onClick={handleRetry} disabled={retrying} className="text-sm text-white bg-[#1a73e8] hover:bg-[#1765cc] px-4 py-1.5 rounded-full font-medium transition-colors disabled:opacity-50">
            {retrying ? "Retrying..." : "Retry"}
          </button>
          )}
          <button onClick={() => router.push("/analyze")} className="text-sm text-[#5f6368] dark:text-[#94a3b8] hover:text-red-600 dark:hover:text-red-400 font-medium transition-colors">
            Cancel Analysis
          </button>
        </div>
      </div>
    </div>

    <div className="mt-6 text-center">
      <p className="text-xs text-[#5f6368] dark:text-[#94a3b8] opacity-70">
        &copy; 2026 ProofStack. Built for truth.
      </p>
    </div>
  </div>
</main>
</div>
  );
}
