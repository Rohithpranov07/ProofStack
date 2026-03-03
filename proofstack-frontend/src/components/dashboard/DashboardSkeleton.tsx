"use client";

export default function DashboardSkeleton() {
  return (
    <div className="min-h-screen dash-bg">
      {/* Header skeleton */}
      <header className="bg-white border-b border-[#DADCE0] sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="skeleton w-8 h-8 rounded-full" />
              <div className="skeleton w-24 h-5 rounded" />
            </div>
            <div className="h-6 w-px bg-[#DADCE0] mx-2" />
            <div className="flex items-center gap-3">
              <div className="skeleton w-8 h-8 rounded-full" />
              <div>
                <div className="skeleton w-32 h-4 rounded mb-1" />
                <div className="skeleton w-20 h-3 rounded" />
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="skeleton w-32 h-9 rounded-full" />
            <div className="skeleton w-28 h-9 rounded-full" />
          </div>
        </div>
      </header>

      {/* Body skeleton */}
      <main className="max-w-[1600px] mx-auto p-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left column */}
          <div className="col-span-12 lg:col-span-4 space-y-6">
            {/* Trust score */}
            <div className="dash-card p-6">
              <div className="flex justify-between mb-4">
                <div className="skeleton w-40 h-5 rounded" />
                <div className="skeleton w-20 h-6 rounded-full" />
              </div>
              <div className="flex flex-col items-center py-12">
                <div className="skeleton w-32 h-16 rounded mb-4" />
                <div className="skeleton w-48 h-48 rounded-full" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="skeleton w-full h-4 rounded" />
                ))}
              </div>
            </div>

            {/* Risk signals */}
            <div className="dash-card p-0 overflow-hidden">
              <div className="px-6 py-4 bg-gray-50 border-b border-[#DADCE0]/50">
                <div className="skeleton w-28 h-4 rounded" />
              </div>
              <div className="divide-y divide-[#DADCE0]/30">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="p-4 space-y-2">
                    <div className="skeleton w-3/4 h-4 rounded" />
                    <div className="skeleton w-full h-3 rounded" />
                  </div>
                ))}
              </div>
            </div>

            {/* Problem solving mini */}
            <div className="dash-card p-6">
              <div className="skeleton w-32 h-5 rounded mb-4" />
              <div className="flex items-end gap-2 h-32 justify-between px-2">
                {[60, 80, 35, 50, 45].map((h, i) => (
                  <div key={i} className="flex flex-col items-center flex-1 gap-1">
                    <div className="skeleton w-8 rounded-t" style={{ height: `${h}%` }} />
                    <div className="skeleton w-6 h-3 rounded" />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right column */}
          <div className="col-span-12 lg:col-span-8 space-y-6">
            {/* Code Authenticity */}
            <div className="dash-card p-6">
              <div className="flex justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="skeleton w-10 h-10 rounded-lg" />
                  <div>
                    <div className="skeleton w-36 h-5 rounded mb-1" />
                    <div className="skeleton w-48 h-3 rounded" />
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="skeleton w-16 h-10 rounded" />
                  <div className="skeleton w-16 h-10 rounded" />
                </div>
              </div>
              <div className="skeleton w-full h-48 rounded" />
            </div>

            {/* Profile consistency table */}
            <div className="dash-card overflow-hidden">
              <div className="p-6 border-b border-[#DADCE0]/50">
                <div className="skeleton w-56 h-5 rounded" />
              </div>
              <div className="p-0">
                <div className="grid grid-cols-4 gap-4 px-6 py-3 bg-gray-50 border-b">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="skeleton w-full h-3 rounded" />
                  ))}
                </div>
                {[1, 2, 3].map((i) => (
                  <div key={i} className="grid grid-cols-4 gap-4 px-6 py-4 border-b border-[#DADCE0]/30">
                    {[1, 2, 3, 4].map((j) => (
                      <div key={j} className="skeleton w-full h-4 rounded" />
                    ))}
                  </div>
                ))}
              </div>
            </div>

            {/* Product + Digital 2-col */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2].map((i) => (
                <div key={i} className="dash-card p-6 space-y-3">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="skeleton w-10 h-10 rounded-lg" />
                    <div className="skeleton w-28 h-5 rounded" />
                  </div>
                  {[1, 2, 3].map((j) => (
                    <div key={j} className="space-y-1">
                      <div className="skeleton w-full h-3 rounded" />
                      <div className="skeleton w-full h-1.5 rounded-full" />
                    </div>
                  ))}
                </div>
              ))}
            </div>

            {/* Final rec */}
            <div className="dash-card p-6">
              <div className="skeleton w-48 h-6 rounded mb-3" />
              <div className="skeleton w-full h-4 rounded mb-2" />
              <div className="skeleton w-3/4 h-4 rounded mb-4" />
              <div className="flex gap-3">
                <div className="skeleton w-28 h-10 rounded-lg" />
                <div className="skeleton w-36 h-10 rounded-lg" />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
