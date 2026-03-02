"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Pickaxe, TrendingUp, Zap, Clock, Users, ArrowRight } from "lucide-react";
import Link from "next/link";

interface Miner {
    id: string;
    name: string;
    model: string;
    rate: number;
    tasksCompleted: number;
    earnings: number;
    status: "active" | "idle" | "offline";
    uptime: string;
    trustScore: number;
}

interface ActivityEvent {
    id: string;
    time: string;
    type: "task_completed" | "miner_joined" | "payout" | "task_routed";
    message: string;
}

const MINERS: Miner[] = [
    { id: "miner_a3f8c1e92b", name: "gpt4-heavy", model: "GPT-4", rate: 0.02, tasksCompleted: 312, earnings: 6.24, status: "active", uptime: "99.7%", trustScore: 94 },
    { id: "miner_d7e2b4a1f0", name: "claude-fast", model: "Claude 3.5", rate: 0.015, tasksCompleted: 189, earnings: 2.84, status: "active", uptime: "98.2%", trustScore: 87 },
    { id: "miner_f1c9a8b3d2", name: "llama-local", model: "Llama 3", rate: 0.005, tasksCompleted: 847, earnings: 4.24, status: "idle", uptime: "95.1%", trustScore: 72 },
    { id: "miner_b4e6d2c8a1", name: "mixtral-gpu", model: "Mixtral 8x7B", rate: 0.008, tasksCompleted: 523, earnings: 4.18, status: "active", uptime: "97.8%", trustScore: 81 },
    { id: "miner_c2a1e9f7b4", name: "gemini-pro", model: "Gemini Pro", rate: 0.018, tasksCompleted: 156, earnings: 2.81, status: "offline", uptime: "88.4%", trustScore: 65 },
];

const INITIAL_EVENTS: ActivityEvent[] = [
    { id: "e1", time: "00:28:14", type: "task_completed", message: "gpt4-heavy completed inference task #4812 → $0.02 earned" },
    { id: "e2", time: "00:27:51", type: "task_routed", message: "Task #4813 routed to claude-fast (cheapest available)" },
    { id: "e3", time: "00:26:30", type: "payout", message: "Payout batch processed: $2.40 → 3 miners" },
    { id: "e4", time: "00:25:12", type: "miner_joined", message: "mixtral-gpu came online (Mixtral 8x7B @ $0.008/req)" },
];

const EVENT_TEMPLATES: Omit<ActivityEvent, "id" | "time">[] = [
    { type: "task_completed", message: "gpt4-heavy completed inference task → $0.02 earned" },
    { type: "task_routed", message: "Task routed to claude-fast (best latency)" },
    { type: "task_completed", message: "llama-local completed batch analysis → $0.005 earned" },
    { type: "payout", message: "Escrow released: $0.04 → mixtral-gpu" },
    { type: "task_routed", message: "Task routed to gpt4-heavy (highest trust)" },
    { type: "task_completed", message: "mixtral-gpu completed code review → $0.008 earned" },
];

export default function MiningDashboard() {
    const [events, setEvents] = useState<ActivityEvent[]>(INITIAL_EVENTS);
    const [totalTasks, setTotalTasks] = useState(2027);
    const [totalEarnings, setTotalEarnings] = useState(20.31);

    const addEvent = useCallback(() => {
        const template = EVENT_TEMPLATES[Math.floor(Math.random() * EVENT_TEMPLATES.length)];
        const now = new Date();
        const time = now.toLocaleTimeString("en-US", { hour12: false });
        const newEvent: ActivityEvent = { ...template, id: `e${Date.now()}`, time };
        setEvents((prev) => [newEvent, ...prev].slice(0, 12));
        if (template.type === "task_completed") {
            setTotalTasks((t) => t + 1);
            const earn = parseFloat(template.message.match(/\$(\d+\.\d+)/)?.[1] || "0.01");
            setTotalEarnings((e) => parseFloat((e + earn).toFixed(2)));
        }
    }, []);

    useEffect(() => {
        const interval = setInterval(addEvent, 4000 + Math.random() * 3000);
        return () => clearInterval(interval);
    }, [addEvent]);

    const statusColor = {
        active: "bg-emerald-500",
        idle: "bg-amber-400",
        offline: "bg-zinc-600",
    };

    return (
        <main className="min-h-screen bg-black pt-20 pb-24 px-5">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-8">
                    <div>
                        <div className="pill w-fit mb-4">
                            <Pickaxe className="w-3 h-3" /> Mining Pool
                        </div>
                        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-white">
                            Pool Dashboard
                        </h1>
                    </div>
                    <Link
                        href="/docs/mining-pool"
                        className="inline-flex items-center gap-1.5 text-[13px] text-[#ff4d00] font-medium hover:underline"
                    >
                        Mining docs <ArrowRight className="w-3 h-3" />
                    </Link>
                </div>

                {/* Stats row */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
                    {[
                        { icon: <Users className="w-4 h-4" />, label: "Active Miners", value: MINERS.filter((m) => m.status === "active").length.toString(), accent: false },
                        { icon: <Zap className="w-4 h-4" />, label: "Tasks Completed", value: totalTasks.toLocaleString(), accent: false },
                        { icon: <TrendingUp className="w-4 h-4" />, label: "Total Earnings", value: `$${totalEarnings.toFixed(2)}`, accent: true },
                        { icon: <Clock className="w-4 h-4" />, label: "Avg. Uptime", value: "95.8%", accent: false },
                    ].map((s) => (
                        <div key={s.label} className="bento p-5">
                            <div className="text-zinc-500 mb-3">{s.icon}</div>
                            <div className={`text-2xl font-semibold ${s.accent ? "text-[#ff4d00]" : "text-white"}`}>{s.value}</div>
                            <div className="text-[11px] text-zinc-600 mt-0.5">{s.label}</div>
                        </div>
                    ))}
                </div>

                <div className="grid lg:grid-cols-3 gap-3">
                    {/* Miners table — 2 cols */}
                    <div className="lg:col-span-2 bento p-0 overflow-hidden">
                        <div className="px-5 py-4 border-b border-white/[0.04]">
                            <h2 className="text-[14px] font-medium text-white">Registered Miners</h2>
                        </div>
                        <div className="divide-y divide-white/[0.03]">
                            {MINERS.map((miner) => (
                                <div key={miner.id} className="px-5 py-4 flex items-center gap-4 hover:bg-white/[0.02] transition-colors">
                                    <span className={`w-2 h-2 rounded-full shrink-0 ${statusColor[miner.status]}`} />
                                    <div className="flex-1 min-w-0">
                                        <div className="text-[13px] font-medium text-white">{miner.name}</div>
                                        <div className="text-[11px] text-zinc-600 font-mono truncate">{miner.id}</div>
                                    </div>
                                    <div className="hidden sm:block text-[12px] text-zinc-500 w-20">{miner.model}</div>
                                    <div className="hidden sm:block text-[12px] text-zinc-500 w-16 text-right">${miner.rate}/req</div>
                                    <div className="text-[12px] text-zinc-400 w-12 text-right">{miner.tasksCompleted}</div>
                                    <div className="text-[12px] font-medium text-[#ff4d00] w-14 text-right">${miner.earnings.toFixed(2)}</div>
                                    <div className="hidden md:block w-12">
                                        <div className="text-[10px] text-zinc-600">Trust</div>
                                        <div className="flex items-center gap-1">
                                            <div className="flex-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full ${miner.trustScore >= 80 ? "bg-emerald-500" : miner.trustScore >= 60 ? "bg-amber-400" : "bg-red-500"}`}
                                                    style={{ width: `${miner.trustScore}%` }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Live activity feed — 1 col */}
                    <div className="bento p-0 overflow-hidden">
                        <div className="px-5 py-4 border-b border-white/[0.04] flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <h2 className="text-[14px] font-medium text-white">Live Activity</h2>
                        </div>
                        <div className="max-h-[400px] overflow-y-auto">
                            <AnimatePresence initial={false}>
                                {events.map((event) => (
                                    <motion.div
                                        key={event.id}
                                        initial={{ opacity: 0, height: 0, y: -10 }}
                                        animate={{ opacity: 1, height: "auto", y: 0 }}
                                        exit={{ opacity: 0, height: 0 }}
                                        transition={{ duration: 0.3 }}
                                        className="px-5 py-3 border-b border-white/[0.03]"
                                    >
                                        <div className="flex items-center gap-2 mb-0.5">
                                            <span className={`w-1 h-1 rounded-full ${event.type === "task_completed" ? "bg-emerald-500" :
                                                    event.type === "payout" ? "bg-[#ff4d00]" :
                                                        event.type === "miner_joined" ? "bg-sky-400" :
                                                            "bg-zinc-600"
                                                }`} />
                                            <span className="text-[10px] text-zinc-600 font-mono">{event.time}</span>
                                        </div>
                                        <div className="text-[12px] text-zinc-400 leading-relaxed">{event.message}</div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
