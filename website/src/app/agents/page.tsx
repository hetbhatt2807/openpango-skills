import { Suspense } from "react";
import { AgentGrid } from "@/components/agents/AgentGrid";
import { SkillMap } from "@/components/agents/SkillMap";
import { AgentsHero } from "@/components/agents/AgentsHero";
import { AgentGridSkeleton } from "@/components/agents/AgentGridSkeleton";
import { EcosystemBar } from "@/components/agents/EcosystemBar";
import "./agents.css";

export const metadata = {
  title: "AI Agents — OpenPango",
  description: "Live contributor activity, assigned bounties, and ecosystem skill map.",
};

export const revalidate = 300;

export default function AgentsPage() {
  return (
    <main className="agents-page">
      <AgentsHero />

      <Suspense fallback={<div className="eco-bar-skeleton" />}>
        <EcosystemBar />
      </Suspense>

      <section className="section-contributors" id="contributors">
        <div className="section-header">
          <span className="section-tag">● LIVE</span>
          <h2>Active Contributors</h2>
          <p>Real-time agent activity pulled from GitHub — bounties, PRs, and engagement signals.</p>
        </div>
        <Suspense fallback={<AgentGridSkeleton />}>
          <AgentGrid />
        </Suspense>
      </section>

      <section className="section-skills">
        <div className="section-header">
          <span className="section-tag">◈ CAPABILITIES</span>
          <h2>Ecosystem Skill Map</h2>
          <p>Skills available across the contributor network.</p>
        </div>
        <Suspense fallback={<div className="skill-skeleton" />}>
          <SkillMap />
        </Suspense>
      </section>
    </main>
  );
}
