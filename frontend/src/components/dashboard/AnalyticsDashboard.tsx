'use client';

import { useAgents } from "@/context/AgentContext";
import { AnalyticsData, SystemStats } from "@/services/api";
import type { TrainingMetric } from "@/types/agent";
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Target, Activity, Zap, TrendingUp, Info } from 'lucide-react';
import { motion } from 'framer-motion';

export function AnalyticsDashboard({ data, stats, metrics }: { data: AnalyticsData | null, stats: SystemStats | null, metrics: TrainingMetric | null }) {
    const { activeAgent } = useAgents();

    if (!activeAgent) return null;

    const acc = typeof metrics?.accuracy === 'number' ? metrics.accuracy : (typeof activeAgent.accuracy === 'number' ? activeAgent.accuracy || 0 : 0);
    const iq = data?.inference_quality ?? [];
    const avgLatency = iq.reduce((sum, d) => sum + d.latency, 0) / Math.max(iq.length, 1);
    const cycles = iq.length;
    const accSeries = iq.map((d) => ({
        ...d,
        accuracy: d.accuracy > 1 ? d.accuracy / 100 : d.accuracy
    }));
    const firstAcc = iq[0]?.accuracy || 0;
    const lastAcc = iq.slice(-1)[0]?.accuracy || 0;
    const growth = lastAcc - firstAcc;
    const growthDisplay = growth.toFixed(1);

    return (
        <div className="space-y-10">
            {/* High-Impact Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                    { label: 'Neural Accuracy', value: `${(acc * 100).toFixed(1)}%`, icon: Target, color: 'text-indigo-400', bg: 'bg-indigo-500/10', sub: 'Current accuracy' },
                    { label: 'Avg. Inference', value: `${Math.round(avgLatency)}ms`, icon: Zap, color: 'text-amber-400', bg: 'bg-amber-500/10', sub: 'Latency average' },
                    { label: 'Neural Cycles', value: `${cycles}`, icon: Activity, color: 'text-emerald-400', bg: 'bg-emerald-500/10', sub: 'Observed periods' },
                    { label: 'Growth Vector', value: `${growth >= 0 ? '+' : ''}${growthDisplay}%`, icon: TrendingUp, color: 'text-sky-400', bg: 'bg-sky-500/10', sub: 'Accuracy change' },
                ].map((stat, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="p-8 rounded-[40px] glass-card glass-card-hover border border-white/[0.03]"
                    >
                        <div className="flex items-center gap-4 mb-6">
                            <div className={`w-12 h-12 rounded-2xl ${stat.bg} flex items-center justify-center border border-white/5`}>
                                <stat.icon className={`w-6 h-6 ${stat.color}`} />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{stat.label}</span>
                                <span className="text-[10px] text-indigo-500/60 font-medium">{stat.sub}</span>
                            </div>
                        </div>
                        <div className="text-4xl font-black text-white tracking-tighter">{stat.value}</div>
                    </motion.div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
                {/* Advanced Chart Card */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="lg:col-span-8 p-10 rounded-[48px] glass-card relative overflow-hidden group border border-white/[0.03]"
                >
                    {/* Subtle Background Circuit Effect (Visual) */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 blur-[100px] pointer-events-none rounded-full" />

                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12 relative z-10">
                        <div>
                            <h3 className="text-2xl font-black text-white tracking-tight">Performance Evolution</h3>
                            <p className="text-sm font-bold text-slate-500 uppercase tracking-widest mt-2">Validation Accuracy & Latency Stream</p>
                        </div>
                        <div className="flex gap-4 p-2 rounded-2xl bg-slate-950/50 border border-slate-800/50">
                            <div className="flex items-center gap-2 px-4 py-2">
                                <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.6)]" />
                                <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Accuracy</span>
                            </div>
                            <div className="flex items-center gap-2 px-4 py-2">
                                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
                                <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Latency</span>
                            </div>
                        </div>
                    </div>

                    <div className="h-[400px] w-full relative z-10">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={accSeries}>
                                <defs>
                                    <linearGradient id="colorAcc" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorLat" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} opacity={0.3} />
                                <XAxis
                                    dataKey="month"
                                    stroke="#334155"
                                    fontSize={10}
                                    fontWeight="bold"
                                    tickLine={false}
                                    axisLine={false}
                                    dy={10}
                                />
                                <YAxis
                                    yAxisId="left"
                                    stroke="#334155"
                                    fontSize={10}
                                    fontWeight="bold"
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(val) => `${val * 100}%`}
                                    dx={-10}
                                />
                                <YAxis
                                    yAxisId="right"
                                    orientation="right"
                                    stroke="#334155"
                                    fontSize={10}
                                    fontWeight="bold"
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(val) => `${Math.round(val)}ms`}
                                    dx={10}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#020617', borderColor: '#1e293b', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.08)', boxShadow: '0 20px 40px rgba(0,0,0,0.4)', padding: '16px' }}
                                    itemStyle={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em' }}
                                    cursor={{ stroke: '#334155', strokeWidth: 1 }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="accuracy"
                                    stroke="#6366f1"
                                    strokeWidth={4}
                                    fillOpacity={1}
                                    fill="url(#colorAcc)"
                                    animationDuration={2000}
                                    yAxisId="left"
                                />
                                <Area
                                    type="monotone"
                                    dataKey="latency"
                                    stroke="#10b981"
                                    strokeWidth={4}
                                    fillOpacity={1}
                                    fill="url(#colorLat)"
                                    animationDuration={2500}
                                    yAxisId="right"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Sidebar Info Cards */}
                <div className="lg:col-span-4 space-y-10">
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="p-10 rounded-[48px] bg-slate-900/40 border border-slate-800/50 space-y-8"
                    >
                        <div className="flex items-center gap-3">
                            <Info className="w-6 h-6 text-indigo-500" />
                            <h4 className="text-xl font-black text-white tracking-tight">Node Topology</h4>
                        </div>

                        <div className="space-y-6">
                            {[
                                { label: 'Embedding Model', val: stats?.ai_config?.embedding_model || 'N/A' },
                                { label: 'Embedding Dimension', val: `${stats?.ai_config?.embedding_dimension || 'N/A'}` },
                                { label: 'Semantic Weight', val: `${stats?.ai_config?.weights?.semantic ?? 'N/A'}` },
                                { label: 'Last Accuracy', val: `${(acc * 100).toFixed(1)}%` },
                            ].map((item, i) => (
                                <div key={i} className="flex flex-col gap-1 border-b border-white/5 pb-4 last:border-0 last:pb-0">
                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{item.label}</span>
                                    <span className="text-sm font-extrabold text-slate-200">{item.val}</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 }}
                        className="p-10 rounded-[48px] bg-indigo-600/10 border border-indigo-500/20 relative overflow-hidden group"
                    >
                        <div className="absolute -top-10 -right-10 w-32 h-32 bg-indigo-500/20 rounded-full blur-2xl pointer-events-none" />
                        <h4 className="text-xl font-black text-white tracking-tight mb-4 flex items-center gap-3">
                            <Target className="w-6 h-6 text-indigo-400" />
                            Next Benchmark
                        </h4>
                        <p className="text-sm text-indigo-200/60 font-medium leading-relaxed mb-6">
                            Targeting improved accuracy with current configuration tuning.
                        </p>
                        <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                            <div className="w-[70%] h-full bg-gradient-to-r from-indigo-500 to-purple-500 animate-pulse" />
                        </div>
                        <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mt-4">Progress</p>
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
