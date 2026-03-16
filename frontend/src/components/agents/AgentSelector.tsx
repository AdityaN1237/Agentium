'use client';

import { useState } from 'react';
import { useAgents } from "@/context/AgentContext";
import { BrainCircuit, CheckCircle2, CircleDashed, AlertCircle, Pencil, Trash2, Info, X, Sparkles, Database, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from "../../lib/utils";
import { AgentForm } from './AgentForm';
import { AgentMetadata, AgentCreatePayload, AgentUpdatePayload } from '@/types/agent';
import { agentApi } from "@/services/api";

export function AgentSelector() {
    const { agents, activeAgent, setActiveAgent, isLoading, createAgent, updateAgent, deleteAgent } = useAgents();
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [isDetailsOpen, setIsDetailsOpen] = useState(false);
    const [formMode, setFormMode] = useState<'create' | 'update'>('create');
    const [selectedAgentForEdit, setSelectedAgentForEdit] = useState<AgentMetadata | null>(null);
    const [agentDetails, setAgentDetails] = useState<AgentMetadata | null>(null);

    const handleOpenCreate = () => {
        setFormMode('create');
        setSelectedAgentForEdit(null);
        setIsFormOpen(true);
    };

    const handleOpenEdit = (e: React.MouseEvent, agent: AgentMetadata) => {
        e.stopPropagation();
        setFormMode('update');
        setSelectedAgentForEdit(agent);
        setIsFormOpen(true);
    };

    const handleViewDetails = async (e: React.MouseEvent, agentId: string) => {
        e.stopPropagation();
        try {
            // Explicitly fetch by ID as requested
            const response = await agentApi.getById(agentId);
            setAgentDetails(response.data);
            setIsDetailsOpen(true);
        } catch {
            alert('Failed to fetch neural node details');
        }
    };

    const handleDelete = async (e: React.MouseEvent, agentId: string) => {
        e.stopPropagation();
        if (window.confirm('Are you sure you want to decommission this neural node? This action is irreversible.')) {
            try {
                await deleteAgent(agentId);
            } catch {
                alert('Failed to delete agent. Root agents are protected.');
            }
        }
    };

    const handleFormSubmit = async (data: AgentCreatePayload | AgentUpdatePayload) => {
        try {
            if (formMode === 'create') {
                await createAgent(data as AgentCreatePayload);
            } else {
                await updateAgent((data as AgentUpdatePayload).id as string, data as AgentUpdatePayload);
            }
            setIsFormOpen(false);
        } catch (err) {
            const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            alert(msg || 'Operation failed');
        }
    };

    if (isLoading) {
        return (
            <div className="flex gap-6 overflow-x-auto pb-8 custom-scrollbar">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="min-w-[340px] h-48 rounded-[32px] bg-slate-900/40 animate-pulse border border-slate-800/50" />
                ))}
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6 pb-8 pt-2">
            <AnimatePresence mode="popLayout">
                {agents.map((agent) => {
                    const isActive = activeAgent?.id === agent.id;

                    return (
                        <motion.div
                            key={agent.id}
                            layout
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8, transition: { duration: 0.2 } }}
                            className="relative group"
                        >
                            <button
                                onClick={() => setActiveAgent(agent)}
                                className={cn(
                                    "w-full p-7 rounded-[32px] border transition-all duration-500 relative text-left overflow-hidden h-full",
                                    isActive
                                        ? "bg-indigo-600/10 border-indigo-500/50 shadow-[0_20px_50px_rgba(79,70,229,0.15)]"
                                        : "bg-slate-900/30 border-slate-800/50 hover:border-slate-700/80 hover:bg-slate-900/50 transition-shadow duration-500"
                                )}
                            >
                                <div className="flex items-start justify-between mb-6 relative z-10">
                                    <div className={cn(
                                        "p-4 rounded-2xl transition-all duration-500 group-hover:scale-110",
                                        isActive
                                            ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/40"
                                            : "bg-slate-950/80 text-slate-500 border border-slate-800 group-hover:text-indigo-400 group-hover:border-indigo-500/30"
                                    )}>
                                        <BrainCircuit className="w-6 h-6" />
                                    </div>

                                    <div className="flex flex-col items-end gap-2">
                                        <div className={cn(
                                            "flex items-center gap-2 px-3.5 py-1.5 rounded-full border text-[10px] font-black uppercase tracking-widest backdrop-blur-md transition-colors",
                                            agent.status === 'active' && (isActive ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" : "bg-slate-950/80 text-emerald-500/80 border-slate-800"),
                                            agent.status === 'training' && (isActive ? "bg-amber-500/20 text-amber-400 border-amber-500/30" : "bg-slate-950/80 text-amber-500/80 border-slate-800"),
                                            agent.status === 'error' && (isActive ? "bg-rose-500/20 text-rose-400 border-rose-500/30" : "bg-slate-950/80 text-rose-500/80 border-slate-800"),
                                        )}>
                                            {agent.status === 'active' && <CheckCircle2 className="w-3.5 h-3.5" />}
                                            {agent.status === 'training' && <CircleDashed className="w-3.5 h-3.5 animate-spin" />}
                                            {agent.status === 'error' && <AlertCircle className="w-3.5 h-3.5" />}
                                            {agent.status}
                                        </div>
                                    </div>
                                </div>

                                <div className="relative z-10">
                                    <h3 className={cn(
                                        "font-black text-xl mb-2 transition-colors duration-300",
                                        isActive ? "text-white" : "text-slate-300 group-hover:text-white"
                                    )}>
                                        {agent.name}
                                    </h3>
                                    <p className="text-sm text-slate-500 line-clamp-2 leading-relaxed font-medium group-hover:text-slate-400 transition-colors">
                                        {agent.description}
                                    </p>
                                </div>

                                {/* Active Bottom Bar */}
                                {isActive && (
                                    <motion.div
                                        layoutId="activeBar"
                                        className="absolute bottom-0 left-0 w-full h-[6px] bg-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.8)]"
                                    />
                                )}
                            </button>

                            {/* Floating Actions */}
                            <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity z-20">
                                <button
                                    onClick={(e) => handleViewDetails(e, agent.id)}
                                    title="View Neural Details"
                                    className="p-2 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all backdrop-blur-md"
                                >
                                    <Info className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={(e) => handleOpenEdit(e, agent)}
                                    title="Synthesize Weight Update"
                                    className="p-2 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all backdrop-blur-md"
                                >
                                    <Pencil className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={(e) => handleDelete(e, agent.id)}
                                    title="Decommission Node"
                                    className="p-2 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-500 hover:text-rose-400 hover:border-rose-500/30 transition-all backdrop-blur-md"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </motion.div>
                    );
                })}
            </AnimatePresence>

            <button
                onClick={handleOpenCreate}
                className="border-2 border-dashed border-slate-800/40 rounded-[32px] flex flex-col items-center justify-center p-8 hover:bg-white/5 transition-all group opacity-40 hover:opacity-100 hover:border-indigo-500/50"
            >
                <div className="w-12 h-12 rounded-full border-2 border-slate-700 flex items-center justify-center mb-3 group-hover:border-indigo-500 group-hover:scale-110 transition-all">
                    <span className="text-2xl text-slate-600 group-hover:text-indigo-400 transition-colors">+</span>
                </div>
                <span className="text-xs font-bold text-slate-500 group-hover:text-slate-300 uppercase tracking-widest text-center">Register New<br />Neural Module</span>
            </button>

            <AgentForm
                isOpen={isFormOpen}
                onClose={() => setIsFormOpen(false)}
                onSubmit={handleFormSubmit}
                initialData={selectedAgentForEdit}
                title={formMode === 'create' ? 'Initialize New Agent' : 'Update Neural Weights'}
            />

            {/* Neural Details Modal */}
            <AnimatePresence>
                {isDetailsOpen && agentDetails && (
                    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsDetailsOpen(false)}
                            className="absolute inset-0 bg-slate-950/80 backdrop-blur-xl"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 20 }}
                            className="relative w-full max-w-lg glass-card rounded-[40px] overflow-hidden border border-white/10 shadow-2xl shadow-indigo-500/10"
                        >
                            <div className="p-10 space-y-8">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-5">
                                        <div className="w-14 h-14 rounded-2xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                                            <BrainCircuit className="w-8 h-8 text-indigo-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-3xl font-black text-white tracking-tighter">{agentDetails.name}</h3>
                                            <p className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] mt-1">Core Neural Specification</p>
                                        </div>
                                    </div>
                                    <button onClick={() => setIsDetailsOpen(false)} className="p-3 hover:bg-white/5 rounded-full transition-colors text-slate-500">
                                        <X className="w-6 h-6" />
                                    </button>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    {[
                                        { label: 'Neural ID', val: agentDetails.id, icon: Database },
                                        { label: 'Module Type', val: agentDetails.type || 'Standard', icon: Sparkles },
                                        { label: 'Core Version', val: agentDetails.version || '1.0.0', icon: Activity },
                                        { label: 'Neural Accuracy', val: agentDetails.accuracy ? `${(agentDetails.accuracy * 100).toFixed(1)}%` : 'Calibrating...', icon: BrainCircuit }, // Changed Target to BrainCircuit as Target is not imported
                                    ].map((spec, i) => (
                                        <div key={i} className="p-5 rounded-3xl bg-slate-900/50 border border-slate-800/50 space-y-2">
                                            <div className="flex items-center gap-2 text-slate-500">
                                                <spec.icon className="w-3.5 h-3.5" />
                                                <span className="text-[10px] font-black uppercase tracking-widest">{spec.label}</span>
                                            </div>
                                            <p className="text-sm font-bold text-slate-200 truncate">{spec.val}</p>
                                        </div>
                                    ))}
                                </div>

                                <div className="space-y-4">
                                    <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Functional Description</h4>
                                    <p className="text-slate-400 text-sm leading-relaxed font-medium bg-slate-900/30 p-6 rounded-3xl border border-slate-800/30 italic">
                                        {agentDetails.description}
                                    </p>
                                </div>

                                <button
                                    onClick={() => setIsDetailsOpen(false)}
                                    className="w-full py-5 rounded-[24px] bg-slate-900 border border-slate-800 text-slate-300 font-black text-xs uppercase tracking-widest hover:bg-slate-800 transition-colors"
                                >
                                    Close Specification
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}
