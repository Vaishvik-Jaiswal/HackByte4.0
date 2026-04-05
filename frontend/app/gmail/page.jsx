"use client";

import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';
import apiClient from '../../lib/apiClient';
import { 
    Mail, RefreshCw, Inbox, ArrowLeft, Loader2, Search, Menu, 
    Settings, HelpCircle, Grid, Send, Trash2, Edit3, AlertCircle, 
    ChevronLeft, ChevronRight, Star, MoreVertical, Database, Sparkles, Workflow, X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    AIPipelineDrawer,
    EmailPipelineTrace,
    PIPELINE_STAGES,
} from '../../components/gmail/AIPipelineVisualization';

/** Pull bare email address from a From header for replies. */
function extractReplyAddress(fromStr) {
    if (!fromStr || typeof fromStr !== 'string') return '';
    const angle = fromStr.match(/<([^>]+)>/);
    if (angle) return angle[1].trim();
    const loose = fromStr.match(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/);
    return loose ? loose[0].trim() : '';
}

const SidebarItem = ({ icon: Icon, label, active, onClick, count }) => (
    <div 
        onClick={onClick}
        className={`flex items-center justify-between gap-4 px-6 py-2 rounded-r-full cursor-pointer transition-all text-sm font-medium pr-4 ${
            active 
                ? 'bg-[#d3e3fd] text-[#001d35]' 
                : 'text-[#444746] hover:bg-[#eaeef3]'
        }`}
    >
        <div className="flex items-center gap-4">
            <Icon className={`w-[18px] h-[18px] ${active ? 'fill-current' : ''}`} />
            <span>{label}</span>
        </div>
        {count > 0 && <span className={`text-xs ${active ? 'font-bold' : ''}`}>{count}</span>}
    </div>
);

export default function RedesignedGmailPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const [emails, setEmails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [label, setLabel] = useState('INBOX'); // INBOX, SENT, STARRED, etc.
    const [visibleCount, setVisibleCount] = useState(10);
    const [searchTerm, setSearchTerm] = useState('');
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [selectedEmail, setSelectedEmail] = useState(null);
    const [starredIds, setStarredIds] = useState([]);
    const [syncLoading, setSyncLoading] = useState(false);
    const [pipelineOpen, setPipelineOpen] = useState(false);
    const [pipelineHighlightIndex, setPipelineHighlightIndex] = useState(0);
    const [lastAiProcessing, setLastAiProcessing] = useState(null);
    const [syncBanner, setSyncBanner] = useState(null);

    useEffect(() => {
        const savedStarred = localStorage.getItem('gmail_starred_ids');
        if (savedStarred) {
            setStarredIds(JSON.parse(savedStarred));
        }
    }, []);

    // Cycle through pipeline stages while sync + AI run (educational animation for demos).
    useEffect(() => {
        if (!syncLoading) return undefined;
        setPipelineHighlightIndex(0);
        const n = PIPELINE_STAGES.length;
        const id = setInterval(() => {
            setPipelineHighlightIndex((i) => (i + 1) % n);
        }, 650);
        return () => clearInterval(id);
    }, [syncLoading]);

    const fetchEmails = async (selectedLabel = label) => {
        if (selectedLabel === 'STARRED') {
            // For STARRED, we fetch INBOX and filter locally for now, 
            // or just keep the emails we already have and filter.
            // A better way is to fetch all and filter.
            setLoading(true);
            try {
                // Fetch both INBOX and SENT to find all starred emails
                const [inboxRes, sentRes] = await Promise.all([
                    apiClient.get('/gmail/messages?label=INBOX'),
                    apiClient.get('/gmail/messages?label=SENT')
                ]);
                const allEmails = [...inboxRes.data, ...sentRes.data];
                // Remove duplicates by ID
                const uniqueEmails = Array.from(new Map(allEmails.map(item => [item.id, item])).values());
                setEmails(uniqueEmails);
            } catch (err) {
                setError('Failed to fetch starred emails.');
            } finally {
                setLoading(false);
            }
            return;
        }

        setLoading(true);
        setError(null);
        try {
            const response = await apiClient.get(`/gmail/messages?label=${selectedLabel}`);
            setEmails(response.data);
            setVisibleCount(10);
        } catch (err) {
            console.error('Failed to fetch emails:', err);
            setError(err.response?.data?.detail || 'Failed to load emails. Check your Google permissions.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!authLoading && !user) {
            router.push('/login');
            return;
        }
        if (user) {
            fetchEmails(label);
        }
    }, [user, authLoading, router, label]);

    const toggleStar = (e, id) => {
        e.stopPropagation();
        const newStarred = starredIds.includes(id) 
            ? starredIds.filter(sid => sid !== id) 
            : [...starredIds, id];
        setStarredIds(newStarred);
        localStorage.setItem('gmail_starred_ids', JSON.stringify(newStarred));
    };

    const handleSyncEmails = async () => {
        setSyncLoading(true);
        setSyncBanner(null);
        try {
            const response = await apiClient.post('/gmail/sync');
            const synced = response.data?.synced ?? 0;
            const ai = response.data?.ai_processing ?? null;
            setLastAiProcessing(ai);

            let banner = `Synced ${synced} new message(s) from Gmail.`;
            if (ai?.status === 'ok') {
                banner += ` AI: ${ai.inbox_processed ?? 0} inbox processed, ${ai.sent_marked_processed ?? 0} sent marked (no generation).`;
            } else if (ai?.status === 'error') {
                banner += ` AI error: ${ai.detail || 'see server logs'}.`;
            } else if (ai?.status === 'skipped') {
                banner += ` AI skipped (${ai.reason || 'config'}). Open “AI pipeline” for details.`;
            }
            setSyncBanner(banner);

            fetchEmails(label);
        } catch (err) {
            console.error('Sync failed:', err);
            setSyncBanner(err.response?.data?.detail || 'Sync failed. Check Google permissions and try again.');
        } finally {
            setSyncLoading(false);
        }
    };

    const openSuggestedReplyInCompose = (email) => {
        const ai = email?.ai;
        if (!ai?.suggested_reply || !ai?.reply_needed) return;
        const to = extractReplyAddress(email.from);
        const sub = email.subject || '';
        const reSubject = sub.toLowerCase().startsWith('re:') ? sub : `Re: ${sub}`;
        try {
            sessionStorage.setItem(
                'gmail_compose_prefill',
                JSON.stringify({
                    to,
                    subject: reSubject,
                    body: ai.suggested_reply,
                })
            );
        } catch (_) {
            return;
        }
        router.push('/gmail/compose');
    };

    if (authLoading) return (
        <div className="flex items-center justify-center min-h-screen bg-slate-50">
            <Loader2 className="w-10 h-10 text-[#0b57d0] animate-spin" />
        </div>
    );

    const sidebarItems = [
        { id: 'INBOX', icon: Inbox, label: 'Inbox', count: label === 'INBOX' ? emails.length : 0 },
        { id: 'STARRED', icon: Star, label: 'Starred', count: starredIds.length },
        { id: 'SENT', icon: Send, label: 'Sent', count: label === 'SENT' ? emails.length : 0 },
        { id: 'DRAFTS', icon: Edit3, label: 'Drafts' },
        { id: 'SPAM', icon: AlertCircle, label: 'Spam' },
        { id: 'TRASH', icon: Trash2, label: 'Trash' },
    ];

    const filteredEmails = label === 'STARRED' 
        ? emails.filter(e => starredIds.includes(e.id))
        : emails;

    const visibleEmails = filteredEmails
        .filter(e => 
            e.subject.toLowerCase().includes(searchTerm.toLowerCase()) || 
            e.from.toLowerCase().includes(searchTerm.toLowerCase()) ||
            e.snippet.toLowerCase().includes(searchTerm.toLowerCase())
        )
        .slice(0, visibleCount);

    return (
        <div className="min-h-screen bg-[#f6f8fc] text-[#1f1f1f] flex flex-col font-sans">
            {/* Top Header */}
            <header className="h-[64px] px-4 flex items-center justify-between select-none">
                <div className="flex items-center gap-4 min-w-[240px]">
                    <button 
                        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                        className="p-3 hover:bg-[#eaeef3] rounded-full transition-colors"
                    >
                        <Menu className="w-5 h-5 text-[#444746]" />
                    </button>
                    <div className="flex items-center gap-2 cursor-pointer" onClick={() => router.push('/dashboard')}>
                        <div className="bg-[#0b57d0] p-1.5 rounded-lg">
                            <Mail className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-[22px] text-[#444746] font-medium tracking-tight">Gmail</span>
                    </div>
                </div>

                <div className="flex-1 max-w-[720px] ml-8">
                    <div className="flex items-center gap-3 bg-[#eaf1fb] px-4 py-2 rounded-full focus-within:bg-white focus-within:shadow-md transition-all">
                        <Search className="w-5 h-5 text-[#444746]" />
                        <input 
                            type="text" 
                            placeholder="Search mail"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="bg-transparent border-none outline-none text-base w-full placeholder:text-[#5e5e5e]"
                        />
                    </div>
                </div>

                <div className="flex items-center gap-2 ml-4">
                    <button className="p-2.5 hover:bg-[#eaeef3] rounded-full text-[#444746]">
                        <HelpCircle className="w-5 h-5" />
                    </button>
                    <button className="p-2.5 hover:bg-[#eaeef3] rounded-full text-[#444746]">
                        <Settings className="w-5 h-5" />
                    </button>
                    <button className="p-2.5 hover:bg-[#eaeef3] rounded-full text-[#444746]">
                        <Grid className="w-5 h-5" />
                    </button>
                    <div className="w-8 h-8 rounded-full bg-[#0b57d0] text-white flex items-center justify-center font-bold text-sm ml-2 cursor-pointer">
                        {user?.username?.charAt(0).toUpperCase()}
                    </div>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                {/* Left Sidebar */}
                <aside className={`transition-all duration-300 ${sidebarCollapsed ? 'w-[72px]' : 'w-[256px]'} flex flex-col pr-4`}>
                    <div className="px-2 py-4">
                        <button 
                            onClick={() => router.push('/gmail/compose')}
                            className={`flex items-center gap-4 bg-[#c2e7ff] hover:bg-[#b3d7f0] text-[#001d35] p-4 transition-all shadow-sm hover:shadow-md rounded-2xl ${sidebarCollapsed ? 'w-14 justify-center pr-4' : 'px-6 pr-8 ml-2'}`}
                        >
                            <Edit3 className="w-6 h-6" />
                            {!sidebarCollapsed && <span className="font-medium">Compose</span>}
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto pt-2">
                        {sidebarItems.map((item) => (
                            !sidebarCollapsed ? (
                                <SidebarItem 
                                    key={item.id}
                                    icon={item.icon}
                                    label={item.label}
                                    active={label === item.id}
                                    count={item.count}
                                    onClick={() => setLabel(item.id)}
                                />
                            ) : (
                                <div 
                                    key={item.id}
                                    onClick={() => setLabel(item.id)}
                                    className={`flex items-center justify-center p-3 mx-2 rounded-full cursor-pointer hover:bg-[#eaeef3] ${label === item.id ? 'bg-[#d3e3fd]' : ''}`}
                                >
                                    <item.icon className={`w-5 h-5 ${label === item.id ? 'text-[#001d35]' : 'text-[#444746]'}`} />
                                </div>
                            )
                        ))}
                    </div>
                </aside>

                {/* Main Email Area */}
                <main className="flex-1 bg-white rounded-t-3xl border border-[#e0e3e9] flex flex-col mr-4 mb-4 shadow-[0_1px_2px_0_rgba(60,64,67,0.3),0_1px_3px_1px_rgba(60,64,67,0.15)] relative">
                    {/* Toolbar */}
                    <div className="shrink-0 border-b border-[#f1f3f4]">
                        <div className="h-[48px] px-4 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <button className="p-2 hover:bg-[#f1f3f4] rounded-full text-[#444746]" onClick={() => fetchEmails(label)} title="Refresh list">
                                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                                </button>
                                <button 
                                    onClick={handleSyncEmails}
                                    disabled={syncLoading}
                                    className={`flex items-center gap-2 px-3 py-1.5 hover:bg-[#f1f3f4] rounded-md text-[#444746] text-xs font-semibold uppercase tracking-wider transition-all border border-transparent hover:border-[#f1f3f4] ${syncLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                                >
                                    {syncLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Database className="w-3.5 h-3.5" />}
                                    Sync Emails
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setPipelineOpen(true)}
                                    className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#e8f0fe] rounded-md text-[#0b57d0] text-xs font-semibold uppercase tracking-wider transition-all border border-[#d3e3fd]"
                                    title="Show how inbox AI runs in the backend"
                                >
                                    <Workflow className="w-3.5 h-3.5" />
                                    AI pipeline
                                </button>
                                <button className="p-2 hover:bg-[#f1f3f4] rounded-full text-[#444746]">
                                    <MoreVertical className="w-4 h-4" />
                                </button>
                            </div>
                            <div className="flex items-center gap-1 text-xs text-[#5e5e5e] font-medium">
                                <span>1 - {visibleEmails.length} of {filteredEmails.length}</span>
                                <button className="p-2 hover:bg-[#f1f3f4] rounded-full ml-2">
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                <button className="p-2 hover:bg-[#f1f3f4] rounded-full">
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                        {syncBanner && (
                            <div className="flex items-start gap-2 border-t border-[#e8f0fe] bg-[#f8fbff] px-4 py-2 text-xs text-[#001d35]">
                                <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#0b57d0]" />
                                <p className="min-w-0 flex-1 leading-snug">{syncBanner}</p>
                                <button
                                    type="button"
                                    onClick={() => setSyncBanner(null)}
                                    className="shrink-0 rounded-full p-1 hover:bg-[#e8f0fe]"
                                    aria-label="Dismiss"
                                >
                                    <X className="h-3.5 w-3.5 text-[#444746]" />
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Email List Container */}
                    <div className="flex-1 overflow-y-auto">
                        <AnimatePresence mode="wait">
                            {loading && emails.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-full gap-4 text-[#5e5e5e]">
                                    <Loader2 className="w-8 h-8 animate-spin text-[#0b57d0]" />
                                    <p className="text-sm">Fetching messages...</p>
                                </div>
                            ) : error ? (
                                <div className="flex flex-col items-center justify-center h-full p-8 text-center text-[#d93025]">
                                    <AlertCircle className="w-12 h-12 mb-4" />
                                    <p className="max-w-md font-medium">{error}</p>
                                    <button 
                                        onClick={() => window.location.reload()}
                                        className="mt-6 px-4 py-2 border border-[#f1f3f4] rounded-lg hover:bg-[#f8f9fa] text-slate-700 font-medium transition-colors"
                                    >
                                        Try Again
                                    </button>
                                </div>
                            ) : filteredEmails.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-full gap-4 opacity-30 text-[#5e5e5e]">
                                    <Inbox className="w-20 h-20" />
                                    <p className="text-lg font-medium">No messages found in your {label.toLowerCase()}</p>
                                </div>
                            ) : (
                                <div className="flex flex-col">
                                    {visibleEmails.map((email, i) => (
                                        <motion.div 
                                            key={email.id}
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            onClick={() => setSelectedEmail(email)}
                                            className={`gmail-email-row ${i === 0 ? 'border-t-0' : ''}`}
                                        >
                                            <div className="flex items-center gap-3 w-[240px] shrink-0">
                                                <div className="flex items-center gap-1">
                                                    <div className="w-5 h-5 flex items-center justify-center hover:bg-[#f2f6fc] rounded shrink-0 cursor-default" onClick={(e) => e.stopPropagation()}>
                                                        <div className="w-4 h-4 border border-[#c4c7c5] rounded-sm"></div>
                                                    </div>
                                                    <div className="w-5 h-5 flex items-center justify-center hover:bg-[#f2f6fc] rounded shrink-0" onClick={(e) => toggleStar(e, email.id)}>
                                                        <Star className={`w-4 h-4 ${starredIds.includes(email.id) ? 'fill-[#f7d600] text-[#f7d600]' : 'text-[#c4c7c5]'}`} />
                                                    </div>
                                                </div>
                                                <span className={`text-sm truncate pr-4 ${!email.isRead ? 'font-bold' : ''}`}>{email.from}</span>
                                            </div>

                                            <div className="flex-1 flex items-baseline gap-2 overflow-hidden">
                                                <span className={`text-sm whitespace-nowrap shrink-0 ${!email.isRead ? 'font-bold' : ''}`}>{email.subject}</span>
                                                {email.ai?.reply_needed && email.ai?.suggested_reply && (
                                                    <span className="inline-flex items-center gap-0.5 shrink-0 text-[11px] font-semibold uppercase tracking-wide text-[#0b57d0] bg-[#e8f0fe] px-1.5 py-0.5 rounded">
                                                        <Sparkles className="w-3 h-3" />
                                                        Draft
                                                    </span>
                                                )}
                                                <span className="text-sm text-[#5e5e5e] truncate break-all">- {email.snippet}</span>
                                            </div>

                                            <div className="w-[100px] shrink-0 flex justify-end text-xs font-medium text-[#5e5e5e]">
                                                {email.date}
                                            </div>
                                        </motion.div>
                                    ))}

                                    {visibleCount < filteredEmails.length && (
                                        <div className="p-8 flex justify-center">
                                            <button 
                                                onClick={() => setVisibleCount(prev => prev + 10)}
                                                className="bg-white border border-[#f1f3f4] px-6 py-2 rounded-full text-sm font-medium text-[#0b57d0] hover:bg-[#f8f9fa] shadow-sm transition-all"
                                            >
                                                Load More
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Email Detail View */}
                    <AnimatePresence>
                        {selectedEmail && (
                            <motion.div 
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.2 }}
                                className="absolute inset-0 z-50 flex w-full min-w-0 flex-col rounded-t-3xl bg-white"
                            >
                                <div className="h-[48px] px-4 flex items-center gap-4 border-b border-[#f1f3f4]">
                                    <button 
                                        onClick={() => setSelectedEmail(null)}
                                        className="p-2 hover:bg-[#f1f3f4] rounded-full text-[#444746]"
                                    >
                                        <ArrowLeft className="w-5 h-5" />
                                    </button>
                                    <button className="p-2 hover:bg-[#f1f3f4] rounded-full text-[#444746]" onClick={(e) => toggleStar(e, selectedEmail.id)}>
                                        <Star className={`w-5 h-5 ${starredIds.includes(selectedEmail.id) ? 'fill-[#f7d600] text-[#f7d600]' : 'text-[#c4c7c5]'}`} />
                                    </button>
                                    <button className="p-2 hover:bg-[#f1f3f4] rounded-full text-[#444746] ml-auto">
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </div>
                                <div className="min-w-0 flex-1 overflow-y-auto overflow-x-hidden">
                                    <div className="w-full px-6 py-8 text-left sm:px-8">
                                        <h2 className="text-2xl font-normal mb-8 text-[#1f1f1f]">{selectedEmail.subject}</h2>
                                        <div className="flex items-start justify-between mb-8">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-[#0b57d0] text-white flex items-center justify-center font-bold">
                                                    {selectedEmail.from.charAt(0).toUpperCase()}
                                                </div>
                                                <div>
                                                    <p className="font-bold text-sm">{selectedEmail.from}</p>
                                                    <p className="text-xs text-[#5e5e5e]">to me</p>
                                                </div>
                                            </div>
                                            <span className="text-xs text-[#5e5e5e] shrink-0 ml-4">{selectedEmail.date}</span>
                                        </div>
                                        {(() => {
                                            const email = selectedEmail;
                                            const ai = email.ai;
                                            const summaryTrimmed = (ai?.summary || '').trim();
                                            const showAiSideRail = Boolean(ai);
                                            const hasSummary = Boolean(summaryTrimmed);
                                            const mainColumn = (
                                                <>
                                                    {ai?.reply_needed && ai?.suggested_reply && (
                                                        <div className="p-5 rounded-2xl bg-[#e8f0fe] border border-[#c7d9fc]">
                                                            <div className="flex items-center gap-2 mb-3 flex-wrap">
                                                                <Sparkles className="w-5 h-5 text-[#0b57d0]" />
                                                                <p className="text-sm font-semibold text-[#001d35]">Suggested reply</p>
                                                                {ai.relay_applied && (
                                                                    <span className="text-[11px] font-semibold uppercase tracking-wide text-[#155e00] bg-[#e6f4ea] px-2 py-0.5 rounded">
                                                                        Uses prior briefing
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <p className="text-sm text-[#1f1f1f] whitespace-pre-wrap leading-relaxed mb-4">
                                                                {ai.suggested_reply}
                                                            </p>
                                                            <button
                                                                type="button"
                                                                onClick={() => openSuggestedReplyInCompose(email)}
                                                                className="inline-flex items-center gap-2 bg-[#0b57d0] hover:bg-[#0842a0] text-white text-sm font-medium px-5 py-2.5 rounded-full shadow-sm transition-colors"
                                                            >
                                                                <Send className="w-4 h-4" />
                                                                Open in compose & send
                                                            </button>
                                                            <p className="text-xs text-[#5e5e5e] mt-3">
                                                                Opens compose with To, Subject, and body filled in — review and tap Send.
                                                            </p>
                                                        </div>
                                                    )}
                                                    {(() => {
                                                        const content = email.body || email.snippet;
                                                        const isHtml = content && (content.includes('<html') || content.includes('<div') || content.includes('<p') || content.includes('<table'));
                                                        const plainClass = showAiSideRail
                                                            ? 'text-sm leading-relaxed text-[#1f1f1f] whitespace-pre-wrap break-words pb-6'
                                                            : 'text-sm leading-relaxed text-[#1f1f1f] whitespace-pre-wrap break-words mb-10';
                                                        if (!isHtml) {
                                                            return (
                                                                <div className={plainClass}>
                                                                    {content}
                                                                </div>
                                                            );
                                                        }
                                                        const iframeWrapClass = showAiSideRail
                                                            ? 'w-full border border-[#f1f3f4] rounded-xl overflow-hidden bg-white'
                                                            : 'w-full mb-10 border border-[#f1f3f4] rounded-xl overflow-hidden bg-white';
                                                        return (
                                                            <div className={iframeWrapClass}>
                                                                <iframe
                                                                    title="Email Content"
                                                                    srcDoc={`
                                                            <!DOCTYPE html>
                                                            <html>
                                                                <head>
                                                                    <style>
                                                                        body {
                                                                            font-family: 'Roboto', sans-serif;
                                                                            font-size: 14px;
                                                                            line-height: 1.6;
                                                                            color: #1f1f1f;
                                                                            margin: 0;
                                                                            padding: 24px;
                                                                            word-wrap: break-word;
                                                                        }
                                                                        img { max-width: 100%; height: auto; }
                                                                        a { color: #0b57d0; }
                                                                    </style>
                                                                </head>
                                                                <body>${content}</body>
                                                            </html>
                                                        `}
                                                                    className="w-full min-h-[600px] border-none"
                                                                    sandbox="allow-popups allow-popups-to-escape-sandbox"
                                                                />
                                                            </div>
                                                        );
                                                    })()}
                                                </>
                                            );

                                            if (showAiSideRail) {
                                                return (
                                                    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(260px,340px)] lg:items-start lg:gap-8 xl:gap-10">
                                                        <div className="min-w-0 max-w-3xl space-y-6">
                                                            {mainColumn}
                                                        </div>
                                                        <aside className="min-w-0 lg:sticky lg:top-4 lg:self-start">
                                                            <div className="p-4 rounded-2xl bg-[#f8fafc] border border-[#e2e8f0] shadow-sm">
                                                                <p className="text-xs font-semibold uppercase tracking-wide text-[#64748b] mb-2">AI summary</p>
                                                                {hasSummary ? (
                                                                    <p className="text-sm text-[#1e293b] leading-relaxed">{summaryTrimmed}</p>
                                                                ) : (
                                                                    <p className="text-sm text-[#94a3b8] leading-relaxed">
                                                                        No summary stored yet — tap Sync emails if this message was just added.
                                                                    </p>
                                                                )}
                                                                {ai.category && (
                                                                    <p className="text-xs text-[#94a3b8] mt-2">Category: {ai.category}</p>
                                                                )}
                                                                {ai.tone_reason && (
                                                                    <p className="text-xs text-[#64748b] mt-2 leading-relaxed border-t border-[#e2e8f0] pt-2">
                                                                        Tone note: {ai.tone_reason}
                                                                    </p>
                                                                )}
                                                                <EmailPipelineTrace ai={ai} />
                                                            </div>
                                                        </aside>
                                                    </div>
                                                );
                                            }
                                            return (
                                                <div className="mx-auto w-full max-w-3xl space-y-6">{mainColumn}</div>
                                            );
                                        })()}
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </main>
            </div>

            <AIPipelineDrawer
                open={pipelineOpen}
                onClose={() => setPipelineOpen(false)}
                syncInProgress={syncLoading}
                highlightIndex={pipelineHighlightIndex}
                lastAiProcessing={lastAiProcessing}
            />
        </div>

    );
}
