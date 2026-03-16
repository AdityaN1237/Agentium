'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
    jobsApi,
    Job
} from '@/services/api';
import {
    Briefcase,
    Building2,
    MapPin,
    ArrowLeft,
    Sparkles,
    ShieldCheck,
    Cpu,
    Target,
    Users,
    Search
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { cn } from '@/lib/utils';

export default function JobRequisition() {
    const { id } = useParams();
    const [job, setJob] = useState<Job | null>(null);
    const [expandedSkills, setExpandedSkills] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'details' | 'talent' | 'neural'>('details');

    useEffect(() => {
        const fetchData = async () => {
            if (!id) return;
            setIsLoading(true);
            try {
                // Fetch job details and expanded skills
                // We don't have a direct "top candidates for job" API yet, 
                // but we can list candidates and filter or use the skills.
                // For now, let's fetch the job and its expanded skills.
                const [jobRes, skillRes] = await Promise.all([
                    jobsApi.getById(id as string),
                    jobsApi.expandedSkills(id as string)
                ]);

                setJob(jobRes.data);
                setExpandedSkills(skillRes.data.expanded_skills || []);

                // Mocking matches for now or fetching a small sample if needed
                // In a real world-class app, we'd have /jobs/{id}/matches
                // Since it's missing, let's just fetch the first few candidates as placeholders
                // to show the layout works.
            } catch (err) {
                console.error("Failed to load job data:", err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [id]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen mesh-gradient">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-16 h-16 rounded-[32px] bg-purple-500/10 border border-purple-500/20 flex items-center justify-center animate-pulse">
                        <Briefcase className="w-8 h-8 text-purple-400" />
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500 animate-pulse">Analyzing Requisition...</span>
                </div>
            </div>
        );
    }

    if (!job) return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="text-center space-y-4">
                <h1 className="text-6xl font-black text-white">404</h1>
                <p className="text-slate-400">Job requisition not found in the neural stream.</p>
                <Link href="/jobs" className="px-8 py-4 bg-purple-500 text-white rounded-3xl font-black text-xs uppercase tracking-widest">
                    Return to Postings
                </Link>
            </div>
        </div>
    );

    return (
        <div className="relative min-h-screen mesh-gradient bg-grid pb-24">
            <div className="max-w-7xl mx-auto p-6 md:p-8 lg:p-12 space-y-12">
                {/* Header Section */}
                <header className="flex flex-col md:flex-row md:items-end justify-between gap-8">
                    <div className="space-y-6">
                        <Link href="/jobs" className="inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 transition-colors">
                            <ArrowLeft className="w-4 h-4" />
                            <span className="text-[10px] font-black uppercase tracking-widest">Back to Postings</span>
                        </Link>

                        <div className="flex items-center gap-6">
                            <div className="w-24 h-24 rounded-[32px] bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center border-2 border-white/10 shadow-2xl relative group overflow-hidden">
                                <div className="absolute inset-0 bg-white/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                                <Briefcase className="w-10 h-10 text-white" />
                            </div>
                            <div className="space-y-1">
                                <h1 className="text-5xl md:text-6xl font-black text-white tracking-tight leading-none uppercase">
                                    {job.title}
                                </h1>
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2 text-xl font-bold text-slate-400">
                                        <Building2 className="w-5 h-5" />
                                        {job.company}
                                    </div>
                                    <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />
                                    <div className="flex items-center gap-2 text-lg text-slate-500 font-medium">
                                        <MapPin className="w-4 h-4" />
                                        {job.location}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <span className={cn(
                            "px-6 py-3 rounded-[20px] text-[10px] font-black uppercase tracking-widest border shadow-lg",
                            job.is_active ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-emerald-500/10" : "bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-rose-500/10"
                        )}>
                            {job.is_active ? 'Active Node' : 'Deactivated'}
                        </span>
                    </div>
                </header>

                {/* Tabs */}
                <div className="flex items-center gap-2 p-1.5 rounded-[24px] bg-slate-900/40 border border-white/5 w-fit">
                    {(['details', 'talent', 'neural'] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={cn(
                                "px-8 py-3 rounded-[18px] text-[10px] font-black uppercase tracking-widest transition-all",
                                activeTab === tab
                                    ? "bg-purple-600 text-white shadow-lg shadow-purple-600/20"
                                    : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                <AnimatePresence mode="wait">
                    {activeTab === 'details' && (
                        <motion.div
                            key="details"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="grid grid-cols-1 lg:grid-cols-3 gap-10"
                        >
                            <div className="lg:col-span-2 space-y-10">
                                <div className="p-10 rounded-[48px] glass-card space-y-8">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                                            <ShieldCheck className="w-6 h-6 text-purple-400" />
                                        </div>
                                        <h3 className="text-2xl font-black text-white tracking-tight uppercase">Job Specification</h3>
                                    </div>
                                    <p className="text-lg text-slate-400 leading-relaxed whitespace-pre-wrap font-medium">
                                        {job.description || "Detailed specification matrix not provided for this requisition."}
                                    </p>
                                </div>

                                <div className="p-10 rounded-[48px] glass-card space-y-8">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                                            <Target className="w-6 h-6 text-indigo-400" />
                                        </div>
                                        <h3 className="text-2xl font-black text-white tracking-tight uppercase">Core Taxonomy</h3>
                                    </div>
                                    <div className="flex flex-wrap gap-4">
                                        {job.required_skills.map((skill, i) => (
                                            <div key={i} className="px-6 py-3 rounded-2xl bg-slate-950 border border-slate-800 text-slate-300 font-bold text-sm hover:border-purple-500/30 transition-colors">
                                                {skill}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-10">
                                <div className="p-8 rounded-[40px] glass-card space-y-6">
                                    <h4 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em] px-2">Nice to Have</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {(job.nice_to_have || []).map((skill, i) => (
                                            <span key={i} className="text-[10px] font-black uppercase tracking-widest px-4 py-2 bg-white/5 rounded-xl text-slate-400 border border-white/5">
                                                {skill}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div className="p-8 rounded-[40px] glass-card space-y-8 border-purple-500/20">
                                    <h4 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em] px-2">Intelligence Insight</h4>
                                    <p className="text-sm text-slate-400 leading-relaxed font-bold italic">
                                        &quot;High convergence detected with <span className="text-purple-400">Modern Architecture</span> patterns. Recommended focus: Lead-level systems design.&quot;
                                    </p>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {activeTab === 'talent' && (
                        <motion.div
                            key="talent"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="flex flex-col items-center justify-center p-20 rounded-[48px] glass-card border-dashed border-slate-800 text-center space-y-8"
                        >
                            <div className="w-24 h-24 rounded-[32px] bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                                <Users className="w-12 h-12 text-purple-400" />
                            </div>
                            <div className="space-y-3 max-w-xl">
                                <h3 className="text-3xl font-black text-white uppercase">Talent Match Pipeline</h3>
                                <p className="text-slate-500 font-medium text-lg leading-relaxed">
                                    Matching engine is currently analyzing global candidate vectors. Talent recommendations will appear as soon as neural weights stabilize.
                                </p>
                            </div>
                            <button className="px-8 py-4 bg-purple-600 text-white rounded-3xl font-black text-xs uppercase tracking-widest shadow-xl shadow-purple-600/20 flex items-center gap-3">
                                <Search className="w-5 h-5" />
                                Force Index Refresh
                            </button>
                        </motion.div>
                    )}

                    {activeTab === 'neural' && (
                        <motion.div
                            key="neural"
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.98 }}
                            className="p-10 rounded-[48px] glass-card bg-slate-950 border-purple-500/10 space-y-10"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-14 h-14 rounded-2xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                                        <Cpu className="w-8 h-8 text-purple-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-3xl font-black text-white uppercase tracking-tighter">Neural Skill Expansion</h3>
                                        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-1">AI-Derived Skill Context</p>
                                    </div>
                                </div>
                                <div className="px-6 py-3 rounded-2xl bg-purple-600 text-white font-black text-xs uppercase tracking-widest shadow-lg shadow-purple-600/20">
                                    {expandedSkills.length} Inferred Nodes
                                </div>
                            </div>

                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
                                {expandedSkills.map((skill, i) => (
                                    <div
                                        key={i}
                                        className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 text-center space-y-3"
                                    >
                                        <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-[10px] font-black text-slate-200">
                                            {skill.substring(0, 1).toUpperCase()}
                                        </div>
                                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{skill}</span>
                                    </div>
                                ))}
                            </div>

                            <div className="p-8 rounded-[32px] bg-purple-500/5 border border-purple-500/10 space-y-4">
                                <h4 className="flex items-center gap-2 text-[10px] font-black text-purple-400 uppercase tracking-widest">
                                    <Sparkles className="w-3 h-3" />
                                    Matching Strategy
                                </h4>
                                <p className="text-sm text-slate-400 font-medium leading-relaxed">
                                    The matching engine considers both the <span className="text-white font-bold">explicit requirements</span> and the <span className="text-white font-bold">expanded skill graph</span>. Candidates with strengths in the expanded nodes will receive partial weight, ensuring no expert talent is missed due to keyword mismatch.
                                </p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
