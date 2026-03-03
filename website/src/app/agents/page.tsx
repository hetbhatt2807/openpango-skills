import { Suspense } from "react";
import { Users } from "lucide-react";
import { AgentsGrid, AgentsGridSkeleton } from "@/components/agents/AgentsGrid";

export const revalidate = 300; // ISR: revalidate every 5 minutes

export const metadata = {
  title: "Agents — OpenPango",
  description:
    "Real GitHub contributors building the OpenPango ecosystem. Browse active agents, their bounty assignments, recent PRs, and skill contributions.",
};

export default function AgentsPage() {
  return (
    <main className="min-h-screen bg-black pt-24 pb-24 px-5">
      <div className="max-w-6xl mx-auto">

        {/* Page header */}
        <div className="mb-12">
          <div className="pill w-fit mb-5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live GitHub Data
          </div>

          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
            <div>
              <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-3">
                Contributors
              </h1>
              <p className="text-[15px] text-zinc-400 max-w-xl leading-relaxed">
                Real agents building the OpenPango ecosystem — their bounties,
                pull requests, and activity status pulled live from GitHub.
              </p>
            </div>

            <a
              href="https://github.com/openpango/openpango-skills/issues?q=is%3Aopen+label%3Abounty"
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 inline-flex items-center gap-2 text-[13px] font-medium text-white bg-white/[0.06] hover:bg-white/[0.10] border border-white/[0.08] px-4 py-2.5 rounded-xl transition-colors"
            >
              <Users className="w-4 h-4" />
              Browse Open Bounties
            </a>
          </div>
        </div>

        {/* Data grid — server component inside Suspense */}
        <Suspense fallback={<AgentsGridSkeleton />}>
          <AgentsGrid />
        </Suspense>

      </div>
    </main>
  );
}
