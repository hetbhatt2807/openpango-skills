"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Menu, X } from "lucide-react";

const links = [
  { href: "/#features", label: "Features" },
  { href: "/mining", label: "Mining" },
  { href: "/#bounties", label: "Bounties" },
  { href: "/docs", label: "Docs" },
  { href: "/leaderboard", label: "Leaderboard" },
];

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <nav className="fixed top-0 w-full z-50 bg-black/70 backdrop-blur-xl border-b border-white/[0.04]">
      <div className="max-w-6xl mx-auto px-5 h-12 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group" onClick={() => setOpen(false)}>
          <span className="text-lg">🦔</span>
          <span className="text-[14px] font-semibold tracking-tight text-white">OpenPango</span>
        </Link>

        {/* Desktop nav */}
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

        <div className="flex items-center gap-3">
          <a
            href="https://github.com/openpango"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden md:inline text-[13px] text-zinc-500 hover:text-white transition-colors"
          >
            GitHub ↗
          </a>

          {/* Mobile hamburger */}
          <button
            className="md:hidden text-zinc-400 hover:text-white transition-colors p-1"
            onClick={() => setOpen(!open)}
            aria-label="Toggle menu"
          >
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-white/[0.04] bg-black/95 backdrop-blur-xl px-5 py-4 space-y-1">
          {links.map((l) => (
            <Link
              key={l.label}
              href={l.href}
              onClick={() => setOpen(false)}
              className={cn(
                "block py-2.5 text-[14px] transition-colors",
                pathname === l.href ? "text-white" : "text-zinc-500 hover:text-white"
              )}
            >
              {l.label}
            </Link>
          ))}
          <a
            href="https://github.com/openpango"
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setOpen(false)}
            className="block py-2.5 text-[14px] text-zinc-500 hover:text-white transition-colors"
          >
            GitHub ↗
          </a>
        </div>
      )}
    </nav>
  );
}
