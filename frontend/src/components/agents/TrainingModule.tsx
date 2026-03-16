'use client';

import { useState, useRef, useEffect } from 'react';
import { useAgents } from "@/context/AgentContext";
import { Upload, Play, CheckCircle2, Loader2, FileText, AlertCircle, BrainCircuit, Cpu, Binary, FastForward, Terminal } from 'lucide-react';
import { agentApi, systemApi } from '@/services/api';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import { useTrainingStream } from '@/hooks/useTrainingStream';

export function TrainingModule({ onStart }: { onStart?: () => void }) {
    const { activeAgent, refreshAgents } = useAgents();
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isTraining, setIsTraining] = useState(false);
    const [isStopping, setIsStopping] = useState(false);
    const [vectorCount, setVectorCount] = useState<number>(0);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const [selectedModel, setSelectedModel] = useState("");
    const [config, setConfig] = useState<{ embedding_model?: string; embedding_dimension?: number }>({});

    // Hook into the training stream for real-time status updates
    const { status, logs, isConnected } = useTrainingStream(activeAgent?.id);
    // Auto-scroll logs
    const logsContainerRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        if (logsContainerRef.current) {
            logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
        }
    }, [logs]);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const { data } = await systemApi.stats();
                setVectorCount(data.system.total_vectors);
                setConfig(data.ai_config);
                setSelectedModel(data.ai_config.embedding_model);
            } catch (e) {
                console.warn(e);
            }
        };
        fetchStats();
        const interval = setInterval(fetchStats, 30000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isTraining || activeAgent?.status === 'training' || status === 'PROCESSING' || status === 'INDEXING') {
            interval = setInterval(refreshAgents, 2000);
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [isTraining, activeAgent?.status, status, refreshAgents]);

    if (!activeAgent) return null;

    const triggerFileInput = () => {
        inputRef.current?.click();
    };

    const buildConfig = () => {
        if (!activeAgent) return {};
        return {
            embedding_model: selectedModel
        };
    };

    const handleFileUpload = async () => {
        if (!file) return;
        setIsUploading(true);
        setMessage(null);
        if (onStart) onStart();
        try {
            const { data } = await agentApi.upload(activeAgent.id, file);
            setMessage({ type: 'success', text: data.message || 'Dataset ingested. Background processing started.' });
            // No longer need to manually trigger training, it's automated in the backend
            setTimeout(refreshAgents, 2000);
            setFile(null);
        } catch (error: unknown) {
            let detailText = 'Ingestion failed';
            if (typeof error === 'object' && error !== null) {
                const maybeResp = error as { response?: { data?: { detail?: string } } };
                const maybeErr = error as { message?: string };
                detailText = maybeResp.response?.data?.detail ?? maybeErr.message ?? detailText;
            } else if (typeof error === 'string') {
                detailText = error;
            }
            setMessage({ type: 'error', text: String(detailText) });
        } finally {
            setIsUploading(false);
        }
    };

    const handleStartTraining = async () => {
        setIsTraining(true);
        setMessage(null);
        if (onStart) onStart();
        try {
            const { data } = await agentApi.train(activeAgent.id, buildConfig());
            const msg = typeof data?.message === 'string' ? data.message : 'Core training sequence initiated.';
            setMessage({ type: 'success', text: msg });
            setTimeout(refreshAgents, 2000);
        } catch (error: unknown) {
            let detailText = 'Sequence failed: Protocol mismatch.';
            if (typeof error === 'object' && error !== null) {
                const maybeResp = error as { response?: { data?: { detail?: string } } };
                if (maybeResp.response?.data?.detail) {
                    detailText = maybeResp.response.data.detail;
                }
            }
            setMessage({ type: 'error', text: detailText });
        } finally {
            setIsTraining(false);
        }
    };

    const handleStopTraining = async () => {
        setIsStopping(true);
        try {
            await agentApi.stop(activeAgent.id);
            setMessage({ type: 'success', text: 'Termination signal received.' });
            setTimeout(refreshAgents, 1000);
        } catch {
            setMessage({ type: 'error', text: 'Termination failed.' });
        } finally {
            setIsStopping(false);
        }
    };

    const isBusy = isTraining || isUploading || ['PENDING', 'PROCESSING', 'INDEXING'].includes(status);

    return (
        <div className="flex flex-col gap-6 lg:gap-8">
            {/* Data Acquisition - Full Width at Top */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full p-6 lg:p-8 rounded-[32px] glass-card flex flex-col relative overflow-hidden group"
            >
                <div className="absolute top-0 right-0 p-8 opacity-[0.05] group-hover:opacity-10 transition-opacity">
                    <Binary className="w-40 h-40 -rotate-12" />
                </div>

                <div className="flex items-center gap-4 mb-10 relative z-10">
                    <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                        <Cpu className="w-7 h-7 text-indigo-400" />
                    </div>
                    <div>
                        <h3 className="text-xl font-black text-white tracking-tight">Data Acquisition</h3>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Automated Ingestion Protocol</p>
                    </div>
                </div>

                <div
                    onClick={triggerFileInput}
                    className="flex-1 flex flex-col items-center justify-center p-12 border-2 border-dashed border-slate-800/50 rounded-[40px] hover:border-indigo-500/30 hover:bg-slate-900/10 transition-all group cursor-pointer relative mb-10"
                >
                    <input
                        ref={inputRef}
                        type="file"
                        accept=".zip,.csv,.json,.txt,.pdf,.docx"
                        className="sr-only"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        disabled={isBusy}
                    />
                    <div className="w-20 h-20 rounded-[28px] bg-slate-950 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-2xl border border-slate-800/30">
                        <FileText className="w-10 h-10 text-slate-700 group-hover:text-indigo-500 transition-colors" />
                    </div>
                    {file ? (
                        <div className="text-center">
                            <span className="text-indigo-400 font-black text-lg block mb-1 underline decoration-indigo-500/30">{file.name}</span>
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Ready for synchronization</p>
                        </div>
                    ) : (
                        <div className="text-center">
                            <p className="text-white font-black text-lg">Load Dataset</p>
                            <p className="text-xs text-slate-500 mt-2 font-medium tracking-wide">Sync ZIP, JSON, CSV, PDF, DOCX</p>
                        </div>
                    )}
                </div>

                <button
                    onClick={handleFileUpload}
                    disabled={!file || isBusy}
                    className="w-full py-5 px-6 bg-slate-950 border border-slate-800 hover:border-indigo-500/50 text-white font-black rounded-3xl flex items-center justify-center gap-3 transition-all active:scale-95 disabled:opacity-30 disabled:hover:border-slate-800 shadow-2xl uppercase tracking-widest text-xs"
                >
                    {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Upload className="w-5 h-5 text-indigo-500" />}
                    Execute Ingestion
                </button>
            </motion.div>

            {/* Core Execution - Full Width Below */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full p-6 lg:p-8 rounded-[32px] glass-card flex flex-col relative overflow-hidden group bg-gradient-to-br from-slate-900/40 to-slate-900/10"
            >
                <div className="flex items-center gap-4 mb-10 relative z-10">
                    <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                        <FastForward className="w-7 h-7 text-emerald-400" />
                    </div>
                    <div>
                        <h3 className="text-xl font-black text-white tracking-tight">Core Execution</h3>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Full Re-Indexing Protocol</p>
                    </div>
                </div>

                <div className="flex-1 space-y-4 mb-6">
                    <div className="flex flex-col gap-4">
                        <div className="p-6 rounded-[24px] bg-slate-950/80 border border-slate-800/50 flex flex-col gap-3 overflow-hidden">
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Neural Node</p>
                            <div className="flex items-start gap-4">
                                <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 shrink-0">
                                    <BrainCircuit className="w-6 h-6 text-indigo-400" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-white font-black text-lg leading-tight">{activeAgent.name}</p>
                                    <p className="text-[10px] text-indigo-500/80 font-bold uppercase tracking-widest mt-1">Version {activeAgent.version}</p>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 rounded-[24px] bg-slate-950/80 border border-slate-800/50 flex flex-col gap-3 overflow-hidden">
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Live Status</p>
                            <div className="flex items-start gap-4">
                                <div className={cn(
                                    "w-12 h-12 rounded-xl flex items-center justify-center border shrink-0",
                                    isBusy ? "bg-amber-500/10 border-amber-500/20 text-amber-500" : "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
                                )}>
                                    {isBusy ? <Loader2 className="w-6 h-6 animate-spin" /> : <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-white font-black text-lg leading-tight uppercase">{status !== 'IDLE' ? status : activeAgent.status}</p>
                                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Ready for Run Sequence</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Live Training Logs */}
                    <div className="p-4 md:p-6 rounded-2xl md:rounded-[32px] bg-slate-950 border border-slate-800/50">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <Terminal className="w-4 h-4 text-emerald-400" />
                                <p className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Live Training Logs</p>
                            </div>
                            <div className="flex items-center gap-1.5">
                                <div className={cn("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500 animate-pulse" : "bg-slate-600")} />
                                <span className="text-[9px] text-slate-500 font-medium">{isConnected ? 'Connected' : 'Offline'}</span>
                            </div>
                        </div>
                        <div ref={logsContainerRef} className="h-32 md:h-40 overflow-y-auto custom-scrollbar bg-black/30 rounded-xl p-3 font-mono text-[10px] md:text-[11px] space-y-1">
                            {logs.length === 0 ? (
                                <p className="text-slate-600 italic">Waiting for training activity...</p>
                            ) : (
                                logs.slice(-50).map((log, i) => (
                                    <div key={i} className={cn(
                                        "leading-relaxed",
                                        log.level === 'ERROR' && 'text-rose-400',
                                        log.level === 'WARNING' && 'text-amber-400',
                                        log.level === 'INFO' && 'text-emerald-400',
                                        log.level === 'DEBUG' && 'text-slate-500',
                                        log.level === 'SYSTEM' && 'text-indigo-400'
                                    )}>
                                        <span className="text-slate-600">[{new Date(log.timestamp).toLocaleTimeString()}]</span> {log.message}
                                    </div>
                                ))
                            )}

                        </div>
                    </div>

                    <div className="p-8 rounded-[32px] border border-slate-800/30 bg-white/[0.02] flex flex-col gap-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                                <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">Knowledge Base Size</span>
                            </div>
                            <div className="flex items-center gap-6">
                                <span className="text-sm font-black text-indigo-400">{vectorCount} Vectors Indexed</span>
                            </div>
                        </div>

                        <div className="pt-6 border-t border-slate-800/20">
                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4 block">
                                Embedding Architecture
                            </label>
                            <div className="relative">
                                <div className="w-full bg-slate-950 border border-slate-800 rounded-2xl px-5 py-4 text-white font-bold text-sm flex items-center justify-between">
                                    <span>
                                        {config.embedding_model || 'Loading Model Config...'}
                                        {config.embedding_dimension ? ` (${config.embedding_dimension}-dim)` : ''}
                                    </span>
                                    <Cpu className="w-4 h-4 text-slate-500" />
                                </div>
                            </div>
                            <p className="text-[10px] text-emerald-500 font-medium mt-3 leading-relaxed">
                                <span className="font-bold uppercase tracking-wide">Production Ready:</span> Using configured backend model settings.
                            </p>
                        </div>
                    </div>
                </div>

                {
                    message && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`mb-6 p-5 rounded-2xl flex items-center gap-4 text-sm font-bold border ${message.type === 'success' ? 'bg-emerald-500/5 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/5 text-rose-400 border-rose-500/20'
                                }`}
                        >
                            {message.type === 'success' ? <CheckCircle2 className="w-5 h-5 shrink-0" /> : <AlertCircle className="w-5 h-5 shrink-0" />}
                            {message.text}
                        </motion.div>
                    )
                }

                <div className="flex gap-4">
                    <button
                        onClick={handleStartTraining}
                        disabled={isBusy}
                        className="flex-1 py-6 px-8 bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-700 hover:from-emerald-500 hover:to-cyan-600 disabled:opacity-30 text-white font-black rounded-3xl flex items-center justify-center gap-4 transition-all active:scale-[0.98] shadow-[0_20px_40px_rgba(16,185,129,0.2)] uppercase tracking-[0.2em] text-sm"
                    >
                        {isBusy ? (
                            <>
                                <Loader2 className="w-6 h-6 animate-spin" />
                                Sequence Active
                            </>
                        ) : (
                            <>
                                <Play className="w-6 h-6 fill-current" />
                                Initiate Full Re-Index
                            </>
                        )}
                    </button>

                    {isBusy && (
                        <button
                            onClick={handleStopTraining}
                            disabled={isStopping}
                            className="px-8 py-6 bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 text-rose-400 font-black rounded-3xl flex items-center justify-center gap-3 transition-all active:scale-95 disabled:opacity-50 uppercase tracking-widest text-xs"
                        >
                            {isStopping ? <Loader2 className="w-4 h-4 animate-spin" /> : <AlertCircle className="w-5 h-5" />}
                            Terminate
                        </button>
                    )}
                </div>
            </motion.div >
        </div >
    );
}
