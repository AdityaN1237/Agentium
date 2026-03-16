'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Plus, Pencil, Trash2, Loader2, X, Save, Mail, User, FileText, Eye } from 'lucide-react';
import { candidatesApi, Candidate, CandidateCreatePayload } from '@/services/api';
import { cn } from '../../lib/utils';

export default function CandidatesPage() {
    const [items, setItems] = useState<Candidate[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [modalOpen, setModalOpen] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isDeleting, setIsDeleting] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(20);
    const [total, setTotal] = useState(0);
    const [search, setSearch] = useState('');
    const [skillFilter, setSkillFilter] = useState('');
    const [editing, setEditing] = useState<Candidate | null>(null);
    const [form, setForm] = useState<CandidateCreatePayload>({
        name: '',
        email: '',
        current_role: '',
        experience_years: 0,
        skills: [],
        resume_text: ''
    });

    const load = async () => {
        setLoading(true);
        setError(null);
        try {
            const { data } = await candidatesApi.list({
                page,
                page_size: pageSize,
                search: search || undefined,
                skill: skillFilter || undefined
            });
            setItems(data.candidates);
            setTotal(data.total);
        } catch {
            setError('Failed to load candidates');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page, pageSize]);

    const openCreate = () => {
        setEditing(null);
        setForm({
            name: '',
            email: '',
            current_role: '',
            experience_years: 0,
            skills: [],
            resume_text: ''
        });
        setModalOpen(true);
    };

    const openEdit = (c: Candidate) => {
        setEditing(c);
        setForm({
            name: c.name,
            email: c.email || '',
            current_role: c.current_role || '',
            experience_years: c.experience_years || 0,
            skills: c.skills || [],
            resume_text: c.resume_text || ''
        });
        setModalOpen(true);
    };
    const handleSubmit = async () => {
        setIsSaving(true);
        try {
            if (editing) {
                await candidatesApi.update(editing._id, form);
            } else {
                await candidatesApi.create(form);
            }
            setModalOpen(false);
            await load();
        } catch {
            setError('Save failed');
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async (id: string) => {
        setIsDeleting(id);
        try {
            await candidatesApi.delete(id);
            await load();
        } catch {
            setError('Delete failed');
        } finally {
            setIsDeleting(null);
        }
    };

    return (
        <div className="p-8 space-y-8 min-h-screen bg-[#030712] text-slate-200">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                        <Users className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-white tracking-tight">Candidates</h1>
                        <p className="text-slate-400 mt-1">Manage and screen potential recruits.</p>
                    </div>
                </div>
                <button
                    onClick={openCreate}
                    className="px-4 py-2 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-black flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    New Candidate
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search by name or email"
                    className="bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                />
                <input
                    value={skillFilter}
                    onChange={(e) => setSkillFilter(e.target.value)}
                    placeholder="Filter by skill"
                    className="bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                />
                <button
                    onClick={() => { setPage(1); load(); }}
                    className="px-4 py-3 rounded-2xl bg-slate-900 border border-slate-800 text-slate-300 font-black"
                >
                    Apply Filters
                </button>
            </div>

            <div className="rounded-[24px] border border-slate-800 bg-slate-900/30 overflow-hidden">
                <div className="grid grid-cols-6 gap-4 px-6 py-3 border-b border-slate-800 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                    <span>Name</span>
                    <span>Email</span>
                    <span>Role</span>
                    <span>Experience</span>
                    <span>Skills</span>
                    <span className="text-right">Actions</span>
                </div>
                {loading ? (
                    <div className="p-8 text-slate-500 flex items-center justify-center gap-3">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Loading
                    </div>
                ) : error ? (
                    <div className="p-8 text-rose-400">{error}</div>
                ) : items.length === 0 ? (
                    <div className="p-8 text-slate-500">No candidates found.</div>
                ) : (
                    <div className="divide-y divide-slate-800">
                        {items.map((c) => (
                            <div key={c._id} className="grid grid-cols-6 gap-4 px-6 py-4">
                                <span className="font-bold text-white">{c.name}</span>
                                <span className="text-slate-400">{c.email || '—'}</span>
                                <span className="text-slate-400">{c.current_role || '—'}</span>
                                <span className="text-slate-400">{c.experience_years ?? 0} yrs</span>
                                <span className="text-slate-400 truncate">{(c.skills || []).join(', ')}</span>
                                <div className="flex justify-end gap-2">
                                    <Link
                                        href={`/candidates/${c._id}`}
                                        className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-indigo-400 hover:border-indigo-500/30"
                                    >
                                        <Eye className="w-4 h-4" />
                                    </Link>
                                    <button
                                        onClick={() => openEdit(c)}
                                        className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-indigo-400 hover:border-indigo-500/30"
                                    >
                                        <Pencil className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(c._id)}
                                        disabled={isDeleting === c._id}
                                        className={cn(
                                            "px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-rose-400 hover:border-rose-500/30",
                                            isDeleting === c._id && "opacity-50"
                                        )}
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
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

            <AnimatePresence>
                {modalOpen && (
                    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setModalOpen(false)}
                            className="absolute inset-0 bg-slate-950/80 backdrop-blur-xl"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.97, y: 10 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.97, y: 10 }}
                            className="relative w-full max-w-2xl glass-card rounded-[40px] overflow-hidden border border-white/10 shadow-2xl"
                        >
                            <div className="p-8 md:p-10 space-y-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                                            <Users className="w-7 h-7 text-indigo-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-2xl font-black text-white tracking-tight">{editing ? 'Edit Candidate' : 'New Candidate'}</h3>
                                            <p className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] mt-1">Profile</p>
                                        </div>
                                    </div>
                                    <button onClick={() => setModalOpen(false)} className="p-3 hover:bg-white/5 rounded-full transition-colors text-slate-500">
                                        <X className="w-6 h-6" />
                                    </button>
                                </div>

                                {error && (
                                    <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 font-bold text-sm">
                                        {error}
                                    </div>
                                )}

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Name</label>
                                        <div className="flex items-center gap-2 bg-slate-900/50 border border-slate-800 rounded-2xl px-3">
                                            <User className="w-4 h-4 text-slate-600" />
                                            <input
                                                value={form.name}
                                                onChange={(e) => setForm({ ...form, name: e.target.value })}
                                                className="w-full bg-transparent py-3 px-1 text-white focus:outline-none"
                                                placeholder="Full name"
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Email</label>
                                        <div className="flex items-center gap-2 bg-slate-900/50 border border-slate-800 rounded-2xl px-3">
                                            <Mail className="w-4 h-4 text-slate-600" />
                                            <input
                                                value={form.email}
                                                onChange={(e) => setForm({ ...form, email: e.target.value })}
                                                className="w-full bg-transparent py-3 px-1 text-white focus:outline-none"
                                                placeholder="Email"
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Current Role</label>
                                        <input
                                            value={form.current_role || ''}
                                            onChange={(e) => setForm({ ...form, current_role: e.target.value })}
                                            className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                                            placeholder="e.g., Senior Engineer"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Experience Years</label>
                                        <input
                                            type="number"
                                            value={form.experience_years || 0}
                                            onChange={(e) => setForm({ ...form, experience_years: Number(e.target.value) })}
                                            className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                                        />
                                    </div>
                                    <div className="col-span-2 space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Skills</label>
                                        <input
                                            value={(form.skills || []).join(', ')}
                                            onChange={(e) => setForm({ ...form, skills: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })}
                                            className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                                            placeholder="Comma separated skills"
                                        />
                                    </div>
                                    <div className="col-span-2 space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Resume Text</label>
                                        <div className="flex items-start gap-2 bg-slate-900/50 border border-slate-800 rounded-2xl px-3">
                                            <FileText className="w-4 h-4 text-slate-600 mt-3" />
                                            <textarea
                                                value={form.resume_text}
                                                onChange={(e) => setForm({ ...form, resume_text: e.target.value })}
                                                className="w-full bg-transparent py-3 px-1 text-white focus:outline-none min-h-[120px]"
                                                placeholder="Paste resume text"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="flex justify-end gap-3 pt-2">
                                    <button
                                        onClick={() => setModalOpen(false)}
                                        className="px-4 py-3 rounded-2xl bg-slate-900 border border-slate-800 text-slate-300 font-black"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleSubmit}
                                        disabled={isSaving}
                                        className={cn(
                                            "px-4 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-black flex items-center gap-2",
                                            isSaving && "opacity-50"
                                        )}
                                    >
                                        {isSaving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
                                        Save
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}
