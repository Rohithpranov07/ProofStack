import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-border-light bg-gray-50 py-16 dark:border-border-dark dark:bg-[#18191a]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-8 mb-16">
          {/* Brand */}
          <div className="lg:col-span-2 pr-8">
            <Link href="/" className="flex items-center gap-2 mb-6">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-google-blue text-white shadow-sm">
                <span className="material-symbols-outlined" style={{ fontSize: 20 }}>verified_user</span>
              </div>
              <span className="text-xl font-bold text-text-primary-light dark:text-text-primary-dark">ProofStack</span>
            </Link>
            <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark mb-8 max-w-xs leading-relaxed">
              The new standard for technical skill verification. Built for engineering leaders, by engineers.
            </p>
            <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-white dark:bg-surface-dark border border-border-light dark:border-border-dark shadow-sm hover:shadow-md transition-shadow cursor-default">
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-google-blue text-white">
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>verified_user</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-semibold text-text-secondary-light uppercase tracking-wide">Verified by</span>
                <span className="text-xs font-bold text-text-primary-light dark:text-text-primary-dark">ProofStack™ Cloud</span>
              </div>
            </div>
          </div>

          {/* Platform */}
          <div>
            <h4 className="font-semibold text-text-primary-light dark:text-text-primary-dark mb-6">Platform</h4>
            <ul className="space-y-4 text-sm text-text-secondary-light dark:text-text-secondary-dark">
              <li><a className="hover:text-google-blue transition-colors" href="/#how-it-works">How It Works</a></li>
              <li><a className="hover:text-google-blue transition-colors" href="/#engines">Engines</a></li>
              <li><a className="hover:text-google-blue transition-colors" href="/#scoring">Scoring Model</a></li>
              <li><Link className="hover:text-google-blue transition-colors" href="/analyze">Demo</Link></li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-semibold text-text-primary-light dark:text-text-primary-dark mb-6">Legal</h4>
            <ul className="space-y-4 text-sm text-text-secondary-light dark:text-text-secondary-dark">
              <li><Link className="hover:text-google-blue transition-colors" href="/privacy">Privacy</Link></li>
              <li><Link className="hover:text-google-blue transition-colors" href="/terms">Terms</Link></li>
              <li><Link className="hover:text-google-blue transition-colors" href="/data-policy">Data Policy</Link></li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-border-light dark:border-border-dark pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark">© 2026 ProofStack. Built for AI4Dev Hackathon — Engineered for real-world hiring.</p>
          <div className="flex gap-4">
            <a className="text-text-secondary-light hover:text-google-blue dark:text-text-secondary-dark dark:hover:text-google-blue transition-colors p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full" href="https://www.linkedin.com/in/rohith-pranov/" target="_blank" rel="noopener noreferrer">
              <span className="sr-only">LinkedIn</span>
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.475-2.236-1.986-2.236-1.081 0-1.722.722-2.004 1.418-.103.249-.129.597-.129.946v5.441h-3.554s.05-8.824 0-9.738h3.554v1.375c.4-.627 1.196-1.514 2.91-1.514 2.122 0 3.714 1.388 3.714 4.369v5.508zM5.337 8.855c-1.188 0-1.962-.793-1.962-1.784 0-1.014.75-1.784 2.009-1.784 1.255 0 1.96.77 1.984 1.784 0 .991-.729 1.784-2.031 1.784zm1.946 11.597H3.392V9.669h3.891v10.783zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z"></path></svg>
            </a>
            <a className="text-text-secondary-light hover:text-google-blue dark:text-text-secondary-dark dark:hover:text-google-blue transition-colors p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full" href="https://github.com/Rohithpranov07" target="_blank" rel="noopener noreferrer">
              <span className="sr-only">GitHub</span>
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" fillRule="evenodd"></path></svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
