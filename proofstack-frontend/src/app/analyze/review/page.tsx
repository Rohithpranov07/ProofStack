"use client";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

interface Step1Data {
  githubUsername: string;
  leetcodeUsername: string;
  linkedinUrl: string;
  linkedinHeadline: string;
  portfolioLinks: string[];
  roleLevel: string;
}
interface Skill { name: string; years: string; }
interface ParsedResumeSkill { name: string; years: number; }
interface ParsedResumeExp { company: string; role: string; start_date: string; end_date: string; }
interface ParsedResumeProject { name: string; tech: string; description: string; }
interface ParsedResume {
  raw_text?: string;
  skills: ParsedResumeSkill[];
  experience: ParsedResumeExp[];
  projects: ParsedResumeProject[];
}
interface Step2Data { skills: Skill[]; parsedResume?: ParsedResume; }
interface Experience { company: string; role: string; startDate: string; endDate: string; description: string; }
interface Project { name: string; tech: string; description: string; link: string; }
interface Step3Data { experiences: Experience[]; projects: Project[]; }

const ROLE_MAP: Record<string, string> = {
  "Junior Level": "entry",
  "Mid Level": "mid",
  "Senior Level": "senior",
  "Staff / Principal": "senior",
};

export default function AnalyzeReviewPage() {
  const router = useRouter();
  const [step1, setStep1] = useState<Step1Data | null>(null);
  const [step2, setStep2] = useState<Step2Data | null>(null);
  const [step3, setStep3] = useState<Step3Data | null>(null);
  const [submitting, setSubmitting] = useState(false);

  /* ── Consent state ────────────────────────────────────── */
  const [consentAuth, setConsentAuth] = useState(false);       // checkbox 1
  const [consentProcess, setConsentProcess] = useState(false);  // checkbox 2
  const [consentPrivacy, setConsentPrivacy] = useState(false);  // checkbox 3
  const [recruiterConfirm, setRecruiterConfirm] = useState(false); // optional
  const [consentError, setConsentError] = useState<string | null>(null);
  const allConsentsGiven = consentAuth && consentProcess && consentPrivacy;

  useEffect(() => {
    const s1 = localStorage.getItem("proofstack_step1");
    const s2 = localStorage.getItem("proofstack_step2");
    const s3 = localStorage.getItem("proofstack_step3");
    if (s1) setStep1(JSON.parse(s1));
    if (s2) setStep2(JSON.parse(s2));
    if (s3) setStep3(JSON.parse(s3));
  }, []);

  const [error, setError] = useState<string | null>(null);

  /* Convert "MM/DD/YYYY" or other date strings to ISO "YYYY-MM-DD" */
  const toISO = (d: string): string => {
    if (!d) return "";
    // Already ISO?
    if (/^\d{4}-\d{2}-\d{2}$/.test(d)) return d;
    // Try MM/DD/YYYY
    const parts = d.split("/");
    if (parts.length === 3) {
      const [mm, dd, yyyy] = parts;
      return `${yyyy}-${mm.padStart(2, "0")}-${dd.padStart(2, "0")}`;
    }
    // Fallback: let Date parse it
    const parsed = new Date(d);
    if (!isNaN(parsed.getTime())) return parsed.toISOString().slice(0, 10);
    return d;
  };

  /* Parse FastAPI 422 detail array into readable string */
  const parseError = (detail: unknown): string => {
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((e: { msg?: string; loc?: string[] }) => {
        const field = e.loc ? e.loc.slice(-1)[0] : "";
        return `${field}: ${e.msg || "invalid"}`;
      }).join("; ");
    }
    return "Please check your inputs.";
  };

  const handleStartAnalysis = async () => {
    if (!step1) {
      setError("Missing profile data. Please go back and fill in Step 1.");
      return;
    }
    /* ── Consent gate (client-side) ─────────────────────── */
    if (!allConsentsGiven) {
      setConsentError("You must accept all three required consent checkboxes before starting the analysis.");
      return;
    }
    setConsentError(null);
    setSubmitting(true);
    setError(null);
    try {
      // Merge manual skills with parsed resume skills (deduplicated)
      const manualSkills = (step2?.skills || []).filter(s => s.name.trim()).map(s => ({ name: s.name.trim(), years: parseFloat(s.years) || 0 }));
      const parsedSkills = (step2?.parsedResume?.skills || []).map(s => ({ name: s.name, years: s.years }));
      const skillMap = new Map<string, number>();
      // Parsed skills first, then manual overrides
      for (const s of parsedSkills) {
        skillMap.set(s.name.toLowerCase(), s.years);
      }
      for (const s of manualSkills) {
        skillMap.set(s.name.toLowerCase(), s.years);
      }
      const mergedSkills = Array.from(skillMap.entries()).map(([name, years]) => {
        // Find the original casing
        const orig = [...manualSkills, ...parsedSkills].find(s => s.name.toLowerCase() === name);
        return { name: orig?.name || name, years };
      });

      // Merge manual experience with parsed resume experience (deduplicated by company name)
      const manualExps = (step3?.experiences || []).filter(e => e.company.trim() || e.role.trim()).map(e => ({
        company: e.company,
        start_date: toISO(e.startDate) || null,
        end_date: toISO(e.endDate) || null,
      }));
      const parsedExps = (step2?.parsedResume?.experience || []).filter(e => e.company.trim()).map(e => ({
        company: e.company,
        start_date: e.start_date || null,
        end_date: e.end_date || null,
      }));
      const expMap = new Map<string, { company: string; start_date: string | null; end_date: string | null }>();
      for (const e of parsedExps) {
        if (e.company && e.company !== "Unknown Company") {
          expMap.set(e.company.toLowerCase(), e);
        }
      }
      for (const e of manualExps) {
        if (e.company) {
          expMap.set(e.company.toLowerCase(), e);
        }
      }
      const mergedExps = Array.from(expMap.values());

      // Merge manual projects with parsed resume projects (deduplicated by name)
      const manualProjects = (step3?.projects || []).filter(p => p.name.trim()).map(p => ({ name: p.name }));
      const parsedProjects = (step2?.parsedResume?.projects || []).filter(p => p.name.trim()).map(p => ({ name: p.name }));
      const projectMap = new Map<string, { name: string }>();
      for (const p of parsedProjects) {
        projectMap.set(p.name.toLowerCase(), p);
      }
      for (const p of manualProjects) {
        projectMap.set(p.name.toLowerCase(), p);
      }
      const mergedProjects = Array.from(projectMap.values());

      const payload = {
        username: step1.githubUsername,
        role_level: ROLE_MAP[step1.roleLevel] || "mid",
        resume_data: {
          skills: mergedSkills,
          projects: mergedProjects,
          experience: mergedExps,
        },
        linkedin_data: step1.linkedinUrl ? {
          profile_url: step1.linkedinUrl || null,
          headline: step1.linkedinHeadline || null,
          skills: mergedSkills.map(s => s.name),
          experience: mergedExps,
        } : null,
        leetcode_username: step1.leetcodeUsername || null,
        resume_text: step2?.parsedResume?.raw_text || null,
        consent: {
          consent_version: "v1.0.0",
          consent_given: true,
          recruiter_confirmation: recruiterConfirm || null,
        },
        recruiter_mode: false,
      };
      const res = await fetch("http://localhost:8000/jobs/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "proofstack-demo-2025",
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => null);
        console.error("Backend error:", res.status, errBody);
        setError(`Analysis request failed (${res.status}). ${parseError(errBody?.detail)}`);
        return;
      }
      const data = await res.json();
      if (data.job_id) {
        router.push(`/analysis/${data.job_id}`);
      } else {
        setError("No job_id returned from server.");
      }
    } catch (err) {
      console.error("Analysis submission failed:", err);
      setError("Network error — is the backend running on localhost:8000?");
    } finally {
      setSubmitting(false);
    }
  };

  return (
<div className="bg-[#F8F9FA] dark:bg-[#111821] min-h-screen flex flex-col antialiased relative" style={{fontFamily: "'Google Sans', sans-serif", color: '#0f172a'}}>
{/* Grid background */}
<div className="fixed inset-0 pointer-events-none z-0">
  <div className="absolute inset-0 bg-[linear-gradient(to_right,#e0e0e0_1px,transparent_1px),linear-gradient(to_bottom,#e0e0e0_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,#333_1px,transparent_1px),linear-gradient(to_bottom,#333_1px,transparent_1px)] opacity-[0.4] dark:opacity-[0.1] grid-bg"></div>
  <div className="absolute top-20 left-10 w-24 h-24 bg-blue-500/5 rounded-full blur-3xl"></div>
  <div className="absolute bottom-40 right-10 w-64 h-64 bg-green-500/5 rounded-full blur-3xl"></div>
</div>

{/* Header */}
<header className="bg-white/80 backdrop-blur-md dark:bg-[#111821]/80 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50 h-16">
  <div className="px-6 flex items-center justify-between w-full h-full mx-auto max-w-[1400px]">
    <div className="flex items-center gap-3">
      <div className="text-primary bg-primary/10 p-1.5 rounded-lg">
        <span className="material-symbols-outlined text-[24px] leading-none">verified_user</span>
      </div>
      <h2 className="text-[20px] font-medium tracking-tight text-slate-800 dark:text-white">ProofStack</h2>
    </div>
    <nav className="hidden md:flex items-center gap-1">
      <a className="text-sm font-medium text-slate-500 dark:text-slate-300 hover:text-primary px-4 py-2 rounded-full hover:bg-blue-50 dark:hover:bg-slate-800 transition-colors" href="#">Dashboard</a>
      <a className="text-sm font-medium text-slate-500 dark:text-slate-300 hover:text-primary px-4 py-2 rounded-full hover:bg-blue-50 dark:hover:bg-slate-800 transition-colors" href="#">History</a>
      <a className="text-sm font-medium text-slate-500 dark:text-slate-300 hover:text-primary px-4 py-2 rounded-full hover:bg-blue-50 dark:hover:bg-slate-800 transition-colors" href="#">Settings</a>
    </nav>
    <div className="flex items-center gap-3">
      <button className="hidden sm:flex items-center justify-center h-9 px-4 rounded-full text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-sm border border-transparent hover:border-slate-200 dark:hover:border-slate-700">
        <span className="material-symbols-outlined text-[18px] mr-2">description</span>
        Docs
      </button>
      <div className="h-9 w-9 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden cursor-pointer border border-slate-200 ring-2 ring-transparent hover:ring-primary/20 transition-all" style={{backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuA-SnFXXXtFORZ1OcJpb2yWqO49McNpliPnDpO6K5kTzBgQP2jw1EhIfmWrcfVyoPh3SYK3yGHRLNC17BQEYQ_nbw1A3QDOh6bsqm_tqWX3wHm5ZPNnOqH-5sbpxo9RoNBT9yiwh8BGi-kPA5PLb_2QusK8_0qU2yG688ACFTyhnJMqx4-nO4Ei2v8nNB_eBg_BlprvnSfDjoI1sAYss4hVl9YURtXNbNHM9eA9gS92E43je6UpUh-wVPjsg7uGTfypY_hDPaHMi80s")', backgroundSize: 'cover'}}></div>
    </div>
  </div>
</header>

{/* Main */}
<main className="flex-1 flex flex-col items-center py-8 px-4 sm:px-6 z-10 relative">
  <div className="flex flex-col lg:flex-row gap-6 w-full max-w-[1100px] justify-center items-start">
    {/* Main Card */}
    <div className="w-full max-w-[780px] bg-white dark:bg-slate-800 rounded-2xl shadow-multi-layer border border-slate-200/60 dark:border-slate-700 flex flex-col overflow-hidden relative">
      {/* Card Header */}
      <div className="border-b border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 px-8 pt-8 pb-6 backdrop-blur-sm">
        <h1 className="text-2xl font-normal text-slate-900 dark:text-white mb-8">Review Summary</h1>
        {/* Stepper */}
        <div className="flex items-center w-full text-sm select-none">
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-success text-white text-sm font-bold shadow-md transition-all">
              <span className="material-symbols-outlined text-[18px]">check</span>
            </div>
            <span className="font-medium text-success dark:text-green-400">Profiles</span>
          </div>
          <div className="h-[2px] w-12 bg-success/30 mx-3 rounded-full"></div>
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-success text-white text-sm font-bold shadow-md transition-all">
              <span className="material-symbols-outlined text-[18px]">check</span>
            </div>
            <span className="font-medium text-success dark:text-green-400">Resume</span>
          </div>
          <div className="h-[2px] w-12 bg-success/30 mx-3 rounded-full"></div>
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-success text-white text-sm font-bold shadow-md transition-all">
              <span className="material-symbols-outlined text-[18px]">check</span>
            </div>
            <span className="font-medium text-success dark:text-green-400">Experience</span>
          </div>
          <div className="h-[2px] w-12 bg-success/30 mx-3 rounded-full"></div>
          <div className="flex items-center gap-2 cursor-default">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white text-sm font-bold shadow-md ring-2 ring-primary/20 transition-all">4</div>
            <span className="font-medium text-primary dark:text-white">Review</span>
          </div>
        </div>
        <p className="mt-6 text-sm text-slate-600 dark:text-slate-400 leading-relaxed max-w-2xl">
          Please review the gathered information before starting the analysis. This data will be used to generate your technical verification report.
        </p>
      </div>

      {/* Review Body */}
      <div className="p-8 bg-white dark:bg-slate-800 space-y-8">
        {/* Identity & Links */}
        <div className="report-section-border pb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-slate-800 dark:text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-slate-400">badge</span>
              Identity &amp; Links
            </h3>
            <button onClick={() => router.push("/analyze")} className="text-primary text-xs font-medium hover:underline flex items-center">
              Edit <span className="material-symbols-outlined text-[14px] ml-0.5">edit</span>
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* GitHub */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50 flex items-start gap-4">
              <div className="p-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-100 dark:border-slate-700">
                <svg className="h-5 w-5 text-slate-800 dark:text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" fillRule="evenodd"></path>
                </svg>
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">GitHub</span>
                <span className="text-sm text-slate-900 dark:text-white font-medium">{step1?.githubUsername || "—"}</span>
                {step1?.githubUsername && (
                <a className="text-xs text-primary hover:underline mt-1 block" href={`https://github.com/${step1.githubUsername}`} target="_blank" rel="noopener noreferrer">View Profile</a>
                )}
              </div>
            </div>
            {/* LinkedIn */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50 flex items-start gap-4">
              <div className="p-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-100 dark:border-slate-700">
                <svg className="h-5 w-5 text-[#0077b5]" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"></path>
                </svg>
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">LinkedIn</span>
                <span className="text-sm text-slate-900 dark:text-white font-medium">{step1?.linkedinUrl || "—"}</span>
                {step1?.linkedinHeadline && (
                <span className="text-xs text-slate-500 mt-0.5">{step1.linkedinHeadline}</span>
                )}
              </div>
            </div>
            {/* Portfolio */}
            {step1?.portfolioLinks && step1.portfolioLinks.filter(l => l.trim()).length > 0 && (
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50 flex items-start gap-4 md:col-span-2">
              <div className="p-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-100 dark:border-slate-700">
                <span className="material-symbols-outlined text-[20px] text-slate-600 dark:text-slate-400">link</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Portfolio</span>
                {step1.portfolioLinks.filter(l => l.trim()).map((link, i) => (
                <span key={i} className="text-sm text-slate-900 dark:text-white font-medium truncate max-w-[200px] sm:max-w-md">{link}</span>
                ))}
              </div>
            </div>
            )}
          </div>
        </div>

        {/* Document Analysis */}
        <div className="report-section-border pb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-slate-800 dark:text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-slate-400">description</span>
              Skills &amp; Resume
            </h3>
            <button onClick={() => router.push("/analyze/skills")} className="text-primary text-xs font-medium hover:underline flex items-center">
              Edit <span className="material-symbols-outlined text-[14px] ml-0.5">edit</span>
            </button>
          </div>
          <div className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              {(step2?.skills || []).filter(s => s.name.trim()).map((skill, i) => (
              <span key={i} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-100 dark:border-blue-800">
                {skill.name}{skill.years ? ` · ${skill.years}y` : ""}
              </span>
              ))}
              {(!step2?.skills || step2.skills.filter(s => s.name.trim()).length === 0) && (
              <span className="text-xs text-slate-400 italic">No skills added</span>
              )}
            </div>
          </div>
        </div>

        {/* Professional Experience */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-slate-800 dark:text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-slate-400">history_edu</span>
              Professional Experience
            </h3>
            <button onClick={() => router.push("/analyze/experience")} className="text-primary text-xs font-medium hover:underline flex items-center">
              Edit <span className="material-symbols-outlined text-[14px] ml-0.5">edit</span>
            </button>
          </div>
          <div className="relative border-l-2 border-slate-200 dark:border-slate-700 ml-3 space-y-6">
            {(step3?.experiences || []).filter(e => e.company.trim() || e.role.trim()).map((exp, i) => (
            <div key={i} className="relative pl-6">
              <div className={`absolute -left-[9px] top-1.5 h-4 w-4 rounded-full bg-white dark:bg-slate-800 border-2 ${i === 0 ? 'border-primary' : 'border-slate-300 dark:border-slate-600'}`}></div>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                <h4 className="text-sm font-bold text-slate-900 dark:text-white">{exp.role || "Untitled Role"}</h4>
                {(exp.startDate || exp.endDate) && (
                <span className="text-xs text-slate-500 font-medium bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded">{exp.startDate}{exp.endDate ? ` - ${exp.endDate}` : ""}</span>
                )}
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5 font-medium">{exp.company}</p>
              {exp.description && (
              <p className="text-xs text-slate-500 mt-1 line-clamp-2">{exp.description}</p>
              )}
            </div>
            ))}
            {(!step3?.experiences || step3.experiences.filter(e => e.company.trim() || e.role.trim()).length === 0) && (
            <p className="pl-6 text-xs text-slate-400 italic">No experience added</p>
            )}
          </div>
        </div>
      </div>

      {/* ── Legal Consent & Authorization ─────────────────── */}
      <div className="px-8 pb-6 pt-2 bg-white dark:bg-slate-800">
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/60 dark:bg-slate-900/50 p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-[20px] text-primary">gavel</span>
            <h3 className="text-sm font-bold text-slate-800 dark:text-white">Consent &amp; Authorization</h3>
            <span className="text-[10px] font-medium text-slate-400 ml-auto">Required</span>
          </div>
          <div className="space-y-4">
            {/* Checkbox 1 — Authorization */}
            <label className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={consentAuth}
                onChange={e => { setConsentAuth(e.target.checked); setConsentError(null); }}
                className="mt-0.5 h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary/30 cursor-pointer accent-[#4285F4]"
              />
              <span className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                I authorize ProofStack to access and analyze my publicly available GitHub data, provided resume content, and optional LeetCode &amp; LinkedIn information for the purpose of generating a technical verification report.
              </span>
            </label>

            {/* Checkbox 2 — Processing & Disclaimer */}
            <label className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={consentProcess}
                onChange={e => { setConsentProcess(e.target.checked); setConsentError(null); }}
                className="mt-0.5 h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary/30 cursor-pointer accent-[#4285F4]"
              />
              <span className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                I understand that the analysis uses algorithmic scoring; results are informational only and do not constitute a professional assessment. I consent to the processing of this data as described.
              </span>
            </label>

            {/* Checkbox 3 — Privacy Policy */}
            <label className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={consentPrivacy}
                onChange={e => { setConsentPrivacy(e.target.checked); setConsentError(null); }}
                className="mt-0.5 h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary/30 cursor-pointer accent-[#4285F4]"
              />
              <span className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                I have read and agree to the{" "}
                <a href="/privacy" className="text-primary hover:underline font-medium" target="_blank" rel="noopener noreferrer">
                  Privacy Policy
                </a>{" "}
                and{" "}
                <a href="/terms" className="text-primary hover:underline font-medium" target="_blank" rel="noopener noreferrer">
                  Terms of Use
                </a>.
              </span>
            </label>

            {/* Divider */}
            <div className="border-t border-slate-200 dark:border-slate-700 pt-3 mt-1">
              <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wider font-semibold mb-2">
                Optional — Recruiter Confirmation
              </p>
              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={recruiterConfirm}
                  onChange={e => setRecruiterConfirm(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary/30 cursor-pointer accent-[#4285F4]"
                />
                <span className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  I confirm that the candidate whose data I am submitting has given explicit consent for this analysis to be performed.
                </span>
              </label>
            </div>
          </div>

          {/* Consent error */}
          {consentError && (
            <div className="mt-4 flex items-center gap-2 text-red-600 dark:text-red-400 text-xs font-medium bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg border border-red-200 dark:border-red-800">
              <span className="material-symbols-outlined text-[16px]">error</span>
              {consentError}
            </div>
          )}
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="px-8 py-3 bg-red-50 border-t border-red-200 text-red-700 text-sm flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px]">error</span>
          {error}
        </div>
      )}

      {/* Footer */}
      <div className="px-8 py-6 border-t border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row gap-4 sm:gap-0 justify-between items-center bg-slate-50 dark:bg-slate-800/80 backdrop-blur-sm">
        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-medium select-none bg-white dark:bg-slate-700 px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-600 shadow-sm">
          <span className="material-symbols-outlined text-[16px] text-primary">verified</span>
          Data Integrity Check Passed
        </div>
        <div className="flex gap-4 w-full sm:w-auto justify-end">
          <button onClick={() => router.push("/analyze/experience")} className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white font-medium text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" type="button">
            Back
          </button>
          <button onClick={handleStartAnalysis} disabled={submitting || !allConsentsGiven} className={`px-8 py-3 rounded-full font-medium text-sm shadow-glow-primary transition-all flex items-center justify-center gap-2 transform active:scale-95 w-full sm:w-auto disabled:opacity-60 ${allConsentsGiven ? 'bg-primary text-white hover:bg-primary-hover' : 'bg-slate-300 text-slate-500 cursor-not-allowed shadow-none'}`} type="button">
            <span className="material-symbols-outlined text-[20px] animate-pulse">auto_awesome</span>
            {submitting ? "Submitting..." : "Start Full Analysis"}
          </button>
        </div>
      </div>
    </div>

    {/* Sidebar */}
    <div className="hidden lg:block w-80 sticky top-24 shrink-0">
      <div className="bg-tip-bg border border-yellow-200/60 rounded-xl p-6 shadow-subtle relative overflow-hidden">
        <span className="material-symbols-outlined absolute -right-4 -bottom-4 text-[120px] text-yellow-500/10 pointer-events-none select-none">lightbulb</span>
        <div className="flex items-center gap-3 mb-4 relative z-10">
          <div className="bg-yellow-100 p-2 rounded-full text-yellow-700">
            <span className="material-symbols-outlined text-[20px]">lightbulb</span>
          </div>
          <h3 className="font-bold text-slate-800 text-sm">Review Tips</h3>
        </div>
        <ul className="space-y-4 relative z-10">
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>Double-check your <strong>Git</strong> handle. Invalid handles are the #1 cause of analysis failure.</span>
          </li>
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>Ensure your resume PDF is text-readable (not a scanned image) for best skill parsing.</span>
          </li>
        </ul>
      </div>
      <div className="mt-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2">Estimated Time</h4>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center text-primary">
            <span className="material-symbols-outlined">timer</span>
          </div>
          <div>
            <p className="text-sm font-bold text-slate-900 dark:text-white">~2 Minutes</p>
            <p className="text-xs text-slate-500">Analysis duration</p>
          </div>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed border-t border-slate-100 dark:border-slate-700 pt-3 mt-1">
          Once started, the analysis runs in the background. You can close this tab safely.
        </p>
      </div>
    </div>
  </div>
</main>

<footer className="py-8 text-center text-xs text-slate-400 dark:text-slate-500 z-10 relative">
  <p>&copy; 2026 ProofStack. Built for truth.</p>
</footer>
</div>
  );
}
