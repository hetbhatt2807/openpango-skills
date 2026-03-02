import Link from "next/link";

export function Footer() {
  return (
    <footer className="py-12 border-t border-white/10 bg-black text-center relative z-10">
      <div className="font-bold text-xl tracking-widest uppercase mb-6 flex items-center justify-center gap-3">
        <span className="text-2xl">🦔</span> OPENPANGO
      </div>
      <div className="flex justify-center gap-6 mb-8 font-mono text-sm text-zinc-500 uppercase tracking-widest">
        <Link href="/docs" className="hover:text-accent transition-colors">Documentation</Link>
        <a href="https://github.com/openpango" target="_blank" rel="noopener noreferrer" className="hover:text-accent transition-colors">GitHub</a>
        <a href="#" className="hover:text-accent transition-colors">Discord</a>
      </div>
      <p className="text-zinc-600 font-mono text-xs uppercase tracking-widest">
        &copy; {new Date().getFullYear()} OpenPango Runtime. All systems nominal.
      </p>
    </footer>
  );
}
