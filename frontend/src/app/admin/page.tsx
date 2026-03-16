'use client';

import { useEffect, useState } from 'react';
import { Shield, Loader2 } from 'lucide-react';
import { resumesApi, ResumeRecord } from '@/services/api';

export default function AdminPage() {
    const [items, setItems] = useState<ResumeRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(20);
    const [total, setTotal] = useState(0);

    const load = async () => {
        setLoading(true);
        setError(null);
        try {
            const { data } = await resumesApi.list({ page, page_size: pageSize });
            setItems(data.resumes);
            setTotal(data.total);
        } catch {
            setError('Failed to load resumes');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page, pageSize]);

    return (
        <div className="p-8 space-y-8 min-h-screen bg-[#030712] text-slate-200">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                    <Shield className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                    <h1 className="text-3xl font-black text-white tracking-tight">Admin: User Resumes</h1>
                    <p className="text-slate-400 mt-1">View resumes uploaded by all users.</p>
                </div>
            </div>

            <div className="rounded-[24px] border border-slate-800 bg-slate-900/30 overflow-hidden">
                <div className="grid grid-cols-5 gap-4 px-6 py-3 border-b border-slate-800 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                    <span>User</span>
                    <span>Filename</span>
                    <span>Type</span>
                    <span>Skills</span>
                    <span className="text-right">Uploaded</span>
                </div>
                {loading ? (
                    <div className="p-8 text-slate-500 flex items-center justify-center gap-3">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Loading
                    </div>
                ) : error ? (
                    <div className="p-8 text-rose-400">{error}</div>
                ) : items.length === 0 ? (
                    <div className="p-8 text-slate-500">No resumes found.</div>
                ) : (
                    <div className="divide-y divide-slate-800">
                        {items.map((r) => (
                            <div key={r._id} className="grid grid-cols-5 gap-4 px-6 py-4">
                                <span className="text-slate-300">{r.user_id}</span>
                                <span className="text-white font-bold">{r.filename}</span>
                                <span className="text-slate-400">{r.content_type}</span>
                                <span className="text-slate-400 truncate">{(r.extracted_skills || []).join(', ')}</span>
                                <span className="text-slate-400 text-right">{new Date(r.created_at || '').toLocaleString() || '—'}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Total: {total}</span>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        className="px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-50"
                        disabled={page <= 1}
                    >
                        Prev
                    </button>
                    <span className="text-xs text-slate-400">{page} / {Math.max(1, Math.ceil(total / pageSize))}</span>
                    <button
                        onClick={() => setPage((p) => p + 1)}
                        className="px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-50"
                        disabled={items.length < pageSize}
                    >
                        Next
                    </button>
                </div>
            </div>
        </div>
    );
}
