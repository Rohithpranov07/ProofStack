"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { getJobStatus } from "@/lib/api";
import type { JobStatusResponse } from "@/types";

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const ANALYSIS_STEPS = [
  "Fetching GitHub repositories...",
  "Analyzing commit behavior...",
  "Cross-verifying resume claims...",
  "Evaluating problem-solving profile...",
  "Detecting systemic red flags...",
  "Computing ProofStack Trust Score...",
] as const;

const STEP_REVEAL_MS = 800;
const POLL_INTERVAL_MS = 2000;
const MIN_DISPLAY_MS = 3000;
const STUCK_TIMEOUT_MS = 30_000;

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

interface Props {
  jobId: string;
}

export default function AnalysisProgress({ jobId }: Props) {
  const router = useRouter();

  /* state */
  const [status, setStatus] = useState<JobStatusResponse["status"]>("PENDING");
  const [visibleStep, setVisibleStep] = useState(0);
  const [errorMessage, setErrorMessage] = useState("");
  const [exiting, setExiting] = useState(false);

  /* refs for cleanup */
  const startTime = useRef(Date.now());
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stepRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const redirectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const statusRef = useRef(status);
  statusRef.current = status;

  /* ---- step progression ---- */

  useEffect(() => {
    stepRef.current = setInterval(() => {
      setVisibleStep((prev) => {
        if (prev >= ANALYSIS_STEPS.length - 1) return prev;
        return prev + 1;
      });
    }, STEP_REVEAL_MS);

    return () => {
      if (stepRef.current) clearInterval(stepRef.current);
    };
  }, []);

  /* ---- handle completion with min display time ---- */

  const handleComplete = useCallback(
    (finalStatus: "COMPLETED" | "FAILED", result?: JobStatusResponse) => {
      /* stop polling & step progression */
      if (pollRef.current) clearInterval(pollRef.current);
      if (stepRef.current) clearInterval(stepRef.current);

      const elapsed = Date.now() - startTime.current;
      const remaining = Math.max(0, MIN_DISPLAY_MS - elapsed);

      const finish = () => {
        /* reveal all steps before completing */
        setVisibleStep(ANALYSIS_STEPS.length - 1);

        if (finalStatus === "COMPLETED") {
          setStatus("COMPLETED");
          setExiting(true);
          redirectRef.current = setTimeout(() => {
            router.push(`/results/${jobId}`);
          }, 1000);
        } else {
          setStatus("FAILED");
          const msg =
            (result?.result as unknown as { detail?: string })?.detail ||
            "Analysis failed. Please try again.";
          setErrorMessage(msg);
        }
      };

      if (remaining > 0) {
        setTimeout(finish, remaining);
      } else {
        finish();
      }
    },
    [jobId, router]
  );

  /* ---- polling ---- */

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const data = await getJobStatus(jobId);
        if (cancelled) return;

        if (data.status === "RUNNING" && statusRef.current !== "RUNNING") {
          setStatus("RUNNING");
        }

        if (data.status === "COMPLETED") {
          handleComplete("COMPLETED", data);
          return;
        }

        if (data.status === "FAILED") {
          handleComplete("FAILED", data);
          return;
        }

        /* detect stuck PENDING jobs */
        if (
          data.status === "PENDING" &&
          Date.now() - startTime.current > STUCK_TIMEOUT_MS
        ) {
          handleComplete("FAILED", {
            job_id: jobId,
            status: "FAILED",
            result: { detail: "Job timed out — the analysis worker may be unavailable. Please try again." } as unknown as null,
          } as JobStatusResponse);
          return;
        }
      } catch {
        /* network hiccup — keep polling */
      }
    };

    poll(); /* immediate first check */
    pollRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
      if (redirectRef.current) clearTimeout(redirectRef.current);
    };
  }, [jobId, handleComplete]);

  /* ---- derived ---- */

  const progress = ((visibleStep + 1) / ANALYSIS_STEPS.length) * 100;
  const isActive = status === "PENDING" || status === "RUNNING";

  /* ================================================================ */
  /*  RENDER                                                           */
  /* ================================================================ */

  /* ---- Failure state ---- */
  if (status === "FAILED") {
    return (
      <div className="mx-auto w-full max-w-[700px] py-16">
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-2xl border border-accent-red/20 bg-bg-card p-10 shadow-md shadow-black/10"
        >
          <div className="flex flex-col items-center text-center">
            {/* X icon */}
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent-red/10">
              <svg
                className="h-7 w-7 text-accent-red"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>

            <h2 className="mt-5 text-xl font-semibold">Analysis Failed</h2>
            <p className="mt-2 max-w-md text-sm text-text-muted">
              {errorMessage}
            </p>

            <button
              type="button"
              onClick={() => router.push("/analyze")}
              className="mt-8 rounded-xl bg-accent-primary px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-accent-primary/20 transition-all duration-200 hover:scale-[1.03] hover:opacity-90"
            >
              Back to Analyze
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  /* ---- Active / Completed state ---- */
  return (
    <div className="mx-auto w-full max-w-[700px] py-20">
      <AnimatePresence>
        {!exiting && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.4 }}
            className="rounded-2xl border border-border-subtle bg-bg-card p-10 shadow-md shadow-black/10"
          >
            {/* Header */}
            <div className="text-center">
              <h1 className="text-2xl font-bold tracking-tight">
                Analyzing Candidate
              </h1>
              <p className="mt-2 text-sm text-text-muted">
                Verifying authenticity across multiple signals
              </p>
            </div>

            {/* Steps */}
            <div className="mt-10 flex flex-col gap-1">
              {ANALYSIS_STEPS.map((label, i) => {
                const isCompleted = i < visibleStep;
                const isCurrent = i === visibleStep && isActive;
                const isFuture = i > visibleStep;

                return (
                  <motion.div
                    key={label}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{
                      opacity: isFuture ? 0.25 : 1,
                      y: 0,
                    }}
                    transition={{
                      duration: 0.3,
                      delay: i * 0.08,
                    }}
                    className="flex items-center gap-3 rounded-lg px-4 py-3"
                  >
                    {/* Icon */}
                    {isCompleted ? (
                      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-emerald/15">
                        <svg
                          className="h-3.5 w-3.5 text-accent-emerald"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={3}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                    ) : isCurrent ? (
                      <div className="relative flex h-6 w-6 shrink-0 items-center justify-center">
                        <div className="absolute h-6 w-6 animate-ping rounded-full bg-accent-primary/20" />
                        <div className="h-2.5 w-2.5 rounded-full bg-accent-primary" />
                      </div>
                    ) : (
                      <div className="flex h-6 w-6 shrink-0 items-center justify-center">
                        <div className="h-1.5 w-1.5 rounded-full bg-text-muted/20" />
                      </div>
                    )}

                    {/* Label */}
                    <span
                      className={`text-sm ${
                        isCompleted
                          ? "text-accent-emerald"
                          : isCurrent
                          ? "font-medium text-text-primary"
                          : "text-text-muted/40"
                      }`}
                    >
                      {label}
                    </span>
                  </motion.div>
                );
              })}
            </div>

            {/* Progress bar */}
            <div className="mt-8">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-border-subtle/30">
                <motion.div
                  className="h-full rounded-full bg-accent-primary"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                />
              </div>
              <p className="mt-3 text-center text-xs text-text-muted">
                {status === "COMPLETED"
                  ? "Analysis complete"
                  : `Step ${visibleStep + 1} of ${ANALYSIS_STEPS.length}`}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Success flash before redirect */}
      <AnimatePresence>
        {exiting && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="rounded-2xl border border-accent-emerald/20 bg-bg-card p-10 text-center shadow-md shadow-black/10"
          >
            <div className="flex flex-col items-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent-emerald/15">
                <svg
                  className="h-7 w-7 text-accent-emerald"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h2 className="mt-5 text-xl font-semibold">Analysis Complete</h2>
              <p className="mt-2 text-sm text-text-muted">
                Redirecting to results...
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
