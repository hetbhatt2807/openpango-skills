import { fetchEcosystemStats } from "@/lib/agents-github";

export async function EcosystemBar() {
  const stats = await fetchEcosystemStats();
  const items = [
    { label: "Contributors", value: stats.totalContributors },
    { label: "Total Bounties", value: stats.totalBounties },
    { label: "Open Bounties", value: stats.openBounties },
    { label: "Total Paid Out", value: stats.totalPayout },
  ];
  return (
    <div className="eco-bar">
      {items.map((item) => (
        <div key={item.label} className="eco-bar-item">
          <span className="eco-value">{item.value}</span>
          <span className="eco-label">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
