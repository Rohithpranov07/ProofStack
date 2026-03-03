"use client";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

export default function AnalyzeProfilesPage() {
  const router = useRouter();
  const [githubUsername, setGithubUsername] = useState("");
  const [leetcodeUsername, setLeetcodeUsername] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [linkedinHeadline, setLinkedinHeadline] = useState("");
  const [roleLevel, setRoleLevel] = useState("Mid Level");
  const [portfolioLinks, setPortfolioLinks] = useState([""]);

  useEffect(() => {
    // Clear all wizard data on fresh page load (step 1 = entry point)
    localStorage.removeItem("proofstack_step1");
    localStorage.removeItem("proofstack_step2");
    localStorage.removeItem("proofstack_step3");
  }, []);

  const handleContinue = () => {
    localStorage.setItem("proofstack_step1", JSON.stringify({ githubUsername, leetcodeUsername, linkedinUrl, linkedinHeadline, roleLevel, portfolioLinks }));
    router.push("/analyze/skills");
  };

  const addLink = () => setPortfolioLinks([...portfolioLinks, ""]);
  const removeLink = (i: number) => setPortfolioLinks(portfolioLinks.filter((_, idx) => idx !== i));
  const updateLink = (i: number, v: string) => { const c = [...portfolioLinks]; c[i] = v; setPortfolioLinks(c); };

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
        <h1 className="text-2xl font-normal text-slate-900 dark:text-white mb-8">Profiles &amp; Links</h1>
        {/* Stepper */}
        <div className="flex items-center w-full text-sm select-none">
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white text-sm font-bold shadow-md ring-2 ring-primary/20 transition-all group-hover:scale-105">1</div>
            <span className="font-medium text-primary dark:text-white">Profiles</span>
          </div>
          <div className="h-[2px] w-12 bg-slate-200 mx-3 rounded-full"></div>
          <div className="flex items-center gap-2 opacity-60 group cursor-not-allowed">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 border border-slate-300 text-slate-500 dark:text-slate-400 text-sm font-medium">2</div>
            <span className="font-medium text-slate-600 dark:text-slate-400">Resume</span>
          </div>
          <div className="h-[2px] w-12 bg-slate-200 mx-3 rounded-full opacity-60"></div>
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
          Connect your professional identity. Providing these links allows our AI to verify your technical footprint across the ecosystem.
        </p>
      </div>

      {/* Form */}
      <div className="p-8 bg-white dark:bg-slate-800">
        <form className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="relative group">
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2" htmlFor="github-username">GitHub Username <span className="text-red-500">*</span></label>
              <div className="relative transition-all duration-200 ease-in-out focus-within:scale-[1.01]">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-slate-500 dark:text-slate-400" fill="currentColor" viewBox="0 0 24 24">
                    <path clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" fillRule="evenodd"></path>
                  </svg>
                </div>
                <input className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900/50 text-slate-900 dark:text-white text-sm py-3 pl-11 pr-4 focus:border-primary focus:ring-2 focus:ring-primary/20 focus:bg-white dark:focus:bg-slate-900 transition-all shadow-sm placeholder:text-slate-400" id="github-username" placeholder="e.g. torvalds" type="text" value={githubUsername} onChange={(e) => setGithubUsername(e.target.value)} />
              </div>
            </div>
            <div className="relative group">
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2" htmlFor="leetcode-username">LeetCode / HackerRank</label>
              <div className="relative transition-all duration-200 ease-in-out focus-within:scale-[1.01]">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <span className="material-symbols-outlined text-slate-400 text-[20px]">code</span>
                </div>
                <input className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900/50 text-slate-900 dark:text-white text-sm py-3 pl-11 pr-4 focus:border-primary focus:ring-2 focus:ring-primary/20 focus:bg-white dark:focus:bg-slate-900 transition-all shadow-sm placeholder:text-slate-400" id="leetcode-username" placeholder="e.g. neetcode" type="text" value={leetcodeUsername} onChange={(e) => setLeetcodeUsername(e.target.value)} />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="relative group">
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2" htmlFor="linkedin-url">LinkedIn URL</label>
              <div className="relative transition-all duration-200 ease-in-out focus-within:scale-[1.01]">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-[#0077b5]" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"></path>
                  </svg>
                </div>
                <input className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900/50 text-slate-900 dark:text-white text-sm py-3 pl-11 pr-4 focus:border-primary focus:ring-2 focus:ring-primary/20 focus:bg-white dark:focus:bg-slate-900 transition-all shadow-sm placeholder:text-slate-400" id="linkedin-url" placeholder="linkedin.com/in/username" type="url" value={linkedinUrl} onChange={(e) => setLinkedinUrl(e.target.value)} />
              </div>
            </div>
            <div className="relative group">
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2" htmlFor="linkedin-headline">Headline</label>
              <div className="relative transition-all duration-200 ease-in-out focus-within:scale-[1.01]">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <span className="material-symbols-outlined text-slate-400 text-[20px]">badge</span>
                </div>
                <input className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900/50 text-slate-900 dark:text-white text-sm py-3 pl-11 pr-4 focus:border-primary focus:ring-2 focus:ring-primary/20 focus:bg-white dark:focus:bg-slate-900 transition-all shadow-sm placeholder:text-slate-400" id="linkedin-headline" placeholder="e.g. Senior SWE" type="text" value={linkedinHeadline} onChange={(e) => setLinkedinHeadline(e.target.value)} />
              </div>
            </div>
          </div>

          <div className="relative group pt-2">
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2" htmlFor="role-level">Target Role Level <span className="text-red-500">*</span></label>
            <div className="relative transition-all duration-200 ease-in-out focus-within:scale-[1.01]">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                <span className="material-symbols-outlined text-slate-400 text-[20px]">equalizer</span>
              </div>
              <select className="block w-full appearance-none rounded-lg border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900/50 text-slate-900 dark:text-white text-sm py-3 pl-11 pr-10 focus:border-primary focus:ring-2 focus:ring-primary/20 focus:bg-white dark:focus:bg-slate-900 transition-all shadow-sm" id="role-level" value={roleLevel} onChange={(e) => setRoleLevel(e.target.value)}>
                <option>Mid Level</option>
                <option>Junior Level</option>
                <option>Senior Level</option>
                <option>Staff / Principal</option>
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-slate-500">
                <span className="material-symbols-outlined">expand_more</span>
              </div>
            </div>
          </div>

          {/* Portfolio Links */}
          <div className="pt-6 border-t border-dashed border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-5">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Portfolio / Project Links</label>
                <p className="text-xs text-slate-400 mt-1">Add personal websites, blogs, or specific project demos.</p>
              </div>
              <button onClick={addLink} className="text-primary hover:text-primary-hover text-sm font-medium flex items-center justify-center transition-colors py-2 px-4 rounded-full border border-primary/30 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-primary" type="button">
                <span className="material-symbols-outlined text-[18px] mr-2">add_link</span>
                Add Link
              </button>
            </div>
            <div className="space-y-4">
              {portfolioLinks.map((link, i) => (
              <div key={i} className="relative transition-all duration-200 ease-in-out hover:scale-[1.01]">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <span className="material-symbols-outlined text-slate-400 text-[20px]">link</span>
                </div>
                <input className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm py-3 pl-11 pr-12 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-sm placeholder:text-slate-400" placeholder="https://myportfolio.com" type="url" value={link} onChange={(e) => updateLink(i, e.target.value)} />
                <button onClick={() => removeLink(i)} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-red-500 p-1.5 rounded-full hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors" type="button">
                  <span className="material-symbols-outlined text-[18px]">delete</span>
                </button>
              </div>
              ))}
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
          <button onClick={() => router.push("/")} className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white font-medium text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" type="button">
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
          <h3 className="font-bold text-slate-800 text-sm">Quick Tips</h3>
        </div>
        <ul className="space-y-4 relative z-10">
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>Make sure your <strong>GitHub</strong> public activity is visible. We analyze commit history and language distribution.</span>
          </li>
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>For <strong>LinkedIn</strong>, a customized URL (e.g., /in/johndoe) looks more professional.</span>
          </li>
          <li className="flex gap-3 text-xs text-tip-text leading-5">
            <span className="material-symbols-outlined text-[16px] text-yellow-600 mt-0.5">check_circle</span>
            <span>Including a portfolio link significantly increases your visibility score for frontend roles.</span>
          </li>
        </ul>
      </div>
      <div className="mt-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2">Need assistance?</h4>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">Our support team can help you export your data from other platforms.</p>
        <a className="text-primary text-xs font-medium hover:underline flex items-center gap-1" href="#">
          Contact Support <span className="material-symbols-outlined text-[14px]">open_in_new</span>
        </a>
      </div>
    </div>
  </div>
</main>

<footer className="py-8 text-center text-xs text-slate-400 dark:text-slate-500 z-10 relative">
  <p>© 2026 ProofStack. Built for truth.</p>
</footer>
</div>
  );
}
