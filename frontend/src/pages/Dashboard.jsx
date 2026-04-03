import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Layout, LogOut, ShieldCheck, Mail, Database, User, Calendar, Activity } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    if (!user) return null;

    const cards = [
        { icon: Mail, title: 'Email Address', value: user.email, color: 'text-emerald-400' },
        { icon: User, title: 'Username', value: user.username, color: 'text-primary-400' },
        { icon: Calendar, title: 'Joined On', value: new Date(user.createdAt || Date.now()).toLocaleDateString(), color: 'text-amber-400' },
        { icon: Activity, title: 'Account Status', value: user.isActive ? 'Active' : 'Inactive', color: 'text-purple-400' }
    ];

    return (
        <div className="min-h-screen bg-slate-950 p-6 md:p-12 relative overflow-hidden">
            {/* Background elements */}
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary-900/10 rounded-full blur-[120px] translate-x-1/4 -translate-y-1/4"></div>
            <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-indigo-900/10 rounded-full blur-[120px] -translate-x-1/4 translate-y-1/4"></div>

            <div className="max-w-6xl mx-auto relative z-10">
                <header className="flex flex-col md:flex-row md:items-center justify-between mb-12 gap-6">
                    <div>
                        <motion.h1 
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="text-4xl md:text-5xl font-bold text-white tracking-tight"
                        >
                            Welcome back, <span className="bg-gradient-to-r from-primary-400 to-indigo-400 bg-clip-text text-transparent">{user.username}</span>!
                        </motion.h1>
                        <motion.p 
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 }}
                            className="text-slate-400 mt-2 text-lg"
                        >
                            You successfully logged in to the secure dashboard.
                        </motion.p>
                    </div>
                    <motion.button 
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleLogout}
                        id="logout-button"
                        className="btn-secondary flex items-center justify-center gap-2 px-6"
                    >
                        <LogOut className="w-5 h-5 text-slate-400" />
                        <span>Sign Out</span>
                    </motion.button>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                    {cards.map((card, i) => (
                        <motion.div 
                            key={i}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="glass-morphism p-6 rounded-2xl group hover:border-primary-500/30 transition-all cursor-default"
                        >
                            <div className={`p-3 bg-slate-800 rounded-xl w-fit mb-4 group-hover:scale-110 transition-transform`}>
                                <card.icon className={`w-6 h-6 ${card.color}`} />
                            </div>
                            <p className="text-slate-500 text-sm font-medium mb-1">{card.title}</p>
                            <p className="text-white text-lg font-bold truncate">{card.value}</p>
                        </motion.div>
                    ))}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="lg:col-span-2 glass-morphism rounded-2xl overflow-hidden"
                    >
                        <div className="p-6 border-b border-white/10 flex items-center gap-3">
                            <ShieldCheck className="w-6 h-6 text-primary-400" />
                            <h2 className="text-xl font-bold text-white">Security Information</h2>
                        </div>
                        <div className="p-8">
                            <div className="bg-slate-900/50 rounded-xl p-6 border border-slate-800">
                                <h3 className="text-primary-400 font-semibold mb-4 flex items-center gap-2">
                                    <Database className="w-4 h-4" /> System Backend
                                </h3>
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center text-sm border-b border-slate-800 pb-3">
                                        <span className="text-slate-400">Authentication Strategy</span>
                                        <span className="text-slate-100 font-mono uppercase tracking-wider">{user.provider === 'google' ? 'OAuth 2.0 (Google)' : 'JWT Service (Local)'}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-sm border-b border-slate-800 pb-3">
                                        <span className="text-slate-400">Token Management</span>
                                        <span className="text-slate-100 font-mono">Access + Refresh JWT</span>
                                    </div>
                                    <div className="flex justify-between items-center text-sm border-b border-slate-800 pb-3">
                                        <span className="text-slate-400">Secure Transport</span>
                                        <span className="text-emerald-400 flex items-center gap-1"><ShieldCheck className="w-3 h-3" /> Encrypted</span>
                                    </div>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="text-slate-400">Last Password Change</span>
                                        <span className="text-slate-100">None</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                        className="glass-morphism h-full rounded-2xl p-8 flex flex-col items-center justify-center text-center group"
                    >
                        <div className="w-24 h-24 bg-gradient-to-br from-primary-500/20 to-indigo-500/20 rounded-full flex items-center justify-center mb-6 border border-white/10 group-hover:scale-110 transition-transform duration-500">
                            <User className="w-12 h-12 text-primary-400" />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">{user.username}</h3>
                        <p className="text-slate-400 text-sm mb-6 max-w-[200px] leading-relaxed">Your profile is currently set to public visibility within our internal network.</p>
                        <button className="btn-secondary w-full text-sm py-2 group-hover:border-primary-500/50 transition-colors">Edit Profile</button>
                    </motion.div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
