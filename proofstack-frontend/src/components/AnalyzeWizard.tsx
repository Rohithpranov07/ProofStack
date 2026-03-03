"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import FormInput from "@/components/FormInput";
import SelectInput from "@/components/SelectInput";
import DynamicList from "@/components/DynamicList";
import { createAnalysisJob } from "@/lib/api";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Skill {
  name: string;
  years: number;
}

interface Experience {
  company: string;
  start_date: string;
  end_date: string;
}

interface FormState {
  github_username: string;
  leetcode_username: string;
  linkedin_url: string;
  linkedin_headline: string;
  resume_file: File | null;
  resume_file_name: string;
  skills: Skill[];
  projects: string[];
  experience: Experience[];
  portfolio_links: string[];
  role_level: string;
}

type Errors = Record<string, string>;

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const STEPS = ["Profiles", "Resume", "Experience", "Review"] as const;

const ROLE_OPTIONS = [
  { value: "entry", label: "Entry Level" },
  { value: "mid", label: "Mid Level" },
  { value: "senior", label: "Senior Level" },
];

const INITIAL_STATE: FormState = {
  github_username: "",
  leetcode_username: "",
  linkedin_url: "",
  linkedin_headline: "",
  resume_file: null,
  resume_file_name: "",
  skills: [{ name: "", years: 0 }],
  projects: [""],
  experience: [{ company: "", start_date: "", end_date: "" }],
  portfolio_links: [""],
  role_level: "mid",
};

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function AnalyzeWizard() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(INITIAL_STATE);
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  /* ---- helpers ---- */

  const set = useCallback(
    <K extends keyof FormState>(key: K, value: FormState[K]) =>
      setForm((prev) => ({ ...prev, [key]: value })),
    []
  );

  /* ---- validation ---- */

  const validate = (): boolean => {
    const e: Errors = {};

    if (step === 0) {
      if (!form.github_username || form.github_username.length < 2)
        e.github_username = "GitHub username is required (min 2 chars)";
      if (!form.role_level) e.role_level = "Select a role level";
    }

    if (step === 1) {
      if (form.skills.length === 0) e.skills = "Add at least one skill";
      form.skills.forEach((s, i) => {
        if (!s.name.trim()) e[`skill_name_${i}`] = "Skill name required";
        if (s.years < 0) e[`skill_years_${i}`] = "Years must be 0 or greater";
      });
    }

    if (step === 2) {
      form.experience.forEach((exp, i) => {
        if (!exp.company.trim()) e[`exp_company_${i}`] = "Company required";
        if (!exp.start_date) e[`exp_start_${i}`] = "Start date required";
        if (!exp.end_date) e[`exp_end_${i}`] = "End date required";
        if (exp.start_date && exp.end_date && exp.end_date < exp.start_date)
          e[`exp_end_${i}`] = "End date must be after start date";
      });
    }

    setErrors(e);
    return Object.keys(e).length === 0;
  };

  /* ---- navigation ---- */

  const next = () => {
    if (!validate()) return;
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const back = () => setStep((s) => Math.max(s - 1, 0));

  /* ---- resume file handler ---- */

  const handleResumeUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      set("resume_file", file);
      set("resume_file_name", file.name);
    }
  };

  const removeResume = () => {
    set("resume_file", null);
    set("resume_file_name", "");
  };

  /* ---- item update helpers ---- */

  const updateSkill = (index: number, field: keyof Skill, value: string | number) => {
    const next = [...form.skills];
    next[index] = { ...next[index], [field]: value };
    set("skills", next);
  };

  const updateExperience = (
    index: number,
    field: keyof Experience,
    value: string
  ) => {
    const next = [...form.experience];
    next[index] = { ...next[index], [field]: value };
    set("experience", next);
  };

  const updateProject = (index: number, value: string) => {
    const next = [...form.projects];
    next[index] = value;
    set("projects", next);
  };

  const updatePortfolioLink = (index: number, value: string) => {
    const next = [...form.portfolio_links];
    next[index] = value;
    set("portfolio_links", next);
  };

  /* ---- submit ---- */

  const submit = async () => {
    if (!validate()) return;
    setSubmitting(true);
    setSubmitError("");

    try {
      const linkedinData =
        form.linkedin_url || form.linkedin_headline
          ? {
              profile_url: form.linkedin_url || undefined,
              headline: form.linkedin_headline || undefined,
              skills: undefined,
              experience: undefined,
            }
          : undefined;

      const payload = {
        username: form.github_username,
        role_level: form.role_level,
        resume_data: {
          skills: form.skills
            .filter((s) => s.name.trim())
            .map((s) => ({ name: s.name, years: s.years })),
          projects: form.projects
            .filter((p) => p.trim())
            .map((p) => ({ name: p })),
          experience: form.experience
            .filter((e) => e.company.trim())
            .map((exp) => ({
              company: exp.company,
              start_date: exp.start_date,
              end_date: exp.end_date,
            })),
        },
        linkedin_data: linkedinData,
        leetcode_username: form.leetcode_username || form.github_username,
        consent: {
          consent_version: "v1.0.0",
          consent_given: true,
          recruiter_confirmation: undefined,
        },
      };

      const { job_id } = await createAnalysisJob(payload);
      router.push(`/analysis/${job_id}`);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Submission failed. Try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  /* ================================================================ */
  /*  RENDER                                                           */
  /* ================================================================ */

  const transition = {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
    transition: { duration: 0.3 },
  };

  const isFinal = step === STEPS.length - 1;

  return (
    <div className="mx-auto w-full max-w-[800px] py-12">
      {/* ---- Progress Bar ---- */}
      <div className="mb-10 flex items-center justify-center gap-2">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                if (i < step) setStep(i);
              }}
              className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold transition-colors ${
                i === step
                  ? "bg-accent-primary text-white"
                  : i < step
                  ? "bg-accent-primary/20 text-accent-primary"
                  : "bg-bg-secondary text-text-muted"
              }`}
            >
              {i + 1}
            </button>
            <span
              className={`hidden text-xs sm:inline ${
                i === step ? "text-text-primary font-medium" : "text-text-muted"
              }`}
            >
              {label}
            </span>
            {i < STEPS.length - 1 && (
              <div
                className={`h-px w-8 ${
                  i < step ? "bg-accent-primary/40" : "bg-border-subtle"
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* ---- Card ---- */}
      <div className="rounded-2xl border border-border-subtle bg-bg-card p-8 shadow-md shadow-black/10">
        <AnimatePresence mode="wait">
          {/* ============================================= */}
          {/* Step 0: Profiles & Links                       */}
          {/* ============================================= */}
          {step === 0 && (
            <motion.div key="step-0" {...transition} className="flex flex-col gap-6">
              <div>
                <h2 className="text-xl font-semibold">Profiles &amp; Links</h2>
                <p className="mt-1 text-sm text-text-secondary">
                  Enter the candidate&apos;s coding profiles and relevant links.
                </p>
              </div>

              <div className="grid gap-6 sm:grid-cols-2">
                <FormInput
                  id="github_username"
                  label="GitHub Username *"
                  placeholder="e.g. torvalds"
                  value={form.github_username}
                  onChange={(e) => set("github_username", e.target.value)}
                  error={errors.github_username}
                />
                <FormInput
                  id="leetcode_username"
                  label="LeetCode / HackerRank"
                  placeholder="e.g. neetcode"
                  value={form.leetcode_username}
                  onChange={(e) => set("leetcode_username", e.target.value)}
                  error={errors.leetcode_username}
                />
              </div>

              <FormInput
                id="linkedin_url"
                label="LinkedIn Profile URL"
                placeholder="https://linkedin.com/in/username"
                value={form.linkedin_url}
                onChange={(e) => set("linkedin_url", e.target.value)}
              />

              <FormInput
                id="linkedin_headline"
                label="LinkedIn Headline"
                placeholder="e.g. Senior Software Engineer at Google"
                value={form.linkedin_headline}
                onChange={(e) => set("linkedin_headline", e.target.value)}
              />

              {/* Portfolio & Project Links */}
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <label className="text-sm font-medium text-text-secondary">
                    Portfolio / Project Links
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      set("portfolio_links", [...form.portfolio_links, ""])
                    }
                    className="rounded-lg border border-border-subtle px-3 py-1 text-xs font-medium text-accent-primary transition-colors hover:bg-accent-primary/10"
                  >
                    + Add Link
                  </button>
                </div>
                <div className="flex flex-col gap-3">
                  {form.portfolio_links.map((link, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <input
                        type="url"
                        placeholder="https://myportfolio.com or project URL"
                        value={link}
                        onChange={(e) => updatePortfolioLink(i, e.target.value)}
                        className="flex-1 rounded-lg border border-border-subtle bg-bg-primary px-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted/50 outline-none transition-colors focus:border-accent-primary"
                      />
                      {form.portfolio_links.length > 1 && (
                        <button
                          type="button"
                          onClick={() =>
                            set(
                              "portfolio_links",
                              form.portfolio_links.filter((_, idx) => idx !== i)
                            )
                          }
                          className="rounded-lg border border-border-subtle px-2 py-2 text-xs text-accent-red transition-colors hover:bg-accent-red/10"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <SelectInput
                id="role_level"
                label="Target Role Level *"
                options={ROLE_OPTIONS}
                value={form.role_level}
                onChange={(e) => set("role_level", e.target.value)}
                error={errors.role_level}
              />
            </motion.div>
          )}

          {/* ============================================= */}
          {/* Step 1: Resume & Skills                        */}
          {/* ============================================= */}
          {step === 1 && (
            <motion.div key="step-1" {...transition} className="flex flex-col gap-6">
              <div>
                <h2 className="text-xl font-semibold">Resume &amp; Skills</h2>
                <p className="mt-1 text-sm text-text-secondary">
                  Upload a resume and list the candidate&apos;s skills.
                </p>
              </div>

              {/* Resume Upload */}
              <div>
                <label className="mb-2 block text-sm font-medium text-text-secondary">
                  Resume Upload
                </label>
                {form.resume_file_name ? (
                  <div className="flex items-center gap-3 rounded-xl border border-accent-primary/30 bg-accent-primary/5 px-4 py-3">
                    <svg className="h-5 w-5 text-accent-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="flex-1 truncate text-sm text-text-primary">
                      {form.resume_file_name}
                    </span>
                    <button
                      type="button"
                      onClick={removeResume}
                      className="rounded-lg px-2 py-1 text-xs text-accent-red hover:bg-accent-red/10"
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <label
                    htmlFor="resume-upload"
                    className="flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed border-border-subtle bg-bg-primary px-6 py-8 text-center transition-colors hover:border-accent-primary/40 hover:bg-bg-secondary"
                  >
                    <svg className="h-8 w-8 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                    <span className="text-sm text-text-muted">
                      Drop your resume here or{" "}
                      <span className="text-accent-primary">browse</span>
                    </span>
                    <span className="text-xs text-text-muted/60">
                      PDF, DOC, DOCX — max 10 MB
                    </span>
                    <input
                      id="resume-upload"
                      type="file"
                      accept=".pdf,.doc,.docx"
                      onChange={handleResumeUpload}
                      className="hidden"
                    />
                  </label>
                )}
              </div>

              {/* Skills */}
              <DynamicList
                label="Skills"
                items={form.skills}
                error={errors.skills}
                onAdd={() => set("skills", [...form.skills, { name: "", years: 0 }])}
                onRemove={(i) =>
                  set("skills", form.skills.filter((_, idx) => idx !== i))
                }
                renderItem={(skill, i) => (
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <FormInput
                        id={`skill-name-${i}`}
                        label="Skill"
                        placeholder="e.g. Python"
                        value={skill.name}
                        onChange={(e) => updateSkill(i, "name", e.target.value)}
                        error={errors[`skill_name_${i}`]}
                      />
                    </div>
                    <div className="w-28">
                      <FormInput
                        id={`skill-years-${i}`}
                        label="Years"
                        type="number"
                        min={0}
                        step={0.5}
                        value={skill.years}
                        onChange={(e) =>
                          updateSkill(i, "years", parseFloat(e.target.value) || 0)
                        }
                        error={errors[`skill_years_${i}`]}
                      />
                    </div>
                  </div>
                )}
              />
            </motion.div>
          )}

          {/* ============================================= */}
          {/* Step 2: Projects & Experience                   */}
          {/* ============================================= */}
          {step === 2 && (
            <motion.div key="step-2" {...transition} className="flex flex-col gap-8">
              <div>
                <h2 className="text-xl font-semibold">Projects &amp; Experience</h2>
                <p className="mt-1 text-sm text-text-secondary">
                  Add notable projects and work experience from the resume.
                </p>
              </div>

              {/* Projects */}
              <DynamicList
                label="Projects"
                items={form.projects}
                onAdd={() => set("projects", [...form.projects, ""])}
                onRemove={(i) =>
                  set("projects", form.projects.filter((_, idx) => idx !== i))
                }
                renderItem={(project, i) => (
                  <FormInput
                    id={`project-${i}`}
                    label="Project Name"
                    placeholder="e.g. Distributed Cache"
                    value={project}
                    onChange={(e) => updateProject(i, e.target.value)}
                  />
                )}
              />

              {/* Experience */}
              <DynamicList
                label="Work Experience"
                items={form.experience}
                onAdd={() =>
                  set("experience", [
                    ...form.experience,
                    { company: "", start_date: "", end_date: "" },
                  ])
                }
                onRemove={(i) =>
                  set("experience", form.experience.filter((_, idx) => idx !== i))
                }
                renderItem={(exp, i) => (
                  <div className="flex flex-col gap-3">
                    <FormInput
                      id={`exp-company-${i}`}
                      label="Company"
                      placeholder="e.g. Google"
                      value={exp.company}
                      onChange={(e) =>
                        updateExperience(i, "company", e.target.value)
                      }
                      error={errors[`exp_company_${i}`]}
                    />
                    <div className="flex gap-3">
                      <div className="flex-1">
                        <FormInput
                          id={`exp-start-${i}`}
                          label="Start Date"
                          type="date"
                          value={exp.start_date}
                          onChange={(e) =>
                            updateExperience(i, "start_date", e.target.value)
                          }
                          error={errors[`exp_start_${i}`]}
                        />
                      </div>
                      <div className="flex-1">
                        <FormInput
                          id={`exp-end-${i}`}
                          label="End Date"
                          type="date"
                          value={exp.end_date}
                          onChange={(e) =>
                            updateExperience(i, "end_date", e.target.value)
                          }
                          error={errors[`exp_end_${i}`]}
                        />
                      </div>
                    </div>
                  </div>
                )}
              />
            </motion.div>
          )}

          {/* ============================================= */}
          {/* Step 3: Review & Submit                        */}
          {/* ============================================= */}
          {step === 3 && (
            <motion.div key="step-3" {...transition} className="flex flex-col gap-6">
              <div>
                <h2 className="text-xl font-semibold">Review &amp; Analyze</h2>
                <p className="mt-1 text-sm text-text-secondary">
                  Confirm the details below before launching the analysis.
                </p>
              </div>

              <div className="space-y-5 rounded-xl border border-border-subtle bg-bg-primary p-6">
                <ReviewSection title="Profiles">
                  <ReviewRow label="GitHub" value={form.github_username} />
                  <ReviewRow label="LeetCode / HackerRank" value={form.leetcode_username || "\u2014"} />
                  <ReviewRow label="LinkedIn" value={form.linkedin_url || "\u2014"} />
                  <ReviewRow
                    label="Role Level"
                    value={form.role_level.charAt(0).toUpperCase() + form.role_level.slice(1)}
                  />
                </ReviewSection>

                <ReviewSection title="Resume">
                  <ReviewRow label="File" value={form.resume_file_name || "Not uploaded"} />
                  <ReviewRow
                    label="Skills"
                    value={
                      form.skills
                        .filter((s) => s.name.trim())
                        .map((s) => `${s.name} (${s.years}y)`)
                        .join(", ") || "\u2014"
                    }
                  />
                </ReviewSection>

                <ReviewSection title="Experience">
                  <ReviewRow
                    label="Projects"
                    value={form.projects.filter((p) => p.trim()).join(", ") || "\u2014"}
                  />
                  <ReviewRow
                    label="Companies"
                    value={
                      form.experience
                        .filter((e) => e.company.trim())
                        .map((e) => e.company)
                        .join(", ") || "\u2014"
                    }
                  />
                </ReviewSection>

                {form.portfolio_links.some((l) => l.trim()) && (
                  <ReviewSection title="Portfolio Links">
                    {form.portfolio_links
                      .filter((l) => l.trim())
                      .map((l, i) => (
                        <p key={i} className="truncate text-sm text-accent-primary">
                          {l}
                        </p>
                      ))}
                  </ReviewSection>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ---- Submit Error ---- */}
        {submitError && (
          <p className="mt-4 text-sm text-accent-red">{submitError}</p>
        )}

        {/* ---- Navigation Buttons ---- */}
        <div className="mt-8 flex items-center justify-between border-t border-border-subtle pt-6">
          {step > 0 ? (
            <button
              type="button"
              onClick={back}
              className="rounded-xl border border-border-subtle px-6 py-3 text-sm font-medium text-text-muted transition-all duration-200 hover:border-text-muted hover:text-text-primary"
            >
              Back
            </button>
          ) : (
            <div />
          )}

          {!isFinal ? (
            <button
              type="button"
              onClick={next}
              className="rounded-xl bg-accent-primary px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-accent-primary/20 transition-all duration-200 hover:scale-[1.03] hover:opacity-90"
            >
              Continue
            </button>
          ) : (
            <button
              type="button"
              onClick={submit}
              disabled={submitting}
              className="rounded-xl bg-accent-primary px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-accent-primary/20 transition-all duration-200 hover:scale-[1.03] hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Analyzing...
                </span>
              ) : (
                "Analyze Candidate"
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Review helpers                                                     */
/* ------------------------------------------------------------------ */

function ReviewSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
        {title}
      </h3>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-3 text-sm">
      <span className="w-40 shrink-0 text-text-muted">{label}</span>
      <span className="text-text-primary">{value}</span>
    </div>
  );
}
