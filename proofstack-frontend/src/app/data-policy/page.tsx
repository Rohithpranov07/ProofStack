import type { Metadata } from "next";
import Link from "next/link";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Data Handling & Processing Policy — ProofStack",
  description:
    "Understand how ProofStack handles data. Deterministic scoring, strict minimization, and full auditability — no black-box AI.",
};

const sections = [
  { id: "data-minimization", label: "Data Minimization" },
  { id: "public-data-principle", label: "Public Data Principle" },
  { id: "deterministic-scoring", label: "Deterministic Scoring" },
  { id: "retention-schedule", label: "Retention Schedule" },
  { id: "auditability", label: "Auditability" },
  { id: "encryption", label: "Encryption" },
  { id: "deletion-requests", label: "Deletion Requests" },
];

export default function DataPolicyPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background-light dark:bg-background-dark font-display text-text-primary-light dark:text-text-primary-dark antialiased" style={{ fontFamily: "'Inter', sans-serif" }}>

      <main className="flex-grow">
        <div className="mx-auto max-w-4xl px-6 py-20">

          {/* Back link */}
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary-light hover:text-google-blue dark:text-text-secondary-dark dark:hover:text-google-blue transition-colors mb-10"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            Back to Home
          </Link>

          {/* Title */}
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-3">Data Handling &amp; Processing Policy</h1>
          <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark mb-6">Last Updated: January 2026</p>
          <div className="h-px bg-border-light dark:bg-border-dark mb-12" />

          {/* Table of Contents */}
          <nav className="mb-14 rounded-2xl border border-border-light dark:border-border-dark bg-surface-light dark:bg-surface-dark p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary-light dark:text-text-secondary-dark mb-4">Table of Contents</h2>
            <ol className="list-decimal list-inside space-y-2 text-sm">
              {sections.map((s) => (
                <li key={s.id}>
                  <a href={`#${s.id}`} className="text-google-blue hover:underline">{s.label}</a>
                </li>
              ))}
            </ol>
          </nav>

          {/* Content */}
          <article className="prose-container space-y-14 text-text-secondary-light dark:text-text-secondary-dark leading-relaxed">

            {/* 1 */}
            <section id="data-minimization" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">1. Data Minimization</h2>
              <p>ProofStack follows strict data minimization.</p>
              <p className="mt-2">We process only necessary fields.</p>
            </section>

            {/* 2 */}
            <section id="public-data-principle" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">2. Public Data Principle</h2>
              <p>We analyze only publicly accessible information.</p>
              <p className="mt-2">We do not bypass authentication systems.</p>
            </section>

            {/* 3 */}
            <section id="deterministic-scoring" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">3. Deterministic Scoring</h2>
              <p>No black-box AI models are used.</p>
              <p className="mt-2">All scoring is rule-based and traceable.</p>
            </section>

            {/* 4 */}
            <section id="retention-schedule" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">4. Retention Schedule</h2>
              <ul className="list-disc list-inside space-y-1.5 ml-2">
                <li>Cached API responses: Temporary</li>
                <li>Completed reports: Limited retention</li>
                <li>Expired tokens: Automatically invalidated</li>
              </ul>
            </section>

            {/* 5 */}
            <section id="auditability" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">5. Auditability</h2>
              <p>Every trust score can be decomposed into:</p>
              <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
                <li>Engine-level scores</li>
                <li>Weight redistribution logic</li>
                <li>Red flag severity contributions</li>
              </ul>
            </section>

            {/* 6 */}
            <section id="encryption" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">6. Encryption</h2>
              <p>Data in transit protected via HTTPS.</p>
              <p className="mt-2">Database access restricted.</p>
            </section>

            {/* 7 */}
            <section id="deletion-requests" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">7. Deletion Requests</h2>
              <p>Users may request deletion via:</p>
              <p className="mt-2">
                <a href="mailto:support@proofstack.dev" className="text-google-blue hover:underline">support@proofstack.dev</a>
              </p>
            </section>
          </article>
        </div>
      </main>

      <Footer />
    </div>
  );
}
