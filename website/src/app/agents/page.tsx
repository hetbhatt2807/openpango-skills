// ╔══════════════════════════════════════════════════════════════╗
// ║  📄 FILE 3 — src/app/agents/page.tsx                        ║
// ╚══════════════════════════════════════════════════════════════╝

import { Suspense } from "react";
import { getAgentContributors, getEcosystemSkills } from "@/lib/agents";
import { AgentCard } from "@/components/agents/AgentCard";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Agents | OpenPango",
  description: "Live GitHub contributors, bounties, and skill ecosystem powering OpenPango.",
};

// Revalidate every 5 minutes
export const revalidate = 300;

// ─── Skeleton ────────────────────────────────────────────────────────────────

function AgentCardSkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-white/[0.06] bg-[#0d0d0d] p-5 space-y-4">
      <div className="flex items-start gap-4">
        <div className="h-12 w-12 rounded-full bg-white/[0.06]" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-32 rounded bg-white/[0.06]" />
          <div className="h-3 w-20 rounded bg-white/[0.04]" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full rounded bg-white/[0.04]" />
        <div className="h-3 w-3/4 rounded bg-white/[0.04]" />
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full rounded bg-white/[0.04]" />
        <div className="h-3 w-2/3 rounded bg-white/[0.04]" />
      </div>
    </div>
  );
}

// ─── Agent Grid (async server component) ─────────────────────────────────────

async function AgentGrid() {
  const contributors = await getAgentContributors();

  if (contributors.length === 0) {
    return (
      <div className="col-span-full flex flex-col items-center justify-center rounded-2xl border border-white/[0.06] bg-[#0d0d0d] py-20 text-center">
        <div className="mb-4 text-4xl">🤖</div>
        <p className="text-zinc-400 font-medium">No agents found yet.</p>
        <p className="mt-1 text-sm text-zinc-600">Contributors who apply to bounties will appear here.</p>
      </div>
    );
  }

  const active = contributors.filter((c) => c.activityStatus === "ACTIVE").length;
  const idle   = contributors.filter((c) => c.activityStatus === "IDLE").length;
  const newC   = contributors.filter((c) => c.activityStatus === "NEW").length;

  return (
    <>
      {/* Stat row */}
      <div className="col-span-full mb-2 flex flex-wrap gap-6">
        {[
          { label: "Total Agents",   value: contributors.length, color: "text-white"       },
          { label: "Active",         value: active,              color: "text-emerald-400" },
          { label: "Idle",           value: idle,                color: "text-amber-400"   },
          { label: "New",            value: newC,                color: "text-sky-400"     },
        ].map(({ label, value, color }) => (
          <div key={label} className="flex flex-col">
            <span className={`text-2xl font-bold tabular-nums ${color}`}>{value}</span>
            <span className="text-xs text-zinc-500">{label}</span>
          </div>
        ))}
      </div>

      {/* Cards */}
      {contributors.map((contributor) => (
        <AgentCard key={contributor.login} contributor={contributor} />
      ))}
    </>
  );
}

// ─── Skills Section (async server component) ──────────────────────────────────

async function SkillMap() {
  const skills = await getEcosystemSkills();

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
      {skills.map((skill) => (
        <div
          key={skill.name}
          className="group relative overflow-hidden rounded-xl border border-white/[0.06] bg-[#0d0d0d] p-4 transition-all hover:border-white/[0.12]"
        >
          <div
            className="absolute inset-0 opacity-5 transition-opacity group-hover:opacity-10"
            style={{ background: `radial-gradient(circle at 30% 30%, ${skill.color}, transparent 70%)` }}
          />
          <div className="relative">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white text-sm">{skill.name}</span>
              <span
                className="h-2 w-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: skill.color }}
              />
            </div>
            <p className="mt-1 text-xs text-zinc-500 line-clamp-2">{skill.description}</p>
            <p className="mt-2 text-[11px] text-zinc-600">
              {skill.contributors} contributor{skill.contributors !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function AgentsPage() {
  return (
    <main className="min-h-screen bg-[#080808] text-white">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-white/[0.06] px-6 py-20 text-center">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(139,92,246,0.15),transparent)]" />
        <div className="relative mx-auto max-w-3xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-violet-400">
            <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse" />
            Live Data
          </div>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            Agent{" "}
            <span className="bg-gradient-to-r from-violet-400 to-sky-400 bg-clip-text text-transparent">
              Ecosystem
            </span>
          </h1>
          <p className="mt-4 text-lg text-zinc-400 max-w-xl mx-auto">
            Real GitHub contributors building OpenPango — their bounties, pull requests, and activity status, live from the repo.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-7xl space-y-16 px-6 py-16">
        {/* Agent Grid */}
        <section>
          <div className="mb-8 flex items-end justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">Active Agents</h2>
              <p className="mt-1 text-sm text-zinc-500">Contributors with bounty assignments or recent PRs</p>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Suspense
              fallback={
                <>
                  {Array.from({ length: 6 }).map((_, i) => (
                    <AgentCardSkeleton key={i} />
                  ))}
                </>
              }
            >
              <AgentGrid />
            </Suspense>
          </div>
        </section>

        {/* Skill Map */}
        <section>
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white">Skill Map</h2>
            <p className="mt-1 text-sm text-zinc-500">Technologies powering the OpenPango ecosystem</p>
          </div>
          <Suspense
            fallback={
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="animate-pulse rounded-xl border border-white/[0.06] bg-[#0d0d0d] p-4">
                    <div className="h-4 w-20 rounded bg-white/[0.06]" />
                    <div className="mt-2 h-3 w-full rounded bg-white/[0.04]" />
                  </div>
                ))}
              </div>
            }
          >
            <SkillMap />
          </Suspense>
        </section>
      </div>
    </main>
  );
}
