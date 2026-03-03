import type { Metadata } from "next";
import Link from "next/link";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Terms of Service — ProofStack",
  description:
    "Read the Terms of Service governing your use of the ProofStack candidate verification platform.",
};

const sections = [
  { id: "acceptance", label: "Acceptance" },
  { id: "service-description", label: "Service Description" },
  { id: "user-responsibilities", label: "User Responsibilities" },
  { id: "algorithmic-nature", label: "Algorithmic Nature" },
  { id: "limitation-of-liability", label: "Limitation of Liability" },
  { id: "intellectual-property", label: "Intellectual Property" },
  { id: "termination", label: "Termination" },
  { id: "governing-law", label: "Governing Law" },
  { id: "contact", label: "Contact" },
];

export default function TermsPage() {
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
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-3">Terms of Service</h1>
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
            <section id="acceptance" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">1. Acceptance</h2>
              <p>By using ProofStack, you agree to these Terms.</p>
            </section>

            {/* 2 */}
            <section id="service-description" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">2. Service Description</h2>
              <p>ProofStack provides deterministic, algorithmic verification of publicly available technical activity.</p>
              <p className="mt-4">ProofStack does not:</p>
              <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
                <li>Guarantee hiring outcomes</li>
                <li>Provide employment recommendations</li>
                <li>Replace human judgment</li>
              </ul>
            </section>

            {/* 3 */}
            <section id="user-responsibilities" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">3. User Responsibilities</h2>
              <p>Users must:</p>
              <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
                <li>Submit accurate information</li>
                <li>Have authorization to analyze candidate data</li>
                <li>Not misuse the platform for harassment or profiling</li>
              </ul>
            </section>

            {/* 4 */}
            <section id="algorithmic-nature" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">4. Algorithmic Nature</h2>
              <p>
                ProofStack generates probabilistic assessments based on mathematical models including entropy analysis, statistical anomaly detection, and cross-platform consistency checks.
              </p>
              <p className="mt-4 font-medium text-text-primary-light dark:text-text-primary-dark">All outputs are informational and non-binding.</p>
            </section>

            {/* 5 */}
            <section id="limitation-of-liability" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">5. Limitation of Liability</h2>
              <p>ProofStack is provided &quot;as is&quot;.</p>
              <p className="mt-4">We are not liable for:</p>
              <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
                <li>Hiring decisions</li>
                <li>Business losses</li>
                <li>Indirect damages</li>
                <li>Misinterpretation of results</li>
              </ul>
            </section>

            {/* 6 */}
            <section id="intellectual-property" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">6. Intellectual Property</h2>
              <p>All platform code, scoring logic, and design are protected.</p>
            </section>

            {/* 7 */}
            <section id="termination" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">7. Termination</h2>
              <p>We may suspend misuse.</p>
            </section>

            {/* 8 */}
            <section id="governing-law" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">8. Governing Law</h2>
              <p>Applicable laws depend on deployment jurisdiction.</p>
            </section>

            {/* 9 */}
            <section id="contact" className="scroll-mt-24">
              <h2 className="text-2xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">9. Contact</h2>
              <p>
                <a href="mailto:legal@proofstack.dev" className="text-google-blue hover:underline">legal@proofstack.dev</a>
              </p>
            </section>
          </article>
        </div>
      </main>

      <Footer />
    </div>
  );
}
