export function AgentsGridSkeleton() {
  return (
    <div>
      {/* Stats skeleton */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-10">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bento p-4 animate-pulse">
            <div className="h-8 w-12 bg-white/[0.04] rounded mx-auto mb-2" />
            <div className="h-3 w-20 bg-white/[0.04] rounded mx-auto" />
          </div>
        ))}
      </div>

      {/* Cards skeleton */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bento p-5 animate-pulse">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-white/[0.04]" />
              <div className="flex-1">
                <div className="h-3.5 w-24 bg-white/[0.04] rounded mb-2" />
                <div className="h-2.5 w-16 bg-white/[0.04] rounded" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3 mb-4">
              {Array.from({ length: 3 }).map((_, j) => (
                <div key={j} className="h-12 bg-white/[0.04] rounded-lg" />
              ))}
            </div>
            <div className="space-y-2">
              <div className="h-2 w-20 bg-white/[0.04] rounded" />
              <div className="h-8 bg-white/[0.04] rounded-lg" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
