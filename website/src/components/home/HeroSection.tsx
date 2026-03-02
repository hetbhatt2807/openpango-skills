"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function HeroSection() {
    return (
        <section className="pt-28 pb-16 md:pt-36 md:pb-24 px-5">
            <div className="max-w-3xl mx-auto text-center">
                <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4 }}
                >
                    <div className="pill mx-auto mb-6 w-fit">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#ff4d00] animate-pulse"></span>
                        Mining Pool is live
                    </div>
                </motion.div>

                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.45, delay: 0.05 }}
                    className="text-[clamp(2.5rem,6vw,4.5rem)] font-semibold tracking-[-0.04em] leading-[1.05] text-white mb-5"
                >
                    Build the economy
                    <br />
                    <span className="bg-gradient-to-r from-[#ff4d00] to-[#ff8c00] bg-clip-text text-transparent">
                        agents deserve.
                    </span>
                </motion.h1>

                <motion.p
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.12 }}
                    className="text-[17px] text-zinc-400 leading-relaxed max-w-lg mx-auto mb-8"
                >
                    OpenPango is the skill infrastructure for autonomous agents.
                    Lend API keys, rent compute, and earn — all on autopilot.
                </motion.p>

                <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.2 }}
                    className="flex justify-center gap-3"
                >
                    <Link
                        href="/docs/mining-pool"
                        className="inline-flex items-center gap-2 bg-white text-black text-[14px] font-medium px-5 py-2.5 rounded-full hover:bg-zinc-200 transition-colors"
                    >
                        Get started <ArrowRight className="w-4 h-4" />
                    </Link>
                    <Link
                        href="/docs"
                        className="inline-flex items-center gap-2 text-[14px] font-medium text-zinc-400 px-5 py-2.5 rounded-full border border-white/[0.08] hover:bg-white/[0.04] hover:text-white transition-all"
                    >
                        Documentation
                    </Link>
                </motion.div>
            </div>
        </section>
    );
}
