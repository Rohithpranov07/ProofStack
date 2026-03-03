"use client";

import { motion } from "framer-motion";

interface Props {
  trustLevel: string;
  pstScore: number;
}

function getRecommendation(trustLevel: string): {
  text: string;
  tone: string;
} {
  switch (trustLevel) {
    case "Highly Verified":
      return {
        text: "Proceed directly to final technical round.",
        tone: "text-accent-emerald",
      };
    case "Strong":
      return {
        text: "Proceed to technical interview.",
        tone: "text-accent-primary",
      };
    case "Moderate":
      return {
        text: "Proceed with focused technical screening.",
        tone: "text-accent-yellow",
      };
    case "Weak":
      return {
        text: "Manual review recommended.",
        tone: "text-accent-yellow",
      };
    case "High Risk":
      return {
        text: "Strong review required before proceeding.",
        tone: "text-accent-red",
      };
    default:
      return {
        text: "Evaluation pending.",
        tone: "text-text-muted",
      };
  }
}

function getScoreLabel(score: number): string {
  if (score >= 85) return "Exceptional";
  if (score >= 70) return "Above Average";
  if (score >= 50) return "Average";
  if (score >= 30) return "Below Average";
  return "Critical";
}

export default function RecruiterSummary({ trustLevel, pstScore }: Props) {
  const { text, tone } = getRecommendation(trustLevel);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.6 }}
      className="rounded-2xl border border-border-subtle bg-bg-card p-8 shadow-md shadow-black/10"
    >
      <h2 className="text-lg font-semibold">Recruiter Recommendation</h2>
      <p className="mt-1 text-sm text-text-secondary">
        Automated guidance based on the candidate&apos;s trust profile
      </p>

      <div className="mt-8 rounded-lg border border-border-subtle bg-bg-primary px-6 py-6">
        {/* Recommendation */}
        <p className={`text-xl font-semibold leading-relaxed ${tone}`}>
          {text}
        </p>

        {/* Context */}
        <div className="mt-5 flex flex-wrap gap-4 text-sm text-text-muted">
          <div className="flex items-center gap-2">
            <span className="text-text-muted/60">Trust Level:</span>
            <span className="font-medium text-text-primary">{trustLevel}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-text-muted/60">Score Band:</span>
            <span className="font-medium text-text-primary">
              {getScoreLabel(pstScore)}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
