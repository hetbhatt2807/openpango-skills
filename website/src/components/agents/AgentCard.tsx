import type { Contributor } from "@/lib/agents-github";

const STATUS_META = {
  ACTIVE: { color: "#00ff87", label: "ACTIVE", dot: "●" },
  IDLE:   { color: "#fbbf24", label: "IDLE",   dot: "◑" },
  NEW:    { color: "#94a3b8", label: "NEW",    dot: "○" },
} as const;

const PR_STATE_META = {
  open:   { color: "#3fb950", label: "OPEN"   },
  merged: { color: "#a371f7", label: "MERGED" },
  closed: { color: "#f85149", label: "CLOSED" },
} as const;

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 60) return `${min}m ago`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function truncate(str: string, max: number) {
  return str.length <= max ? str : str.slice(0, max - 1) + "…";
}

export function AgentCard({ contributor: c }: { contributor: Contributor }) {
  const status = STATUS_META[c.activityStatus];

  return (
    <article className="agent-card">
      <div className="card-ribbon" style={{ "--ribbon-color": status.color } as React.CSSProperties} />

      <div className="card-header">
        <a href={c.profileUrl} target="_blank" rel="noopener noreferrer">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={c.avatarUrl} alt={`${c.login} avatar`} width={52} height={52} className="avatar" />
        </a>
        <div className="card-identity">
          <a href={c.profileUrl} target="_blank" rel="noopener noreferrer" className="username">
            {c.name ?? c.login}
          </a>
          {c.name && <span className="login-handle">@{c.login}</span>}
          {c.bio && <p className="bio">{truncate(c.bio, 72)}</p>}
        </div>
        <div className="status-badge" style={{ color: status.color } as React.CSSProperties}>
          <span>{status.dot}</span>
          <span>{status.label}</span>
        </div>
      </div>

      {c.assignedBounties.length > 0 && (
        <div className="card-section">
          <h3 className="section-title">Bounties</h3>
          <ul className="bounty-list">
            {c.assignedBounties.slice(0, 3).map((b) => (
              <li key={b.number} className="bounty-item">
                <a href={b.url} target="_blank" rel="noopener noreferrer" className="bounty-title">
                  #{b.number} {truncate(b.title, 50)}
                </a>
                <div className="bounty-meta">
                  <span className={`bounty-status ${b.status}`}>
                    {b.status === "completed" ? "Done" : "In Progress"}
                  </span>
                  {b.reward && <span className="bounty-reward">{b.reward}</span>}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {c.recentPRs.length > 0 && (
        <div className="card-section">
          <h3 className="section-title">Recent PRs</h3>
          <ul className="pr-list">
            {c.recentPRs.map((pr) => {
              const meta = PR_STATE_META[pr.state];
              return (
                <li key={pr.number} className="pr-item">
                  <a href={pr.url} target="_blank" rel="noopener noreferrer" className="pr-title">
                    {truncate(pr.title, 52)}
                  </a>
                  <div className="pr-meta">
                    <span className="pr-state" style={{ color: meta.color } as React.CSSProperties}>
                      {meta.label}
                    </span>
                    <span className="pr-time">{timeAgo(pr.mergedAt ?? pr.createdAt)}</span>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <div className="card-footer">
        <div className="stat"><span className="stat-value">{c.totalMerged}</span><span className="stat-label">Merged</span></div>
        <div className="stat"><span className="stat-value">{c.assignedBounties.length}</span><span className="stat-label">Bounties</span></div>
        <div className="stat">
          <span className="stat-value">{c.assignedBounties.filter((b) => b.status === "completed").length}</span>
          <span className="stat-label">Done</span>
        </div>
        {c.lastActivityAt && (
          <div className="stat">
            <span className="stat-value">{timeAgo(c.lastActivityAt)}</span>
            <span className="stat-label">Last Active</span>
          </div>
        )}
      </div>
    </article>
  );
}
