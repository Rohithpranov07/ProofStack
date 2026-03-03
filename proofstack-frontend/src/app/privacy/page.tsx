import type { Metadata } from "next";
import Link from "next/link";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Privacy Policy — ProofStack",
  description:
    "Learn how ProofStack collects, uses, and protects your data. We follow strict data minimization and algorithmic transparency principles.",
};

const sections = [
  { id: "introduction", label: "Introduction" },
  { id: "information-we-collect", label: "Information We Collect" },
  { id: "how-we-use-information", label: "How We Use Information" },
  { id: "lawful-basis", label: "Lawful Basis of Processing" },
  { id: "data-retention", label: "Data Retention" },
  { id: "security-measures", label: "Security Measures" },
  { id: "candidate-rights", label: "Candidate Rights" },
  { id: "international-transfers", label: "International Data Transfers" },
  { id: "changes", label: "Changes to Policy" },
  { id: "contact", label: "Contact" },
];

export default function PrivacyPage() {
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
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-3">Privacy Policy</h1>
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
            <section id="introduction" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">1. Introduction</h2>
              <p>
                ProofStack (&quot;we&quot;, &quot;our&quot;, &quot;us&quot;) is a deterministic candidate verification platform that analyzes publicly available technical signals to generate structured trust assessments.
              </p>
              <p className="mt-4">
                This Privacy Policy explains how we collect, use, process, store, and protect information when you use our platform.
              </p>
              <p className="mt-4">
                ProofStack is designed around principles of minimal data collection, algorithmic transparency, and auditability.
              </p>
            </section>

            {/* 2 */}
            <section id="information-we-collect" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">2. Information We Collect</h2>

              <h3 className="text-lg font-semibold text-text-primary-light dark:text-text-primary-dark mt-6 mb-3">2.1 Information Provided by Users</h3>
              <ul className="list-disc list-inside space-y-1.5 ml-2">
                <li>GitHub usernames</li>
                <li>LeetCode usernames</li>
                <li>Resume files (if uploaded)</li>
                <li>Role level selections</li>
                <li>Optional LinkedIn profile URLs</li>
              </ul>

              <h3 className="text-lg font-semibold text-text-primary-light dark:text-text-primary-dark mt-6 mb-3">2.2 Publicly Available Data</h3>
              <p>ProofStack analyzes only publicly accessible data including:</p>
              <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
                <li>Public GitHub repositories</li>
                <li>Public commit history</li>
                <li>Public repository metadata</li>
                <li>Public StackOverflow contributions</li>
                <li>Public LeetCode activity statistics</li>
              </ul>
              <p className="mt-4 font-medium text-text-primary-light dark:text-text-primary-dark">ProofStack does not access private repositories or private accounts.</p>

              <h3 className="text-lg font-semibold text-text-primary-light dark:text-text-primary-dark mt-6 mb-3">2.3 Technical Metadata</h3>
              <ul className="list-disc list-inside space-y-1.5 ml-2">
                <li>IP address (for abuse prevention)</li>
                <li>Browser type</li>
                <li>Device information</li>
                <li>Request timestamps</li>
              </ul>
            </section>

            {/* 3 */}
            <section id="how-we-use-information" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">3. How We Use Information</h2>
              <p>We use collected information solely to:</p>
              <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
                <li>Generate deterministic trust scores</li>
                <li>Detect anomaly patterns</li>
                <li>Cross-reference skill claims</li>
                <li>Produce structured verification reports</li>
                <li>Improve platform stability and performance</li>
              </ul>
              <p className="mt-6 font-medium text-text-primary-light dark:text-text-primary-dark">We do NOT:</p>
              <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
                <li>Sell user data</li>
                <li>Share personal data with advertisers</li>
                <li>Use data for profiling outside verification</li>
                <li>Train external AI models on submitted data</li>
              </ul>
            </section>

            {/* 4 */}
            <section id="lawful-basis" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">4. Lawful Basis of Processing</h2>
              <p>Processing is performed under:</p>
              <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
                <li>Legitimate interest in fraud prevention</li>
                <li>User-provided consent</li>
                <li>Public data analysis principles</li>
              </ul>
            </section>

            {/* 5 */}
            <section id="data-retention" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">5. Data Retention</h2>
              <ul className="list-disc list-inside space-y-1.5 ml-2">
                <li>Analysis results stored for limited retention period</li>
                <li>Share tokens expire automatically</li>
                <li>Public data cached temporarily</li>
                <li>Users may request deletion of stored reports</li>
              </ul>
            </section>

            {/* 6 */}
            <section id="security-measures" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">6. Security Measures</h2>
              <p>We implement:</p>
              <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
                <li>API authentication</li>
                <li>Input validation</li>
                <li>Rate limiting</li>
                <li>Token-based sharing controls</li>
                <li>Isolated job processing</li>
                <li>Secure database access controls</li>
              </ul>
            </section>

            {/* 7 */}
            <section id="candidate-rights" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">7. Candidate Rights</h2>
              <p>Candidates may:</p>
              <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
                <li>Request access to analysis reports</li>
                <li>Request correction</li>
                <li>Request deletion</li>
                <li>Object to processing</li>
                <li>Withdraw consent</li>
              </ul>
            </section>

            {/* 8 */}
            <section id="international-transfers" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">8. International Data Transfers</h2>
              <p>Data may be processed in cloud environments.</p>
              <p className="mt-2">We apply industry-standard safeguards.</p>
            </section>

            {/* 9 */}
            <section id="changes" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">9. Changes to Policy</h2>
              <p>We may update this policy.</p>
              <p className="mt-2">Updated version will include new revision date.</p>
            </section>

            {/* 10 */}
            <section id="contact" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">10. Contact</h2>
              <p>
                <a href="mailto:privacy@proofstack.dev" className="text-google-blue hover:underline">privacy@proofstack.dev</a>
              </p>
            </section>
          </article>
        </div>
      </main>

      <Footer />
    </div>
  );
}
