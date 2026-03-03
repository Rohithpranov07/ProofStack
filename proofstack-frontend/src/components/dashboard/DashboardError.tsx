"use client";

interface DashboardErrorProps {
  message: string;
  onRetry?: () => void;
}

export default function DashboardError({ message, onRetry }: DashboardErrorProps) {
  return (
    <div className="min-h-screen dash-bg flex items-center justify-center">
      <div className="dash-card p-10 max-w-md w-full text-center">
        <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-4">
          <span className="material-symbols-outlined text-[#D93025] text-3xl filled">error</span>
        </div>
        <h2
          className="text-xl font-bold text-gray-900 mb-2"
          style={{ fontFamily: "'Google Sans', 'Inter', sans-serif" }}
        >
          Dashboard Load Failed
        </h2>
        <p className="text-sm text-gray-500 mb-6 leading-relaxed">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-6 py-2.5 rounded-full bg-[#1A73E8] text-white text-sm font-medium shadow-sm hover:bg-[#1557b0] transition-colors"
          >
            <span className="material-symbols-outlined text-base align-middle mr-1">refresh</span>
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
