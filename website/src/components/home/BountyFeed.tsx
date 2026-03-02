import { fetchBounties, type BountyIssue } from "@/lib/github";

const status: Record<string, { label: string; color: string; dot: string }> = {
    open: { label: "Claimable", color: "text-emerald-400", dot: "bg-emerald-400" },
    assigned: { label: "In Progress", color: "text-amber-400", dot: "bg-amber-400" },
    completed: { label: "Done", color: "text-zinc-600", dot: "bg-zinc-600" },
};

function Card({ bounty }: { bounty: BountyIssue }) {
    const s = status[bounty.status];
    return (
        <a href={bounty.url} target="_blank" rel="noopener noreferrer"
            className="block bg-black/30 rounded-xl p-5 hover:bg-black/50 transition-colors group">
            <div className="flex items-center justify-between mb-2.5">
                <span className={`text-[11px] font-medium ${s.color}`}>#{bounty.number}</span>
                {bounty.reward && (
                    <span className="text-[12px] font-semibold text-[#ff4d00]">{bounty.reward}</span>
                )}
            </div>
            <h3 className="text-[13px] font-medium text-zinc-200 group-hover:text-white transition-colors leading-snug line-clamp-2 mb-3">
                {bounty.title}
            </h3>
            <div className="flex items-center gap-1.5">
                {bounty.status !== "completed" && (
                    <span className={`w-1.5 h-1.5 rounded-full ${s.dot} ${bounty.status === "open" ? "animate-pulse" : ""}`} />
                )}
                <span className={`text-[11px] ${s.color}`}>{s.label}</span>
            </div>
        </a>
    );
}

export async function BountyFeed() {
    const bounties = await fetchBounties();
    const displayed = [
        ...bounties.filter((b) => b.status === "open").slice(0, 6),
        ...bounties.filter((b) => b.status === "assigned").slice(0, 3),
    ].slice(0, 6);

    if (!displayed.length) return <div className="text-zinc-600 text-[13px] py-8">Loading bounties…</div>;

    return (
        <div className="grid md:grid-cols-3 gap-3">
            {displayed.map((b) => <Card key={b.number} bounty={b} />)}
        </div>
    );
}
