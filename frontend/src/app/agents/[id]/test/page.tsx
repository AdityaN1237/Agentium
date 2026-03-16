'use client';

import { useParams } from 'next/navigation';
import { TestAgentPanel } from '@/components/agents/TestAgentPanel';
import Link from 'next/link';
import { BrainCircuit, ArrowLeft } from 'lucide-react';

export default function AgentTestPage() {
  const { id } = useParams();
  const agentId = String(id || '');

  return (
    <div className="relative min-h-screen mesh-gradient bg-grid pb-20">
      <div className="max-w-[1200px] mx-auto p-6 md:p-8 lg:p-12 space-y-10">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href={`/agents/${agentId}`} className="p-3 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
              <ArrowLeft className="w-5 h-5 text-slate-400" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <BrainCircuit className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-2xl font-black text-white tracking-tight">Test Agent: {agentId}</h1>
            </div>
          </div>
        </div>

        {/* Test Panel */}
        <div className="grid grid-cols-1 gap-8">
          <section className="space-y-6">
            <div className="p-6 rounded-[32px] glass-card space-y-6">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Interactive Debug Console</p>

              <TestAgentPanel agentId={agentId} agentType={agentId} />

            </div>
          </section>
        </div>

      </div>
    </div>
  );
}
