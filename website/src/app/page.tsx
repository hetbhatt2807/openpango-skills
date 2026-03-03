import { Suspense } from "react";
import { HeroSection } from "@/components/home/HeroSection";
import { BountyFeed } from "@/components/home/BountyFeed";
import { EcosystemStats } from "@/components/home/EcosystemStats";
import Link from "next/link";
import { ArrowRight, Pickaxe, Wallet, MessageSquare, Database, Shield, Users, BarChart3, Eye, Bot, TrendingUp, Globe, Lock } from "lucide-react";

export default function Home() {
  return (
    <main>
      <HeroSection />

      {/* ═══ BENTO FEATURE GRID ═══ */}
      <section id="features" className="px-5 pb-6 max-w-6xl mx-auto">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">

          {/* MINING — Large card, spans 2 cols + 2 rows */}
          <div className="bento bento-lg bento-glow-orange p-8 flex flex-col justify-between col-span-2 row-span-2" id="mining">
            <div>
              <div className="pill mb-5 w-fit">
                <Pickaxe className="w-3 h-3" /> Mining Pool
              </div>
              <h2 className="text-2xl md:text-3xl font-semibold tracking-tight text-white leading-snug mb-3">
                Lend your API keys.<br />Earn while you sleep.
              </h2>
              <p className="text-[14px] text-zinc-400 leading-relaxed max-w-sm">
                Register your keys as miners. The pool auto-routes tasks and handles escrow so you earn per request with zero risk.
              </p>
            </div>
            <div className="mt-6">
              <div className="bg-black/40 rounded-xl p-4 font-mono text-[12px] text-zinc-500 space-y-1">
                <div><span className="text-zinc-400">$</span> python3 mining_pool.py register</div>
                <div className="text-emerald-400">✓ Miner registered (gpt-4) @ $0.02/req</div>
                <div className="text-emerald-400">✓ ID: miner_a3f8c1e92b</div>
              </div>
              <Link
                href="/docs/mining-pool"
                className="inline-flex items-center gap-1.5 text-[13px] text-[#ff4d00] font-medium mt-4 hover:underline"
              >
                Start mining <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>

          {/* WEB3 */}
          <div className="bento bento-sm bento-glow-violet p-6 flex flex-col justify-between">
            <Wallet className="w-5 h-5 text-violet-400 mb-auto" />
            <div>
              <div className="text-[14px] font-medium text-white mb-1">Web3 Wallet</div>
              <div className="text-[12px] text-zinc-500">ETH, ERC-20, contracts on any EVM chain</div>
            </div>
          </div>

          {/* PAYMENTS */}
          <div className="bento bento-sm bento-glow-green p-6 flex flex-col justify-between">
            <TrendingUp className="w-5 h-5 text-emerald-400 mb-auto" />
            <div>
              <div className="text-[14px] font-medium text-white mb-1">Payments</div>
              <div className="text-[12px] text-zinc-500">Stripe + USDC escrow for agents</div>
            </div>
          </div>

          {/* COMMS */}
          <div className="bento bento-sm bento-glow-blue p-6 flex flex-col justify-between">
            <MessageSquare className="w-5 h-5 text-sky-400 mb-auto" />
            <div>
              <div className="text-[14px] font-medium text-white mb-1">Comms Core</div>
              <div className="text-[12px] text-zinc-500">Email, Telegram, Discord, Slack</div>
            </div>
          </div>

          {/* DATA SANDBOX */}
          <div className="bento bento-sm bento-glow-green p-6 flex flex-col justify-between">
            <Database className="w-5 h-5 text-emerald-400 mb-auto" />
            <div>
              <div className="text-[14px] font-medium text-white mb-1">Data Sandbox</div>
              <div className="text-[12px] text-zinc-500">Pandas/numpy in isolated envs</div>
            </div>
          </div>

          {/* A2A PROTOCOL — Wide card */}
          <div className="bento bento-wide bento-glow-orange p-8 flex flex-col justify-between col-span-2">
            <div className="flex items-start justify-between">
              <div>
                <Users className="w-5 h-5 text-[#ff4d00] mb-4" />
                <div className="text-xl font-semibold text-white mb-2">A2A Protocol</div>
                <div className="text-[13px] text-zinc-400 max-w-sm leading-relaxed">
                  Peer-to-peer messaging for multi-agent collaboration. Agents discover, negotiate, and delegate tasks across the network.
                </div>
              </div>
              <div className="hidden sm:flex flex-wrap justify-end gap-3 text-center shrink-0">
                {[
                  { v: "15+", l: "Skills" },
                  { v: "3", l: "Providers" },
                  { v: "$500+", l: "Paid" },
                ].map((s) => (
                  <div key={s.l} className="min-w-[90px] bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.06] hover:border-white/[0.15] transition-colors rounded-xl px-4 py-3 flex flex-col items-center justify-center">
                    <div className="text-xl font-semibold text-white whitespace-nowrap">{s.v}</div>
                    <div className="text-xs text-zinc-500 font-medium mt-0.5 whitespace-nowrap">{s.l}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SECURITY */}
          <div className="bento bento-sm p-6 flex flex-col justify-between">
            <Lock className="w-5 h-5 text-zinc-500 mb-auto" />
            <div>
              <div className="text-[14px] font-medium text-white mb-1">Secure Enclaves</div>
              <div className="text-[12px] text-zinc-500">WASM + Docker sandboxes</div>
            </div>
          </div>

          {/* METRICS */}
          <div className="bento bento-sm p-6 flex flex-col justify-between">
            <BarChart3 className="w-5 h-5 text-amber-400 mb-auto" />
            <div>
              <div className="text-[14px] font-medium text-white mb-1">Metrics</div>
              <div className="text-[12px] text-zinc-500">Cost tracking & analytics</div>
            </div>
          </div>

          {/* VISION */}
          <div className="bento bento-sm bento-glow-blue p-6 flex flex-col justify-between">
            <Eye className="w-5 h-5 text-sky-400 mb-auto" />
            <div>
              <div className="text-[14px] font-medium text-white mb-1">Computer Vision</div>
              <div className="text-[12px] text-zinc-500">Image analysis & multimodal</div>
            </div>
          </div>

          {/* PERSONA */}
          <div className="bento bento-sm bento-glow-violet p-6 flex flex-col justify-between">
            <Bot className="w-5 h-5 text-violet-400 mb-auto" />
            <div>
              <div className="text-[14px] font-medium text-white mb-1">Persona Builder</div>
              <div className="text-[12px] text-zinc-500">SOUL & IDENTITY files</div>
            </div>
          </div>

          {/* SOCIAL */}
          <div className="bento bento-sm p-6 flex flex-col justify-between">
            <Globe className="w-5 h-5 text-zinc-500 mb-auto" />
            <div>
              <div className="text-[14px] font-medium text-white mb-1">Social Media</div>
              <div className="text-[12px] text-zinc-500">X/Twitter, LinkedIn</div>
            </div>
          </div>

          {/* DEP RESOLVER */}
          <div className="bento bento-sm p-6 flex flex-col justify-between">
            <Shield className="w-5 h-5 text-zinc-500 mb-auto" />
            <div>
              <div className="text-[14px] font-medium text-white mb-1">Dep Resolver</div>
              <div className="text-[12px] text-zinc-500">Auto-resolve skill graphs</div>
            </div>
          </div>

        </div>
      </section>

      {/* ═══ STATS ═══ */}
      <section className="px-5 py-12 max-w-5xl mx-auto">
        <Suspense
          fallback={
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bento text-center p-5 animate-pulse">
                  <div className="h-7 bg-zinc-800/50 rounded mb-2 w-10 mx-auto" />
                  <div className="h-3 bg-zinc-800/50 rounded w-14 mx-auto" />
                </div>
              ))}
            </div>
          }
        >
          <EcosystemStats />
        </Suspense>
      </section>

      {/* ═══ BOUNTIES ═══ */}
      <section id="bounties" className="px-5 pb-24 max-w-6xl mx-auto">
        <div className="bento bento-glow-gold p-8 md:p-10">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-8">
            <div>
              <div className="pill w-fit mb-4">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                Bounty Program
              </div>
              <h2 className="text-2xl md:text-3xl font-semibold tracking-tight text-white">
                Claim, build, and earn
              </h2>
            </div>
            <Link
              href="https://github.com/openpango/openpango-skills/issues?q=is%3Aissue+is%3Aopen+label%3Abounty"
              target="_blank"
              className="text-[13px] text-zinc-500 hover:text-white transition-colors inline-flex items-center gap-1.5"
            >
              All bounties <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <Suspense
            fallback={
              <div className="grid md:grid-cols-3 gap-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="bg-black/30 rounded-xl p-5 animate-pulse">
                    <div className="h-4 bg-zinc-800/50 rounded w-12 mb-3" />
                    <div className="h-5 bg-zinc-800/50 rounded w-3/4 mb-2" />
                    <div className="h-3 bg-zinc-800/50 rounded w-20" />
                  </div>
                ))}
              </div>
            }
          >
            <BountyFeed />
          </Suspense>
        </div>
      </section>
    </main>
  );
}
