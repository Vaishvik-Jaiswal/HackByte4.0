"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Send, Loader2, X, Paperclip, MoreVertical, Trash2, CheckCircle2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import apiClient from '../../../lib/apiClient';

export default function RedesignedComposePage() {
    const router = useRouter();
    const [to, setTo] = useState('');
    const [subject, setSubject] = useState('');
    const [body, setBody] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null); // 'success', 'error'
    const [message, setMessage] = useState('');

    const handleSend = async (e) => {
        e.preventDefault();
        setLoading(true);
        setStatus(null);
        try {
            await apiClient.post('/gmail/send', { to, subject, body });
            setStatus('success');
            setMessage('Message sent successfully!');
            setTimeout(() => router.push('/gmail'), 1500);
        } catch (err) {
            console.error('Failed to send email:', err);
            setStatus('error');
            setMessage(err.response?.data?.detail || 'Failed to send message. Check permissions.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#f6f8fc] flex items-center justify-center p-4">
            <motion.div 
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className="w-full max-w-2xl bg-white rounded-3xl shadow-[0_8px_24px_rgba(149,157,165,0.2)] border border-[#e0e3e9] overflow-hidden"
            >
                {/* Header Overlay */}
                <div className="h-[64px] bg-[#f2f6fc] px-6 flex items-center justify-between border-b border-[#e0e3e9]">
                    <div className="flex items-center gap-3">
                        <button 
                            onClick={() => router.push('/gmail')}
                            className="p-2 hover:bg-[#d3e3fd] rounded-full text-[#444746] transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <h2 className="text-base font-medium text-[#1f1f1f]">New Message</h2>
                    </div>
                    <div className="flex items-center gap-2">
                        <button className="p-2 hover:bg-[#d3e3fd] rounded-full text-[#444746]">
                            <X className="w-5 h-5" onClick={() => router.push('/gmail')} />
                        </button>
                    </div>
                </div>

                <div className="p-6">
                    <AnimatePresence mode="wait">
                        {status && (
                            <motion.div 
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className={`p-4 rounded-xl mb-6 flex items-center gap-3 border ${
                                    status === 'success' 
                                        ? 'bg-emerald-50 text-emerald-700 border-emerald-100' 
                                        : 'bg-red-50 text-red-700 border-red-100'
                                }`}
                            >
                                {status === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                                <p className="text-sm font-medium">{message}</p>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <form onSubmit={handleSend} className="space-y-4">
                        <div className="border-b border-[#f1f3f4] py-1">
                            <input 
                                type="email" 
                                required
                                placeholder="Recipients"
                                value={to}
                                onChange={(e) => setTo(e.target.value)}
                                className="w-full py-2 bg-transparent border-none outline-none text-sm text-[#1f1f1f] placeholder:text-[#5e5e5e]"
                            />
                        </div>
                        
                        <div className="border-b border-[#f1f3f4] py-1">
                            <input 
                                type="text" 
                                required
                                placeholder="Subject"
                                value={subject}
                                onChange={(e) => setSubject(e.target.value)}
                                className="w-full py-2 bg-transparent border-none outline-none text-sm text-[#1f1f1f] placeholder:text-[#5e5e5e]"
                            />
                        </div>

                        <div className="py-2">
                            <textarea 
                                required
                                placeholder="Compose email"
                                rows={12}
                                value={body}
                                onChange={(e) => setBody(e.target.value)}
                                className="w-full py-2 bg-transparent border-none outline-none text-sm text-[#1f1f1f] placeholder:text-[#5e5e5e] resize-none"
                            ></textarea>
                        </div>


                        <div className="pt-4 flex items-center justify-between border-t border-[#f1f3f4]">
                            <div className="flex items-center gap-2">
                                <button 
                                    type="submit"
                                    disabled={loading}
                                    className="bg-[#0b57d0] hover:bg-[#0842a0] text-white px-8 py-2.5 rounded-full font-medium flex items-center gap-2 transition-all shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed group"
                                >
                                    {loading ? (
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                    ) : (
                                        <>
                                            <span>Send</span>
                                            <Send className="w-4 h-4 ml-1 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                                        </>
                                    )}
                                </button>
                                <button type="button" className="p-2.5 hover:bg-[#f1f3f4] rounded-full text-[#444746]">
                                    <Paperclip className="w-5 h-5" />
                                </button>
                                <button type="button" className="p-2.5 hover:bg-[#f1f3f4] rounded-full text-[#444746]">
                                    <MoreVertical className="w-5 h-5" />
                                </button>
                            </div>
                            <button type="button" className="p-2.5 hover:bg-[#f1f3f4] rounded-full text-[#444746]" onClick={() => {setTo(''); setSubject(''); setBody('');}}>
                                <Trash2 className="w-5 h-5" />
                            </button>
                        </div>
                    </form>
                </div>
            </motion.div>
        </div>
    );
}
