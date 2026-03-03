"use client";
import { useRouter } from "next/navigation";
import { useState, useEffect, useRef, useCallback } from "react";

interface Skill {
  name: string;
  years: string;
}

interface UploadedFile {
  name: string;
  size: number;
  type: string;
}

interface ParsedResume {
  raw_text?: string;
  skills: { name: string; years: number }[];
  experience: { company: string; role: string; start_date: string; end_date: string }[];
  projects: { name: string; tech: string; description: string }[];
}

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];
const ACCEPTED_EXT = [".pdf", ".docx", ".txt"];
const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function AnalyzeSkillsPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [skills, setSkills] = useState<Skill[]>([
    { name: "", years: "" },
  ]);
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [parseSuccess, setParseSuccess] = useState(false);
  const [parsedData, setParsedData] = useState<ParsedResume | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("proofstack_step2");
    if (saved) {
      const d = JSON.parse(saved);
      if (d.skills && d.skills.length > 0) setSkills(d.skills.map((s: Partial<Skill>) => ({
        name: s.name ?? "",
        years: s.years ?? "",
      })));
      if (d.resume) {
        setUploadedFile(d.resume);
        setParseSuccess(true);
      }
      if (d.parsedResume) setParsedData(d.parsedResume);
    }
  }, []);

  /* --- file validation & parsing --- */
  const validateAndSetFile = useCallback(async (file: File) => {
    setUploadError(null);
    setParseSuccess(false);
    setParsedData(null);
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (!ACCEPTED_TYPES.includes(file.type) && !ACCEPTED_EXT.includes(ext)) {
      setUploadError("Unsupported file type. Please upload a PDF, DOCX, or TXT file.");
      return;
    }
    if (file.size > MAX_SIZE) {
      setUploadError("File is too large. Maximum size is 10 MB.");
      return;
    }
    const meta: UploadedFile = { name: file.name, size: file.size, type: file.type || ext };
    setUploadedFile(meta);

    // persist metadata to localStorage
    const prev = localStorage.getItem("proofstack_step2");
    const existing = prev ? JSON.parse(prev) : {};
    localStorage.setItem("proofstack_step2", JSON.stringify({ ...existing, resume: meta }));

    // Send file to backend for parsing
    setParsing(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("http://localhost:8000/api/resume/parse", {
        method: "POST",
        headers: { "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "proofstack-demo-2025" },
        body: formData,
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => null);
        throw new Error(errBody?.detail || `Parse failed (${res.status})`);
      }
      const parsed: ParsedResume & { filename: string } = await res.json();
      setParsedData(parsed);
      setParseSuccess(true);

      // Auto-populate skills from parsed resume (merge with existing manual skills)
      if (parsed.skills && parsed.skills.length > 0) {
        const existingNames = new Set(skills.filter(s => s.name.trim()).map(s => s.name.trim().toLowerCase()));
        const newSkills: Skill[] = skills.filter(s => s.name.trim()); // keep existing manual skills
        for (const ps of parsed.skills) {
          if (!existingNames.has(ps.name.toLowerCase())) {
            newSkills.push({ name: ps.name, years: String(ps.years) });
            existingNames.add(ps.name.toLowerCase());
          }
        }
        if (newSkills.length === 0) newSkills.push({ name: "", years: "" });
        setSkills(newSkills);
      }

      // Store parsed resume data (experience + projects) for Step 3 auto-population
      const prevStep2 = localStorage.getItem("proofstack_step2");
      const existingStep2 = prevStep2 ? JSON.parse(prevStep2) : {};
      localStorage.setItem("proofstack_step2", JSON.stringify({
        ...existingStep2,
        resume: meta,
        parsedResume: parsed,
        skills: (parsed.skills && parsed.skills.length > 0)
          ? parsed.skills.map(s => ({ name: s.name, years: String(s.years) }))
          : existingStep2.skills,
      }));

      // Also store parsed experience/projects for Step 3 pre-fill
      if (parsed.experience?.length || parsed.projects?.length) {
        const prevStep3 = localStorage.getItem("proofstack_step3");
        const existingStep3 = prevStep3 ? JSON.parse(prevStep3) : {};
        const parsedExperiences = (parsed.experience || []).map(e => ({
          company: e.company || "",
          role: e.role || "",
          startDate: e.start_date || "",
          endDate: e.end_date || "",
          description: "",
        }));
        const parsedProjects = (parsed.projects || []).map(p => ({
          name: p.name || "",
          tech: p.tech || "",
          description: p.description || "",
          link: "",
        }));
        localStorage.setItem("proofstack_step3", JSON.stringify({
          experiences: parsedExperiences.length > 0 ? parsedExperiences : existingStep3.experiences,
          projects: parsedProjects.length > 0 ? parsedProjects : existingStep3.projects,
        }));
      }
    } catch (err) {
      console.error("Resume parsing failed:", err);
      setUploadError(`Resume parsing failed: ${err instanceof Error ? err.message : "Unknown error"}. Your manual entries will still be used.`);
    } finally {
      setParsing(false);
    }
  }, [skills]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) validateAndSetFile(file);
    // reset so same file can be re-selected
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setUploadError(null);
    setParseSuccess(false);
    setParsedData(null);
    const prev = localStorage.getItem("proofstack_step2");
    if (prev) {
      const existing = JSON.parse(prev);
      delete existing.resume;
      delete existing.parsedResume;
      localStorage.setItem("proofstack_step2", JSON.stringify(existing));
    }
  };

  /* --- drag & drop --- */
  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setDragging(true); };
  const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setDragging(false); };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) validateAndSetFile(file);
  };

  const handleContinue = () => {
    const prev = localStorage.getItem("proofstack_step2");
    const existing = prev ? JSON.parse(prev) : {};
    localStorage.setItem("proofstack_step2", JSON.stringify({ ...existing, skills: skills.filter(s => s.name.trim()) }));
    router.push("/analyze/experience");
  };

  const addSkill = () => setSkills([...skills, { name: "", years: "" }]);
  const removeSkill = (i: number) => setSkills(skills.filter((_, idx) => idx !== i));
  const updateSkill = (i: number, field: keyof Skill, value: string) => {
    const c = [...skills];
    c[i] = { ...c[i], [field]: value };
    setSkills(c);
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
        <h1 className="text-2xl font-normal text-slate-900 dark:text-white mb-8">Resume &amp; Skills</h1>
        {/* Stepper */}
        <div className="flex items-center w-full text-sm select-none">
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 text-sm font-bold shadow-sm transition-all">
              <span className="material-symbols-outlined text-[18px]">check</span>
            </div>
            <span className="font-medium text-slate-700 dark:text-slate-300">Profiles</span>
          </div>
          <div className="h-[2px] w-12 bg-green-500 mx-3 rounded-full"></div>
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white text-sm font-bold shadow-md shadow-blue-500/30 ring-2 ring-primary/20 transition-all scale-105">2</div>
            <span className="font-medium text-primary dark:text-white">Resume</span>
          </div>
          <div className="h-[2px] w-12 bg-slate-200 mx-3 rounded-full"></div>
          <div className="flex items-center gap-2 opacity-60 group cursor-not-allowed">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 border border-slate-300 text-slate-500 dark:text-slate-400 text-sm font-medium">3</div>
            <span className="font-medium text-slate-600 dark:text-slate-400">Experience</span>
          </div>
          <div className="h-[2px] w-12 bg-slate-200 mx-3 rounded-full opacity-60"></div>
          <div className="flex items-center gap-2 opacity-60 group cursor-not-allowed">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 border border-slate-300 text-slate-500 dark:text-slate-400 text-sm font-medium">4</div>
            <span className="font-medium text-slate-600 dark:text-slate-400">Review</span>
          </div>
        </div>
        <p className="mt-6 text-sm text-slate-600 dark:text-slate-400 leading-relaxed max-w-2xl">
          Upload your latest CV to help our AI parse your work history, and manually tag your top technical skills for better matching.
        </p>
      </div>

      {/* Form */}
      <div className="p-8 bg-white dark:bg-slate-800">
        <form className="space-y-10">
          {/* Resume Upload */}
          <div className="space-y-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Resume Upload</label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
              className="hidden"
              onChange={handleFileChange}
            />

            {!uploadedFile ? (
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center transition-all cursor-pointer group ${
                  dragging
                    ? "border-primary bg-blue-50 dark:bg-slate-900/50"
                    : "border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900/30 hover:bg-blue-50 dark:hover:bg-slate-900/50 hover:border-primary/50"
                }`}
              >
                <div className="w-16 h-16 bg-white dark:bg-slate-800 rounded-full shadow-sm flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200">
                  <span className="material-symbols-outlined text-[32px] text-primary">cloud_upload</span>
                </div>
                <h3 className="text-sm font-medium text-slate-900 dark:text-white">
                  <span className="text-primary hover:underline">Click to upload</span> or drag and drop
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  PDF, DOCX, or TXT up to 10MB
                </p>
              </div>
            ) : (
              <div className="border border-slate-200 dark:border-slate-600 rounded-xl p-5 bg-white dark:bg-slate-900/30 flex flex-col gap-3">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                    <span className="material-symbols-outlined text-[28px] text-primary">description</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{uploadedFile.name}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{formatSize(uploadedFile.size)}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {parsing ? (
                      <span className="material-symbols-outlined text-[20px] text-primary animate-spin">progress_activity</span>
                    ) : parseSuccess ? (
                      <span className="material-symbols-outlined text-[20px] text-green-500">check_circle</span>
                    ) : (
                      <span className="material-symbols-outlined text-[20px] text-green-500">check_circle</span>
                    )}
                    <button
                      type="button"
                      onClick={handleRemoveFile}
                      className="text-slate-400 hover:text-red-500 p-1.5 rounded-full hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      title="Remove file"
                    >
                      <span className="material-symbols-outlined text-[20px]">close</span>
                    </button>
                  </div>
                </div>
                {parsing && (
                  <div className="flex items-center gap-2 px-2 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <span className="material-symbols-outlined text-[16px] text-primary animate-spin">progress_activity</span>
                    <span className="text-xs text-primary font-medium">Parsing resume — extracting skills, experience &amp; projects...</span>
                  </div>
                )}
                {parseSuccess && parsedData && (
                  <div className="flex items-center gap-2 px-2 py-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <span className="material-symbols-outlined text-[16px] text-green-600">check_circle</span>
                    <span className="text-xs text-green-700 dark:text-green-400 font-medium">
                      Parsed: {parsedData.skills?.length || 0} skills, {parsedData.experience?.length || 0} experiences, {parsedData.projects?.length || 0} projects
                    </span>
                  </div>
                )}
              </div>
            )}

            {uploadError && (
              <p className="text-xs text-red-500 flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px]">error</span>
                {uploadError}
              </p>
            )}
          </div>

          {/* Technical Skills */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Top Technical Skills</label>
                <p className="text-xs text-slate-500 mt-0.5">List your strongest languages and frameworks.</p>
              </div>
              <button onClick={addSkill} className="group flex items-center text-sm font-medium text-slate-500 hover:text-primary transition-colors px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" type="button">
                <span className="material-symbols-outlined text-[18px] mr-1.5 group-hover:text-primary">add</span>
                Add Skill
              </button>
            </div>
            <div className="space-y-3">
              {skills.map((skill, i) => {
                const isLast = i === skills.length - 1 && !skill.name;
                return (
                <div key={i} className={`flex gap-4 items-start${isLast ? ' opacity-60 hover:opacity-100 transition-opacity' : ''}`}>
                  <div className="relative flex-grow group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <span className="material-symbols-outlined text-slate-400 text-[18px]">code</span>
                    </div>
                    <input className={`block w-full rounded-lg ${isLast ? 'border-dashed border-slate-300 dark:border-slate-600 bg-slate-50' : 'border-slate-300 dark:border-slate-600 bg-white'} dark:bg-slate-900 text-slate-900 dark:text-white text-sm py-2.5 pl-10 pr-4 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-sm placeholder:text-slate-400`} placeholder={isLast ? "Add another skill..." : "e.g. React.js"} type="text" value={skill.name} onChange={(e) => updateSkill(i, 'name', e.target.value)} />
                  </div>
                  <div className="relative w-32 group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <span className="material-symbols-outlined text-slate-400 text-[18px]">schedule</span>
                    </div>
                    <input className={`block w-full rounded-lg ${isLast ? 'border-dashed border-slate-300 dark:border-slate-600 bg-slate-50' : 'border-slate-300 dark:border-slate-600 bg-white'} dark:bg-slate-900 text-slate-900 dark:text-white text-sm py-2.5 pl-10 pr-4 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-sm placeholder:text-slate-400`} placeholder="Years" type="number" value={skill.years} onChange={(e) => updateSkill(i, 'years', e.target.value)} />
                  </div>
                  {!isLast ? (
                    <button onClick={() => removeSkill(i)} className="mt-1.5 text-slate-400 hover:text-red-500 p-1 rounded-full hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors" type="button">
                      <span className="material-symbols-outlined text-[20px]">close</span>
                    </button>
                  ) : (
                    <div className="w-7"></div>
                  )}
                </div>
                );
              })}
            </div>
          </div>
        </form>
      </div>

      {/* Footer */}
      <div className="px-8 py-6 border-t border-slate-200 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-800/80 backdrop-blur-sm">
        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-medium select-none bg-white dark:bg-slate-700 px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-600 shadow-sm">
          <span className="material-symbols-outlined text-[16px] text-primary">cloud_done</span>
          Auto-saved
        </div>
        <div className="flex gap-4">
          <button onClick={() => router.push("/analyze")} className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white font-medium text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" type="button">
            Back
          </button>
          <button onClick={handleContinue} className="px-8 py-2.5 rounded-full bg-primary text-white font-medium text-sm shadow-lg shadow-blue-500/20 hover:shadow-xl hover:shadow-blue-500/30 hover:bg-primary-hover transition-all flex items-center gap-2 transform active:scale-95" type="button">
            Continue
            <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
          </button>
        </div>
      </div>
    </div>

    {/* Sidebar */}
    <div className="hidden lg:block w-80 sticky top-24 shrink-0 space-y-4">
      <div className="bg-tip-bg border border-yellow-200/60 rounded-xl p-6 shadow-subtle relative overflow-hidden">
        <span className="material-symbols-outlined absolute -right-4 -bottom-4 text-[120px] text-yellow-500/10 pointer-events-none select-none">lightbulb</span>
        <div className="flex items-center gap-3 mb-4 relative z-10">
          <div className="bg-yellow-100 p-2 rounded-full text-yellow-700">
            <span className="material-symbols-outlined text-[20px]">lightbulb</span>
          </div>
          <h3 className="font-bold text-slate-800 text-sm">Resume Tips</h3>
        </div>
        <ul className="space-y-4 relative z-10">
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>Ensure your resume is in <strong>PDF format</strong> for best parsing results.</span>
          </li>
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>Highlight <strong>measurable impacts</strong> in your experience descriptions.</span>
          </li>
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>List skills relevant to the role you are targeting to improve match score.</span>
          </li>
        </ul>
      </div>
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2">Need assistance?</h4>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">Having trouble uploading? Contact our support team for manual verification.</p>
        <a className="text-primary text-xs font-medium hover:underline flex items-center gap-1" href="#">
          Contact Support <span className="material-symbols-outlined text-[14px]">open_in_new</span>
        </a>
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
