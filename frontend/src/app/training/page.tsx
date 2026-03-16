'use client';

import { TrainingModule } from "@/components/agents/TrainingModule";
import { useAgents } from "@/context/AgentContext";
import { useTrainingStream } from "@/hooks/useTrainingStream";
import { Database, AlertCircle, Settings2, Terminal, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from "../../lib/utils";
import { useEffect, useRef, useState } from "react";
import { agentApi } from "@/services/api";
import { AgentChat } from "@/components/agents/AgentChat";
import { BatchUpload } from "@/components/BatchUpload";
import { modelApi } from "@/services/api";
import { HardDrive } from "lucide-react";
import { ModelStatus as ModelStatusType } from "@/types/agent";

function ModelStatus({ agentId }: { agentId: string }) {
    const [status, setStatus] = useState<ModelStatusType | null>(null);

    useEffect(() => {
        modelApi.getAgentStatus(agentId).then(({ data }) => setStatus(data)).catch(() => setStatus(null));
    }, [agentId]);

    if (!status || !status.has_embeddings) return null;

    return (
        <div className="p-6 rounded-[32px] glass-card border border-slate-800 space-y-6">
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
                    <HardDrive className="w-6 h-6 text-emerald-400" />
                </div>
                <div>
                    <h3 className="text-xl font-black text-white">Model Artifacts</h3>
                    <p className="text-sm text-slate-400">Persisted training data</p>
                </div>
            </div>

            <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-white/5">
                    <span className="text-slate-500 text-sm font-bold">Latest Version</span>
                    <span className="font-mono text-emerald-400">{status.latest_version}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-white/5">
                    <span className="text-slate-500 text-sm font-bold">Embeddings</span>
                    <span className="font-mono text-white">{status.embedding_count} vectors</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-white/5">
                    <span className="text-slate-500 text-sm font-bold">Last Saved</span>
                    <span className="font-mono text-slate-400 text-xs">
                        {new Date(status.last_saved).toLocaleString()}
                    </span>
                </div>
            </div>
        </div>
    );
}


export default function TrainingPage() {
    const { activeAgent } = useAgents();
    const { logs, isConnected, clearLogs } = useTrainingStream(activeAgent?.id);
    const scrollRef = useRef<HTMLDivElement>(null);
    const [protocol, setProtocol] = useState<Record<string, unknown> | null>(null);

    // Auto-scroll to bottom of logs
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    // Load protocol parameters for active agent
    useEffect(() => {
        const loadProtocol = async () => {
            if (!activeAgent) {
                setProtocol(null);
                return;
            }
            try {
                const { data } = await agentApi.protocol(activeAgent.id);
                setProtocol(data);
            } catch (e) {
                setProtocol(null);
                console.error("Failed to load protocol parameters", e);
            }
        };
        loadProtocol();
    }, [activeAgent]);

    return (
        <div className="relative min-h-screen mesh-gradient bg-grid">
            <div className="max-w-7xl mx-auto p-6 md:p-8 lg:p-12 space-y-12 md:space-y-16 pb-20">
                <header className="space-y-6">
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center gap-2 text-emerald-400"
                    >
                        <Settings2 className="w-4 h-4" />
                        <span className="text-[10px] font-black uppercase tracking-[0.2em]">Compute Workflow</span>
                    </motion.div>
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white flex items-center gap-4 md:gap-6 tracking-tighter leading-tight lg:leading-none">
                        <div className="w-12 h-12 md:w-16 md:h-16 rounded-[22px] md:rounded-[28px] bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-2xl shadow-emerald-500/30 shrink-0">
                            <Database className="w-6 h-6 md:w-9 md:h-9 text-white" />
                        </div>
                        <span>Neural <span className="text-slate-500">Training</span></span>
                    </h1>
                    <p className="text-lg md:text-xl text-slate-400 max-w-2xl font-medium leading-relaxed">
                        Execute model refinement sequences and dataset ingestions. Monitor live compute status and protocol synchronization.
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
                        <h3 className="text-2xl md:text-3xl font-black text-white tracking-tight mb-4">Node Not Synchronized</h3>
                        <p className="text-base md:text-lg text-slate-500 max-w-md font-medium">Please authorize an intelligence module from the registry to initialize training protocols.</p>
                        <button className="mt-8 md:mt-10 px-6 md:px-8 py-3 md:py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-black rounded-2xl uppercase tracking-widest text-[10px] md:text-xs transition-all shadow-xl shadow-indigo-500/20 active:scale-95">
                            Open Registry
                        </button>
                    </motion.div>
                ) : (
                    <div className="space-y-16">
                        <TrainingModule onStart={clearLogs} />

                        {/* Extended Training Logs/Status section */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-10">
                            <div className="lg:col-span-2 p-6 md:p-10 rounded-[32px] md:rounded-[48px] glass-card space-y-6 md:space-y-8 min-h-[400px] md:min-h-[500px] flex flex-col">
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                    <h4 className="text-lg md:text-xl font-black text-white flex items-center gap-3 tracking-tight">
                                        <Terminal className="w-5 h-5 md:w-6 md:h-6 text-indigo-400" />
                                        Live Sequence Stream
                                    </h4>
                                    <div className="flex items-center gap-3">
                                        <div className={cn(
                                            "w-2 h-2 rounded-full",
                                            isConnected ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
                                        )} />
                                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                                            {isConnected ? 'Sync Active' : 'Sync Offline'}
                                        </span>
                                    </div>
                                </div>

                                <div
                                    ref={scrollRef}
                                    className="flex-1 space-y-2 md:space-y-3 font-mono text-[10px] md:text-[11px] overflow-y-auto max-h-[300px] md:max-h-[400px] custom-scrollbar p-5 md:p-8 bg-black/40 rounded-[24px] md:rounded-[32px] border border-white/5 shadow-inner"
                                >
                                    <AnimatePresence initial={false}>
                                        {logs.length === 0 ? (
                                            <div className="h-full flex flex-col items-center justify-center text-slate-600 opacity-50">
                                                <Terminal className="w-10 h-10 mb-4" />
                                                <p className="uppercase tracking-[0.2em] font-bold text-center">Awaiting initialization...</p>
                                            </div>
                                        ) : (
                                            logs.map((log, i) => (
                                                <motion.div
                                                    key={i}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    className="flex gap-3 md:gap-4 group hover:bg-white/[0.02] -mx-1 md:-mx-2 px-1 md:px-2 py-1 rounded transition-colors"
                                                >
                                                    <span className="text-slate-600 shrink-0 font-bold select-none hidden sm:inline">[{new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}]</span>
                                                    <span className={cn(
                                                        "font-semibold break-words",
                                                        log.level === 'ERROR' ? 'text-rose-400' :
                                                            log.level === 'SUCCESS' ? 'text-emerald-400' :
                                                                log.level === 'WARNING' ? 'text-amber-400' :
                                                                    log.level === 'DEBUG' ? 'text-slate-500' : 'text-indigo-400'
                                                    )}>
                                                        {log.message}
                                                    </span>
                                                </motion.div>
                                            ))
                                        )}
                                    </AnimatePresence>
                                </div>
                            </div>

                            <div className="p-6 md:p-10 rounded-[32px] md:rounded-[48px] bg-slate-900/40 border border-slate-800/50 space-y-6 md:space-y-8 flex flex-col justify-between">
                                <div>
                                    <h4 className="text-lg md:text-xl font-black text-white flex items-center gap-3 tracking-tight mb-6">
                                        <Info className="w-5 h-5 md:w-6 md:h-6 text-slate-500" />
                                        Protocol Parameters
                                    </h4>
                                    <div className="space-y-4 md:space-y-6">
                                        {protocol ? (
                                            <>
                                                <div className="flex justify-between border-b border-white/5 pb-3 md:pb-4">
                                                    <span className="text-[9px] md:text-[10px] font-black text-slate-600 uppercase tracking-widest">Optimizer</span>
                                                    <span className="text-xs md:text-sm font-black text-slate-300">{String(protocol.optimizer ?? '—')}</span>
                                                </div>
                                                <div className="flex justify-between border-b border-white/5 pb-3 md:pb-4">
                                                    <span className="text-[9px] md:text-[10px] font-black text-slate-600 uppercase tracking-widest">Batch Size</span>
                                                    <span className="text-xs md:text-sm font-black text-slate-300">{String(protocol.batch_size ?? '—')}</span>
                                                </div>
                                                <div className="flex justify-between border-b border-white/5 pb-3 md:pb-4">
                                                    <span className="text-[9px] md:text-[10px] font-black text-slate-600 uppercase tracking-widest">Seed</span>
                                                    <span className="text-xs md:text-sm font-black text-slate-300">{String(protocol.seed ?? '—')}</span>
                                                </div>
                                                <div className="flex justify-between border-b border-white/5 pb-3 md:pb-4">
                                                    <span className="text-[9px] md:text-[10px] font-black text-slate-600 uppercase tracking-widest">Parallelism</span>
                                                    <span className="text-xs md:text-sm font-black text-slate-300">{String(protocol.parallelism ?? '—')}</span>
                                                </div>
                                                <div className="flex justify-between border-b border-white/5 pb-3 md:pb-4 last:border-0">
                                                    <span className="text-[9px] md:text-[10px] font-black text-slate-600 uppercase tracking-widest">Learning Rate</span>
                                                    <span className="text-xs md:text-sm font-black text-slate-300">{String(protocol.learning_rate ?? '—')}</span>
                                                </div>
                                            </>
                                        ) : (
                                            <div className="text-slate-600 text-sm">Protocol not available.</div>
                                        )}
                                    </div>
                                </div>
                                <div className="p-5 md:p-6 rounded-2xl md:rounded-3xl bg-indigo-500/5 border border-indigo-500/10 mt-6 lg:mt-0">
                                    <p className="text-[11px] md:text-xs font-medium text-indigo-300 leading-relaxed text-center italic">
                                        Training cycles optimize for cosine similarity between candidate embedding vectors and job requirements.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Model Management & Batch Ingest */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-10">
                            <ModelStatus agentId={activeAgent.id} />
                            <BatchUpload />
                        </div>

                        {/* Interactive Chat Section */}
                        <div className="mt-16">
                            <h2 className="text-2xl md:text-3xl font-black text-white mb-8 flex items-center gap-4">
                                <div className="w-1.5 h-12 bg-indigo-500 rounded-full" />
                                Live Inference & Validation
                            </h2>
                            <AgentChat />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
