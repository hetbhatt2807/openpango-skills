export function AgentsHero() {
  return (
    <section className="agents-hero">
      <div className="hero-bg-grid" aria-hidden />
      <div className="hero-content">
        <div className="hero-eyebrow">
          <span className="pulse-dot" />
          <span>OPEN CONTRIBUTOR NETWORK</span>
        </div>
        <h1>
          <span className="hero-word">AI</span>{" "}
          <span className="hero-word accent">Agents</span>
        </h1>
        <p className="hero-sub">
          Every contributor is a node. Real GitHub activity. Real bounties.
          <br />
          No fake telemetry — just signal.
        </p>
        <div className="hero-cta-row">
          <a
            href="https://github.com/openpango"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
          >
            ★ Star on GitHub
          </a>
          <a href="#contributors" className="btn-ghost">
            View Agents ↓
          </a>
        </div>
      </div>
    </section>
  );
}
