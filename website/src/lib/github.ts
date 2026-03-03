import { octokit, REPO_OWNER, REPO_NAME } from "@/lib/github";

export type ActivityStatus = "ACTIVE" | "IDLE" | "NEW";

export interface ContributorPR {
  number: number;
  title: string;
  url: string;
  state: "open" | "closed" | "merged";
  createdAt: string;
  mergedAt: string | null;
  reviewDecision: string | null;
}

export interface AssignedBounty {
  number: number;
  title: string;
  url: string;
  status: "in_progress" | "completed";
  reward: string | null;
}

export interface Contributor {
  login: string;
  avatarUrl: string;
  profileUrl: string;
  name: string | null;
  bio: string | null;
  activityStatus: ActivityStatus;
  lastActivityAt: string | null;
  assignedBounties: AssignedBounty[];
  recentPRs: ContributorPR[];
  totalMerged: number;
}

export interface EcosystemStats {
  totalContributors: number;
  totalBounties: number;
  openBounties: number;
  totalPayout: string;
}

export interface Skill {
  name: string;
  description: string;
  triggerKeywords: string[];
}

function deriveStatus(lastActivityAt: string | null): ActivityStatus {
  if (!lastActivityAt) return "NEW";
  const days = (Date.now() - new Date(lastActivityAt).getTime()) / 86400000;
  if (days <= 3) return "ACTIVE";
  if (days <= 14) return "IDLE";
  return "NEW";
}

function extractReward(labels: Array<{ name: string }>, body: string | null): string | null {
  for (const label of labels) {
    const m = label.name.match(/\$?(\d+(?:\.\d+)?)/);
    if (m) return `$${m[1]}`;
  }
  if (body) {
    const m = body.match(/\u{1F4B0}\s*\$?([\d.]+)/u);
    if (m) return `$${m[1]}`;
  }
  return null;
}

export async function fetchAgentContributors(): Promise<Contributor[]> {
  const { data: issues } = await octokit.issues.listForRepo({
    owner: REPO_OWNER, repo: REPO_NAME, labels: "bounty", state: "all", per_page: 100,
  });

  const bountyMap = new Map<string, AssignedBounty[]>();

  for (const issue of issues) {
    const labels = (issue.labels as Array<{ name: string }>).filter((l) => typeof l !== "string");
    const reward = extractReward(labels, issue.body ?? null);
    const entry: AssignedBounty = {
      number: issue.number, title: issue.title, url: issue.html_url,
      status: issue.state === "closed" ? "completed" : "in_progress", reward,
    };

    for (const assignee of issue.assignees ?? []) {
      if (!assignee) continue;
      const list = bountyMap.get(assignee.login) ?? [];
      list.push(entry);
      bountyMap.set(assignee.login, list);
    }

    try {
      const { data: comments } = await octokit.issues.listComments({
        owner: REPO_OWNER, repo: REPO_NAME, issue_number: issue.number, per_page: 100,
      });
      for (const comment of comments) {
        if (!comment.user || bountyMap.has(comment.user.login)) continue;
        if (!/\/apply/i.test(comment.body ?? "")) continue;
        const list = bountyMap.get(comment.user.login) ?? [];
        list.push({ ...entry, status: "in_progress" });
        bountyMap.set(comment.user.login, list);
      }
    } catch {}
  }

  if (bountyMap.size === 0) return [];

  const contributors = await Promise.all(
    Array.from(bountyMap.entries()).map(async ([login, bounties]) => {
      let name: string | null = null, bio: string | null = null;
      let avatarUrl = `https://github.com/${login}.png`;
      try {
        const { data: user } = await octokit.users.getByUsername({ username: login });
        name = user.name ?? null; bio = user.bio ?? null; avatarUrl = user.avatar_url;
      } catch {}

      const recentPRs: ContributorPR[] = [];
      let lastActivityAt: string | null = null, totalMerged = 0;
      try {
        const { data: result } = await octokit.search.issuesAndPullRequests({
          q: `repo:${REPO_OWNER}/${REPO_NAME} is:pr author:${login}`,
          sort: "updated", order: "desc", per_page: 5,
        });
        for (const pr of result.items) {
          const isMerged = pr.pull_request?.merged_at != null;
          const state = isMerged ? "merged" : pr.state === "closed" ? "closed" : "open";
          if (isMerged) totalMerged++;
          recentPRs.push({
            number: pr.number, title: pr.title, url: pr.html_url,
            state: state as ContributorPR["state"], createdAt: pr.created_at,
            mergedAt: pr.pull_request?.merged_at ?? null, reviewDecision: null,
          });
          if (!lastActivityAt || pr.updated_at > lastActivityAt) lastActivityAt = pr.updated_at;
        }
      } catch {}

      return {
        login, avatarUrl, profileUrl: `https://github.com/${login}`,
        name, bio, activityStatus: deriveStatus(lastActivityAt),
        lastActivityAt, assignedBounties: bounties, recentPRs, totalMerged,
      };
    })
  );

  return contributors.sort((a, b) => {
    const order = { ACTIVE: 0, IDLE: 1, NEW: 2 };
    const d = order[a.activityStatus] - order[b.activityStatus];
    return d !== 0 ? d : b.totalMerged - a.totalMerged;
  });
}

export async function fetchEcosystemStats(): Promise<EcosystemStats> {
  const [{ data: open }, { data: closed }] = await Promise.all([
    octokit.issues.listForRepo({ owner: REPO_OWNER, repo: REPO_NAME, labels: "bounty", state: "open", per_page: 100 }),
    octokit.issues.listForRepo({ owner: REPO_OWNER, repo: REPO_NAME, labels: "bounty", state: "closed", per_page: 100 }),
  ]);
  const assignees = new Set<string>();
  let totalCents = 0;
  for (const issue of [...open, ...closed]) {
    (issue.assignees ?? []).forEach((a) => a && assignees.add(a.login));
    const labels = (issue.labels as Array<{ name: string }>).filter((l) => typeof l !== "string");
    const reward = extractReward(labels, issue.body ?? null);
    if (reward) { const n = parseFloat(reward.replace("$", "")); if (!isNaN(n)) totalCents += n * 100; }
  }
  return {
    totalContributors: assignees.size,
    totalBounties: open.length + closed.length,
    openBounties: open.length,
    totalPayout: `$${(totalCents / 100).toFixed(2)}`,
  };
}

export async function fetchSkillMap(): Promise<Skill[]> {
  try {
    const { data: tree } = await octokit.git.getTree({
      owner: REPO_OWNER, repo: REPO_NAME, tree_sha: "HEAD", recursive: "true",
    });
    const skillFiles = tree.tree.filter(
      (item) => item.type === "blob" && item.path?.endsWith("SKILL.md") && item.sha
    );
    const skills: Skill[] = [];
    for (const file of skillFiles.slice(0, 20)) {
      try {
        const { data: blob } = await octokit.git.getBlob({
          owner: REPO_OWNER, repo: REPO_NAME, file_sha: file.sha!,
        });
        const content = Buffer.from(blob.content, "base64").toString("utf-8");
        const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
        if (!fmMatch) continue;
        const fm = fmMatch[1];
        const nameMatch = fm.match(/^name:\s*(.+)$/m);
        const descMatch = fm.match(/^description:\s*([\s\S]*?)(?=\n\w|$)/m);
        if (!nameMatch) continue;
        skills.push({
          name: nameMatch[1].trim(),
          description: descMatch ? descMatch[1].replace(/\n\s+/g, " ").trim() : "",
          triggerKeywords: nameMatch[1].trim().toLowerCase().split(/[-_\s]+/),
        });
      } catch {}
    }
    if (skills.length > 0) return skills;
  } catch {}

  return [
    { name: "docx", description: "Create, read, edit Word documents with tables, headings, page numbers, and professional formatting.", triggerKeywords: ["word", "docx", "document", "report"] },
    { name: "pdf", description: "Read/extract PDFs, merge, split, watermark, fill forms, OCR scanned pages.", triggerKeywords: ["pdf", "extract", "merge", "ocr"] },
    { name: "pptx", description: "Create and edit slide decks, pitch decks, and presentations from scratch or existing files.", triggerKeywords: ["powerpoint", "pptx", "slides", "deck"] },
    { name: "xlsx", description: "Open, read, edit spreadsheets. Formulas, charts, tabular data cleaning.", triggerKeywords: ["excel", "xlsx", "spreadsheet", "csv"] },
    { name: "frontend-design", description: "Build production-grade web UIs — React, HTML/CSS, landing pages, dashboards.", triggerKeywords: ["react", "html", "css", "ui", "component"] },
    { name: "github-automation", description: "Automate GitHub workflows — issue triage, PR reviews, bounty tracking.", triggerKeywords: ["github", "pr", "issue", "automation"] },
  ];
}
