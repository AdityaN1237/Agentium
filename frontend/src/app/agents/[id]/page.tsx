'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { useAgents } from '@/context/AgentContext';
import { agentApi } from '@/services/api';
import { AgentMetadata } from '@/types/agent';
import {
    BrainCircuit,
    Activity,
    Terminal,
    Database,
    Cpu,
    ShieldCheck,
    BarChart3,
    ArrowLeft,
    LucideIcon
} from 'lucide-react';
import Link from 'next/link';
import { AgentChat } from '@/components/agents/AgentChat';
import { TrainingModule } from '@/components/agents/TrainingModule';
import { cn } from '@/lib/utils';

export default function AgentDashboard() {
    const { id } = useParams();
    const { setActiveAgent } = useAgents();
    const [agent, setAgent] = useState<AgentMetadata | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [metrics, setMetrics] = useState<Record<string, unknown> | null>(null);
    const [protocol, setProtocol] = useState<Record<string, unknown> | null>(null);

    useEffect(() => {
        const fetchAgent = async () => {
            if (!id) return;
            // Force scroll to top on navigation
            window.scrollTo(0, 0);

            setIsLoading(true);
            try {
                const { data } = await agentApi.getById(id as string);
                setAgent(data);
                setActiveAgent(data);
            } catch (err) {
                console.error("Failed to load agent:", err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchAgent();
    }, [id, setActiveAgent]);

    useEffect(() => {
        const fetchMeta = async () => {
            if (!id) return;
            try {
                const [m, p] = await Promise.all([
                    agentApi.getMetrics(id as string),
                    agentApi.protocol(id as string)
                ]);
                setMetrics(m.data as unknown as Record<string, unknown>);
                setProtocol(p.data as Record<string, unknown>);
            } catch (e) {
                console.error("Failed to load agent meta:", e);
                setMetrics(null);
                setProtocol(null);
            }
        };
        fetchMeta();
    }, [id]);

    const metricItems = useMemo(() => {
        if (!metrics) return [];
        const entries = Object.entries(metrics);
        const iconMap: Record<string, { icon: LucideIcon; color: string; label?: string }> = {
            latency_ms: { icon: Cpu, color: 'text-indigo-400', label: 'Inference Latency' },
            memory_gb: { icon: Database, color: 'text-purple-400', label: 'Memory Allocation' },
            security: { icon: ShieldCheck, color: 'text-emerald-400', label: 'Security Health' },
            epochs: { icon: Activity, color: 'text-amber-400', label: 'Training Epochs' },
            documents: { icon: Database, color: 'text-indigo-400' },
            chunks: { icon: Database, color: 'text-purple-400' },
            accuracy: { icon: Activity, color: 'text-emerald-400' },
            precision: { icon: Activity, color: 'text-emerald-400' },
            recall: { icon: Activity, color: 'text-emerald-400' },
            f1_score: { icon: Activity, color: 'text-emerald-400' },
            matching_accuracy: { icon: Activity, color: 'text-emerald-400' },
            indexed_resumes: { icon: Database, color: 'text-indigo-400' },
            status: { icon: ShieldCheck, color: 'text-emerald-400' },
            last_trained: { icon: Activity, color: 'text-amber-400' }
        };
        return entries.map(([key, value]) => {
            const m = iconMap[key] || { icon: Activity, color: 'text-slate-400' };
            const label = m.label || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            return { label, value, icon: m.icon, color: m.color };
        });
    }, [metrics]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-16 h-16 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center animate-pulse">
                        <BrainCircuit className="w-8 h-8 text-indigo-400" />
                    </div>
                    <span className="text-xs font-black uppercase tracking-widest text-slate-500 animate-pulse">Synchronizing Neural Node...</span>
                </div>
            </div>
        );
    }

    if (!agent) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center space-y-4">
                    <h2 className="text-4xl font-black text-white">404: Node Not Found</h2>
                    <p className="text-slate-400">The requested agent does not exist in the neural registry.</p>
                    <Link href="/agents" className="inline-block px-6 py-3 bg-indigo-500 text-white rounded-xl font-bold">
                        Return to Registry
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="relative min-h-screen mesh-gradient bg-grid pb-20">
            <div className="max-w-[1600px] mx-auto p-6 md:p-8 lg:p-12 space-y-10">
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="flex items-center gap-6">
                        <Link href="/agents" className="p-3 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                            <ArrowLeft className="w-5 h-5 text-slate-400" />
                        </Link>
                        <div className="space-y-1">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                                    <BrainCircuit className="w-5 h-5 text-white" />
                                </div>
                                <h1 className="text-3xl font-black text-white tracking-tight">{agent.name}</h1>
                                <span className={cn(
                                    "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border",
                                    agent.status === 'active' ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                )}>
                                    {agent.status}
                                </span>
                            </div>
                            <p className="text-sm text-slate-400 font-medium">{agent.description}</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="px-5 py-3 rounded-2xl bg-slate-900/50 border border-white/5 flex items-center gap-4">
                            <div className="flex flex-col">
                                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Accuracy</span>
                                <span className="text-sm font-black text-indigo-400">{(agent.accuracy || 0) * 100}%</span>
                            </div>
                            <div className="w-px h-8 bg-white/5" />
                            <div className="flex flex-col">
                                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Ver</span>
                                <span className="text-sm font-black text-white">{agent.version}</span>
                            </div>
                        </div>
                        <Link href={`/agents/${agent.id}/test`} className="p-4 rounded-2xl bg-indigo-600 text-white font-bold hover:bg-indigo-500 transition-colors">
                            Test Interface
                        </Link>
                    </div>
                </header>

                <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
                    <div className="xl:col-span-8 space-y-10">
                        {/* Training Section */}
                        <section className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-black text-white flex items-center gap-3">
                                    <div className="w-1 h-6 bg-indigo-500 rounded-full" />
                                    Node Configuration & Ingestion
                                </h2>
                            </div>
                            <TrainingModule />
                        </section>

                        {/* Chat Section */}
                        <section className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-black text-white flex items-center gap-3">
                                    <div className="w-1 h-6 bg-purple-500 rounded-full" />
                                    Live Neural Interaction
                                </h2>
                            </div>
                            <AgentChat agent={agent} />
                        </section>
                    </div>

                    <div className="xl:col-span-4 space-y-10">
                        {/* Metrics Panel */}
                        <section className="p-8 rounded-[40px] glass-card space-y-8">
                            <div className="flex items-center gap-3">
                                <BarChart3 className="w-5 h-5 text-indigo-400" />
                                <h3 className="text-lg font-black text-white uppercase tracking-tighter">Performance Metrics</h3>
                            </div>

                            <div className="space-y-6">
                                {metricItems.map((m, i) => (
                                    <div key={i} className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5">
                                        <div className="flex items-center gap-3">
                                            <m.icon className={cn("w-4 h-4", m.color)} />
                                            <span className="text-xs font-bold text-slate-400">{m.label}</span>
                                        </div>
                                        <span className="text-sm font-black text-white">{String(m.value)}</span>
                                    </div>
                                ))}
                            </div>

                            <div className="pt-6 border-t border-white/5">
                                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4">Registry Protocol</p>
                                <div className="p-4 rounded-2xl bg-slate-950 font-mono text-[10px] text-indigo-300/70 leading-relaxed overflow-x-auto">
                                    {JSON.stringify(protocol || { id: agent.id, type: agent.type }, null, 2)}
                                </div>
                            </div>
                        </section>

                        {/* Terminal / Logs Output */}
                        <section className="p-8 rounded-[40px] bg-slate-950 border border-white/5 space-y-6">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <Terminal className="w-5 h-5 text-emerald-400" />
                                    <h3 className="text-sm font-black text-white uppercase tracking-widest">Neural Stream</h3>
                                </div>
                                <div className="flex gap-1">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/50" />
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/20" />
                                </div>
                            </div>

                            <div className="space-y-3 h-[300px] overflow-y-auto custom-scrollbar font-mono text-[11px]">
                                {agent.status === 'training' ? (
                                    <p className="text-amber-400/80 animate-pulse">[SYSTEM] Training sequence active...</p>
                                ) : (
                                    <p className="text-emerald-500/80">[SYSTEM] Agent {agent.id} ready.</p>
                                )}
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        </div>
    );
}
