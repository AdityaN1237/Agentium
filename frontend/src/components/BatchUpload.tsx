'use client';

import { useState } from 'react';
import { FolderUp, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';
import { resumesApi } from '@/services/api';
import { motion } from 'framer-motion';
import axios from 'axios';

export function BatchUpload() {
    const [directory, setDirectory] = useState('');
    const [status, setStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');

    const handleBatchProcess = async () => {
        if (!directory) return;
        setStatus('processing');
        try {
            const { data } = await resumesApi.batchProcess(directory);
            setStatus('success');
            setMessage((data as { message?: string }).message || 'Batch processing started');
        } catch (err: unknown) {
            setStatus('error');
            if (axios.isAxiosError(err)) {
                setMessage(err.response?.data?.detail || 'Failed to start batch processing');
            } else {
                setMessage('An unexpected error occurred');
            }
        }
    };

    return (
        <div className="p-6 rounded-[32px] glass-card border border-slate-800 space-y-6">
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                    <FolderUp className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                    <h3 className="text-xl font-black text-white">Batch Resume Ingest</h3>
                    <p className="text-sm text-slate-400">Process directory of PDFs</p>
                </div>
            </div>

            <div className="space-y-4">
                <div>
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest pl-1">
                        Server Directory Path
                    </label>
                    <input
                        value={directory}
                        onChange={(e) => setDirectory(e.target.value)}
                        placeholder="/app/data/resumes"
                        className="w-full mt-2 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-sm"
                    />
                </div>

                <button
                    onClick={handleBatchProcess}
                    disabled={status === 'processing' || !directory}
                    className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-black rounded-xl transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2"
                >
                    {status === 'processing' ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span>Processing...</span>
                        </>
                    ) : (
                        <span>Start Batch Job</span>
                    )}
                </button>

                {status === 'success' && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-3 text-emerald-400">
                        <CheckCircle className="w-5 h-5 shrink-0" />
                        <span className="text-sm font-bold">{message}</span>
                    </motion.div>
                )}

                {status === 'error' && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-400">
                        <AlertTriangle className="w-5 h-5 shrink-0" />
                        <span className="text-sm font-bold">{message}</span>
                    </motion.div>
                )}
            </div>
        </div>
    );
}
