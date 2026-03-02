"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/#features", label: "Features" },
  { href: "/#mining", label: "Mining" },
  { href: "/#bounties", label: "Bounties" },
  { href: "/docs", label: "Docs" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 w-full z-50 bg-black/70 backdrop-blur-xl border-b border-white/[0.04]">
      <div className="max-w-6xl mx-auto px-5 h-12 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-lg">🦔</span>
          <span className="text-[14px] font-semibold tracking-tight text-white">OpenPango</span>
        </Link>

        <div className="hidden md:flex items-center bg-white/[0.04] rounded-full px-1 py-0.5">
          {links.map((l) => (
            <Link
              key={l.label}
              href={l.href}
              className={cn(
                "text-[13px] px-3.5 py-1 rounded-full transition-all",
                pathname === l.href
                  ? "bg-white/[0.1] text-white"
                  : "text-zinc-500 hover:text-white"
              )}
            >
              {l.label}
            </Link>
          ))}
        </div>

        <a
          href="https://github.com/openpango"
          target="_blank"
          rel="noopener noreferrer"
          className="text-[13px] text-zinc-500 hover:text-white transition-colors"
        >
          GitHub ↗
        </a>
      </div>
    </nav>
  );
}
