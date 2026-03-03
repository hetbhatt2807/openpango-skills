import { Octokit } from "@octokit/rest";
import { type BountyIssue, fetchBounties } from "./github";

const REPO_OWNER = "openpango";
const REPO_NAME = "openpango-skills";

function getOctokit() {
  const auth = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  return new Octokit(auth ? { auth } : {});
}

const cache = new Map<string, { data: unknown; expiry: number }>();
const CACHE_TTL = 5 * 60 * 1000;

function getCached<T>(key: string): T | null {
  const entry = cache.get(key);
  if (entry && Date.now() < entry.expiry) return entry.data as T;
  return null;
}
function setCache(key: string, data: unknown) {
  cache.set(key, { data, expiry: Date.now() + CACHE_TTL });
}

export type ActivityStatus = "ACTIVE" | "IDLE" | "NEW";

export interface ContributorPR {
  number: number;
  title: string;
  url: string;
  state: "open" | "merged" | "changes_requested" | "closed";
  createdAt: string;
}

export interface Contributor {
  login: string;
  avatarUrl: string;
  profileUrl: string;
  contributions: number;
  activityStatus: ActivityStatus;
  lastActiveAt: string | null;
  assignedBounties: BountyIssue[];
  completedBounties: BountyIssue[];
  recentPRs: ContributorPR[];
}

export interface SkillEntry {
  name: string;
  description: string;
  path: string;
}

/** Derive activity status from last active timestamp */
function deriveStatus(lastActiveAt: string | null): ActivityStatus {
  if (!lastActiveAt) return "NEW";
  const diffMs = Date.now() - new Date(lastActiveAt).getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  if (diffDays < 3) return "ACTIVE";
  if (diffDays < 14) return "IDLE";
  return "NEW";
}

/** Fetch all contributors with their bounty assignments and recent PRs */
export async function fetchContributors(): Promise<Contributor[]> {
  const cacheKey = "contributors_v2";
  const cached = getCached<Contributor[]>(cacheKey);
  if (cached) return cached;

  try {
    const octokit = getOctokit();

    // Fetch bounties, PRs, and contributors in parallel
    const [bounties, prsResponse, contributorsResponse] = await Promise.all([
      fetchBounties(),
      octokit.pulls.list({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        state: "all",
        per_page: 100,
        sort: "updated",
        direction: "desc",
      }),
      octokit.repos.listContributors({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        per_page: 50,
      }),
    ]);

    // Skip bots and the repo owner
    const humanContributors = contributorsResponse.data.filter(
      (c) =>
        c.login &&
        !c.login.includes("[bot]") &&
        c.login.toLowerCase() !== REPO_OWNER.toLowerCase()
    );

    // Group PRs by author login
    const prsByUser = new Map<string, ContributorPR[]>();
    for (const pr of prsResponse.data) {
      const login = pr.user?.login;
      if (!login) continue;
      if (!prsByUser.has(login)) prsByUser.set(login, []);

      let prState: ContributorPR["state"] = "open";
      if (pr.merged_at) prState = "merged";
      else if (pr.state === "closed") prState = "closed";
      else {
        // Check for changes_requested via review state (approximation)
        prState = "open";
      }

      prsByUser.get(login)!.push({
        number: pr.number,
        title: pr.title,
        url: pr.html_url,
        state: prState,
        createdAt: pr.created_at,
      });
    }

    // Group bounties by assignee
    const assignedByUser = new Map<string, BountyIssue[]>();
    const completedByUser = new Map<string, BountyIssue[]>();

    for (const bounty of bounties) {
      if (bounty.assignee) {
        if (bounty.status === "assigned") {
          if (!assignedByUser.has(bounty.assignee))
            assignedByUser.set(bounty.assignee, []);
          assignedByUser.get(bounty.assignee)!.push(bounty);
        } else if (bounty.status === "completed") {
          if (!completedByUser.has(bounty.assignee))
            completedByUser.set(bounty.assignee, []);
          completedByUser.get(bounty.assignee)!.push(bounty);
        }
      }
    }

    // Build contributor profiles
    const contributors: Contributor[] = humanContributors.map((c) => {
      const login = c.login!;
      const userPRs = (prsByUser.get(login) || []).slice(0, 5);
      const lastPR = userPRs[0];
      const lastActiveAt = lastPR?.createdAt || null;

      return {
        login,
        avatarUrl: c.avatar_url || `https://github.com/${login}.png`,
        profileUrl: `https://github.com/${login}`,
        contributions: c.contributions || 0,
        activityStatus: deriveStatus(lastActiveAt),
        lastActiveAt,
        assignedBounties: assignedByUser.get(login) || [],
        completedBounties: completedByUser.get(login) || [],
        recentPRs: userPRs,
      };
    });

    // Sort: ACTIVE first, then IDLE, then NEW; within each group by contributions
    const order: Record<ActivityStatus, number> = { ACTIVE: 0, IDLE: 1, NEW: 2 };
    contributors.sort(
      (a, b) =>
        order[a.activityStatus] - order[b.activityStatus] ||
        b.contributions - a.contributions
    );

    setCache(cacheKey, contributors);
    return contributors;
  } catch (err) {
    console.error("fetchContributors error:", err);
    return [];
  }
}

/** Fetch available skills from the repo tree (SKILL.md files) */
export async function fetchSkills(): Promise<SkillEntry[]> {
  const cacheKey = "skills_list";
  const cached = getCached<SkillEntry[]>(cacheKey);
  if (cached) return cached;

  try {
    const octokit = getOctokit();

    const { data: tree } = await octokit.git.getTree({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      tree_sha: "main",
      recursive: "1",
    });

    const skillFiles = tree.tree.filter(
      (f) => f.path?.endsWith("SKILL.md") && f.path.includes("skills/")
    );

    const skills: SkillEntry[] = skillFiles.map((f) => {
      const parts = f.path!.split("/");
      // e.g. skills/public/docx/SKILL.md -> "docx"
      const name = parts[parts.length - 2] || parts[parts.length - 1];
      return {
        name: name.charAt(0).toUpperCase() + name.slice(1),
        description: `Skill module for ${name} processing and generation`,
        path: f.path!,
      };
    });

    setCache(cacheKey, skills);
    return skills;
  } catch {
    // Return a reasonable fallback
    return [
      { name: "DOCX", description: "Word document generation and editing", path: "skills/public/docx/SKILL.md" },
      { name: "PDF", description: "PDF creation, parsing, and manipulation", path: "skills/public/pdf/SKILL.md" },
      { name: "PPTX", description: "Presentation deck generation", path: "skills/public/pptx/SKILL.md" },
      { name: "XLSX", description: "Spreadsheet processing and creation", path: "skills/public/xlsx/SKILL.md" },
    ];
  }
}
