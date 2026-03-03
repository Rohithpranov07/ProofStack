"use client";
import { useRouter } from "next/navigation";
import { motion, useInView, type Variants } from "framer-motion";
import { useRef } from "react";
import Footer from "@/components/Footer";

/* ── smooth easing — Apple-style ease-out-expo ────────────── */
const smooth: [number, number, number, number] = [0.16, 1, 0.3, 1];

/* ── reusable scroll-triggered wrapper ────────────────────── */
function ScrollReveal({
  children,
  className = "",
  delay = 0,
  y = 24,
  once = true,
  duration = 0.9,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  y?: number;
  once?: boolean;
  duration?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once, margin: "-80px" });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y, filter: "blur(6px)" }}
      animate={
        inView
          ? { opacity: 1, y: 0, filter: "blur(0px)" }
          : { opacity: 0, y, filter: "blur(6px)" }
      }
      transition={{ duration, delay, ease: smooth }}
      style={{ willChange: "transform, opacity, filter" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ── stagger container ────────────────────────────────────── */
function StaggerContainer({
  children,
  className = "",
  stagger = 0.1,
}: {
  children: React.ReactNode;
  className?: string;
  stagger?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={inView ? "visible" : "hidden"}
      variants={{
        hidden: {},
        visible: { transition: { staggerChildren: stagger } },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

const staggerChild: Variants = {
  hidden: { opacity: 0, y: 20, filter: "blur(4px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] },
  },
};

const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.92, filter: "blur(4px)" },
  visible: {
    opacity: 1,
    scale: 1,
    filter: "blur(0px)",
    transition: { type: "spring", stiffness: 80, damping: 20, mass: 0.8 },
  },
};

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="relative flex min-h-screen w-full flex-col overflow-x-hidden bg-background-light dark:bg-background-dark font-display text-text-primary-light dark:text-text-primary-dark antialiased transition-colors duration-200" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* Background effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(#DADCE0_1.5px,transparent_1.5px)] dark:bg-[radial-gradient(#3c4043_1.5px,transparent_1.5px)] [background-size:24px_24px] opacity-60"></div>
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-[#4285F4]/10 rounded-full blur-[120px] dark:bg-[#4285F4]/20 mix-blend-multiply dark:mix-blend-screen"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-[#34A853]/10 rounded-full blur-[120px] dark:bg-[#34A853]/20 mix-blend-multiply dark:mix-blend-screen"></div>
        <div className="absolute top-[40%] right-[-5%] w-[30%] h-[30%] bg-[#FBBC04]/10 rounded-full blur-[100px] dark:bg-[#FBBC04]/15 mix-blend-multiply dark:mix-blend-screen"></div>
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-white/50 dark:border-white/10 glass-panel">
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center gap-2">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg text-white">
              <span className="material-symbols-outlined" style={{ fontSize: 24 }}>verified_user</span>
              <div className="absolute inset-0 rounded-xl bg-white/20"></div>
            </div>
            <span className="text-xl font-semibold tracking-tight text-text-primary-light dark:text-text-primary-dark">ProofStack</span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a className="text-sm font-medium text-text-secondary-light hover:text-google-blue dark:text-text-secondary-dark dark:hover:text-google-blue transition-colors" href="#how-it-works">How It Works</a>
            <a className="text-sm font-medium text-text-secondary-light hover:text-google-blue dark:text-text-secondary-dark dark:hover:text-google-blue transition-colors" href="#engines">Engines</a>
            <a className="text-sm font-medium text-text-secondary-light hover:text-google-blue dark:text-text-secondary-dark dark:hover:text-google-blue transition-colors" href="#scoring">Scoring</a>
           
            <a
              href=""
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-text-secondary-light hover:text-google-blue dark:text-text-secondary-dark dark:hover:text-google-blue transition-colors"
            >
              Docs
            </a>
          </nav>
          <div className="flex items-center gap-4">
            <button onClick={() => router.push("/analyze")} className="flex items-center justify-center rounded-full bg-google-blue px-6 py-2.5 text-sm font-medium text-white shadow-google transition-all hover:bg-blue-600 hover:shadow-google-hover hover:-translate-y-0.5 active:translate-y-0 focus:outline-none focus:ring-2 focus:ring-google-blue focus:ring-offset-2 dark:focus:ring-offset-background-dark">
              Get Started
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-grow relative z-10">
        {/* Hero */}
        <section className="relative pt-16 pb-24 lg:pt-32 lg:pb-36 overflow-visible">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col lg:flex-row items-center gap-16 lg:gap-20">
              <motion.div
                className="flex-1 text-center lg:text-left z-20"
                initial={{ opacity: 0, x: -30, filter: "blur(8px)" }}
                animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                transition={{ duration: 1, ease: smooth }}
                style={{ willChange: "transform, opacity, filter" }}
              >
                <motion.div
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.25, ease: smooth }}
                  className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50/80 px-4 py-1.5 text-xs font-semibold text-google-blue backdrop-blur-sm dark:border-blue-900/50 dark:bg-blue-900/20 dark:text-blue-300 shadow-sm mb-8 transition-transform hover:scale-105 cursor-default"
                >
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-google-blue opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-google-blue"></span>
                  </span>
                  10-Engine Algorithmic Verification
                </motion.div>
                <motion.h1
                  initial={{ opacity: 0, y: 20, filter: "blur(4px)" }}
                  animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                  transition={{ duration: 0.9, delay: 0.4, ease: smooth }}
                  className="text-5xl font-extrabold tracking-tight text-text-primary-light sm:text-7xl dark:text-text-primary-dark mb-8 leading-[1.1]"
                >
                  Résumés describe intent. <br />
                  <span className="bg-google-gradient text-transparent bg-clip-text filter drop-shadow-sm">Evidence proves reality.</span>
                </motion.h1>
                <motion.p
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.9, delay: 0.55, ease: smooth }}
                  className="mx-auto lg:mx-0 mt-6 max-w-2xl text-xl text-text-secondary-light dark:text-text-secondary-dark leading-relaxed font-light"
                >
                  Cross-reference résumé claims against GitHub commit history, LeetCode patterns, and StackOverflow contributions using Shannon entropy, z-score anomaly detection, and behavioral pattern analysis. Trust scores backed by math, not gut feelings.
                </motion.p>
                <motion.div
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.7, ease: smooth }}
                  className="mt-10 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4"
                >
                  <button onClick={() => router.push("/analyze")} className="h-14 w-full sm:w-auto min-w-[180px] rounded-full bg-text-primary-light dark:bg-white px-8 text-base font-semibold text-white dark:text-text-primary-light shadow-lg transition-all hover:shadow-xl hover:-translate-y-1 focus:outline-none focus:ring-2 focus:ring-offset-2 ring-offset-white dark:ring-offset-black">
                    Analyze Candidate
                  </button>
                  <button className="group h-14 w-full sm:w-auto min-w-[180px] rounded-full border border-border-light bg-white px-8 text-base font-medium text-text-secondary-light transition-all hover:border-google-blue hover:text-google-blue hover:bg-blue-50/50 dark:border-border-dark dark:bg-surface-dark dark:text-text-secondary-dark dark:hover:border-google-blue dark:hover:text-google-blue dark:hover:bg-blue-900/10 flex items-center justify-center gap-2">
                    <span className="material-symbols-outlined text-xl group-hover:scale-110 transition-transform">play_circle</span>
                    View Demo
                  </button>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.9, ease: smooth }}
                  className="mt-12 flex items-center justify-center lg:justify-start gap-8 text-sm text-text-secondary-light dark:text-text-secondary-dark"
                >
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-google-green" style={{ fontSize: 20 }}>check_circle</span>
                    No credit card required
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-google-blue" style={{ fontSize: 20 }}>bolt</span>
                    Setup in 2 minutes
                  </div>
                </motion.div>
              </motion.div>

              {/* Hero Card */}
              <motion.div
                className="flex-1 w-full relative h-[600px] flex items-center justify-center"
                style={{ perspective: "2000px", willChange: "transform, opacity, filter" }}
                initial={{ opacity: 0, x: 40, rotateY: -5, filter: "blur(10px)" }}
                animate={{ opacity: 1, x: 0, rotateY: 0, filter: "blur(0px)" }}
                transition={{ duration: 1.2, delay: 0.5, ease: smooth }}
              >
                {/* Floating code snippet */}
                <div className="absolute top-[10%] left-[-5%] bg-white/90 dark:bg-surface-dark/90 p-3 rounded-lg shadow-lg border border-border-light/50 dark:border-border-dark/50 z-10 animate-[float_8s_ease-in-out_infinite_1s]">
                  <pre className="text-[10px] font-mono leading-tight text-text-secondary-light dark:text-text-secondary-dark"><span className="text-google-blue">const</span> verify = <span className="text-google-red">async</span> () =&gt; {"{"}<br />{"  "}<span className="text-google-green">await</span> check(user);<br />{"}"}</pre>
                </div>
                {/* Floating verified badge */}
                <div className="absolute bottom-[20%] right-[-5%] bg-white/90 dark:bg-surface-dark/90 p-3 rounded-lg shadow-lg border border-border-light/50 dark:border-border-dark/50 z-10 animate-[float_7s_ease-in-out_infinite_2s]">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="h-2 w-2 rounded-full bg-google-green"></div>
                    <span className="text-[10px] font-bold text-google-green">Verified</span>
                  </div>
                  <div className="h-1 w-24 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full w-[98%] bg-google-green"></div>
                  </div>
                </div>

                {/* Main profile card */}
                <div className="relative w-[420px] bg-white dark:bg-[#202124] rounded-3xl shadow-2xl border border-white/40 dark:border-white/10 overflow-hidden floating-card">
                  {/* Card header */}
                  <div className="h-24 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 p-6 flex items-start justify-between relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-2xl -mr-10 -mt-10"></div>
                    <div className="flex items-center gap-4 z-10">
                      <div className="h-16 w-16 rounded-2xl bg-white p-1 shadow-lg">
                        <img alt="User" className="h-full w-full rounded-xl object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBZq7v-lYIFbA0-krCSpHVibZ4Vr8KeAraZFw9uoQBdXDr0N4lQRgb9IJMenB4OZrwwWWG4Kgt931FbiZ-qpmtATkV4X2ZEUDy2M228I52ahhkVZcuuMIwi0fX2wONs0edOEbhfETAZhICU3sCR_TJUwuOS4fAzRnLDCUindF5ZJQsVDS-wjUHue5xMQUh1BI11-FkJOXhr1tthDDFFBxp1M8l9tVCgRRo8VcSF8qkcmPIZZgKe1dGkALdI25i3t-_6TXyKUftIv4_p" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-text-primary-light dark:text-text-primary-dark">Alex Chen</h3>
                        <p className="text-xs font-medium text-text-secondary-light dark:text-text-secondary-dark bg-white/50 dark:bg-white/10 px-2 py-0.5 rounded-md inline-block mt-1">Full Stack Engineer</p>
                      </div>
                    </div>
                    <div className="bg-white/80 dark:bg-black/20 backdrop-blur-sm p-2 rounded-lg shadow-sm border border-white/50 dark:border-white/10 z-10">
                      <span className="material-symbols-outlined text-google-blue">verified</span>
                    </div>
                  </div>
                  {/* Card body */}
                  <div className="p-6 space-y-6">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-xs text-text-secondary-light uppercase tracking-wider font-semibold mb-1">Trust Score</p>
                        <div className="flex items-baseline gap-1">
                          <span className="text-4xl font-black text-text-primary-light dark:text-white tracking-tight">98</span>
                          <span className="text-xl text-text-secondary-light dark:text-text-secondary-dark font-medium">/100</span>
                        </div>
                      </div>
                      <div className="h-14 w-14 rounded-full bg-gradient-to-br from-google-green to-emerald-400 shadow-3d-badge flex items-center justify-center text-white font-bold text-lg transform rotate-12">
                        A+
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="group">
                        <div className="flex justify-between text-sm mb-1.5">
                          <span className="font-medium text-text-secondary-light dark:text-text-secondary-dark flex items-center gap-1.5"><span className="material-symbols-outlined text-[16px]">architecture</span> System Design</span>
                          <span className="font-bold text-text-primary-light dark:text-text-primary-dark">Top 5%</span>
                        </div>
                        <div className="h-2.5 w-full bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden shadow-inner">
                          <div className="h-full bg-gradient-to-r from-blue-400 to-blue-600 w-[95%] rounded-full shadow-sm"></div>
                        </div>
                      </div>
                      <div className="group">
                        <div className="flex justify-between text-sm mb-1.5">
                          <span className="font-medium text-text-secondary-light dark:text-text-secondary-dark flex items-center gap-1.5"><span className="material-symbols-outlined text-[16px]">code</span> Algorithms</span>
                          <span className="font-bold text-text-primary-light dark:text-text-primary-dark">Top 8%</span>
                        </div>
                        <div className="h-2.5 w-full bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden shadow-inner">
                          <div className="h-full bg-gradient-to-r from-green-400 to-green-600 w-[92%] rounded-full shadow-sm"></div>
                        </div>
                      </div>
                      <div className="group">
                        <div className="flex justify-between text-sm mb-1.5">
                          <span className="font-medium text-text-secondary-light dark:text-text-secondary-dark flex items-center gap-1.5"><span className="material-symbols-outlined text-[16px]">bug_report</span> Debugging</span>
                          <span className="font-bold text-text-primary-light dark:text-text-primary-dark">Top 2%</span>
                        </div>
                        <div className="h-2.5 w-full bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden shadow-inner">
                          <div className="h-full bg-gradient-to-r from-yellow-400 to-yellow-500 w-[98%] rounded-full shadow-sm"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                  {/* Card footer */}
                  <div className="bg-gray-50 dark:bg-[#252629] p-4 border-t border-border-light dark:border-border-dark flex justify-between items-center">
                    <div className="flex -space-x-2">
                      <div className="h-8 w-8 rounded-full border-2 border-white dark:border-surface-dark bg-purple-100 flex items-center justify-center text-xs font-bold text-purple-600">JD</div>
                      <div className="h-8 w-8 rounded-full border-2 border-white dark:border-surface-dark bg-pink-100 flex items-center justify-center text-xs font-bold text-pink-600">MA</div>
                      <div className="h-8 w-8 rounded-full border-2 border-white dark:border-surface-dark bg-gray-100 flex items-center justify-center text-[10px] font-medium text-gray-500">+3</div>
                    </div>
                    <span className="text-xs font-medium text-green-600 flex items-center gap-1 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded-md">
                      <span className="material-symbols-outlined text-[14px]">thumb_up</span> Recommended
                    </span>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Trusted By */}
        <section className="border-y border-border-light bg-surface-light/50 py-12 dark:border-border-dark dark:bg-black/20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal>
              <p className="text-center text-sm font-semibold text-text-secondary-light uppercase tracking-wider mb-10 opacity-70">Built on verified open APIs</p>
            </ScrollReveal>
            <StaggerContainer className="flex flex-wrap justify-center items-center gap-x-16 gap-y-10" stagger={0.1}>
              <motion.div variants={staggerChild} className="group flex items-center gap-2.5 opacity-40 grayscale hover:grayscale-0 hover:opacity-100 transition-all duration-300 cursor-pointer">
                <span className="material-symbols-outlined text-4xl group-hover:text-gray-900 dark:group-hover:text-white">code</span>
                <span className="text-2xl font-bold text-gray-800 dark:text-gray-200 group-hover:text-gray-900 dark:group-hover:text-white">GitHub REST v3</span>
              </motion.div>
              <motion.div variants={staggerChild} className="group flex items-center gap-2.5 opacity-40 grayscale hover:grayscale-0 hover:opacity-100 transition-all duration-300 cursor-pointer">
                <span className="material-symbols-outlined text-4xl group-hover:text-yellow-500">emoji_events</span>
                <span className="text-2xl font-bold text-gray-800 dark:text-gray-200 group-hover:text-yellow-500">LeetCode GraphQL</span>
              </motion.div>
              <motion.div variants={staggerChild} className="group flex items-center gap-2.5 opacity-40 grayscale hover:grayscale-0 hover:opacity-100 transition-all duration-300 cursor-pointer">
                <span className="material-symbols-outlined text-4xl group-hover:text-orange-500">forum</span>
                <span className="text-2xl font-bold text-gray-800 dark:text-gray-200 group-hover:text-orange-500">StackOverflow API</span>
              </motion.div>
              <motion.div variants={staggerChild} className="group flex items-center gap-2.5 opacity-40 grayscale hover:grayscale-0 hover:opacity-100 transition-all duration-300 cursor-pointer">
                <span className="material-symbols-outlined text-4xl group-hover:text-blue-600">work</span>
                <span className="text-2xl font-bold text-gray-800 dark:text-gray-200 group-hover:text-blue-600">LinkedIn HTTP</span>
              </motion.div>
            </StaggerContainer>
          </div>
        </section>

        {/* Enterprise-grade verification */}
        <section id="engines" className="py-24 bg-white dark:bg-background-dark relative">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal className="text-center max-w-3xl mx-auto mb-20">
              <h2 className="text-3xl sm:text-4xl font-bold text-text-primary-light dark:text-text-primary-dark mb-4 tracking-tight">10 cross-validating verification engines</h2>
              <p className="text-text-secondary-light dark:text-text-secondary-dark text-lg leading-relaxed">Deterministic algorithmic scoring — every score is traceable, reproducible, and mathematically auditable.</p>
            </ScrollReveal>
            <StaggerContainer className="grid grid-cols-1 gap-8 md:grid-cols-3" stagger={0.15}>
              <motion.div variants={staggerChild} className="group relative rounded-3xl border border-border-light bg-surface-light p-8 transition-all hover:bg-white hover:border-blue-200 hover:shadow-card-hover dark:border-border-dark dark:bg-surface-dark dark:hover:border-blue-800/50 dark:hover:bg-[#28292c]">
                <div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100 text-google-blue shadow-sm group-hover:scale-110 transition-transform duration-300 dark:bg-blue-900/30 dark:text-blue-300">
                  <span className="material-symbols-outlined text-[32px]">code_blocks</span>
                </div>
                <h3 className="mb-3 text-xl font-semibold text-text-primary-light dark:text-text-primary-dark group-hover:text-google-blue transition-colors">Commit Authenticity Analysis</h3>
                <p className="text-text-secondary-light dark:text-text-secondary-dark leading-relaxed mb-6">
                  Shannon entropy measures commit message quality. Sliding-window burst detection flags suspicious activity spikes. Z-score anomaly detection catches LOC inflation.
                </p>
                <div className="absolute bottom-8 left-8">
                  <span className="inline-flex items-center text-sm font-semibold text-google-blue dark:text-blue-300">
                    Engines 1 &amp; 1b <span className="material-symbols-outlined ml-1 text-sm">verified</span>
                  </span>
                </div>
                <div className="h-6"></div>
              </motion.div>
              <motion.div variants={staggerChild} className="group relative rounded-3xl border border-border-light bg-surface-light p-8 transition-all hover:bg-white hover:border-red-200 hover:shadow-card-hover dark:border-border-dark dark:bg-surface-dark dark:hover:border-red-800/50 dark:hover:bg-[#28292c]">
                <div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-red-100 text-google-red shadow-sm group-hover:scale-110 transition-transform duration-300 dark:bg-red-900/30 dark:text-red-300">
                  <span className="material-symbols-outlined text-[32px]">compare_arrows</span>
                </div>
                <h3 className="mb-3 text-xl font-semibold text-text-primary-light dark:text-text-primary-dark group-hover:text-google-red transition-colors">Cross-Platform Verification</h3>
                <p className="text-text-secondary-light dark:text-text-secondary-dark leading-relaxed mb-6">
                  Résumé skills cross-referenced against GitHub repos with 50+ framework-to-language mappings. LinkedIn reachability + StackOverflow reputation validation.
                </p>
                <div className="absolute bottom-8 left-8">
                  <span className="inline-flex items-center text-sm font-semibold text-google-red dark:text-red-300">
                    Engines 2 &amp; 6 <span className="material-symbols-outlined ml-1 text-sm">verified</span>
                  </span>
                </div>
                <div className="h-6"></div>
              </motion.div>
              <motion.div variants={staggerChild} className="group relative rounded-3xl border border-border-light bg-surface-light p-8 transition-all hover:bg-white hover:border-green-200 hover:shadow-card-hover dark:border-border-dark dark:bg-surface-dark dark:hover:border-green-800/50 dark:hover:bg-[#28292c]">
                <div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-green-100 text-google-green shadow-sm group-hover:scale-110 transition-transform duration-300 dark:bg-green-900/30 dark:text-green-300">
                  <span className="material-symbols-outlined text-[32px]">fact_check</span>
                </div>
                <h3 className="mb-3 text-xl font-semibold text-text-primary-light dark:text-text-primary-dark group-hover:text-google-green transition-colors">Red Flag Detection</h3>
                <p className="text-text-secondary-light dark:text-text-secondary-dark leading-relaxed mb-6">
                  14 deterministic flag types with explicit severity scoring. Detects tutorial clones, keyword stuffing, timeline mismatches, and cross-repo timestamp overlaps.
                </p>
                <div className="absolute bottom-8 left-8">
                  <span className="inline-flex items-center text-sm font-semibold text-google-green dark:text-green-300">
                    Engines 4 &amp; 8 <span className="material-symbols-outlined ml-1 text-sm">verified</span>
                  </span>
                </div>
                <div className="h-6"></div>
              </motion.div>
            </StaggerContainer>
          </div>
        </section>

        {/* Scale with confidence */}
        <section id="scoring" className="py-24 relative overflow-hidden bg-surface-light dark:bg-[#1E1F21]">
          <div className="absolute inset-0 bg-[radial-gradient(#DADCE0_1.5px,transparent_1.5px)] [background-size:24px_24px] opacity-30"></div>
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
            <ScrollReveal className="mx-auto max-w-4xl text-center mb-16">
              <h2 className="text-3xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-4">System depth, by the numbers</h2>
              <p className="text-text-secondary-light dark:text-text-secondary-dark text-lg">Every number below maps to real code — no marketing inflation.</p>
            </ScrollReveal>
            <StaggerContainer className="grid grid-cols-2 gap-8 md:grid-cols-4" stagger={0.12}>
              <motion.div variants={scaleIn} className="flex flex-col items-center justify-center p-6 text-center group">
                <p className="text-5xl font-bold text-google-blue mb-2 group-hover:scale-110 transition-transform">10</p>
                <p className="text-sm font-semibold uppercase tracking-wider text-text-secondary-light dark:text-text-secondary-dark">Analysis Engines</p>
              </motion.div>
              <motion.div variants={scaleIn} className="flex flex-col items-center justify-center p-6 text-center group">
                <p className="text-5xl font-bold text-google-red mb-2 group-hover:scale-110 transition-transform">14</p>
                <p className="text-sm font-semibold uppercase tracking-wider text-text-secondary-light dark:text-text-secondary-dark">Red Flag Types</p>
              </motion.div>
              <motion.div variants={scaleIn} className="flex flex-col items-center justify-center p-6 text-center group">
                <p className="text-5xl font-bold text-google-yellow mb-2 group-hover:scale-110 transition-transform">3</p>
                <p className="text-sm font-semibold uppercase tracking-wider text-text-secondary-light dark:text-text-secondary-dark">Role-Weighted Profiles</p>
              </motion.div>
              <motion.div variants={scaleIn} className="flex flex-col items-center justify-center p-6 text-center group">
                <p className="text-5xl font-bold text-google-green mb-2 group-hover:scale-110 transition-transform">100%</p>
                <p className="text-sm font-semibold uppercase tracking-wider text-text-secondary-light dark:text-text-secondary-dark">Deterministic Scoring</p>
              </motion.div>
            </StaggerContainer>
          </div>
        </section>

        {/* How It Works — Engine Pipeline */}
        <section id="how-it-works" className="py-24 bg-white dark:bg-background-dark relative">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal className="text-center max-w-3xl mx-auto mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-text-primary-light dark:text-text-primary-dark mb-4 tracking-tight">How It Works</h2>
              <p className="text-text-secondary-light dark:text-text-secondary-dark text-lg leading-relaxed">10 engines execute sequentially, each feeding cross-validation signals to the next. One shared GitHub fetch, zero duplicate API calls.</p>
            </ScrollReveal>
            <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4" stagger={0.08}>
              {[
                { num: "1", label: "GitHub Authenticity", desc: "Shannon entropy + burst detection", icon: "commit", color: "blue" },
                { num: "2", label: "Behavioral Anomaly", desc: "Z-score LOC + timestamp overlap", icon: "psychology", color: "red" },
                { num: "3", label: "Profile Consistency", desc: "50+ skill-to-language mappings", icon: "compare_arrows", color: "green" },
                { num: "4", label: "LeetCode Analysis", desc: "Difficulty distribution + archetypes", icon: "code", color: "yellow" },
                { num: "5", label: "Product Mindset", desc: "Clone detection + deploy evidence", icon: "lightbulb", color: "blue" },
                { num: "6", label: "Digital Footprint", desc: "SO rep + merged PRs + blog check", icon: "public", color: "red" },
                { num: "7", label: "ATS Intelligence", desc: "10-phase resume analysis pipeline", icon: "description", color: "green" },
                { num: "8", label: "Red Flag Engine", desc: "14 flags, cross-engine severity", icon: "flag", color: "yellow" },
                { num: "9", label: "PST Aggregation", desc: "Role-weighted dynamic scoring", icon: "balance", color: "blue" },
                { num: "10", label: "Recruiter Report", desc: "Strengths, concerns, questions", icon: "assignment", color: "red" },
              ].map((engine) => (
                <motion.div
                  key={engine.num}
                  variants={staggerChild}
                  className="relative rounded-2xl border border-border-light bg-surface-light p-5 transition-all hover:shadow-card-hover dark:border-border-dark dark:bg-surface-dark"
                >
                  <div className={`inline-flex h-8 w-8 items-center justify-center rounded-lg text-white text-xs font-bold mb-3 ${
                    engine.color === "blue" ? "bg-google-blue" : engine.color === "red" ? "bg-google-red" : engine.color === "green" ? "bg-google-green" : "bg-google-yellow"
                  }`}>
                    {engine.num}
                  </div>
                  <h4 className="text-sm font-semibold text-text-primary-light dark:text-text-primary-dark mb-1">{engine.label}</h4>
                  <p className="text-xs text-text-secondary-light dark:text-text-secondary-dark leading-relaxed">{engine.desc}</p>
                </motion.div>
              ))}
            </StaggerContainer>
          </div>
        </section>

        

        {/* CTA */}
        <section className="relative overflow-hidden py-32 bg-white dark:bg-background-dark">
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-[300px] left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-gradient-to-b from-blue-50 to-transparent rounded-full blur-3xl opacity-50 dark:from-blue-900/10 dark:to-transparent"></div>
          </div>
          <ScrollReveal className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 relative z-10 text-center" y={30} duration={1}>
            <motion.div
              initial={{ scale: 0.85, opacity: 0, filter: "blur(6px)" }}
              whileInView={{ scale: 1, opacity: 1, filter: "blur(0px)" }}
              viewport={{ once: true }}
              transition={{ type: "spring", stiffness: 90, damping: 18 }}
              className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-white mb-8 shadow-google shadow-blue-200 dark:shadow-none"
            >
              <span className="material-symbols-outlined" style={{ fontSize: 32 }}>verified_user</span>
            </motion.div>
            <h2 className="text-4xl sm:text-5xl font-bold tracking-tight text-text-primary-light dark:text-text-primary-dark mb-6">
              Ready to verify your next hire?
            </h2>
            <p className="mx-auto max-w-2xl text-xl text-text-secondary-light dark:text-text-secondary-dark mb-10 font-light">
              Submit a GitHub username. Get a mathematically auditable trust score in under 90 seconds. No black boxes, no hidden bias — every point is traceable.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <button onClick={() => router.push("/analyze")} className="h-14 min-w-[200px] rounded-full bg-google-blue px-8 text-lg font-medium text-white shadow-google transition-all hover:bg-blue-600 hover:shadow-google-hover hover:-translate-y-1 focus:outline-none focus:ring-2 focus:ring-google-blue focus:ring-offset-2 dark:focus:ring-offset-background-dark">
                Get Started for Free
              </button>
              <button className="h-14 min-w-[200px] rounded-full border border-border-light bg-white px-8 text-lg font-medium text-text-primary-light transition-all hover:bg-gray-50 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-200 focus:ring-offset-2 dark:bg-surface-dark dark:text-white dark:border-border-dark dark:hover:bg-gray-700">
                View Demo
              </button>
            </div>
          </ScrollReveal>
        </section>
      </main>

      {/* Footer */}
      <ScrollReveal y={20} duration={0.8}>
        <Footer />
      </ScrollReveal>
    </div>
  );
}
