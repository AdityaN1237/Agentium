'use client';

import { useState } from 'react';
import { Bot } from 'lucide-react';
import { agentApi, MatchedJob } from '@/services/api';
import axios from 'axios';

export function FileValidation({ agentId }: { agentId: string }) {
    const [file, setFile] = useState<File | null>(null);
    const [result, setResult] = useState<MatchedJob[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const { data } = await agentApi.predictFile(agentId, file);
            setResult(data);
        } catch (err: unknown) {
            if (axios.isAxiosError(err)) {
                setError(err.response?.data?.detail || "Validation failed");
            } else {
                setError("An unexpected error occurred");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-full p-8 flex flex-col gap-6 overflow-y-auto custom-scrollbar">
            <div className="bg-slate-900/50 border-2 border-dashed border-slate-700 rounded-2xl p-12 flex flex-col items-center justify-center text-center hover:border-indigo-500/50 transition-colors group">
                <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4 group-hover:bg-indigo-500/20 transition-colors">
                    <Bot className="w-8 h-8 text-slate-400 group-hover:text-indigo-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Upload Resume for Validation</h3>
                <p className="text-slate-400 mb-6 max-w-md">
                    Upload a PDF or DOCX resume to test the matching algorithm against the current active job index.
                </p>
                <div className="relative">
                    <input
                        type="file"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        accept=".pdf,.docx,.txt"
                    />
                    <button className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-colors shadow-lg shadow-indigo-600/20">
                        {file ? file.name : "Select Resume File"}
                    </button>
                </div>
            </div>

            {file && (
                <div className="flex justify-end">
                    <button
                        onClick={handleUpload}
                        disabled={loading}
                        className="bg-emerald-500 hover:bg-emerald-400 text-white font-bold py-3 px-8 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {loading ? 'Processing...' : 'Run Analysis'}
                    </button>
                </div>
            )}

            {error && (
                <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-sm font-medium">
                    {error}
                </div>
            )}

            {result && (
                <div className="bg-slate-950 rounded-2xl border border-white/10 p-6 space-y-4">
                    <div className="flex items-center justify-between pb-4 border-b border-white/5">
                        <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Analysis Results</h4>
                        <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">
                            {Array.isArray(result) ? result.length : 0} Matches Found
                        </span>
                    </div>

                    <div className="space-y-3">
                        {Array.isArray(result) ? result.map((job: MatchedJob, i: number) => (
                            <div key={i} className="bg-white/5 rounded-xl p-4 hover:bg-white/10 transition-colors border border-transparent hover:border-indigo-500/30">
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <div className="font-bold text-indigo-300">{job.title}</div>
                                        <div className="text-sm text-slate-400">{job.company}</div>
                                    </div>
                                    <div className="text-xl font-black text-white">{Math.round(job.score * 100)}%</div>
                                </div>
                                <div className="flex flex-wrap gap-2 mt-3">
                                    {job.required_skills?.slice(0, 5).map((skill: string, idx: number) => (
                                        <span key={idx} className="text-[10px] bg-black/30 text-slate-300 px-2 py-1 rounded border border-white/5">
                                            {skill}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )) : (
                            <pre className="text-xs text-slate-500 overflow-auto max-h-60">
                                {JSON.stringify(result, null, 2)}
                            </pre>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
