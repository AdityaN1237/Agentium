'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Briefcase, Plus, Pencil, Trash2, Loader2, X, Save, Building2, MapPin, Eye } from 'lucide-react';
import { jobsApi, Job, JobCreatePayload } from '@/services/api';
import { cn } from '../../lib/utils';

export default function JobsPage() {
    const [items, setItems] = useState<Job[]>([]);
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
    const [companyFilter, setCompanyFilter] = useState('');
    const [locationFilter, setLocationFilter] = useState('');
    const [editing, setEditing] = useState<Job | null>(null);
    const [form, setForm] = useState<JobCreatePayload>({
        title: '',
        company: '',
        location: '',
        description: '',
        required_skills: [],
        nice_to_have: [],
        is_active: true
    });

    const load = async () => {
        setLoading(true);
        setError(null);
        try {
            const { data } = await jobsApi.list({
                page,
                page_size: pageSize,
                search: search || undefined,
                skill: skillFilter || undefined,
                company: companyFilter || undefined,
                location: locationFilter || undefined
            });
            setItems(data.jobs);
            setTotal(data.total);
        } catch {
            setError('Failed to load jobs');
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
            title: '',
            company: '',
            location: '',
            description: '',
            required_skills: [],
            nice_to_have: [],
            is_active: true
        });
        setModalOpen(true);
    };

    const openEdit = (j: Job) => {
        setEditing(j);
        setForm({
            title: j.title,
            company: j.company || '',
            location: j.location || '',
            description: j.description || '',
            required_skills: j.required_skills || [],
            nice_to_have: j.nice_to_have || [],
            is_active: j.is_active ?? true
        });
        setModalOpen(true);
    };
    const handleSubmit = async () => {
        setIsSaving(true);
        try {
            if (editing) {
                await jobsApi.update(editing._id, form);
            } else {
                await jobsApi.create(form);
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
            await jobsApi.delete(id);
            await load();
        } catch {
            setError('Delete failed');
        } finally {
            setIsDeleting(null);
        }
    };

    const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize]);

    return (
        <div className="p-8 space-y-8 min-h-screen bg-[#030712] text-slate-200">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                        <Briefcase className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-white tracking-tight">Jobs</h1>
                        <p className="text-slate-400 mt-1">Active requisitions and skill taxonomies.</p>
                    </div>
                </div>
                <button
                    onClick={openCreate}
                    className="px-4 py-2 rounded-2xl bg-purple-600 hover:bg-purple-500 text-white font-black flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    New Job
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search title/description"
                    className="bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                />
                <input
                    value={skillFilter}
                    onChange={(e) => setSkillFilter(e.target.value)}
                    placeholder="Filter by required skill"
                    className="bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                />
                <input
                    value={companyFilter}
                    onChange={(e) => setCompanyFilter(e.target.value)}
                    placeholder="Filter by company"
                    className="bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                />
                <input
                    value={locationFilter}
                    onChange={(e) => setLocationFilter(e.target.value)}
                    placeholder="Filter by location"
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
                    <span>Title</span>
                    <span>Company</span>
                    <span>Location</span>
                    <span>Status</span>
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
                    <div className="p-8 text-slate-500">No jobs found.</div>
                ) : (
                    <div className="divide-y divide-slate-800">
                        {items.map((j) => (
                            <div key={j._id} className="grid grid-cols-6 gap-4 px-6 py-4">
                                <span className="font-bold text-white">{j.title}</span>
                                <span className="text-slate-400">{j.company || '—'}</span>
                                <span className="text-slate-400">{j.location || '—'}</span>
                                <span className={cn("font-bold", j.is_active ? "text-emerald-400" : "text-rose-400")}>
                                    {j.is_active ? 'Active' : 'Inactive'}
                                </span>
                                <span className="text-slate-400 truncate">{(j.required_skills || []).join(', ')}</span>
                                <div className="flex justify-end gap-2">
                                    <Link
                                        href={`/jobs/${j._id}`}
                                        className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-purple-400 hover:border-purple-500/30"
                                    >
                                        <Eye className="w-4 h-4" />
                                    </Link>
                                    <button
                                        onClick={() => openEdit(j)}
                                        className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-purple-400 hover:border-purple-500/30"
                                    >
                                        <Pencil className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(j._id)}
                                        disabled={isDeleting === j._id}
                                        className={cn(
                                            "px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-rose-400 hover:border-rose-500/30",
                                            isDeleting === j._id && "opacity-50"
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
                    <span className="text-xs text-slate-400">{page} / {totalPages}</span>
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
                                        <div className="w-12 h-12 rounded-2xl bg-purple-500/20 flex items-center justify-center border border-purple-500/30">
                                            <Briefcase className="w-7 h-7 text-purple-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-2xl font-black text-white tracking-tight">{editing ? 'Edit Job' : 'New Job'}</h3>
                                            <p className="text-[10px] font-black text-purple-400 uppercase tracking-[0.2em] mt-1">Requisition</p>
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
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Title</label>
                                        <input
                                            value={form.title}
                                            onChange={(e) => setForm({ ...form, title: e.target.value })}
                                            className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                                            placeholder="Role title"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Company</label>
                                        <div className="flex items-center gap-2 bg-slate-900/50 border border-slate-800 rounded-2xl px-3">
                                            <Building2 className="w-4 h-4 text-slate-600" />
                                            <input
                                                value={form.company || ''}
                                                onChange={(e) => setForm({ ...form, company: e.target.value })}
                                                className="w-full bg-transparent py-3 px-1 text-white focus:outline-none"
                                                placeholder="Company"
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Location</label>
                                        <div className="flex items-center gap-2 bg-slate-900/50 border border-slate-800 rounded-2xl px-3">
                                            <MapPin className="w-4 h-4 text-slate-600" />
                                            <input
                                                value={form.location || ''}
                                                onChange={(e) => setForm({ ...form, location: e.target.value })}
                                                className="w-full bg-transparent py-3 px-1 text-white focus:outline-none"
                                                placeholder="Location"
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Status</label>
                                        <select
                                            value={form.is_active ? 'active' : 'inactive'}
                                            onChange={(e) => setForm({ ...form, is_active: e.target.value === 'active' })}
                                            className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                                        >
                                            <option value="active">Active</option>
                                            <option value="inactive">Inactive</option>
                                        </select>
                                    </div>
                                    <div className="col-span-2 space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Description</label>
                                        <textarea
                                            value={form.description || ''}
                                            onChange={(e) => setForm({ ...form, description: e.target.value })}
                                            className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white min-h-[120px]"
                                            placeholder="Job description"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Required Skills</label>
                                        <input
                                            value={(form.required_skills || []).join(', ')}
                                            onChange={(e) => setForm({ ...form, required_skills: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })}
                                            className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                                            placeholder="Comma separated"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Nice To Have</label>
                                        <input
                                            value={(form.nice_to_have || []).join(', ')}
                                            onChange={(e) => setForm({ ...form, nice_to_have: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })}
                                            className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white"
                                            placeholder="Comma separated"
                                        />
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
                                            "px-4 py-3 rounded-2xl bg-purple-600 hover:bg-purple-500 text-white font-black flex items-center gap-2",
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
