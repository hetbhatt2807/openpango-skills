import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-white/[0.04] py-10 px-5">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2">
          <span className="text-lg">🦔</span>
          <span className="text-[14px] font-semibold text-white">OpenPango</span>
        </div>
        <div className="flex flex-wrap gap-6 text-[13px] text-zinc-600">
          <Link href="/docs" className="hover:text-white transition-colors">Docs</Link>
          <Link href="/docs/mining-pool" className="hover:text-white transition-colors">Mining</Link>
          <Link href="/docs/bounty-program" className="hover:text-white transition-colors">Bounties</Link>
          <Link href="/leaderboard" className="hover:text-white transition-colors">Leaderboard</Link>
          <a href="https://github.com/openpango" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">GitHub ↗</a>
        </div>
        <div className="text-[12px] text-zinc-700">© {new Date().getFullYear()}</div>
      </div>
    </footer>
  );
}
