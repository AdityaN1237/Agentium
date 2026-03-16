'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
// import { useAuth } from '@/context/AuthContext'; // Removed for local mode
import {
    LayoutDashboard,
    BrainCircuit,
    Users,
    Briefcase,
    Settings,
    LineChart,
    LogOut,
    Menu,
    X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';

import { AgentMetadata } from '@/types/agent';
import { agentApi } from '@/services/api';

const baseNavItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Analytics', href: '/analytics', icon: LineChart },
    { name: 'Candidates', href: '/candidates', icon: Users },
    { name: 'Jobs', href: '/jobs', icon: Briefcase },
    { name: 'Settings', href: '/settings', icon: Settings },
];

function SidebarContent({ pathname, onNavClick }: { pathname: string, onNavClick: () => void }) {
    const [mounted, setMounted] = useState(false);
    const [agents, setAgents] = useState<AgentMetadata[]>([]);

    // Hardcoded user for local mode
    const user = { username: 'Admin', role: 'admin' };

    useEffect(() => {
        setTimeout(() => setMounted(true), 0);
        const fetchAgents = async () => {
            try {
                const { data } = await agentApi.list();
                setAgents(data);
            } catch (err) {
                // console.error("Failed to load agents for sidebar:", err);
            }
        };
        fetchAgents();
    }, []);

    const avatarText = 'AD';
    const username = 'Admin User';
    const role = 'System Architect';

    return (
        <div className="flex flex-col h-full">
            <div className="p-8 relative">
                <Link href="/" className="flex items-center gap-4 group">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform duration-300">
                        <BrainCircuit className="w-7 h-7 text-white" />
                    </div>
                    <div className="flex flex-col">
                        <span className="text-xl font-black tracking-tight text-white group-hover:text-indigo-300 transition-colors">
                            Agentium
                        </span>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest -mt-1">
                            Neural Platform
                        </span>
                    </div>
                </Link>
            </div>

            <nav className="flex-1 px-4 space-y-1 py-4 overflow-y-auto custom-scrollbar relative">
                {baseNavItems.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;

                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            onClick={onNavClick}
                            className={cn(
                                "flex items-center gap-3 px-5 py-3 rounded-xl transition-all duration-300 group relative",
                                isActive
                                    ? "bg-indigo-500/10 text-white font-bold"
                                    : "text-slate-400 hover:bg-slate-900/50 hover:text-slate-200"
                            )}
                        >
                            <Icon className={cn(
                                "w-5 h-5 transition-transform duration-300 group-hover:scale-110",
                                isActive ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300"
                            )} />
                            <span className="text-sm tracking-wide">{item.name}</span>
                            {isActive && <div className="ml-auto w-1 h-4 rounded-full bg-indigo-500" />}
                        </Link>
                    );
                })}

                <div className="pt-4 pb-2 px-5">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Neural Agents</span>
                </div>

                {agents.map((agent) => {
                    const href = `/agents/${agent.id}`;
                    const isActive = pathname === href;

                    return (
                        <Link
                            key={agent.id}
                            href={href}
                            onClick={onNavClick}
                            className={cn(
                                "flex items-center gap-3 px-5 py-3 rounded-xl transition-all duration-300 group relative",
                                isActive
                                    ? "bg-purple-500/10 text-white font-bold"
                                    : "text-slate-400 hover:bg-slate-900/50 hover:text-slate-200"
                            )}
                        >
                            <BrainCircuit className={cn(
                                "w-5 h-5 transition-transform duration-300 group-hover:scale-110",
                                isActive ? "text-purple-400" : "text-slate-500 group-hover:text-slate-300"
                            )} />
                            <span className="text-sm tracking-wide truncate">{agent.name}</span>
                            {isActive && <div className="ml-auto w-1 h-4 rounded-full bg-purple-500" />}
                        </Link>
                    );
                })}
            </nav>

            <div className="p-6 border-t border-slate-800/50 space-y-4 relative bg-[#030712]/50 backdrop-blur-md">
                <div className="flex items-center gap-3 p-3 rounded-2xl bg-white/5 border border-white/5">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-slate-700 to-slate-500 flex items-center justify-center text-xs font-bold ring-2 ring-indigo-500/20 shadow-xl border border-white/10 uppercase">
                        {avatarText}
                    </div>
                    <div className="flex flex-col overflow-hidden">
                        <span className="text-sm font-bold text-slate-200 truncate">{username}</span>
                        <span className="text-[10px] text-slate-500 uppercase tracking-tighter">{role}</span>
                    </div>
                    <button className="ml-auto p-1.5 hover:bg-white/5 rounded-lg text-slate-500 transition-colors">
                        <Settings className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}

export function Sidebar() {
    // const { logout, user } = useAuth(); // Removed
    const [isOpen, setIsOpen] = useState(false);
    const pathname = usePathname();

    return (
        <>
            {/* Mobile Header Toggle */}
            <div className="lg:hidden fixed top-0 left-0 right-0 h-16 px-6 glass-card border-b border-white/5 flex items-center justify-between z-[60]">
                <Link href="/" className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
                        <BrainCircuit className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-sm font-black text-white tracking-widest uppercase">Agentium</span>
                </Link>
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-white"
                >
                    {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                </button>
            </div>

            {/* Backdrop for Mobile */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsOpen(false)}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[70] lg:hidden"
                    />
                )}
            </AnimatePresence>

            {/* Desktop Sidebar */}
            <aside className="hidden lg:flex w-72 glass-card border-r-0 flex-col h-screen sticky top-0 z-50 overflow-hidden shrink-0">
                <div className="absolute -top-24 -left-24 w-64 h-64 bg-indigo-600/10 blur-[100px] rounded-full pointer-events-none" />
                <SidebarContent pathname={pathname} onNavClick={() => setIsOpen(false)} />
            </aside>

            {/* Mobile Sidebar Content */}
            <AnimatePresence>
                {isOpen && (
                    <motion.aside
                        initial={{ x: '-100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '-100%' }}
                        transition={{ type: "spring", damping: 25, stiffness: 200 }}
                        className="fixed left-0 top-0 bottom-0 w-80 bg-[#030712] border-r border-white/10 z-[80] lg:hidden shadow-2xl"
                    >
                        <SidebarContent pathname={pathname} onNavClick={() => setIsOpen(false)} />
                        <button
                            onClick={() => setIsOpen(false)}
                            className="absolute top-6 right-6 p-2 rounded-full hover:bg-white/10 text-slate-500 lg:hidden"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </motion.aside>
                )}
            </AnimatePresence>
        </>
    );
}
