'use client';

import { Shield, Lock, Settings, Key, Bell } from 'lucide-react';

export default function SettingsPage() {
    const user = { username: 'Admin', role: 'administrator' };
    const isAdmin = true; // Hardcoded administrative access for local mode

    return (
        <div className="p-4 md:p-8 space-y-6 md:space-y-8 min-h-screen bg-[#030712] text-slate-200">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                        <Settings className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight">System Settings</h1>
                        <p className="text-sm text-slate-400 mt-0.5">Configure agent parameters and global keys.</p>
                    </div>
                </div>
                {isAdmin && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                        <Shield className="w-4 h-4 text-emerald-400" />
                        <span className="text-xs font-medium text-emerald-400">Administrator Access</span>
                    </div>
                )}
            </div>

            {/* Content Grid */}
            <div className={`grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6 ${!isAdmin ? 'opacity-50 pointer-events-none grayscale' : ''}`}>
                {/* API Configuration Card */}
                <div className="p-5 md:p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                            <Key className="w-5 h-5 text-indigo-400" />
                        </div>
                        <h3 className="text-lg font-bold text-white">API Configuration</h3>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-medium text-slate-500 mb-1.5">OpenAI API Key</label>
                            <input
                                type="password"
                                placeholder="sk-..."
                                className="w-full h-10 px-4 bg-slate-800 border border-slate-700 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-slate-500 mb-1.5">Gemini API Key</label>
                            <input
                                type="password"
                                placeholder="AIza..."
                                className="w-full h-10 px-4 bg-slate-800 border border-slate-700 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                            />
                        </div>
                    </div>
                </div>

                {/* Notification Preferences Card */}
                <div className="p-5 md:p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                            <Bell className="w-5 h-5 text-purple-400" />
                        </div>
                        <h3 className="text-lg font-bold text-white">Notification Preferences</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                            <span className="text-sm text-slate-300">Email Notifications</span>
                            <div className="w-10 h-6 rounded-full bg-indigo-600 flex items-center justify-end px-1 cursor-pointer">
                                <div className="w-4 h-4 rounded-full bg-white shadow" />
                            </div>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                            <span className="text-sm text-slate-300">Training Alerts</span>
                            <div className="w-10 h-6 rounded-full bg-slate-700 flex items-center justify-start px-1 cursor-pointer">
                                <div className="w-4 h-4 rounded-full bg-slate-400 shadow" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Lock Message for Non-Admins */}
            {!isAdmin && (
                <div className="text-center pt-8 md:pt-12">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-800/50 border border-slate-700">
                        <Lock className="w-4 h-4 text-slate-500" />
                        <p className="text-slate-500 font-medium text-sm">Settings module requires administrator privileges.</p>
                    </div>
                </div>
            )}

            {/* Save Button for Admins */}
            {isAdmin && (
                <div className="flex justify-end pt-4">
                    <button className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-xl shadow-lg shadow-indigo-500/25 transition-all duration-300 hover:scale-[1.02]">
                        Save Changes
                    </button>
                </div>
            )}
        </div>
    );
}
