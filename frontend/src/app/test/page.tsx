'use client';

import { useState, useEffect } from 'react';
import { AgentChat } from "@/components/agents/AgentChat";
import { FileValidation } from "@/components/agents/FileValidation";
import { agentApi } from "@/services/api";
import { AgentMetadata } from "@/types/agent";
import { Bot, TestTube, AlertTriangle } from 'lucide-react';

export default function TestPage() {
    const [agents, setAgents] = useState<AgentMetadata[]>([]);
    const [selectedAgentId, setSelectedAgentId] = useState<string>("");

    useEffect(() => {
        agentApi.list().then(({ data }) => {
            setAgents(data);
            if (data.length > 0) setSelectedAgentId(data[0].id);
        });
    }, []);

    const selectedAgent = agents.find(a => a.id === selectedAgentId);

    return (
        <div className="min-h-screen bg-[#0B0F19] text-white p-6 md:p-12">
            <div className="max-w-6xl mx-auto space-y-8">
                <header className="flex items-center justify-between">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3 text-amber-500">
                            <TestTube className="w-6 h-6" />
                            <span className="text-xs font-black uppercase tracking-[0.2em]">Sandbox Environment</span>
                        </div>
                        <h1 className="text-4xl font-black text-white tracking-tight">Agent Validation</h1>
                        <p className="text-slate-400 max-w-xl">
                            Test agent responses in isolation before deployment. This environment bypasses the main intent router.
                        </p>
                    </div>

                    <div className="bg-amber-500/10 border border-amber-500/20 p-4 rounded-2xl flex items-center gap-4 max-w-sm">
                        <AlertTriangle className="w-8 h-8 text-amber-500 shrink-0" />
                        <p className="text-xs text-amber-200/80 font-medium">
                            Actions performed here (e.g., state updates) may affect the live agent memory depending on agent configuration.
                        </p>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    {/* Sidebar / Agent Selector */}
                    <div className="lg:col-span-3 space-y-4">
                        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest pl-2">Available Agents</h3>
                        <div className="space-y-2">
                            {agents.map((agent) => (
                                <button
                                    key={agent.id}
                                    onClick={() => setSelectedAgentId(agent.id)}
                                    className={`w-full text-left p-4 rounded-2xl flex items-center gap-3 transition-all ${selectedAgentId === agent.id
                                        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                                        : 'bg-slate-900/50 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                                        }`}
                                >
                                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${selectedAgentId === agent.id ? 'bg-white/20' : 'bg-slate-800'
                                        }`}>
                                        <Bot className="w-4 h-4" />
                                    </div>
                                    <div className="overflow-hidden">
                                        <div className="font-bold truncate">{agent.name}</div>
                                        <div className="text-[10px] opacity-70 truncate">{agent.type}</div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Chat Area */}
                    <div className="lg:col-span-9">
                        <div className="bg-slate-900/50 border border-slate-800 rounded-[32px] overflow-hidden min-h-[600px] flex flex-col">
                            <div className="p-6 border-b border-white/5 bg-slate-900/80 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                    <span className="font-mono text-xs text-emerald-400">ACTIVE_SESSION: {selectedAgentId}</span>
                                </div>
                                <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                                    v{selectedAgent?.version || '0.0.0'}
                                </div>
                            </div>

                            <div className="flex-1 relative">
                                {selectedAgent && (
                                    (selectedAgent.type === 'matching' || selectedAgent.id === 'skill_job_matching') ? (
                                        <FileValidation agentId={selectedAgent.id} />
                                    ) : (
                                        <AgentChat
                                            key={selectedAgent.id}
                                            agent={selectedAgent}
                                        />
                                    )
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}


