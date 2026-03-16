'use client';

import { useState, useEffect } from 'react';
import { useAgents } from "@/context/AgentContext";
import { Sparkles, BrainCircuit, Activity, BarChart3, Database, Target, Zap, ArrowUpRight, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { AgentSelector } from "@/components/agents/AgentSelector";
import { cn } from "../lib/utils";
import { systemApi, SystemStats } from '@/services/api';
export default function Dashboard() {
  const { agents } = useAgents();
  const [sysStats, setSysStats] = useState<SystemStats | null>(null);
  const user = { username: 'Admin' }; // Hardcoded default user

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const { data } = await systemApi.stats();
        setSysStats(data);
      } catch (e) {
        console.error("Failed to fetch system stats", e);
      }
    };
    fetchStats();
    // Refresh every 30s
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    { label: 'Active Swarm Nodes', value: sysStats?.system.active_agents ?? '...', icon: BrainCircuit, color: 'text-indigo-400', bg: 'bg-indigo-500/10', trend: 'Online' },
    { label: 'Active Training Sessions', value: sysStats?.system.training_active ?? '0', icon: Database, color: 'text-purple-400', bg: 'bg-purple-500/10', trend: 'Real-time' },
    { label: 'Vector Index Size', value: sysStats?.system.total_vectors ?? '...', icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/10', trend: 'Indexed' },
    { label: 'System Health', value: sysStats ? `${sysStats.system.health_score}%` : '...', icon: Zap, color: 'text-amber-400', bg: 'bg-amber-500/10', trend: 'Optimal' },
  ];

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  // Generate dynamic logs based on real state
  const systemLogs = [
    { m: `System synchronized with ${sysStats?.candidates || 0} candidate profiles.`, t: 'Just now' },
    { m: `${sysStats?.jobs.active || 0} Job configurations active and indexed.`, t: 'Live' },
    { m: `Neural Engine weights loaded: ${sysStats?.system.total_vectors || 0} vectors.`, t: 'Ready' }
  ];

  return (
    <div className="relative min-h-screen mesh-gradient bg-grid">
      {/* Background Glows */}
      <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-indigo-600/10 blur-[150px] rounded-full pointer-events-none -z-10" />
      <div className="fixed bottom-0 left-0 w-[500px] h-[500px] bg-purple-600/5 blur-[150px] rounded-full pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto p-6 md:p-8 lg:p-12 space-y-12 md:space-y-16 relative">
        {/* Advanced Header */}
        <header className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 md:gap-10">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex-1"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mb-6 group cursor-default">
              <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
              <span className="text-[10px] font-black uppercase tracking-[0.2em] whitespace-nowrap overflow-hidden text-ellipsis max-w-[200px] md:max-w-none">Neural Intelligence Ecosystem</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-black text-white leading-tight lg:leading-none tracking-tighter mb-4 md:mb-6 underline decoration-indigo-500/30 underline-offset-8">
              System <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-500">Overview</span>
            </h1>
            <p className="text-lg md:text-xl text-slate-400 max-w-2xl leading-relaxed font-medium">
              Welcome back, <span suppressHydrationWarning className="text-slate-100 font-bold border-b border-indigo-500/50">{user?.username || 'User'}</span>. Orchestrate your AI swarm with real-time neural diagnostics.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-row gap-4"
          >
            <div className="p-6 md:p-8 rounded-[32px] md:rounded-[40px] glass-card flex flex-col items-center justify-center gap-2 md:gap-3 flex-1 lg:flex-none min-w-[100px]">
              <div className="text-3xl md:text-4xl font-black text-white">{sysStats?.system.active_agents ?? '-'}</div>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest text-center">Local Nodes</div>
            </div>
            <div className="p-6 md:p-8 rounded-[32px] md:rounded-[40px] glass-card flex flex-col items-center justify-center gap-2 md:gap-3 border-emerald-500/20 flex-1 lg:flex-none min-w-[100px]">
              <div className="w-3 md:w-4 h-3 md:h-4 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_15px_rgba(16,185,129,0.5)]" />
              <div className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest text-center">Active Status</div>
            </div>
          </motion.div>
        </header>

        {/* Dynamic Stats Grid */}
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6"
        >
          {stats.map((stat) => (
            <motion.div
              key={stat.label}
              variants={item}
              whileHover={{ scale: 1.02 }}
              className="p-6 md:p-8 rounded-[32px] md:rounded-[36px] glass-card glass-card-hover group relative overflow-hidden"
            >
              <div className={`w-12 h-12 md:w-14 md:h-14 rounded-2xl ${stat.bg} flex items-center justify-center mb-4 md:mb-6 group-hover:scale-110 transition-transform duration-500`}>
                <stat.icon className={`w-6 h-6 md:w-7 md:h-7 ${stat.color}`} />
              </div>
              <div>
                <p className="text-[10px] md:text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">{stat.label}</p>
                <div className="flex items-center justify-between">
                  <div className="text-2xl md:text-3xl font-black text-white tracking-tight">{stat.value}</div>
                  <div className={cn(
                    "px-2 py-1 rounded-lg text-[10px] font-black",
                    stat.trend.includes('+') || stat.trend === 'Online' || stat.trend === 'Real-time' || stat.trend === 'Indexed' || stat.trend === 'Optimal' ? "bg-emerald-500/10 text-emerald-400" : "bg-indigo-500/10 text-indigo-400"
                  )}>
                    {stat.trend}
                  </div>
                </div>
              </div>
              <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <ArrowUpRight className="w-5 h-5 text-slate-600" />
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Main Neural Hub SECTION */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 md:gap-10">
          {/* Agent Selector Column (Full Width in Inner Grid) */}
          <div className="lg:col-span-3 space-y-6 md:space-y-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <h2 className="text-xl md:text-2xl font-black flex items-center gap-3 text-white">
                <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 md:w-6 md:h-6 text-indigo-500" />
                </div>
                Active Intelligence <span className="hidden sm:inline text-slate-500 font-medium">Modules</span>
              </h2>
              <Link href="/agents" className="text-xs md:text-sm font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-2 group">
                System Registry
                <ArrowUpRight className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </Link>
            </div>

            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8 }}
            >
              <AgentSelector />
            </motion.div>
          </div>

          {/* Quick Metrics & Actions Section */}
          <div className="lg:col-span-2 space-y-6 md:space-y-8">
            <h2 className="text-xl md:text-2xl font-black text-white flex items-center gap-3">
              <TrendingUp className="w-5 h-5 md:w-6 md:h-6 text-purple-500" />
              Neural Fabric <span className="hidden sm:inline text-slate-500 font-medium">Insights</span>
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-6">
              {agents.slice(0, 4).map((agent) => (
                <motion.div
                  key={agent.id}
                  whileHover={{ x: 5 }}
                  className="p-6 md:p-8 rounded-[32px] md:rounded-[36px] border border-slate-800/50 bg-slate-900/10 hover:bg-slate-900/30 transition-all group"
                >
                  <div className="flex justify-between items-start mb-4 md:mb-6">
                    <div className="p-2.5 md:p-3 rounded-2xl bg-slate-950 border border-slate-800 group-hover:border-indigo-500/30 transition-colors">
                      <BrainCircuit className="w-5 h-5 md:w-6 md:h-6 text-indigo-400" />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                      <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{agent.status}</span>
                    </div>
                  </div>
                  <h3 className="font-black text-lg md:text-xl text-white mb-2">{agent.name}</h3>
                  <div className="flex items-center justify-between pt-4 md:pt-6 border-t border-slate-800/50 mt-2">
                    <div className="flex items-center gap-2">
                      <Target className="w-3.5 h-3.5 text-slate-500" />
                      <span className="text-[9px] md:text-[10px] font-black text-slate-500 uppercase tracking-widest italic">Core Accuracy:</span>
                      <span className="text-indigo-400 font-black text-base md:text-lg ml-1">
                        {((agent.accuracy ?? 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Link href="/analytics" className="text-[9px] md:text-[10px] font-black text-slate-400 hover:text-indigo-400 tracking-widest">DIAGNOSTICS →</Link>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="space-y-8 md:space-y-10 pt-8 lg:pt-0">
            <div className="p-8 md:p-10 rounded-[40px] md:rounded-[48px] bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 shadow-[0_30px_70px_rgba(79,70,229,0.3)] text-white relative overflow-hidden group">
              {/* Decorative Circle */}
              <div className="absolute -top-10 -right-10 w-32 h-32 md:w-40 md:h-40 bg-white/10 rounded-full blur-3xl pointer-events-none group-hover:scale-150 transition-transform duration-1000" />

              <div className="relative z-10 space-y-6">
                <div className="w-12 h-12 md:w-14 md:h-14 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/20">
                  <Zap className="w-6 h-6 md:w-8 md:h-8 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl md:text-3xl font-black leading-tight mb-3 md:mb-4 tracking-tighter">Scale Your Swarm.</h3>
                  <p className="text-sm md:text-base text-indigo-100/70 font-medium leading-relaxed">
                    Instantly deploy custom neural nodes specialized for your unique enterprise workflows.
                  </p>
                </div>
                <Link
                  href="/agents"
                  className="inline-flex items-center justify-center w-full py-4 md:py-5 bg-white text-indigo-900 font-black rounded-2xl md:rounded-3xl text-xs uppercase tracking-widest hover:bg-slate-100 transition-all active:scale-[0.98] shadow-2xl"
                >
                  Deploy New Node
                </Link>
              </div>
            </div>

            <div className="p-6 md:p-8 rounded-[32px] md:rounded-[40px] glass-card space-y-6 md:space-y-8">
              <h3 className="text-base md:text-lg font-black text-slate-200 flex items-center gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                Neural Log Stream
              </h3>
              <div className="space-y-5 md:space-y-6">
                {systemLogs.map((log, i) => (
                  <div key={i} className="flex gap-4 group">
                    <div className="w-0.5 h-auto rounded-full bg-slate-800 group-hover:bg-indigo-500 transition-colors" />
                    <div className="flex-1">
                      <p className="text-xs md:text-sm text-slate-400 leading-snug group-hover:text-slate-300 transition-colors">{log.m}</p>
                      <p className="text-[9px] md:text-[10px] text-slate-600 mt-2 font-bold uppercase tracking-widest">{log.t}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
