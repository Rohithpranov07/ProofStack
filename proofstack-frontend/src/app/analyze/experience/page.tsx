"use client";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

interface Experience {
  company: string;
  role: string;
  startDate: string;
  endDate: string;
  description: string;
}

interface Project {
  name: string;
  tech: string;
  description: string;
  link: string;
}

export default function AnalyzeExperiencePage() {
  const router = useRouter();
  const [experiences, setExperiences] = useState<Experience[]>([
    { company: "", role: "", startDate: "", endDate: "", description: "" },
  ]);
  const [projects, setProjects] = useState<Project[]>([
    { name: "", tech: "", description: "", link: "" },
  ]);

  useEffect(() => {
    const saved = localStorage.getItem("proofstack_step3");
    if (saved) {
      const d = JSON.parse(saved);
      if (d.experiences?.length) setExperiences(d.experiences.map((e: Partial<Experience>) => ({
        company: e.company ?? "",
        role: e.role ?? "",
        startDate: e.startDate ?? "",
        endDate: e.endDate ?? "",
        description: e.description ?? "",
      })));
      if (d.projects?.length) setProjects(d.projects.map((p: Partial<Project>) => ({
        name: p.name ?? "",
        tech: p.tech ?? "",
        description: p.description ?? "",
        link: p.link ?? "",
      })));
    }
  }, []);

  const handleContinue = () => {
    localStorage.setItem("proofstack_step3", JSON.stringify({
      experiences: experiences.filter(e => e.company.trim() || e.role.trim()),
      projects: projects.filter(p => p.name.trim()),
    }));
    router.push("/analyze/review");
  };

  const addExperience = () => setExperiences([...experiences, { company: "", role: "", startDate: "", endDate: "", description: "" }]);
  const removeExperience = (i: number) => setExperiences(experiences.filter((_, idx) => idx !== i));
  const updateExperience = (i: number, field: keyof Experience, value: string) => {
    const c = [...experiences]; c[i] = { ...c[i], [field]: value }; setExperiences(c);
  };

  const addProject = () => setProjects([...projects, { name: "", tech: "", description: "", link: "" }]);
  const removeProject = (i: number) => setProjects(projects.filter((_, idx) => idx !== i));
  const updateProject = (i: number, field: keyof Project, value: string) => {
    const c = [...projects]; c[i] = { ...c[i], [field]: value }; setProjects(c);
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
        <h1 className="text-2xl font-normal text-slate-900 dark:text-white mb-8">Professional Experience</h1>
        {/* Stepper */}
        <div className="flex items-center w-full text-sm select-none">
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-success text-white text-sm font-bold shadow-sm transition-all">
              <span className="material-symbols-outlined text-[18px]">check</span>
            </div>
            <span className="font-medium text-slate-700 dark:text-slate-300">Profiles</span>
          </div>
          <div className="h-[2px] w-12 bg-success/30 mx-3 rounded-full"></div>
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-success text-white text-sm font-bold shadow-sm transition-all">
              <span className="material-symbols-outlined text-[18px]">check</span>
            </div>
            <span className="font-medium text-slate-700 dark:text-slate-300">Resume</span>
          </div>
          <div className="h-[2px] w-12 bg-success/30 mx-3 rounded-full"></div>
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white text-sm font-bold shadow-md ring-2 ring-primary/20 transition-all group-hover:scale-105">3</div>
            <span className="font-medium text-primary dark:text-white">Experience</span>
          </div>
          <div className="h-[2px] w-12 bg-slate-200 mx-3 rounded-full opacity-60"></div>
          <div className="flex items-center gap-2 opacity-60 group cursor-not-allowed">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 border border-slate-300 text-slate-500 dark:text-slate-400 text-sm font-medium">4</div>
            <span className="font-medium text-slate-600 dark:text-slate-400">Review</span>
          </div>
        </div>
        <p className="mt-6 text-sm text-slate-600 dark:text-slate-400 leading-relaxed max-w-2xl">
          Detail your work history and highlight specific projects. Our AI analyzes the progression of your roles and the technical complexity of your projects.
        </p>
      </div>

      {/* Form */}
      <div className="p-8 bg-white dark:bg-slate-800">
        <form className="space-y-10">
          {/* Work Experience */}
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-white">Work Experience</h3>
                <p className="text-xs text-slate-500 mt-1">Add your most relevant professional roles.</p>
              </div>
              <button onClick={addExperience} className="text-primary hover:text-primary-hover text-sm font-medium flex items-center justify-center transition-colors py-2 px-4 rounded-full border border-primary/30 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-primary" type="button">
                <span className="material-symbols-outlined text-[18px] mr-2">add</span>
                Add Role
              </button>
            </div>
            <div className="space-y-6">
              {experiences.map((exp, i) => {
                const isEmpty = !exp.company && !exp.role && !exp.startDate;
                return (
                <div key={i} className={`bg-slate-50 dark:bg-slate-900/40 rounded-xl p-5 border border-slate-200 dark:border-slate-700 relative group transition-all hover:shadow-subtle${isEmpty ? ' border-dashed' : ''}`}>
                  {!isEmpty && (
                  <button onClick={() => removeExperience(i)} className="absolute right-4 top-4 text-slate-400 hover:text-red-500 p-1.5 rounded-full hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors" type="button">
                    <span className="material-symbols-outlined text-[18px]">delete</span>
                  </button>
                  )}
                  <div className={`grid grid-cols-1 md:grid-cols-12 gap-5${isEmpty ? ' opacity-60 group-hover:opacity-100 transition-opacity' : ''}`}>
                    <div className="md:col-span-4 relative">
                      <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Company</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <span className="material-symbols-outlined text-slate-400 text-[18px]">apartment</span>
                        </div>
                        <input className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm py-2.5 pl-10 pr-4 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-sm" placeholder={isEmpty ? "e.g. Startup Inc." : "e.g. Google"} type="text" value={exp.company} onChange={(e) => updateExperience(i, 'company', e.target.value)} />
                      </div>
                    </div>
                    <div className="md:col-span-4 relative">
                      <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Role Title</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <span className="material-symbols-outlined text-slate-400 text-[18px]">badge</span>
                        </div>
                        <input className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm py-2.5 pl-10 pr-4 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-sm" placeholder={isEmpty ? "e.g. Developer" : "e.g. Senior Engineer"} type="text" value={exp.role} onChange={(e) => updateExperience(i, 'role', e.target.value)} />
                      </div>
                    </div>
                    <div className="md:col-span-4 relative">
                      <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Duration</label>
                      <div className="flex gap-2 items-center">
                        <div className="relative w-full">
                          <input className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm py-2.5 px-3 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-sm" placeholder="Start" type="text" value={exp.startDate} onChange={(e) => updateExperience(i, 'startDate', e.target.value)} />
                        </div>
                        <span className="text-slate-400 text-xs">to</span>
                        <div className="relative w-full">
                          <input className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm py-2.5 px-3 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-sm" placeholder="End" type="text" value={exp.endDate} onChange={(e) => updateExperience(i, 'endDate', e.target.value)} />
                        </div>
                      </div>
                    </div>
                    {!isEmpty && (
                    <div className="md:col-span-12 relative mt-1">
                      <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Description / Achievements</label>
                      <textarea className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm py-2.5 px-4 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-sm min-h-[80px] resize-y" placeholder="Describe your key responsibilities and achievements..." value={exp.description} onChange={(e) => updateExperience(i, 'description', e.target.value)}></textarea>
                    </div>
                    )}
                  </div>
                </div>
                );
              })}
            </div>
          </div>

          <div className="w-full border-t border-slate-200 dark:border-slate-700"></div>

          {/* Project Highlights */}
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-white">Project Highlights</h3>
                <p className="text-xs text-slate-500 mt-1">Showcase specific technical achievements.</p>
              </div>
              <button onClick={addProject} className="text-primary hover:text-primary-hover text-sm font-medium flex items-center justify-center transition-colors py-2 px-4 rounded-full border border-primary/30 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-primary" type="button">
                <span className="material-symbols-outlined text-[18px] mr-2">add</span>
                Add Project
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {projects.map((proj, i) => {
                const hasData = proj.name.trim();
                if (hasData) {
                  return (
                  <div key={i} className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-700 relative group transition-all hover:shadow-subtle hover:border-primary/40">
                    <button onClick={() => removeProject(i)} className="absolute right-3 top-3 text-slate-400 hover:text-red-500 p-1.5 rounded-full hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors" type="button">
                      <span className="material-symbols-outlined text-[18px]">delete</span>
                    </button>
                    <div className="flex items-start gap-4 mb-4">
                      <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
                        <span className="material-symbols-outlined">rocket_launch</span>
                      </div>
                      <div className="flex-1">
                        <input className="font-medium text-slate-900 dark:text-white text-sm bg-transparent border-0 p-0 focus:ring-0 w-full placeholder:text-slate-400" placeholder="Project Name" value={proj.name} onChange={(e) => updateProject(i, 'name', e.target.value)} />
                        <input className="text-xs text-slate-500 mt-1 bg-transparent border-0 p-0 focus:ring-0 w-full placeholder:text-slate-400" placeholder="Tech stack (e.g. React, TypeScript, GraphQL)" value={proj.tech} onChange={(e) => updateProject(i, 'tech', e.target.value)} />
                      </div>
                    </div>
                    <textarea className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed mb-3 bg-transparent border-0 p-0 focus:ring-0 w-full resize-none min-h-[48px] placeholder:text-slate-400" placeholder="Describe the project..." value={proj.description} onChange={(e) => updateProject(i, 'description', e.target.value)}></textarea>
                    <div className="flex gap-2">
                      <input className="text-xs font-medium text-primary bg-transparent border-0 p-0 focus:ring-0 placeholder:text-slate-400" placeholder="Link (optional)" value={proj.link} onChange={(e) => updateProject(i, 'link', e.target.value)} />
                    </div>
                  </div>
                  );
                }
                return (
                <div key={i} onClick={() => { if (!hasData) { const c = [...projects]; c[i] = { ...c[i], name: "New Project" }; setProjects(c); } }} className="bg-slate-50 dark:bg-slate-900/30 rounded-xl p-5 border border-dashed border-slate-300 dark:border-slate-700 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-slate-100/80 dark:hover:bg-slate-800/50 transition-colors h-full min-h-[160px]">
                  <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-400 flex items-center justify-center mb-3">
                    <span className="material-symbols-outlined">add</span>
                  </div>
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Add another project</span>
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
          <span className="material-symbols-outlined text-[16px] text-green-600 dark:text-green-400">lock</span>
          Safe &amp; Encrypted
        </div>
        <div className="flex gap-4">
          <button onClick={() => router.push("/analyze/skills")} className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white font-medium text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" type="button">
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
    <div className="hidden lg:block w-80 sticky top-24 shrink-0">
      <div className="bg-tip-bg border border-yellow-200/60 rounded-xl p-6 shadow-subtle relative overflow-hidden">
        <span className="material-symbols-outlined absolute -right-4 -bottom-4 text-[120px] text-yellow-500/10 pointer-events-none select-none">lightbulb</span>
        <div className="flex items-center gap-3 mb-4 relative z-10">
          <div className="bg-yellow-100 p-2 rounded-full text-yellow-700">
            <span className="material-symbols-outlined text-[20px]">lightbulb</span>
          </div>
          <h3 className="font-bold text-slate-800 text-sm">Experience Tips</h3>
        </div>
        <ul className="space-y-4 relative z-10">
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>Focus on <strong>impact</strong>. Use numbers and percentages to quantify your achievements (e.g., &quot;Increased efficiency by 20%&quot;).</span>
          </li>
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>For <strong>Project Highlights</strong>, mention the tech stack used. This helps our AI match your skills to job requirements.</span>
          </li>
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>Don&apos;t just list responsibilities; explain what you built or solved.</span>
          </li>
        </ul>
      </div>
      <div className="mt-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2">Need assistance?</h4>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">Our support team can review your experience entries for optimization.</p>
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
