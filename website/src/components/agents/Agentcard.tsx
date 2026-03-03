/ ╔══════════════════════════════════════════════════════════════╗
// ║   src/components/agents/AgentCard.tsx            ║
// ╚══════════════════════════════════════════════════════════════╝

import Image from "next/image";
import Link from "next/link";
import type { AgentContributor } from "@/lib/agents";

const STATUS_CONFIG = {
  ACTIVE: { dot: "bg-emerald-400 animate-pulse", text: "text-emerald-400", ring: "ring-emerald-400/20", bg: "bg-emerald-400/10" },
  IDLE:   { dot: "bg-amber-400",                 text: "text-amber-400",   ring: "ring-amber-400/20",   bg: "bg-amber-400/10"   },
  NEW:    { dot: "bg-sky-400",                   text: "text-sky-400",     ring: "ring-sky-400/20",     bg: "bg-sky-400/10"     },
} as const;

function StatusBadge({ status }: { status: "ACTIVE" | "IDLE" | "NEW" }) {
  const c = STATUS_CONFIG[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-bold tracking-widest ring-1 ${c.bg} ${c.text} ${c.ring}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {status}
    </span>
  );
}

function PRPill({ state }: { state: "open" | "closed" | "merged" }) {
  const s = {
    open:   "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20",
    closed: "bg-rose-500/10   text-rose-400   ring-rose-500/20",
    merged: "bg-violet-500/10 text-violet-400 ring-violet-500/20",
  }[state];
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${s}`}>
      {state}
    </span>
  );
}

function BountyStatus({ status }: { status: "in_progress" | "completed" }) {
  return status === "completed"
    ? <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 ring-1 ring-emerald-500/20">✓ DONE</span>
    : <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-400 ring-1 ring-amber-500/20">⟳ IN PROGRESS</span>;
}

export function AgentCard({ contributor }: { contributor: AgentContributor }) {
  const { login, avatarUrl, profileUrl, name, bio, activityStatus, assignedBounties, recentPRs, lastActiveAt } = contributor;

  const lastActiveFmt = lastActiveAt
    ? new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(
        -Math.floor((Date.now() - new Date(lastActiveAt).getTime()) / 86_400_000), "day"
      )
    : null;

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl border border-white/[0.06] bg-[#0d0d0d] transition-all duration-300 hover:border-violet-500/30 hover:shadow-[0_0_40px_-12px_rgba(139,92,246,0.25)]">
      {/* Header */}
      <div className="flex items-start gap-4 border-b border-white/[0.06] p-5">
        <Link href={profileUrl} target="_blank" rel="noopener noreferrer" className="relative flex-shrink-0">
          <div className="relative h-12 w-12 overflow-hidden rounded-full ring-2 ring-white/10 transition-all group-hover:ring-violet-500/40">
            <Image src={avatarUrl} alt={`${login} avatar`} fill className="object-cover" sizes="48px" />
          </div>
          {activityStatus === "ACTIVE" && (
            <span className="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-[#0d0d0d] bg-emerald-400" />
          )}
        </Link>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Link href={profileUrl} target="_blank" rel="noopener noreferrer"
              className="truncate font-semibold text-white hover:text-violet-300 transition-colors">
              {name || login}
            </Link>
            <StatusBadge status={activityStatus} />
          </div>
          <p className="mt-0.5 text-sm text-zinc-500">@{login}</p>
          {lastActiveFmt && <p className="mt-1 text-xs text-zinc-600">Last active {lastActiveFmt}</p>}
        </div>
      </div>

      {bio && <p className="px-5 pt-4 text-sm text-zinc-400 line-clamp-2">{bio}</p>}

      <div className="flex-1 space-y-4 px-5 py-4">
        {assignedBounties.length > 0 && (
          <div>
            <h3 className="mb-2 text-[11px] font-bold uppercase tracking-widest text-zinc-500">Assigned Bounties</h3>
            <ul className="space-y-2">
              {assignedBounties.map((b) => (
                <li key={b.id} className="flex items-start justify-between gap-2">
                  <Link href={b.url} target="_blank" rel="noopener noreferrer"
                    className="flex-1 text-sm text-zinc-300 hover:text-white line-clamp-1 transition-colors">
                    #{b.id} {b.title}
                  </Link>
                  <div className="flex flex-shrink-0 items-center gap-1.5">
                    {b.reward && <span className="text-xs font-bold text-violet-400">{b.reward}</span>}
                    <BountyStatus status={b.status} />
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {recentPRs.length > 0 && (
          <div>
            <h3 className="mb-2 text-[11px] font-bold uppercase tracking-widest text-zinc-500">Recent Pull Requests</h3>
            <ul className="space-y-2">
              {recentPRs.map((pr) => (
                <li key={pr.id} className="flex items-start justify-between gap-2">
                  <Link href={pr.url} target="_blank" rel="noopener noreferrer"
                    className="flex-1 text-sm text-zinc-300 hover:text-white line-clamp-1 transition-colors">
                    #{pr.number} {pr.title}
                  </Link>
                  <PRPill state={pr.state} />
                </li>
              ))}
            </ul>
          </div>
        )}

        {assignedBounties.length === 0 && recentPRs.length === 0 && (
          <p className="text-sm text-zinc-600 italic">No activity yet</p>
        )}
      </div>

      <div className="flex items-center justify-between border-t border-white/[0.06] px-5 py-3">
        <span className="text-xs text-zinc-600">{assignedBounties.length} bounties</span>
        <span className="text-xs text-zinc-600">{recentPRs.length} PRs</span>
      </div>
    </article>
  );
}

