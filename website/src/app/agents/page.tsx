"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Cpu, X } from "lucide-react";

interface Agent {
  id: string;
  role: string;
  status: "IDLE" | "RUNNING" | "WAITING";
  memory: string;
  compute: "Standard" | "High";
  load: number;
}

const INITIAL_AGENTS: Agent[] = [
  { id: "planner-01", role: "Planner", status: "IDLE", memory: "1.2GB", compute: "Standard", load: 0 },
  { id: "researcher-02", role: "Researcher", status: "RUNNING", memory: "4.8GB", compute: "High", load: 45 },
  { id: "coder-03", role: "Coder", status: "WAITING", memory: "2.1GB", compute: "Standard", load: 12 },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>(INITIAL_AGENTS);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setAgents((prev) =>
        prev.map((agent) => ({
          ...agent,
          load: agent.status === "RUNNING"
            ? Math.floor(Math.random() * 40) + 40
            : agent.status === "WAITING"
              ? Math.floor(Math.random() * 10) + 5
              : 0
        }))
      );
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="min-h-screen bg-black pt-24 pb-24 px-5">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-10">
          <div>
            <div className="pill w-fit mb-5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Live Network
            </div>
            <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-3">
              Active Souls
            </h1>
            <p className="text-[15px] text-zinc-400">Real-time agent telemetry</p>
          </div>
        </div>

        <div className="grid gap-3">
          <AnimatePresence mode="popLayout">
            {agents.map((agent) => (
              <motion.div
                key={agent.id}
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.4 }}
                className="bento p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-5 cursor-pointer"
                onClick={() => setSelectedAgent(agent)}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-white/[0.04] flex items-center justify-center text-zinc-400">
                    <Activity className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-[14px] font-medium text-white">{agent.role}</div>
                    <div className="text-[11px] text-zinc-600 font-mono">{agent.id}</div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-6 md:gap-8">
                  <div className="w-24">
                    <div className="text-[11px] text-zinc-600 mb-1">Load</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-grow bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${agent.load}%` }}
                          className={`h-full rounded-full ${agent.load > 70 ? 'bg-red-500' : 'bg-[#ff4d00]'}`}
                        />
                      </div>
                      <span className="text-[11px] text-zinc-500 w-7">{agent.load}%</span>
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-zinc-600 mb-1">Compute</div>
                    <div className="text-[13px] text-zinc-300 flex items-center gap-1.5">
                      <Cpu className="w-3 h-3 text-zinc-600" /> {agent.compute}
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-zinc-600 mb-1">Memory</div>
                    <div className="text-[13px] text-zinc-300">{agent.memory}</div>
                  </div>
                  <div>
                    <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full ${agent.status === "RUNNING" ? "bg-emerald-500/10 text-emerald-400" :
                        agent.status === "IDLE" ? "bg-zinc-500/10 text-zinc-500" :
                          "bg-amber-400/10 text-amber-400"
                      }`}>
                      {agent.status}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Inspect Modal */}
        <AnimatePresence>
          {selectedAgent && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setSelectedAgent(null)}
                className="absolute inset-0 bg-black/80 backdrop-blur-md"
              />
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="relative w-full max-w-lg bento p-0 overflow-hidden"
              >
                <div className="px-6 py-4 border-b border-white/[0.06] flex justify-between items-center">
                  <h3 className="text-[14px] font-medium text-white">
                    {selectedAgent.role} · <span className="text-zinc-500 font-mono text-[12px]">{selectedAgent.id}</span>
                  </h3>
                  <button onClick={() => setSelectedAgent(null)} className="text-zinc-600 hover:text-white transition-colors">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="p-6 space-y-5">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-[11px] text-zinc-600 mb-2">Identity</div>
                      <div className="space-y-1 text-[13px]">
                        <div className="text-zinc-400">Name: <span className="text-white">{selectedAgent.role} Agent</span></div>
                        <div className="text-zinc-400">Type: <span className="text-white">Autonomous</span></div>
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-zinc-600 mb-2">Resources</div>
                      <div className="space-y-1 text-[13px]">
                        <div className="text-zinc-400">Compute: <span className="text-white">{selectedAgent.compute}</span></div>
                        <div className="text-zinc-400">Memory: <span className="text-white">{selectedAgent.memory}</span></div>
                        <div className="text-zinc-400">Load: <span className="text-white">{selectedAgent.load}%</span></div>
                      </div>
                    </div>
                  </div>
                  <div className="border-t border-white/[0.06] pt-5">
                    <div className="text-[11px] text-zinc-600 mb-3">Active Contract (SOUL.md)</div>
                    <div className="bg-black/40 p-4 rounded-xl text-[13px] text-zinc-400 italic leading-relaxed">
                      &quot;Strict adherence to the workspace protocol is mandatory. No execution outside sandbox boundaries.&quot;
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
