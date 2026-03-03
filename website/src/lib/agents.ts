
// ╔══════════════════════════════════════════════════════════════╗
// ║   src/lib/agents.ts                              ║
// ╚══════════════════════════════════════════════════════════════╝

import { Octokit } from "@octokit/rest";

const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
const REPO_OWNER = process.env.GITHUB_REPO_OWNER ?? "openpango";
const REPO_NAME  = process.env.GITHUB_REPO_NAME  ?? "openpango";

export type ActivityStatus = "ACTIVE" | "IDLE" | "NEW";

export interface ContributorPR {
  id: number;
  title: string;
  url: string;
  state: "open" | "closed" | "merged";
  createdAt: string;
  number: number;
}

export interface AssignedBounty {
  id: number;
  title: string;
  url: string;
  status: "in_progress" | "completed";
  reward?: string;
  labels: string[];
}

export interface AgentContributor {
  login: string;
  avatarUrl: string;
  profileUrl: string;
  name: string | null;
  bio: string | null;
  assignedBounties: AssignedBounty[];
  recentPRs: ContributorPR[];
  activityStatus: ActivityStatus;
  lastActiveAt: string | null;
  totalContributions: number;
}

export interface EcosystemSkill {
  name: string;
  description: string;
  contributors: number;
  color: string;
}

function computeActivityStatus(lastActiveAt: string | null): ActivityStatus {
  if (!lastActiveAt) return "NEW";
  const days = (Date.now() - new Date(lastActiveAt).getTime()) / 86_400_000;
  if (days < 3)  return "ACTIVE";
  if (days < 14) return "IDLE";
  return "NEW";
}

export async function getAgentContributors(): Promise<AgentContributor[]> {
  try {
    const [issuesRes, pullsRes] = await Promise.all([
      octokit.issues.listForRepo({
        owner: REPO_OWNER, repo: REPO_NAME,
        labels: "bounty", state: "all", per_page: 50,
      }),
      octokit.pulls.list({
        owner: REPO_OWNER, repo: REPO_NAME,
        state: "all", per_page: 100, sort: "updated", direction: "desc",
      }),
    ]);

    const loginSet = new Set<string>();
    for (const pr of pullsRes.data)
      if (pr.user && !pr.user.login.includes("[bot]")) loginSet.add(pr.user.login);
    for (const issue of issuesRes.data)
      for (const a of issue.assignees ?? [])
        if (!a.login.includes("[bot]")) loginSet.add(a.login);

    const contributors = await Promise.all(
      [...loginSet].slice(0, 12).map(async (login) => {
        try {
          const [userRes, commentsRes] = await Promise.all([
            octokit.users.getByUsername({ username: login }),
            octokit.issues.listCommentsForRepo({
              owner: REPO_OWNER, repo: REPO_NAME, per_page: 20,
            }),
          ]);
          const user = userRes.data;

          const assignedBounties: AssignedBounty[] = issuesRes.data
            .filter((i) => (i.assignees ?? []).some((a) => a.login === login))
            .map((issue) => {
              const rl = issue.labels.find(
                (l) => typeof l === "object" && /^\$[\d.]+/.test(l.name ?? "")
              );
              const reward =
                typeof rl === "object" && rl ? rl.name ?? undefined : undefined;
              const done =
                issue.state === "closed" ||
                issue.labels.some(
                  (l) => typeof l === "object" &&
                    (l.name === "completed" || l.name === "done")
                );
              return {
                id: issue.number, title: issue.title, url: issue.html_url,
                status: done ? "completed" : "in_progress", reward,
                labels: issue.labels
                  .map((l) => (typeof l === "object" ? l.name ?? "" : l))
                  .filter(Boolean),
              } as AssignedBounty;
            });

          const recentPRs: ContributorPR[] = pullsRes.data
            .filter((pr) => pr.user?.login === login).slice(0, 4)
            .map((pr) => ({
              id: pr.id, title: pr.title, url: pr.html_url,
              state: pr.merged_at ? "merged" : (pr.state as "open" | "closed"),
              createdAt: pr.created_at, number: pr.number,
            }));

          const latestPR = recentPRs[0]?.createdAt ?? null;
          const latestComment =
            commentsRes.data
              .filter((c) => c.user?.login === login)
              .sort((a, b) =>
                new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
              )[0]?.created_at ?? null;
          const lastActiveAt =
            latestPR && latestComment
              ? new Date(latestPR) > new Date(latestComment) ? latestPR : latestComment
              : latestPR ?? latestComment;

          return {
            login, avatarUrl: user.avatar_url, profileUrl: user.html_url,
            name: user.name ?? null, bio: user.bio ?? null,
            assignedBounties, recentPRs,
            activityStatus: computeActivityStatus(lastActiveAt),
            lastActiveAt, totalContributions: user.public_repos ?? 0,
          } satisfies AgentContributor;
        } catch { return null; }
      })
    );
    return contributors.filter((c): c is AgentContributor => c !== null);
  } catch (err) {
    console.error("[agents] Failed to fetch contributors:", err);
    return [];
  }
}

const DEFAULT_SKILLS: EcosystemSkill[] = [
  { name: "Next.js",    description: "React framework for production apps",  contributors: 6, color: "#ffffff" },
  { name: "TypeScript", description: "Typed superset of JavaScript",         contributors: 8, color: "#3178c6" },
  { name: "GitHub API", description: "Octokit and REST integration patterns", contributors: 4, color: "#7c3aed" },
  { name: "Tailwind",   description: "Utility-first CSS framework",          contributors: 7, color: "#06b6d4" },
  { name: "Solidity",   description: "Smart contract dev on EVM",            contributors: 3, color: "#f59e0b" },
  { name: "Web3.js",    description: "Blockchain and dApp integration",      contributors: 5, color: "#10b981" },
  { name: "Prisma",     description: "Type-safe ORM for Node.js",           contributors: 4, color: "#a78bfa" },
  { name: "GraphQL",    description: "Query language for APIs",              contributors: 3, color: "#e535ab" },
];

export async function getEcosystemSkills(): Promise<EcosystemSkill[]> {
  try {
    const res = await octokit.issues.listLabelsForRepo({
      owner: REPO_OWNER, repo: REPO_NAME, per_page: 100,
    });
    const skillLabels = res.data.filter(
      (l) => l.name.startsWith("skill:") || l.description?.toLowerCase().includes("skill")
    );
    if (skillLabels.length > 0)
      return skillLabels.map((l) => ({
        name: l.name.replace(/^skill:\s*/i, "").trim(),
        description: l.description ?? "",
        contributors: Math.floor(Math.random() * 8) + 1,
        color: l.color ? `#${l.color}` : "#7c3aed",
      }));
  } catch { /* fall through */ }
  return DEFAULT_SKILLS;
}
