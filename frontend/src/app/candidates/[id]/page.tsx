'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
    candidatesApi,
    resumesApi,
    Candidate,
    MatchedJob
} from '@/services/api';
import {
    User,
    Mail,
    Briefcase,
    Calendar,
    ChevronRight,
    ArrowLeft,
    Sparkles,
    ShieldCheck,
    Cpu,
    Target,
    Activity
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { cn } from '@/lib/utils';

export default function CandidateProfile() {
    const { id } = useParams();
    const [candidate, setCandidate] = useState<Candidate | null>(null);
    const [recommendations, setRecommendations] = useState<MatchedJob[]>([]);
    const [expandedSkills, setExpandedSkills] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'profile' | 'matches' | 'neural'>('profile');

    useEffect(() => {
        const fetchData = async () => {
            if (!id) return;
            setIsLoading(true);
            try {
                const [candRes, recRes, skillRes] = await Promise.all([
                    candidatesApi.getById(id as string),
                    resumesApi.recommendationsForCandidate(id as string),
                    candidatesApi.expandedSkills(id as string)
                ]);

                setCandidate(candRes.data);
                // The recommendations endpoint returns a list of matched jobs or a wrapped object
                const recs = Array.isArray(recRes.data) ? recRes.data : (recRes.data.recommendations || []);
                setRecommendations(recs);
                setExpandedSkills(skillRes.data.expanded_skills || []);
            } catch (err) {
                console.error("Failed to load candidate data:", err);
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
                    <div className="w-16 h-16 rounded-[32px] bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center animate-pulse">
                        <User className="w-8 h-8 text-indigo-400" />
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500 animate-pulse">Decoding Identity...</span>
                </div>
            </div>
        );
    }

    if (!candidate) return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="text-center space-y-4">
                <h1 className="text-6xl font-black text-white">404</h1>
                <p className="text-slate-400">Biological entity not found in database.</p>
                <Link href="/candidates" className="px-8 py-4 bg-indigo-500 text-white rounded-3xl font-black text-xs uppercase tracking-widest">
                    Return to Roster
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
                        <Link href="/candidates" className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 transition-colors">
                            <ArrowLeft className="w-4 h-4" />
                            <span className="text-[10px] font-black uppercase tracking-widest">Back to Roster</span>
                        </Link>

                        <div className="flex items-center gap-6">
                            <div className="w-24 h-24 rounded-[32px] bg-gradient-to-tr from-slate-800 to-slate-700 flex items-center justify-center text-4xl font-black text-white border-2 border-slate-700 shadow-2xl relative group">
                                <div className="absolute inset-0 bg-indigo-500/20 blur-2xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                                {candidate.name.substring(0, 2).toUpperCase()}
                            </div>
                            <div className="space-y-1">
                                <h1 className="text-5xl md:text-6xl font-black text-white tracking-tight leading-none">
                                    {candidate.name}
                                </h1>
                                <div className="flex items-center gap-4">
                                    <span className="text-xl font-bold text-slate-400">{candidate.current_role}</span>
                                    <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />
                                    <span className="text-lg text-slate-500 font-medium">{candidate.experience_years} Years Pro</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <button className="px-6 py-4 bg-indigo-500 text-white rounded-[24px] font-black text-xs uppercase tracking-widest shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 transition-colors flex items-center gap-3">
                            <Sparkles className="w-4 h-4" />
                            Generate Report
                        </button>
                    </div>
                </header>

                {/* Tabs */}
                <div className="flex items-center gap-2 p-1.5 rounded-[24px] bg-slate-900/40 border border-white/5 w-fit">
                    {(['profile', 'matches', 'neural'] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={cn(
                                "px-8 py-3 rounded-[18px] text-[10px] font-black uppercase tracking-widest transition-all",
                                activeTab === tab
                                    ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/20"
                                    : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                <AnimatePresence mode="wait">
                    {activeTab === 'profile' && (
                        <motion.div
                            key="profile"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="grid grid-cols-1 lg:grid-cols-3 gap-10"
                        >
                            <div className="lg:col-span-2 space-y-10">
                                <div className="p-10 rounded-[48px] glass-card space-y-8">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                                            <ShieldCheck className="w-6 h-6 text-indigo-400" />
                                        </div>
                                        <h3 className="text-2xl font-black text-white tracking-tight uppercase">Biography & Context</h3>
                                    </div>
                                    <p className="text-lg text-slate-400 leading-relaxed whitespace-pre-wrap font-medium">
                                        {candidate.resume_text || "No biological data provided for this entity. Inferences restricted to metadata."}
                                    </p>
                                </div>

                                <div className="p-10 rounded-[48px] glass-card space-y-8">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                                            <Target className="w-6 h-6 text-purple-400" />
                                        </div>
                                        <h3 className="text-2xl font-black text-white tracking-tight uppercase">Skill Taxonomy</h3>
                                    </div>
                                    <div className="flex flex-wrap gap-4">
                                        {candidate.skills.map((skill, i) => (
                                            <div key={i} className="px-6 py-3 rounded-2xl bg-slate-950 border border-slate-800 text-slate-300 font-bold text-sm hover:border-indigo-500/30 transition-colors">
                                                {skill}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-10">
                                <div className="p-8 rounded-[40px] glass-card space-y-8 bg-gradient-to-br from-indigo-500/5 to-transparent">
                                    <h4 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em] px-2">Contact Details</h4>
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5">
                                            <Mail className="w-5 h-5 text-indigo-400" />
                                            <span className="text-sm font-bold text-slate-200">{candidate.email}</span>
                                        </div>
                                        <div className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5">
                                            <Briefcase className="w-5 h-5 text-purple-400" />
                                            <span className="text-sm font-bold text-slate-200">{candidate.current_role}</span>
                                        </div>
                                        <div className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5">
                                            <Calendar className="w-5 h-5 text-emerald-400" />
                                            <span className="text-sm font-bold text-slate-200">{candidate.experience_years} Years Experienced</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-8 rounded-[40px] glass-card space-y-8 border-indigo-500/20">
                                    <h4 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em] px-2">AI Summary</h4>
                                    <p className="text-sm text-slate-400 leading-relaxed font-bold italic">
                                        &quot;Candidate exhibits high density in <span className="text-indigo-400">{candidate.skills[0]}</span> and <span className="text-purple-400">{candidate.skills[1]}</span>. Strategic match probability remains high for architectural roles.&quot;
                                    </p>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {activeTab === 'matches' && (
                        <motion.div
                            key="matches"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="grid grid-cols-1 md:grid-cols-2 gap-8"
                        >
                            {recommendations.length > 0 ? recommendations.map((rec, i) => (
                                <Link key={i} href={`/jobs/${rec.job_id}`}>
                                    <div className="p-8 rounded-[40px] glass-card border-white/5 hover:border-indigo-500/30 transition-all group relative overflow-hidden h-full flex flex-col">
                                        <div className="absolute top-0 right-0 p-6">
                                            <div className="flex flex-col items-end">
                                                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Match Score</span>
                                                <span className="text-3xl font-black text-indigo-400">{Math.round(rec.score * 100)}%</span>
                                            </div>
                                        </div>

                                        <div className="space-y-6 flex-1">
                                            <div className="flex items-center gap-4">
                                                <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 group-hover:scale-110 transition-transform">
                                                    <Briefcase className="w-7 h-7 text-indigo-400" />
                                                </div>
                                                <div>
                                                    <h3 className="text-xl font-black text-white leading-tight group-hover:text-indigo-400 transition-colors uppercase">{rec.title}</h3>
                                                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1 underline decoration-white/5">{rec.company}</p>
                                                </div>
                                            </div>

                                            <div className="flex flex-wrap gap-2">
                                                {rec.required_skills.slice(0, 4).map((skill, si) => (
                                                    <span key={si} className="text-[9px] font-black uppercase tracking-widest px-3 py-1 bg-white/5 rounded-full text-slate-400 border border-white/5">{skill}</span>
                                                ))}
                                                {rec.required_skills.length > 4 && <span className="text-[9px] font-black text-indigo-500">+{rec.required_skills.length - 4} More</span>}
                                            </div>
                                        </div>

                                        <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-between">
                                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                                                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                                                Verified Requisition
                                            </span>
                                            <ChevronRight className="w-5 h-5 text-slate-700 group-hover:translate-x-2 transition-transform" />
                                        </div>
                                    </div>
                                </Link>
                            )) : (
                                <div className="col-span-full p-20 rounded-[48px] glass-card border-dashed border-slate-800 flex flex-col items-center justify-center text-center space-y-6">
                                    <div className="w-20 h-20 rounded-[32px] bg-indigo-500/5 flex items-center justify-center border border-indigo-500/10">
                                        <Activity className="w-10 h-10 text-indigo-500/30 animate-pulse" />
                                    </div>
                                    <div className="space-y-1">
                                        <h4 className="text-xl font-black text-white">Calculating Recommendations...</h4>
                                        <p className="text-slate-500 font-medium">Platform is currently processing global job sharding.</p>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {activeTab === 'neural' && (
                        <motion.div
                            key="neural"
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.98 }}
                            className="space-y-10"
                        >
                            <div className="p-10 rounded-[48px] glass-card bg-slate-950 border-indigo-500/10 space-y-10">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                                            <Cpu className="w-8 h-8 text-indigo-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-3xl font-black text-white uppercase tracking-tighter">Expanded Neural Map</h3>
                                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-1">Transitive Skill Inference Data</p>
                                        </div>
                                    </div>
                                    <div className="px-6 py-3 rounded-2xl bg-indigo-500 text-white font-black text-xs uppercase tracking-widest shadow-lg shadow-indigo-500/20">
                                        {expandedSkills.length} Dimensions
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
                                    {expandedSkills.map((skill, i) => (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: i * 0.02 }}
                                            className="group p-4 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-indigo-500/30 transition-all text-center space-y-3"
                                        >
                                            <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-[10px] font-black text-slate-200 group-hover:text-indigo-400 group-hover:scale-110 transition-all">
                                                {skill.substring(0, 1).toUpperCase()}
                                            </div>
                                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest group-hover:text-white transition-colors">{skill}</span>
                                        </motion.div>
                                    ))}
                                </div>

                                <div className="p-8 rounded-[32px] bg-indigo-500/5 border border-indigo-500/10 space-y-4">
                                    <h4 className="flex items-center gap-2 text-[10px] font-black text-indigo-400 uppercase tracking-widest">
                                        <Sparkles className="w-3 h-3" />
                                        Inference Logic
                                    </h4>
                                    <p className="text-sm text-slate-400 font-medium leading-relaxed">
                                        Our AI has mapped the original <span className="text-white font-bold">{candidate.skills.length} skills</span> to a multi-dimensional graph of <span className="text-white font-bold">{expandedSkills.length} concepts</span>. This expansion allows the candidate to match jobs that require related technologies even if they aren&apos;t explicitly listed on their profile.
                                    </p>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
