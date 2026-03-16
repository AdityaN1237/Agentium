'use client';

import { AnalyticsDashboard } from "@/components/dashboard/AnalyticsDashboard";
import { useAgents } from "@/context/AgentContext";
import { LineChart as ChartIcon, AlertCircle, BarChart, History, PieChart, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import { systemApi, AnalyticsData, SystemStats, agentApi } from "@/services/api";
import { TrainingMetric } from "@/types/agent";

export default function AnalyticsPage() {
    const { activeAgent } = useAgents();
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [stats, setStats] = useState<SystemStats | null>(null);
    const [metrics, setMetrics] = useState<TrainingMetric | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await systemApi.analytics();
                setData(res.data);
            } catch (e) {
                console.error(e);
            }
        };
        fetchData();
    }, []);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const res = await systemApi.stats();
                setStats(res.data);
            } catch (e) {
                console.error(e);
            }
        };
        fetchStats();
    }, []);

    useEffect(() => {
        const fetchMetrics = async () => {
            if (!activeAgent) {
                setMetrics(null);
                return;
            }
            try {
                const res = await agentApi.getMetrics(activeAgent.id);
                setMetrics(res.data);
            } catch (e) {
                console.error(e);
            }
        };
        fetchMetrics();
    }, [activeAgent]);

    return (
        <div className="relative min-h-screen mesh-gradient bg-grid">
            <div className="max-w-7xl mx-auto p-6 md:p-8 lg:p-12 space-y-12 md:space-y-16 pb-20">
                <header className="space-y-6">
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center gap-2 text-sky-400"
                    >
                        <BarChart className="w-4 h-4" />
                        <span className="text-[10px] font-black uppercase tracking-[0.2em]">Neural Diagnostics</span>
                    </motion.div>
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white flex items-center gap-4 md:gap-6 tracking-tighter leading-tight lg:leading-none">
                        <div className="w-12 h-12 md:w-16 md:h-16 rounded-[22px] md:rounded-[28px] bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-2xl shadow-sky-500/30 shrink-0">
                            <ChartIcon className="w-6 h-6 md:w-9 md:h-9 text-white" />
                        </div>
                        <span>Model <span className="text-slate-500">Analytics</span></span>
                    </h1>
                    <p className="text-lg md:text-xl text-slate-400 max-w-2xl font-medium leading-relaxed">
                        Monitor granular performance metrics, convergence history, and neural throughput. Integrated validation stream.
                    </p>
                </header>

                {!activeAgent ? (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="p-10 md:p-20 text-center rounded-[40px] md:rounded-[60px] glass-card border-dashed border-slate-800 flex flex-col items-center justify-center"
                    >
                        <div className="w-16 h-16 md:w-24 md:h-24 rounded-full bg-slate-900 flex items-center justify-center mb-6 md:mb-8 border border-white/5 shadow-2xl">
                            <AlertCircle className="w-8 h-8 md:w-12 md:h-12 text-slate-700" />
                        </div>
                        <h3 className="text-2xl md:text-3xl font-black text-white tracking-tight mb-4">Telemetry Missing</h3>
                        <p className="text-base md:text-lg text-slate-500 max-w-md font-medium">Please bridge an intelligence module to synchronize live telemetry and performance feeds.</p>
                    </motion.div>
                ) : (
                    <div className="space-y-12 md:space-y-16">
                        <AnalyticsDashboard data={data} stats={stats} metrics={metrics} />

                        {/* Additional Analytics Subview */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-10">
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="p-8 md:p-10 rounded-[32px] md:rounded-[48px] glass-card border border-white/[0.03] space-y-8 md:space-y-10"
                            >
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                    <h4 className="text-lg md:text-xl font-black text-white flex items-center gap-3 tracking-tight">
                                        <History className="w-5 h-5 md:w-6 md:h-6 text-indigo-400" />
                                        Drift Analysis
                                    </h4>
                                    <span className="w-fit px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-black uppercase tracking-widest">Stable</span>
                                </div>

                                <div className="space-y-6 md:space-y-8">
                                    {(data?.market_drift || []).map((m, i) => (
                                        <div key={i} className="space-y-3">
                                            <div className="flex justify-between items-end">
                                                <span className="text-[9px] md:text-[10px] font-black text-slate-500 uppercase tracking-widest">{m.subject}</span>
                                                <span className="text-xs md:text-sm font-black text-white">{m.A}</span>
                                            </div>
                                            <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${(m.A / m.fullMark) * 100}%` }}
                                                    transition={{ duration: 1, delay: 0.5 + (i * 0.1) }}
                                                    className="h-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.5)]"
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>

                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                                className="p-8 md:p-10 rounded-[32px] md:rounded-[48px] glass-card border border-white/[0.03] flex flex-col justify-between"
                            >
                                <div className="flex items-center justify-between">
                                    <h4 className="text-lg md:text-xl font-black text-white flex items-center gap-3 tracking-tight">
                                        <PieChart className="w-5 h-5 md:w-6 md:h-6 text-purple-400" />
                                        Inference Composition
                                    </h4>
                                </div>

                                <div className="flex-1 flex items-center justify-center p-6 md:p-10">
                                    <div className="relative w-36 h-36 md:w-48 md:h-48">
                                        {/* Mock Radial/Doughnut Chart UI */}
                                        <div className="absolute inset-0 rounded-full border-[10px] md:border-[12px] border-slate-900" />
                                        <div className="absolute inset-0 rounded-full border-[10px] md:border-[12px] border-indigo-500 border-t-transparent border-r-transparent rotate-45" />
                                        <div className="absolute inset-0 rounded-full border-[10px] md:border-[12px] border-purple-500 border-b-transparent border-l-transparent -rotate-12" />
                                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                                            <Activity className="w-6 h-6 md:w-8 md:h-8 text-white mb-1" />
                                            <span className="text-xl md:text-2xl font-black text-white leading-none">
                                                {data?.skill_composition.reduce((a, b) => a + b.value, 0) || 0}
                                            </span>
                                            <span className="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">Skills</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4 mt-6 md:mt-0">
                                    {(data?.skill_composition.slice(0, 4) || []).map((skill, i) => (
                                        <div key={i} className="flex items-center gap-2 md:gap-3">
                                            <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full" style={{ backgroundColor: skill.fill }} />
                                            <span className="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest truncate max-w-[100px]">{skill.name}</span>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
