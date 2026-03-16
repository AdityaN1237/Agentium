'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save, BrainCircuit, Type, FileText, Database } from 'lucide-react';
import { AgentMetadata } from '@/types/agent';
import { agentApi } from '@/services/api';

interface AgentFormProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (data: import('@/types/agent').AgentCreatePayload | import('@/types/agent').AgentUpdatePayload) => void;
    initialData?: AgentMetadata | null;
    title: string;
}

export function AgentForm({ isOpen, onClose, onSubmit, initialData, title }: AgentFormProps) {
    const [formData, setFormData] = useState({
        id: '',
        name: '',
        description: '',
        type: '',
        config: {}
    });
    const [availableTypes, setAvailableTypes] = useState<string[]>([]);
    const [isLoadingTypes, setIsLoadingTypes] = useState(false);

    useEffect(() => {
        const fetchTypes = async () => {
            setIsLoadingTypes(true);
            try {
                const { data } = await agentApi.getTypes();
                setAvailableTypes(data);
                if (!initialData && data.length > 0) {
                    setFormData(prev => ({ ...prev, type: data[0] }));
                }
            } catch (err) {
                console.error("Failed to load agent types:", err);
            } finally {
                setIsLoadingTypes(false);
            }
        };

        if (isOpen) {
            fetchTypes();
        }
    }, [isOpen, initialData]);

    useEffect(() => {
        if (initialData) {
            setFormData({
                id: initialData.id,
                name: initialData.name,
                description: initialData.description,
                type: initialData.type || '',
                config: initialData.config || {}
            });
        } else {
            setFormData({
                id: '',
                name: '',
                description: '',
                type: availableTypes[0] || '',
                config: {}
            });
        }
    }, [initialData, isOpen, availableTypes]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
                    />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="relative w-full max-w-xl glass-card rounded-[32px] overflow-hidden shadow-2xl border border-white/10"
                    >
                        <div className="p-8 space-y-8">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                                        <BrainCircuit className="w-6 h-6 text-indigo-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-2xl font-black text-white tracking-tight">{title}</h3>
                                        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Configure Neural Module</p>
                                    </div>
                                </div>
                                <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                                    <X className="w-6 h-6 text-slate-500" />
                                </button>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Agent Identifier (Unique UUID or Slug)</label>
                                        <div className="relative">
                                            <Database className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                            <input
                                                type="text"
                                                required
                                                disabled={!!initialData}
                                                value={formData.id}
                                                onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                                                className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 pl-11 pr-4 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-50"
                                                placeholder="e.g. custom-matching-v1"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Agent Name</label>
                                        <div className="relative">
                                            <Type className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                            <input
                                                type="text"
                                                required
                                                value={formData.name}
                                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                                className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 pl-11 pr-4 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                                                placeholder="Enter friendly name"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Specialization Description</label>
                                        <div className="relative">
                                            <FileText className="absolute left-4 top-4 w-4 h-4 text-slate-500" />
                                            <textarea
                                                required
                                                rows={3}
                                                value={formData.description}
                                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                                className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 pl-11 pr-4 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors resize-none"
                                                placeholder="What is this agent's primary function?"
                                            />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Module Type</label>
                                            <select
                                                value={formData.type}
                                                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                                                disabled={isLoadingTypes}
                                                className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 px-4 text-white focus:outline-none focus:border-indigo-500 transition-colors appearance-none disabled:opacity-50"
                                            >
                                                {isLoadingTypes ? (
                                                    <option>Loading types...</option>
                                                ) : (
                                                    availableTypes.map(type => (
                                                        <option key={type} value={type} className="bg-slate-900">
                                                            {type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                                                        </option>
                                                    ))
                                                )}
                                            </select>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Base State</label>
                                            <div className="w-full bg-slate-900/30 border border-slate-800 rounded-2xl py-3 px-4 text-slate-500 italic text-sm">
                                                Active by Default
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 flex gap-4">
                                    <button
                                        type="button"
                                        onClick={onClose}
                                        className="flex-1 py-4 px-6 rounded-2xl border border-slate-800 text-slate-400 font-black text-xs uppercase tracking-widest hover:bg-white/5 transition-colors"
                                    >
                                        Discard
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 py-4 px-6 rounded-2xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-black text-xs uppercase tracking-widest hover:scale-[1.02] active:scale-[0.98] transition-all shadow-xl shadow-indigo-500/20 flex items-center justify-center gap-2"
                                    >
                                        <Save className="w-4 h-4" />
                                        Initialize Agent
                                    </button>
                                </div>
                            </form>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
