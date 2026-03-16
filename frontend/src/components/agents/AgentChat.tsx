'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, CheckCircle2, Clock, Zap } from 'lucide-react';
import { chatApi, ChatMessage } from '@/services/api';
import { useAgents } from '@/context/AgentContext';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { AgentMetadata } from '@/types/agent';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    sources?: { title: string; source: string; score: number }[];
    metadata?: {
        confidence?: number;
        latency_ms?: number;
        verified?: boolean;
    };
}

export function AgentChat({ agent }: { agent?: AgentMetadata }) {
    const { activeAgent: contextAgent } = useAgents();
    const activeAgent = agent || contextAgent;
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const [contextId, setContextId] = useState<string | undefined>(undefined);

    // clear context when agent changes
    useEffect(() => {
        setContextId(undefined);
        setMessages([]);
    }, [activeAgent?.id]);

    const handleSend = async () => {
        if (!input.trim() || !activeAgent) return;

        const userMsg: Message = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            // Convert to chat format
            const chatMessages: ChatMessage[] = messages.map(m => ({ role: m.role, content: m.content })).concat({ role: 'user', content: userMsg.content });

            // Allow explicit agent override or let backend route
            const targetAgentId = activeAgent.id;

            const { data } = await chatApi.send(chatMessages, contextId, targetAgentId);

            if (data.context_id) setContextId(data.context_id);

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.response,
                sources: data.sources,
                metadata: data.metadata
            }]);
        } catch {
            setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error. Please try again." }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    if (!activeAgent) return null;

    return (
        <div className="flex flex-col h-[600px] rounded-[32px] glass-card border border-white/10 overflow-hidden">
            <div className="p-6 border-b border-white/5 bg-slate-900/30 flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                    <Bot className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                    <h3 className="text-lg font-black text-white">Live Inference</h3>
                    <p className="text-xs text-slate-400 font-medium">
                        Interact with <span className="text-indigo-400">{activeAgent.name}</span>
                    </p>
                </div>
            </div>

            <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-black/20">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4 opacity-50">
                        <Sparkles className="w-12 h-12" />
                        <p className="text-sm font-bold uppercase tracking-widest">Ready for input</p>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={cn(
                            "flex gap-4 max-w-[90%]",
                            msg.role === 'user' ? "ml-auto flex-row-reverse" : ""
                        )}
                    >
                        <div className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                            msg.role === 'user' ? "bg-slate-700" : "bg-indigo-600"
                        )}>
                            {msg.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
                        </div>
                        <div className={cn(
                            "p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap",
                            msg.role === 'user'
                                ? "bg-slate-800 text-slate-200 rounded-tr-none"
                                : "bg-indigo-500/10 border border-indigo-500/20 text-indigo-100 rounded-tl-none"
                        )}>
                            {msg.content}

                            {msg.metadata && (
                                <div className="mt-4 pt-4 border-t border-white/10 flex flex-wrap gap-4 text-xs">
                                    {msg.metadata.confidence !== undefined && (
                                        <div className="flex items-center gap-1.5 text-slate-400" title="Confidence Score">
                                            <Zap className="w-3.5 h-3.5 text-yellow-500" />
                                            <span>{Math.round(msg.metadata.confidence * 100)}% confidence</span>
                                        </div>
                                    )}
                                    {msg.metadata.latency_ms !== undefined && (
                                        <div className="flex items-center gap-1.5 text-slate-400" title="Inference Latency">
                                            <Clock className="w-3.5 h-3.5 text-blue-500" />
                                            <span>{msg.metadata.latency_ms}ms</span>
                                        </div>
                                    )}
                                    {msg.metadata.verified && (
                                        <div className="flex items-center gap-1.5 text-green-400" title="Verified Answer">
                                            <CheckCircle2 className="w-3.5 h-3.5" />
                                            <span className="font-semibold">Verified</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            {msg.sources && msg.sources.length > 0 && (
                                <div className="mt-4 pt-4 border-t border-white/10 space-y-2">
                                    <p className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Sources</p>
                                    <div className="grid gap-2">
                                        {msg.sources.map((src, idx) => (
                                            <div key={idx} className="text-xs bg-black/20 p-2 rounded border border-white/5">
                                                <span className="font-bold text-slate-300">{src.title}</span>
                                                <span className="text-slate-500 ml-2">({Math.round(Math.min(src.score, 1) * 100)}%)</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </motion.div>
                ))}

                {isLoading && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
                        <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
                            <Loader2 className="w-4 h-4 text-white animate-spin" />
                        </div>
                        <div className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-100 p-4 rounded-2xl rounded-tl-none">
                            <span className="text-xs font-bold animate-pulse">Processing...</span>
                        </div>
                    </motion.div>
                )}
            </div>

            <div className="p-4 bg-slate-900/50 border-t border-white/5">
                <div className="relative flex items-center gap-2">
                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={activeAgent.type === 'rag_qa' ? "Ask a question about the documents..." : "Enter input..."}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl py-4 pl-4 pr-12 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                        disabled={isLoading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        className="absolute right-2 p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
