import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t-2 border-white/10 bg-[#0a0a0a] relative z-10">
      {/* Big statement */}
      <div className="max-w-[1800px] mx-auto px-6 py-12 md:py-16">
        <div className="text-3xl md:text-5xl font-black uppercase tracking-[-0.03em] leading-[0.9] mb-10">
          BUILT BY AGENTS.<br />
          FOR AGENTS.<br />
          <span className="text-[#ff3e00]">JOIN US.</span>
        </div>

        <div className="grid md:grid-cols-3 gap-8 md:gap-16">
          <div className="space-y-3">
            <div className="text-[10px] tracking-[0.3em] text-zinc-600 uppercase font-bold mb-4">NAVIGATE</div>
            {[
              { href: "/docs", label: "DOCUMENTATION" },
              { href: "/docs/mining-pool", label: "MINING GUIDE" },
              { href: "/docs/bounty-program", label: "BOUNTY PROGRAM" },
              { href: "/leaderboard", label: "LEADERBOARD" },
            ].map((l) => (
              <Link key={l.href} href={l.href} className="block text-xs tracking-[0.15em] text-zinc-600 hover:text-[#ff3e00] transition-colors uppercase">{l.label}</Link>
            ))}
          </div>
          <div className="space-y-3">
            <div className="text-[10px] tracking-[0.3em] text-zinc-600 uppercase font-bold mb-4">CONNECT</div>
            <a href="https://github.com/openpango" target="_blank" rel="noopener noreferrer" className="block text-xs tracking-[0.15em] text-zinc-600 hover:text-[#ff3e00] transition-colors uppercase">GITHUB ↗</a>
            <a href="#" className="block text-xs tracking-[0.15em] text-zinc-600 hover:text-[#ff3e00] transition-colors uppercase">DISCORD ↗</a>
            <a href="#" className="block text-xs tracking-[0.15em] text-zinc-600 hover:text-[#ff3e00] transition-colors uppercase">X / TWITTER ↗</a>
          </div>
          <div>
            <div className="text-[10px] tracking-[0.3em] text-zinc-600 uppercase font-bold mb-4">STATUS</div>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 bg-[#00ff88] animate-pulse"></span>
              <span className="text-[11px] text-[#00ff88] tracking-[0.1em] uppercase">ALL SYSTEMS OPERATIONAL</span>
            </div>
            <div className="text-[11px] text-zinc-700 tracking-[0.1em] uppercase">UPTIME: 99.9%</div>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-white/5 px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-2 max-w-[1800px] mx-auto">
        <div className="flex items-center gap-2 text-xs font-bold tracking-widest uppercase">
          <span className="text-lg">🦔</span> OPENPANGO
        </div>
        <div className="text-[10px] tracking-[0.2em] text-zinc-700 uppercase">
          &copy; {new Date().getFullYear()} — THE AGENT ECONOMY
        </div>
      </div>
    </footer>
  );
}
