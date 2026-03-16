'use client';

import { AgentSelector } from "@/components/agents/AgentSelector";
import { BrainCircuit, Info, Target, Cpu, Activity, LayoutGrid, Plus } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from "../../lib/utils";
import { useState, useEffect } from 'react';
import { systemApi, SystemStats } from '@/services/api';
import { AgentForm } from "@/components/agents/AgentForm";
import { useAgents } from "@/context/AgentContext";

export default function AgentsPage() {
    const [sysStats, setSysStats] = useState<SystemStats | null>(null);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const { createAgent } = useAgents();

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const { data } = await systemApi.stats();
                setSysStats(data);
            } catch (e) {
                console.error(e);
            }
        };
        fetchStats();
    }, []);

    const handleCreateAgent = async (data: import('@/types/agent').AgentCreatePayload) => {
        try {
            await createAgent(data);
            setIsCreateModalOpen(false);
        } catch (err) {
            const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            alert(msg || 'Failed to create agent');
        }
    };

    return (
        <div className="relative min-h-screen mesh-gradient bg-grid">
            <div className="max-w-7xl mx-auto p-6 md:p-8 lg:p-12 space-y-12 md:space-y-16">
                <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div className="space-y-6">
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex items-center gap-2 text-indigo-400"
                        >
                            <LayoutGrid className="w-4 h-4" />
                            <span className="text-[10px] font-black uppercase tracking-[0.2em]">Neural Registry</span>
                        </motion.div>
                        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white flex items-center gap-4 md:gap-6 tracking-tighter leading-tight lg:leading-none">
                            <div className="w-12 h-12 md:w-16 md:h-16 rounded-[22px] md:rounded-[28px] bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-2xl shadow-indigo-500/30 shrink-0">
                                <BrainCircuit className="w-6 h-6 md:w-9 md:h-9 text-white" />
                            </div>
                            <span>AI Intelligence <span className="text-slate-500">Registry</span></span>
                        </h1>
                        <p className="text-lg md:text-xl text-slate-400 max-w-2xl font-medium leading-relaxed">
                            Manage and orchestrate specialized autonomous nodes. Each agent is a discrete compute unit with specialized vector architecture.
                        </p>
                    </div>

                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => setIsCreateModalOpen(true)}
                        className="px-8 py-4 bg-indigo-500 text-white rounded-[24px] font-black text-xs uppercase tracking-widest shadow-xl shadow-indigo-500/20 flex items-center gap-3 self-start md:mb-2 hover:bg-indigo-400 transition-colors"
                    >
                        <Plus className="w-5 h-5" />
                        Initialize New Node
                    </motion.button>
                </header>

                <AgentForm
                    isOpen={isCreateModalOpen}
                    onClose={() => setIsCreateModalOpen(false)}
                    onSubmit={(data) => { void handleCreateAgent(data as import('@/types/agent').AgentCreatePayload); }}
                    title="Initialize New Agent"
                />

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="p-8 md:p-10 rounded-[32px] md:rounded-[48px] glass-card flex flex-col md:flex-row items-center gap-6 md:gap-8 relative overflow-hidden text-center md:text-left"
                >
                    <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 blur-3xl pointer-events-none rounded-full" />

                    <div className="w-16 h-16 md:w-20 md:h-20 rounded-[24px] md:rounded-[32px] bg-white/[0.03] border border-white/10 flex items-center justify-center shrink-0">
                        <Info className="w-8 h-8 md:w-10 md:h-10 text-indigo-400" />
                    </div>
                    <div className="space-y-2">
                        <h4 className="text-xl md:text-2xl font-black text-white tracking-tight">System Specification</h4>
                        <p className="text-sm md:text-lg text-slate-400 font-medium leading-relaxed max-w-4xl">
                            Switching agents reconfigures the platform topology. Neural weights, embedding contexts, and historical analytics are strictly isolated.
                        </p>
                    </div>
                </motion.div>

                <div className="space-y-8 md:space-y-10">
                    <h2 className="text-xl md:text-2xl font-black text-white flex items-center gap-4">
                        <div className="w-1 md:w-1.5 h-12 md:h-16 bg-indigo-500 rounded-full" />
                        Available Compute Nodes
                    </h2>
                    <AgentSelector />
                </div>

                {/* System Health Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8 pb-10">
                    {[
                        { label: 'Platform Stability', val: sysStats?.system.health_score ? `${sysStats.system.health_score}%` : '---', icon: Target, color: 'text-emerald-400' },
                        { label: 'Compute Clusters', val: sysStats?.system.active_agents ? `Active (${sysStats.system.active_agents})` : 'Offline', icon: Cpu, color: 'text-indigo-400' },
                        { label: 'Total Inferences', val: sysStats?.system.global_queries ? `${sysStats.system.global_queries}` : '0', icon: Activity, color: 'text-purple-400' },
                    ].map((stat, i) => (
                        <div key={i} className="p-6 md:p-8 rounded-[32px] md:rounded-[40px] border border-slate-800/50 bg-slate-900/10 flex items-center gap-4 md:gap-6">
                            <div className="w-12 h-12 md:w-14 md:h-14 rounded-2xl bg-slate-950 flex items-center justify-center border border-slate-800 shrink-0">
                                <stat.icon className={cn("w-6 h-6 md:w-7 md:h-7", stat.color)} />
                            </div>
                            <div>
                                <p className="text-[9px] md:text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">{stat.label}</p>
                                <p className="text-xl md:text-2xl font-black text-white">{stat.val}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
