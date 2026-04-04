"use client";

import { useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';
import { LogOut, ShieldCheck, Mail, User, Calendar, Activity, Plus, Settings, Shield, Loader2, LogOut as LogOutIcon } from 'lucide-react';
import { motion } from 'framer-motion';

const Card = ({ icon: Icon, title, value, color, delay }) => (
    <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay }}
        className="bg-white p-6 rounded-3xl border border-[#e0e3e9] shadow-sm hover:shadow-md transition-all group"
    >
        <div className={`p-3 rounded-2xl w-fit mb-4 group-hover:scale-110 transition-transform ${color.bg}`}>
            <Icon className={`w-6 h-6 ${color.text}`} />
        </div>
        <p className="text-[#5e5e5e] text-xs font-medium mb-1 uppercase tracking-wider">{title}</p>
        <p className="text-[#1f1f1f] text-lg font-bold truncate">{value}</p>
    </motion.div>
);

export default function RedesignedDashboardPage() {
    const { user, loading, logout } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading && !user) {
            router.push('/login');
        }
    }, [user, loading, router]);

    const handleLogout = async () => {
        await logout();
        router.push('/login');
    };

    if (loading || !user) return (
        <div className="flex items-center justify-center min-h-screen bg-[#f6f8fc]">
            <Loader2 className="w-10 h-10 text-[#0b57d0] animate-spin" />
        </div>
    );

    const stats = [
        { icon: Mail, title: 'Email Address', value: user.email, color: { bg: 'bg-emerald-50', text: 'text-emerald-600' } },
        { icon: User, title: 'Username', value: user.username, color: { bg: 'bg-blue-50', text: 'text-blue-600' } },
        { icon: Calendar, title: 'Joined On', value: new Date(user.created_at).toLocaleDateString(), color: { bg: 'bg-amber-50', text: 'text-amber-600' } },
        { icon: Activity, title: 'Account Status', value: user.is_active ? 'Active' : 'Inactive', color: { bg: 'bg-purple-50', text: 'text-purple-600' } }
    ];

    return (
        <div className="min-h-screen bg-[#f6f8fc] text-[#1f1f1f] p-6 md:p-12 font-sans">
            <div className="max-w-6xl mx-auto">
                <header className="flex flex-col md:flex-row md:items-center justify-between mb-12 gap-6">
                    <div>
                        <motion.div 
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="flex items-center gap-3 mb-2"
                        >
                            <div className="bg-[#0b57d0] p-1.5 rounded-lg shadow-sm">
                                <Shield className="w-5 h-5 text-white" />
                            </div>
                            <span className="text-[#5e5e5e] font-medium text-sm">Dashboard</span>
                        </motion.div>
                        <motion.h1 
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 }}
                            className="text-4xl md:text-5xl font-bold tracking-tight text-[#1f1f1f]"
                        >
                            Welcome back, <span className="text-[#0b57d0]">{user.username}</span>
                        </motion.h1>
                    </div>
                    <motion.button 
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleLogout}
                        className="bg-white border border-[#e0e3e9] flex items-center justify-center gap-2 px-6 py-3 rounded-2xl font-medium text-[#444746] hover:bg-[#f2f6fc] transition-all shadow-sm"
                    >
                        <LogOut className="w-5 h-5" />
                        <span>Sign Out</span>
                    </motion.button>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                    {stats.map((stat, i) => (
                        <Card 
                            key={i}
                            icon={stat.icon}
                            title={stat.title}
                            value={stat.value}
                            color={stat.color}
                            delay={i * 0.1}
                        />
                    ))}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="md:col-span-2 bg-[#0b57d0] rounded-[32px] p-8 md:p-12 text-white relative overflow-hidden group cursor-pointer shadow-xl shadow-blue-900/10"
                        onClick={() => router.push('/gmail')}
                    >
                        <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-all translate-x-4 -translate-y-4 group-hover:translate-x-0 group-hover:translate-y-0">
                            <Mail className="w-48 h-48" />
                        </div>
                        <div className="relative z-10 flex flex-col h-full">
                            <div className="bg-white/20 p-3 rounded-2xl w-fit mb-6 backdrop-blur-md">
                                <Mail className="w-8 h-8 text-white" />
                            </div>
                            <h2 className="text-3xl font-bold mb-4">Gmail Integration</h2>
                            <p className="text-blue-100 text-lg mb-8 max-w-md">Access your professional inbox, manage high-priority emails, and send secure messages with our built-in Gmail service.</p>
                            <div className="mt-auto">
                                <button className="bg-white text-[#0b57d0] px-8 py-3 rounded-full font-bold flex items-center gap-2 hover:bg-blue-50 transition-all shadow-lg group-hover:scale-105">
                                    <span>Launch Inbox</span>
                                    <Plus className="w-5 h-5 leading-none" />
                                </button>
                            </div>
                        </div>
                    </motion.div>

                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                        className="bg-white rounded-[32px] p-8 border border-[#e0e3e9] shadow-sm flex flex-col"
                    >
                        <div className="flex items-center gap-3 mb-8">
                            <div className="p-3 bg-emerald-50 rounded-2xl">
                                <ShieldCheck className="w-6 h-6 text-emerald-600" />
                            </div>
                            <h2 className="text-xl font-bold text-[#1f1f1f]">Security Control</h2>
                        </div>
                        <div className="space-y-6 flex-1">
                            <div className="space-y-1">
                                <p className="text-[#5e5e5e] text-xs font-medium uppercase">Authentication</p>
                                <p className="text-[#1f1f1f] font-semibold">{user.provider === 'google' ? 'Connected via Google' : 'Local Password'}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[#5e5e5e] text-xs font-medium uppercase">Last Sync</p>
                                <p className="text-[#1f1f1f] font-semibold">Just now</p>
                            </div>
                            <div className="pt-4 border-t border-[#f1f3f4]">
                                <div className="flex items-center gap-2 text-emerald-600 font-medium text-sm">
                                    <ShieldCheck className="w-4 h-4" />
                                    <span>Verified Account</span>
                                </div>
                            </div>
                        </div>
                        <button className="mt-8 w-full py-3 bg-[#f6f8fc] text-[#444746] rounded-2xl font-medium border border-[#e0e3e9] hover:bg-[#eaeef3] transition-all flex items-center justify-center gap-2">
                            <Settings className="w-4 h-4" />
                            <span>Preferences</span>
                        </button>
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
