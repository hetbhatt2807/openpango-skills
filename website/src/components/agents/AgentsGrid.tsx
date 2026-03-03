import Image from "next/image";
import Link from "next/link";
import {
  GitPullRequest,
  GitMerge,
  GitPullRequestDraft,
  Zap,
  Clock,
  Star,
  Trophy,
  Code2,
} from "lucide-react";
import {
  fetchContributors,
  fetchSkills,
  type Contributor,
  type ActivityStatus,
  type SkillEntry,
} from "@/lib/contributors";

// ── Status badge ──────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  ActivityStatus,
  { label: string; bg: string; text: string; dot: string; pulse: boolean }
> = {
  ACTIVE: {
    label: "ACTIVE",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    dot: "bg-emerald-400",
    pulse: true,
  },
  IDLE: {
    label: "IDLE",
    bg: "bg-amber-400/10",
    text: "text-amber-400",
    dot: "bg-amber-400",
    pulse: false,
  },
  NEW: {
    label: "NEW",
    bg: "bg-[#ff4d00]/10",
    text: "text-[#ff4d00]",
    dot: "bg-[#ff4d00]",
    pulse: false,
  },
};

function StatusBadge({ status }: { status: ActivityStatus }) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold tracking-widest ${cfg.bg} ${cfg.text}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${cfg.pulse ? "animate-pulse" : ""}`}
      />
      {cfg.label}
    </span>
  );
}

// ── PR state icon ─────────────────────────────────────────────────────────────

function PRIcon({ state }: { state: string }) {
  if (state === "merged")
    return <GitMerge className="w-3 h-3 text-purple-400" />;
  if (state === "changes_requested")
    return <GitPullRequestDraft className="w-3 h-3 text-amber-400" />;
  if (state === "open")
    return <GitPullRequest className="w-3 h-3 text-emerald-400" />;
  return <GitPullRequest className="w-3 h-3 text-zinc-600" />;
}

// ── Time ago helper ───────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const d = Math.floor(diff / 86400000);
  if (d === 0) return "today";
  if (d === 1) return "yesterday";
  if (d < 30) return `${d}d ago`;
  const m = Math.floor(d / 30);
  if (m < 12) return `${m}mo ago`;
  return `${Math.floor(m / 12)}y ago`;
}

// ── Single contributor card ───────────────────────────────────────────────────

function ContributorCard({ c }: { c: Contributor }) {
  const totalBounties = c.assignedBounties.length + c.completedBounties.length;

  return (
    <div className="bento group flex flex-col gap-0 overflow-hidden hover:border-white/10 transition-colors duration-300">
      {/* Header */}
      <div className="p-5 pb-4 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            href={c.profileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="relative shrink-0"
          >
            <Image
              src={c.avatarUrl}
              alt={c.login}
              width={40}
              height={40}
              className="rounded-xl object-cover ring-1 ring-white/10 group-hover:ring-white/20 transition-all"
            />
          </Link>
          <div>
            <Link
              href={c.profileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[14px] font-medium text-white hover:text-[#ff4d00] transition-colors leading-none"
            >
              {c.login}
            </Link>
            <div className="text-[11px] text-zinc-600 mt-1">
              {c.contributions} commit{c.contributions !== 1 ? "s" : ""}
              {c.lastActiveAt && <> · {timeAgo(c.lastActiveAt)}</>}
            </div>
          </div>
        </div>
        <StatusBadge status={c.activityStatus} />
      </div>

      {/* Stats row */}
      <div className="px-5 pb-4 grid grid-cols-3 gap-3">
        <div className="bg-white/[0.03] rounded-lg p-2.5 text-center">
          <div className="text-[15px] font-semibold text-white">{totalBounties}</div>
          <div className="text-[10px] text-zinc-600 mt-0.5">Bounties</div>
        </div>
        <div className="bg-white/[0.03] rounded-lg p-2.5 text-center">
          <div className="text-[15px] font-semibold text-emerald-400">
            {c.completedBounties.length}
          </div>
          <div className="text-[10px] text-zinc-600 mt-0.5">Completed</div>
        </div>
        <div className="bg-white/[0.03] rounded-lg p-2.5 text-center">
          <div className="text-[15px] font-semibold text-zinc-300">{c.recentPRs.length}</div>
          <div className="text-[10px] text-zinc-600 mt-0.5">PRs</div>
        </div>
      </div>

      {/* Assigned bounties */}
      {c.assignedBounties.length > 0 && (
        <div className="px-5 pb-4">
          <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Zap className="w-3 h-3" /> In Progress
          </div>
          <div className="flex flex-col gap-1.5">
            {c.assignedBounties.slice(0, 2).map((b) => (
              <a
                key={b.number}
                href={b.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between bg-amber-400/5 border border-amber-400/10 rounded-lg px-3 py-2 hover:border-amber-400/20 transition-colors"
              >
                <span className="text-[12px] text-zinc-300 line-clamp-1 flex-1">
                  {b.title}
                </span>
                {b.reward && (
                  <span className="text-[11px] text-[#ff4d00] font-semibold ml-2 shrink-0">
                    {b.reward}
                  </span>
                )}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Completed bounties */}
      {c.completedBounties.length > 0 && (
        <div className="px-5 pb-4">
          <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Trophy className="w-3 h-3" /> Completed
          </div>
          <div className="flex flex-col gap-1.5">
            {c.completedBounties.slice(0, 2).map((b) => (
              <a
                key={b.number}
                href={b.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between bg-emerald-500/5 border border-emerald-500/10 rounded-lg px-3 py-2 hover:border-emerald-500/20 transition-colors"
              >
                <span className="text-[12px] text-zinc-400 line-clamp-1 flex-1">
                  {b.title}
                </span>
                {b.reward && (
                  <span className="text-[11px] text-emerald-400 font-semibold ml-2 shrink-0">
                    {b.reward}
                  </span>
                )}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Recent PRs */}
      {c.recentPRs.length > 0 && (
        <div className="px-5 pb-5 mt-auto">
          <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <GitPullRequest className="w-3 h-3" /> Recent PRs
          </div>
          <div className="flex flex-col gap-1">
            {c.recentPRs.slice(0, 3).map((pr) => (
              <a
                key={pr.number}
                href={pr.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 group/pr py-1"
              >
                <PRIcon state={pr.state} />
                <span className="text-[12px] text-zinc-500 group-hover/pr:text-zinc-300 transition-colors line-clamp-1 flex-1">
                  {pr.title}
                </span>
                <span className="text-[10px] text-zinc-700 shrink-0">#{pr.number}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {c.assignedBounties.length === 0 &&
        c.completedBounties.length === 0 &&
        c.recentPRs.length === 0 && (
          <div className="px-5 pb-5">
            <p className="text-[12px] text-zinc-600 italic">No activity yet</p>
          </div>
        )}
    </div>
  );
}

// ── Skill map card ────────────────────────────────────────────────────────────

function SkillCard({ skill }: { skill: SkillEntry }) {
  return (
    <div className="bento p-4 flex items-start gap-3 hover:border-white/10 transition-colors">
      <div className="w-8 h-8 rounded-lg bg-[#ff4d00]/10 flex items-center justify-center shrink-0">
        <Code2 className="w-4 h-4 text-[#ff4d00]" />
      </div>
      <div>
        <div className="text-[13px] font-medium text-white">{skill.name}</div>
        <div className="text-[11px] text-zinc-600 mt-0.5 line-clamp-2">{skill.description}</div>
      </div>
    </div>
  );
}

// ── Summary bar ───────────────────────────────────────────────────────────────

function SummaryBar({ contributors }: { contributors: Contributor[] }) {
  const active = contributors.filter((c) => c.activityStatus === "ACTIVE").length;
  const idle = contributors.filter((c) => c.activityStatus === "IDLE").length;
  const totalCompleted = contributors.reduce((n, c) => n + c.completedBounties.length, 0);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-10">
      {[
        { label: "Total Contributors", value: contributors.length, color: "text-white" },
        { label: "Active Now", value: active, color: "text-emerald-400" },
        { label: "Idle", value: idle, color: "text-amber-400" },
        { label: "Bounties Completed", value: totalCompleted, color: "text-[#ff4d00]" },
      ].map(({ label, value, color }) => (
        <div key={label} className="bento p-4 text-center">
          <div className={`text-2xl font-bold ${color}`}>{value}</div>
          <div className="text-[11px] text-zinc-600 mt-1">{label}</div>
        </div>
      ))}
    </div>
  );
}

// ── Main server component ─────────────────────────────────────────────────────

export async function AgentsGrid() {
  const [contributors, skills] = await Promise.all([
    fetchContributors(),
    fetchSkills(),
  ]);

  if (contributors.length === 0) {
    return (
      <div className="bento text-center py-20">
        <Clock className="w-8 h-8 text-zinc-700 mx-auto mb-4" />
        <h3 className="text-[15px] text-zinc-400 mb-2">No contributors yet</h3>
        <p className="text-[13px] text-zinc-600 max-w-sm mx-auto">
          Be the first to contribute to the OpenPango ecosystem.
        </p>
      </div>
    );
  }

  return (
    <div>
      <SummaryBar contributors={contributors} />

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-16">
        {contributors.map((c) => (
          <ContributorCard key={c.login} c={c} />
        ))}
      </div>

      {skills.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-6">
            <Star className="w-4 h-4 text-[#ff4d00]" />
            <h2 className="text-[18px] font-semibold text-white">Skill Map</h2>
            <span className="text-[12px] text-zinc-600 bg-white/[0.04] px-2.5 py-1 rounded-full">
              {skills.length} modules
            </span>
          </div>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {skills.map((s) => (
              <SkillCard key={s.path} skill={s} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
