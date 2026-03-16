import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Loader2, Sparkles, ChevronDown, ChevronUp, Upload, MessageSquare, Briefcase, Brain } from 'lucide-react';

interface TestAgentPanelProps {
    agentId: string;
    agentType: string;
}

export function TestAgentPanel({ agentId, agentType }: TestAgentPanelProps) {
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [debugMode, setDebugMode] = useState(true);
    const [showTrace, setShowTrace] = useState(true);
    const [file, setFile] = useState<File | null>(null);

    const handleTest = async () => {
        if (!query.trim() && !file) return;
        setLoading(true);
        setResponse(null);

        try {
            let res;
            if (file) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('config', JSON.stringify({}));
                res = await fetch(`/api/agents/${agentId}/predict/file`, {
                    method: 'POST',
                    body: formData,
                });
            } else {
                res = await fetch(`/api/agents/${agentId}/predict`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query })
                });
            }
            const data = await res.json();
            setResponse(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const isMatchingAgent = agentId === 'skill_job_matching' || agentType === 'matching';

    return (
        <div className="mt-8 relative">
            {/* Decorative Background Glow */}
            <div className="absolute -top-10 -left-10 w-40 h-40 bg-indigo-500/10 blur-3xl rounded-full pointer-events-none" />
            <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-purple-500/10 blur-3xl rounded-full pointer-events-none" />

            <Card className="relative overflow-hidden backdrop-blur-xl bg-slate-900/80 border border-white/10 rounded-2xl shadow-2xl">
                {/* Header */}
                <div className="p-6 border-b border-white/5 bg-gradient-to-r from-indigo-500/5 to-purple-500/5">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
                                <Sparkles className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white tracking-tight">Test Interface</h3>
                                <p className="text-xs text-slate-400">{isMatchingAgent ? 'Upload resume to find matching jobs' : 'Ask questions to test the agent'}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3 bg-slate-800/50 px-3 py-2 rounded-xl border border-white/5">
                            <label className="text-xs font-medium text-slate-400">Debug</label>
                            <Switch checked={debugMode} onCheckedChange={setDebugMode} />
                        </div>
                    </div>
                </div>

                {/* Input Section */}
                <div className="p-6">
                    <div className="flex gap-3">
                        {isMatchingAgent ? (
                            <div className="flex-1 relative">
                                <div className="relative group">
                                    <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-xl blur-sm group-hover:blur-md transition-all" />
                                    <label className="relative flex flex-col items-center justify-center w-full h-28 border-2 border-dashed border-slate-600 hover:border-indigo-500/50 rounded-xl cursor-pointer bg-slate-800/50 transition-all duration-300">
                                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                            <Upload className={`w-8 h-8 mb-2 ${file ? 'text-green-400' : 'text-slate-400'}`} />
                                            <p className="text-sm text-slate-300 font-medium">
                                                {file ? file.name : 'Click to upload resume'}
                                            </p>
                                            <p className="text-xs text-slate-500 mt-1">PDF, DOCX, or TXT</p>
                                        </div>
                                        <input
                                            type="file"
                                            accept=".pdf,.docx,.txt"
                                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFile(e.target.files?.[0] || null)}
                                            className="hidden"
                                        />
                                    </label>
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 relative group">
                                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 rounded-xl blur-sm opacity-0 group-focus-within:opacity-100 transition-all" />
                                <div className="relative flex items-center">
                                    <MessageSquare className="absolute left-4 w-5 h-5 text-slate-500" />
                                    <Input
                                        placeholder="Ask a question about your documents..."
                                        value={query}
                                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
                                        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleTest()}
                                        className="w-full pl-12 pr-4 py-4 bg-slate-800/50 border-slate-700 hover:border-slate-600 focus:border-indigo-500 rounded-xl text-white placeholder:text-slate-500 transition-all"
                                    />
                                </div>
                            </div>
                        )}

                        <Button
                            onClick={handleTest}
                            disabled={loading}
                            className="h-auto px-6 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-xl shadow-lg shadow-indigo-500/25 transition-all duration-300 hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
                        >
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <span className="flex items-center gap-2">
                                    {isMatchingAgent ? <Briefcase className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
                                    {isMatchingAgent ? 'Match Jobs' : 'Run Query'}
                                </span>
                            )}
                        </Button>
                    </div>
                </div>

                {/* Results Section */}
                {response && (
                    <div className="p-6 pt-0 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

                        {/* Job Matching Results */}
                        {isMatchingAgent && Array.isArray(response.data) ? (
                            <div className="space-y-4">
                                <div className="flex items-center gap-2">
                                    <div className="w-1 h-6 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full" />
                                    <h4 className="text-lg font-bold text-white">Top Matches</h4>
                                    <Badge className="bg-indigo-500/20 text-indigo-300 border-indigo-500/30">{response.data.length} jobs</Badge>
                                </div>

                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                    {response.data.map((job: any, i: number) => (
                                        <div
                                            key={job.job_id || i}
                                            className="group relative overflow-hidden p-5 rounded-xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-white/5 hover:border-indigo-500/30 transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/10"
                                        >
                                            {/* Score Indicator Bar */}
                                            <div className="absolute top-0 left-0 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500" style={{ width: `${(job.match_score || job.score || 0) * 100}%` }} />

                                            <div className="flex justify-between items-start mb-3">
                                                <div className="flex-1">
                                                    <h5 className="font-bold text-white text-base group-hover:text-indigo-300 transition-colors">{job.title || job.job_title}</h5>
                                                    <p className="text-sm text-slate-400 mt-0.5">{job.company}</p>
                                                </div>
                                                <div className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-bold ${(job.match_score || job.score || 0) >= 0.6 ? 'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30' :
                                                    (job.match_score || job.score || 0) >= 0.4 ? 'bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30' :
                                                        'bg-rose-500/15 text-rose-400 ring-1 ring-rose-500/30'
                                                    }`}>
                                                    {((job.match_score || job.score || 0) * 100).toFixed(0)}%
                                                </div>
                                            </div>

                                            <div className="flex flex-wrap gap-1.5">
                                                {(job.matched_skills || job.required_skills || []).slice(0, 6).map((skill: string, idx: number) => (
                                                    <span key={idx} className="text-[11px] bg-slate-700/50 text-slate-300 px-2 py-1 rounded-md border border-slate-600/50">{skill}</span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            /* RAG Answer Display */
                            <div className="space-y-4">
                                <div className="flex items-center gap-2">
                                    <div className="w-1 h-6 bg-gradient-to-b from-emerald-500 to-teal-500 rounded-full" />
                                    <h4 className="text-lg font-bold text-white">Answer</h4>
                                </div>

                                <div className="p-5 rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-white/5">
                                    <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">
                                        {response.data?.answer || response.answer || response.message || JSON.stringify(response.data || response)}
                                    </p>
                                </div>

                                {/* Metrics Grid */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                    <MetricCard label="Confidence" value={response.data?.confidence ?? response.confidence} icon="🎯" />
                                    <MetricCard label="Latency" value={(response.data?.latency_ms ?? response.latency_ms) ? `${response.data?.latency_ms ?? response.latency_ms}ms` : 'N/A'} icon="⚡" />
                                    <MetricCard label="Sources" value={response.data?.sources?.length || response.sources?.length || 0} icon="📚" />
                                    <MetricCard label="Verified" value={(response.data?.verified ?? response.verified) ? 'Yes' : 'No'} icon="✓" />
                                </div>
                            </div>
                        )}

                        {/* Debug Trace Section */}
                        {debugMode && (
                            <div className="rounded-xl overflow-hidden border border-white/5 bg-slate-900/50">
                                <button
                                    onClick={() => setShowTrace(!showTrace)}
                                    className="w-full flex justify-between items-center p-4 bg-slate-800/50 hover:bg-slate-800 text-sm font-medium text-slate-300 transition-colors"
                                >
                                    <span className="flex items-center gap-2">
                                        <span className="text-base">🔬</span>
                                        Execution Trace & Reasoning
                                    </span>
                                    {showTrace ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                </button>

                                {showTrace && (
                                    <div className="p-5 space-y-5 max-h-[400px] overflow-y-auto custom-scrollbar">
                                        {/* Reasoning */}
                                        {(response.data?.reasoning || response.reasoning) && (
                                            <div className="space-y-2">
                                                <h5 className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
                                                    <span>🧠</span> Chain of Thought
                                                </h5>
                                                <div className="pl-4 border-l-2 border-blue-500/30">
                                                    <p className="text-sm text-slate-300 font-mono whitespace-pre-wrap">
                                                        {Array.isArray(response.data?.reasoning || response.reasoning)
                                                            ? (response.data?.reasoning || response.reasoning).map((r: string, i: number) => `${i + 1}. ${r}`).join('\n')
                                                            : (response.data?.reasoning || response.reasoning)}
                                                    </p>
                                                </div>
                                            </div>
                                        )}

                                        {/* RAGAS Metrics */}
                                        {(response.data?.ragas_metrics || response.ragas_metrics) && (
                                            <div className="space-y-2">
                                                <h5 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                                                    <span>📊</span> Quality Metrics
                                                </h5>
                                                <div className="grid grid-cols-2 gap-2">
                                                    {Object.entries(response.data?.ragas_metrics || response.ragas_metrics).map(([key, val]: [string, any]) => (
                                                        <div key={key} className="bg-slate-800/50 p-2 rounded-lg">
                                                            <span className="text-xs text-slate-500 capitalize">{key.replace(/_/g, ' ')}</span>
                                                            <span className="block text-sm font-bold text-slate-200">{typeof val === 'number' ? `${(val * 100).toFixed(1)}%` : val}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Sources */}
                                        {(response.data?.sources || response.sources) && (
                                            <div className="space-y-2">
                                                <h5 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                                                    <span>🗂️</span> Retrieved Sources
                                                </h5>
                                                <div className="space-y-2">
                                                    {(response.data?.sources || response.sources).map((src: any, i: number) => (
                                                        <div key={i} className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                                                            <div className="flex justify-between items-center mb-1">
                                                                <span className="text-xs font-medium text-slate-400">Source {i + 1}</span>
                                                                <Badge variant="outline" className="text-[10px] border-slate-600 text-slate-400">
                                                                    {(src.score * 100).toFixed(0)}% relevance
                                                                </Badge>
                                                            </div>
                                                            <p className="text-xs text-slate-300 line-clamp-2">{src.text || src.text_preview}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </Card>
        </div>
    );
}

function MetricCard({ label, value, icon }: { label: string; value: any; icon?: string }) {
    let displayValue = value;
    if (typeof value === 'number' && value <= 1 && value >= 0 && label !== 'Sources') {
        displayValue = `${(value * 100).toFixed(0)}%`;
    }

    return (
        <div className="p-3 rounded-xl bg-slate-800/50 border border-white/5 hover:border-white/10 transition-colors">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                {icon && <span>{icon}</span>}
                {label}
            </div>
            <div className="text-lg font-bold text-white">{displayValue ?? '—'}</div>
        </div>
    );
}
