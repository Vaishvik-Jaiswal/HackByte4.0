"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import { LogIn, User, Lock, Chrome, Loader2, Shield } from 'lucide-react';
import { motion } from 'framer-motion';

export default function RedesignedLoginPage() {
    const [formData, setFormData] = useState({ identifier: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const router = useRouter();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(formData.identifier, formData.password);
            router.push('/dashboard');
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = () => {
        window.location.href = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/google/login`;
    };

    return (
        <div className="flex items-center justify-center min-h-screen px-4 bg-[#f6f8fc]">
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-[448px] bg-white p-8 md:p-12 rounded-[28px] shadow-sm border border-[#e0e3e9] text-[#1f1f1f]"
            >
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-12 h-12 bg-[#0b57d0] rounded-xl mb-6 shadow-sm">
                        <Shield className="w-6 h-6 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight text-[#1f1f1f]">Sign in</h1>
                    <p className="text-[#5e5e5e] mt-2">Use your HackByte Account</p>
                </div>

                {error && (
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-red-50 text-red-700 p-4 rounded-xl mb-6 text-sm flex items-center gap-3 border border-red-100"
                    >
                        <div className="p-1 bg-red-100 rounded-full">
                            <Lock className="w-4 h-4" />
                        </div>
                        {error}
                    </motion.div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                        <div className="relative group">
                            <input 
                                type="text" 
                                name="identifier" 
                                placeholder="Email or username"
                                className="w-full px-4 py-4 bg-white border border-[#c4c7c5] rounded-xl outline-none focus:border-[#0b57d0] focus:ring-1 focus:ring-[#0b57d0] transition-all text-base" 
                                value={formData.identifier}
                                onChange={handleChange}
                                required
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <div className="relative">
                            <input 
                                type="password" 
                                name="password" 
                                placeholder="Password"
                                className="w-full px-4 py-4 bg-white border border-[#c4c7c5] rounded-xl outline-none focus:border-[#0b57d0] focus:ring-1 focus:ring-[#0b57d0] transition-all text-base" 
                                value={formData.password}
                                onChange={handleChange}
                                required
                            />
                        </div>
                    </div>

                    <div className="flex flex-col gap-3 pt-4">
                        <button   
                            type="submit" 
                            className="w-full bg-[#0b57d0] hover:bg-[#0842a0] text-white font-bold py-3 rounded-full transition-all flex items-center justify-center gap-2 shadow-sm"
                            disabled={loading}
                        >
                            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Next'}
                        </button>

                        <button 
                            type="button" 
                            onClick={handleGoogleLogin} 
                            className="w-full bg-white border border-[#e0e3e9] hover:bg-[#f2f6fc] text-[#444746] font-bold py-3 rounded-full transition-all flex items-center justify-center gap-3 shadow-sm mt-2"
                        >
                            <Chrome className="w-5 h-5 text-red-500" />
                            <span>Sign in with Google</span>
                        </button>
                    </div>
                </form>

                <div className="flex items-center justify-between mt-10">
                    <Link href="/register" className="text-[#0b57d0] text-sm font-bold hover:underline">
                        Create account
                    </Link>
                    <button className="text-[#5e5e5e] text-sm font-medium hover:underline">
                        Forgot password?
                    </button>
                </div>
            </motion.div>
        </div>
    );
}
