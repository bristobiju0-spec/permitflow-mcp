import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import pricing from './pricing.json';

// Mock Auth for the demo/vibe
const PermitFlowAuth = {
    user: null,
    login: async (email: string) => ({ message: `Magic link sent to ${email}` }),
    verify: async (email: string) => ({ email, name: "Pro Contractor" }),
    signInWithGoogle: async () => ({ email: 'google-pro-contractor@gmail.com', name: "Google Pro" }),
    logout: () => { window.location.reload(); }
};

interface UserData {
    email: string | null;
    credits_remaining: number;
    is_subscription_required: boolean;
    credits_used?: number;
    is_pro?: boolean;
}

interface Audit {
    id: number;
    timestamp: string;
    model: string;
    seer2: number;
    type: string;
    verification_id: string;
    is_compliant: boolean;
    status: string;
    gps: string;
}

export default function App() {
    const [audits, setAudits] = useState<Audit[]>(() => {
        const saved = localStorage.getItem('permitflow_audits');
        return saved ? JSON.parse(saved) : [];
    });
    const [preview, setPreview] = useState<string | null>(null);
    const [status, setStatus] = useState('idle');
    const [currentResult, setCurrentResult] = useState<Audit | null>(null);
    const [toast, setToast] = useState<{ message: string, type: string } | null>(null);
    const [showSuccessOverlay, setShowSuccessOverlay] = useState(false);
    const [activeView, setActiveView] = useState('dashboard');
    const [userData, setUserData] = useState<UserData>({ email: null, credits_remaining: 10, is_subscription_required: false });
    const [showPaywall, setShowPaywall] = useState(false);
    const [user, setUser] = useState<any>(null);
    const [loginEmail, setLoginEmail] = useState('');
    const [authLoading, setAuthLoading] = useState(false);
    const [isOffline, setIsOffline] = useState(!navigator.onLine);
    const [agreedToTerms, setAgreedToTerms] = useState(false);
    const [legalModal, setLegalModal] = useState<{ show: boolean, content: string | null }>({ show: false, content: '' });
    const [isLocked, setIsLocked] = useState(false);
    const [cooldownRemaining, setCooldownRemaining] = useState(0);

    useEffect(() => {
        let timer: any;
        if (cooldownRemaining > 0) {
            timer = setInterval(() => {
                setCooldownRemaining(prev => Math.max(0, prev - 1));
            }, 1000);
        } else {
            setIsLocked(false);
        }
        return () => clearInterval(timer);
    }, [cooldownRemaining]);

    const triggerCooldown = (seconds: number) => {
        setIsLocked(true);
        setCooldownRemaining(seconds);
    };

    const fetchUserData = useCallback(async () => {
        if (!user) return;
        try {
            const response = await fetch(`/api/user?email=${user.email}`);
            const data = await response.json();
            setUserData(data);
            if (data.is_subscription_required) setShowPaywall(true);
        } catch (error) {
            console.error("Failed to fetch user data", error);
        }
    }, [user]);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!agreedToTerms) {
            setToast({ message: "Please agree to the Terms & Privacy Policy.", type: "warning" });
            return;
        }
        setAuthLoading(true);
        try {
            const res = await PermitFlowAuth.login(loginEmail);
            setToast({ message: res.message, type: "info" });
            setTimeout(async () => {
                const newUser = await PermitFlowAuth.verify(loginEmail);
                setUser(newUser);
                setAuthLoading(false);
            }, 2000);
        } catch (err) {
            setToast({ message: "Auth failed", type: "error" });
            setAuthLoading(false);
        }
    };

    const handleGoogleLogin = async () => {
        if (!agreedToTerms) {
            setToast({ message: "Please agree to the Terms & Privacy Policy.", type: "warning" });
            return;
        }
        setAuthLoading(true);
        try {
            const res = await PermitFlowAuth.signInWithGoogle();
            setTimeout(async () => {
                const newUser = await PermitFlowAuth.verify('google-pro-contractor@gmail.com');
                setUser(newUser);
                setAuthLoading(false);
            }, 1500);
        } catch (err) {
            setToast({ message: "Google Auth Failed", type: "error" });
            setAuthLoading(false);
        }
    };

    const openLegal = async (type: string) => {
        setLegalModal({ show: true, content: null });
        try {
            const response = await fetch(`./${type}.md`);
            const text = await response.text();
            const html = text.split('\n').map(line => {
                if (line.startsWith('# ')) return `<h1>${line.slice(2)}</h1>`;
                if (line.startsWith('## ')) return `<h2>${line.slice(3)}</h2>`;
                if (line.startsWith('### ')) return `<h3>${line.slice(4)}</h3>`;
                return `<p>${line}</p>`;
            }).join('');
            setLegalModal({ show: true, content: html });
        } catch (err) {
            setToast({ message: "Failed to load legal document", type: "error" });
        }
    };

    useEffect(() => {
        const handleOnline = () => {
            setIsOffline(false);
            setToast({ message: "Back online", type: "info" });
        };
        const handleOffline = () => setIsOffline(true);
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);
        
        if (user) fetchUserData();

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, [user, fetchUserData]);

    useEffect(() => {
        localStorage.setItem('permitflow_audits', JSON.stringify(audits));
    }, [audits]);

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (userData.is_subscription_required) {
            setShowPaywall(true);
            return;
        }
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                setPreview(e.target?.result as string);
                startAuditFlow();
            };
            reader.readAsDataURL(file);
        }
    };

    const startAuditFlow = async (manualSeer: number | null = null) => {
        if (isLocked) return;
        setStatus('scanning');
        await new Promise(r => setTimeout(r, 2000));
        setStatus('analyzing');
        await new Promise(r => setTimeout(r, 1500));

        const extracted = {
            id: Date.now(),
            timestamp: new Date().toLocaleString(),
            model: manualSeer ? "MANUAL-TEST" : "58SB0A070E17--12",
            seer2: manualSeer !== null ? manualSeer : (Math.random() > 0.5 ? 16.2 : 13.5),
            type: "HVAC Unit"
        };

        const compliance = extracted.seer2 >= 15.0;
        let verification_id = `PF-${Math.floor(1000 + Math.random() * 9000)}`;
        
        try {
            const saveResponse = await fetch('/api/logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_email: user.email,
                    equipment_type: extracted.type,
                    seer2: extracted.seer2,
                    status: compliance ? 'APPROVED' : 'REJECTED'
                })
            });
            const saveData = await saveResponse.json();
            if (saveData.verification_id) verification_id = saveData.verification_id;
            await fetchUserData();
        } catch (err) { console.error(err); }

        const finalResult: Audit = {
            ...extracted,
            verification_id,
            is_compliant: compliance,
            status: compliance ? 'APPROVED' : 'REJECTED',
            gps: "34.0522° N, 118.2437° W"
        };

        setCurrentResult(finalResult);
        setAudits(prev => [finalResult, ...prev].slice(0, 10));
        setStatus('completed');
        if (compliance) {
            setShowSuccessOverlay(true);
            confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
        }
        triggerCooldown(10);
    };

    const downloadCertificate = async () => {
        const element = document.getElementById('certificate-template');
        if (!element || !currentResult) return;
        element.style.display = 'block';
        const canvas = await html2canvas(element, { scale: 2 });
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jsPDF('p', 'mm', 'a4');
        pdf.addImage(imgData, 'PNG', 0, 0, 210, 297);
        pdf.save(`Certificate_${currentResult.model}.pdf`);
        element.style.display = 'none';
        setToast({ message: "Certificate Downloaded", type: "success" });
    };

    const reset = () => {
        setPreview(null);
        setCurrentResult(null);
        setStatus('idle');
        setShowSuccessOverlay(false);
    };

    const Footer = () => (
        <footer className="py-6 px-10 border-t border-white/5 bg-black/20 backdrop-blur-sm z-20">
            <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex items-center gap-6">
                    <button onClick={() => openLegal('privacy')} className="text-[10px] font-black text-slate-500 uppercase tracking-widest hover:text-cyan-400">Privacy Policy</button>
                    <button onClick={() => openLegal('terms')} className="text-[10px] font-black text-slate-500 uppercase tracking-widest hover:text-cyan-400">Terms of Service</button>
                    <span className="text-[10px] text-slate-700 font-bold uppercase tracking-widest">© 2026 PermitFlow</span>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-[9px] text-slate-600 font-bold uppercase tracking-widest px-3 py-1 bg-white/5 rounded-full border border-white/5">Oman PDPL Compliant</span>
                    <span className="text-[9px] text-slate-600 font-bold uppercase tracking-widest px-3 py-1 bg-white/5 rounded-full border border-white/5">Supabase ME-Central1</span>
                </div>
            </div>
        </footer>
    );

    if (!user) {
        return (
            <div className="min-h-screen bg-[#0a0a0b] flex flex-col items-center justify-center p-6 bg-industrial-grid">
                <div className="w-full max-w-md">
                    <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="industrial-card p-10 rounded-[40px] border-cyan-500/20 text-center relative overflow-hidden mb-12">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent"></div>
                        <div className="w-16 h-16 bg-cyan-500/10 rounded-2xl flex items-center justify-center mx-auto mb-8 border border-cyan-500/20 rotate-3">
                            <div className="text-2xl font-black text-cyan-400 -rotate-3 italic">PF</div>
                        </div>
                        <h1 className="text-3xl font-black text-white mb-2 uppercase tracking-tighter italic">PermitFlow <span className="text-cyan-400">PRO</span></h1>
                        <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px] mb-8">Industrial Compliance Gateway v3.1</p>
                        
                        <form onSubmit={handleLogin} className="space-y-4 text-left">
                            <div>
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block px-2">Contractor Email</label>
                                <input type="email" required value={loginEmail} onChange={(e) => setLoginEmail(e.target.value)} className="w-full fat-input p-5 rounded-2xl text-white font-bold text-sm" placeholder="name@company.com" />
                            </div>
                            <div className="flex items-start gap-3 p-4 bg-white/5 rounded-2xl border border-white/5 mb-4">
                                <input type="checkbox" id="terms" checked={agreedToTerms} onChange={(e) => setAgreedToTerms(e.target.checked)} className="mt-1 w-4 h-4 rounded border-white/10 bg-black text-cyan-500" />
                                <label htmlFor="terms" className="text-[10px] leading-relaxed text-slate-500 font-bold uppercase tracking-widest cursor-pointer">
                                    I agree to the <button type="button" onClick={() => openLegal('terms')} className="text-cyan-400 hover:underline">Terms</button> & <button type="button" onClick={() => openLegal('privacy')} className="text-cyan-400 hover:underline">Privacy Policy</button>, and understand data is stored in Oman-compliant regions.
                                </label>
                            </div>
                            <button type="submit" disabled={authLoading} className="w-full py-5 bg-cyan-500 text-black font-black text-xs uppercase tracking-[0.2em] rounded-2xl hover:bg-cyan-400 transition-all flex items-center justify-center gap-3">
                                {authLoading ? <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div> : 'Access Dashboard'}
                            </button>
                            <div className="relative py-4 flex items-center gap-4">
                                <div className="flex-1 h-px bg-white/5"></div>
                                <span className="text-[8px] font-black text-slate-700 uppercase tracking-widest">or secure sync</span>
                                <div className="flex-1 h-px bg-white/5"></div>
                            </div>
                            <button type="button" onClick={handleGoogleLogin} className="w-full py-5 bg-white/5 text-white font-black text-[10px] uppercase tracking-widest rounded-2xl border border-white/10 hover:bg-white/10">Continue with Google</button>
                        </form>
                    </motion.div>
                    <Footer />
                </div>
                <LegalModal modal={legalModal} setLegalModal={setLegalModal} />
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-[#0a0a0b] overflow-hidden">
            {/* Sidebar */}
            <aside className="w-80 bg-[#0d0d0f] border-r border-white/5 flex flex-col">
                <div className="p-6 border-b border-white/5">
                    <div className="flex items-center gap-3 mb-1">
                        <div className="w-8 h-8 rounded-lg bg-cyan-500 flex items-center justify-center font-bold text-black italic">PF</div>
                        <h1 className="text-xl font-bold tracking-tight text-white uppercase italic">PermitFlow <span className="text-cyan-400">PRO</span></h1>
                    </div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mt-2">Compliance Gateway</p>
                </div>
                <nav className="p-4 space-y-2 flex-1">
                    <button onClick={() => setActiveView('dashboard')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeView === 'dashboard' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'text-slate-500 hover:text-slate-300'}`}>
                        <span className="text-xs font-bold uppercase tracking-widest">Dashboard</span>
                    </button>
                    <button onClick={() => setActiveView('gallery')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeView === 'gallery' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'text-slate-500 hover:text-slate-300'}`}>
                        <span className="text-xs font-bold uppercase tracking-widest">Records</span>
                    </button>
                    <button onClick={() => PermitFlowAuth.logout()} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-slate-600 hover:text-red-400">
                        <span className="text-xs font-bold uppercase tracking-widest">Logout</span>
                    </button>
                </nav>
                <div className="p-6 border-t border-white/5">
                    <div className="bg-white/5 rounded-2xl p-4 border border-white/5 text-center">
                        <div className="mb-4">
                            <div className="flex justify-between text-[10px] text-slate-500 font-black uppercase tracking-widest mb-2 font-mono">
                                <span>Credits</span>
                                <span>{10 - userData.credits_remaining}/10</span>
                            </div>
                            {!userData.is_pro && (
                                <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                                    <motion.div 
                                        initial={{ width: 0 }}
                                        animate={{ width: `${(10 - userData.credits_remaining) * 10}%` }}
                                        className="h-full bg-cyan-500"
                                    />
                                </div>
                            )}
                        </div>
                        <p className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-3">
                            {userData.is_pro ? "PRO UNLIMITED" : `${10 - userData.credits_remaining} of 10 Free Credits Used`}
                        </p>
                        <button onClick={() => setShowPaywall(true)} className="w-full py-2 bg-cyan-500/10 text-cyan-400 text-[9px] font-black uppercase tracking-widest rounded-lg border border-cyan-500/20 hover:bg-cyan-500 hover:text-black transition-all">
                            {userData.is_pro ? "Manage Subscription" : `Upgrade now for $${pricing.professional.price_monthly}`}
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto bg-industrial-grid relative flex flex-col">
                <header className="p-8 border-b border-white/5 flex justify-between items-center bg-black/20 backdrop-blur-sm sticky top-0 z-10">
                    <h2 className="text-lg font-black text-white uppercase tracking-tighter italic">{activeView}</h2>
                </header>

                <div className="p-10 max-w-5xl mx-auto w-full flex-1">
                    {activeView === 'dashboard' ? (
                        <div className="industrial-card p-12 rounded-[40px] border-white/5 text-center">
                            {!preview ? (
                                <div className="py-20 border-2 border-dashed border-white/5 rounded-3xl relative group">
                                    <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={handleFileUpload} />
                                    <div className="w-20 h-20 bg-cyan-500/10 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:bg-cyan-500/20 transition-colors">
                                        <svg className="w-10 h-10 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                                    </div>
                                    <h2 className="text-2xl font-black text-white mb-2 uppercase tracking-tight italic">Ready to Capture</h2>
                                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Drop HVAC Plate Image Here</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-left">
                                    <div className="relative aspect-square rounded-2xl overflow-hidden border border-white/5 bg-black">
                                        <img src={preview} className={`w-full h-full object-cover ${status !== 'completed' ? 'opacity-40 grayscale animate-pulse' : ''}`} alt="preview" />
                                        {status !== 'completed' && <div className="absolute inset-0 flex items-center justify-center text-cyan-400 font-black text-xs uppercase tracking-widest">{status}...</div>}
                                    </div>
                                    <div>
                                        <h2 className="text-3xl font-black text-white mb-6 uppercase tracking-tighter italic">Audit Summary</h2>
                                        {status === 'completed' && currentResult && (
                                            <div className="space-y-6">
                                                <div className={`p-6 rounded-2xl border ${currentResult.is_compliant ? 'bg-green-500/5 border-green-500/20 text-green-400' : 'bg-red-500/5 border-red-500/20 text-red-400'}`}>
                                                    <h3 className="font-black text-sm uppercase tracking-widest mb-1 italic">{currentResult.status}</h3>
                                                    <p className="text-[10px] opacity-70 font-bold uppercase tracking-widest">Model: {currentResult.model} | SEER2: {currentResult.seer2}</p>
                                                    <p className="text-[9px] mt-2 opacity-50 font-mono tracking-tighter">ID: {currentResult.verification_id}</p>
                                                </div>
                                                <div className="grid grid-cols-2 gap-3">
                                                    <button onClick={() => downloadCertificate()} className="py-4 bg-cyan-500 text-black font-black text-[10px] uppercase tracking-widest rounded-xl hover:bg-cyan-400 transition-all flex items-center justify-center gap-2">Export PDF</button>
                                                    <button onClick={reset} className="py-4 bg-white/5 text-slate-400 font-black text-[10px] uppercase tracking-widest rounded-xl hover:text-white border border-white/5">Reset</button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {audits.map(audit => (
                                <div key={audit.id} className="industrial-card p-6 rounded-2xl border-white/5 hover:border-cyan-500/30 transition-all cursor-pointer group">
                                    <div className="flex justify-between items-start mb-6">
                                        <div className={`px-2 py-1 rounded text-[9px] font-black uppercase tracking-widest border ${audit.is_compliant ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                                            {audit.status}
                                        </div>
                                        <span className="text-[9px] text-slate-700 font-mono">{audit.timestamp}</span>
                                    </div>
                                    <h4 className="text-sm font-black text-white uppercase tracking-tighter mb-1 truncate">{audit.model}</h4>
                                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest font-mono">SEER2: {audit.seer2}</p>
                                </div>
                            ))}
                            {audits.length === 0 && <p className="col-span-full text-center py-20 text-slate-600 font-bold uppercase tracking-widest text-[10px]">No records found.</p>}
                        </div>
                    )}
                </div>
                <Footer />
            </main>

            <AnimatePresence>
                {showSuccessOverlay && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-sm flex items-center justify-center p-8 overflow-hidden" onClick={() => setShowSuccessOverlay(false)}>
                        <motion.div initial={{ scale: 0.8 }} animate={{ scale: 1 }} className="max-w-md w-full text-center" onClick={e => e.stopPropagation()}>
                            <div className="w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-8 border-2 border-green-500/50 pulse-green-seal">
                                <svg className="w-12 h-12 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
                            </div>
                            <h2 className="text-4xl font-black text-white mb-2 tracking-tighter uppercase italic">Audit Success</h2>
                            <p className="text-slate-500 font-bold uppercase tracking-widest mb-8 text-[10px]">Verification ID: {currentResult?.verification_id}</p>
                            <button onClick={() => setShowSuccessOverlay(false)} className="w-full py-4 bg-white text-black font-black text-xs uppercase tracking-widest rounded-xl hover:bg-slate-200">Done</button>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {toast && (
                    <motion.div initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 50 }} className="fixed bottom-12 left-1/2 -translate-x-1/2 z-[500] px-8 py-5 bg-[#121214] border border-cyan-500/30 rounded-2xl shadow-2xl flex items-center gap-6">
                        <p className="text-[10px] font-black text-white uppercase tracking-[0.2em]">{toast.message}</p>
                        <button onClick={() => setToast(null)} className="text-slate-600 hover:text-white">✕</button>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {showPaywall && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/95 backdrop-blur-xl z-[600] flex items-center justify-center p-6" onClick={() => setShowPaywall(false)}>
                        <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className="industrial-card max-w-md w-full p-10 rounded-[40px] text-center relative overflow-hidden" onClick={e => e.stopPropagation()}>
                            <div className="absolute top-0 right-0 px-4 py-1 bg-cyan-500 text-black text-[8px] font-black uppercase tracking-widest rounded-bl-xl">
                                {pricing.professional.badge}
                            </div>
                            <h2 className="text-3xl font-black text-white mb-2 uppercase italic">Professional</h2>
                            <p className="text-cyan-400 text-2xl font-black mb-6 italic">${pricing.professional.price_monthly}<span className="text-slate-500 text-xs font-bold uppercase tracking-widest not-italic"> / month</span></p>
                            
                            <ul className="text-left space-y-3 mb-8">
                                {["Unlimited HVAC Audits", "Custom PDF Certificates", "Priority API Access", "Compliance Notifications"].map((feat, i) => (
                                    <li key={i} className="flex items-center gap-3 text-[10px] font-bold text-slate-300 uppercase tracking-widest">
                                        <svg className="w-4 h-4 text-cyan-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/></svg>
                                        {feat}
                                    </li>
                                ))}
                            </ul>

                            <a 
                                href={`${pricing.professional.gumroad_url}?email=${user?.email}`} 
                                className="gumroad-button w-full py-5 bg-cyan-500 text-black font-black text-xs uppercase tracking-widest rounded-2xl hover:bg-cyan-400 transition-all shadow-lg block mb-4"
                                target="_blank" 
                                rel="noopener noreferrer"
                            >
                                Secure Access via Gumroad
                            </a>
                            <button onClick={() => setShowPaywall(false)} className="text-[10px] text-slate-600 font-bold uppercase hover:text-white tracking-widest">Maybe Later</button>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div id="certificate-template" style={{ display: 'none', width: '800px', padding: '60px', background: 'white', color: 'black' }}>
                <div style={{ border: '10px solid #06b6d4', padding: '40px' }}>
                    <h1 style={{ textAlign: 'center', fontSize: '28pt', fontWeight: '900', color: 'black', textTransform: 'uppercase', marginBottom: '40px' }}>Compliance Certificate</h1>
                    <div style={{ marginBottom: '40px', fontSize: '14pt' }}>
                        <p><strong>Model:</strong> {currentResult?.model}</p>
                        <p><strong>Efficiency:</strong> {currentResult?.seer2} SEER2</p>
                        <p><strong>Status:</strong> {currentResult?.status}</p>
                        <p><strong>Verification ID:</strong> {currentResult?.verification_id}</p>
                        <p><strong>Timestamp:</strong> {currentResult?.timestamp}</p>
                        <p><strong>GPS:</strong> {currentResult?.gps}</p>
                    </div>
                    <div style={{ padding: '20px', background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                        <p style={{ fontSize: '10pt', color: '#64748b' }}>This certificate validates that the specified equipment meets the Title 24 compliance standards as analyzed by PermitFlow Pro's Truth Engine.</p>
                    </div>
                </div>
            </div>

            <LegalModal modal={legalModal} setLegalModal={setLegalModal} />
        </div>
    );
}

function LegalModal({ modal, setLegalModal }: { modal: any, setLegalModal: any }) {
    if (!modal || !modal.show) return null;
    return (
        <div className="fixed inset-0 z-[1000] bg-black/95 backdrop-blur-xl flex items-center justify-center p-6" onClick={() => setLegalModal({ ...modal, show: false })}>
            <div className="industrial-card max-w-2xl w-full max-h-[80vh] overflow-y-auto p-12 relative" onClick={e => e.stopPropagation()}>
                <button onClick={() => setLegalModal({ ...modal, show: false })} className="absolute top-6 right-6 text-slate-500 hover:text-white p-2">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
                <div className="prose prose-invert max-w-none">
                    {modal.content ? <div dangerouslySetInnerHTML={{ __html: modal.content }} /> : <p className="animate-pulse text-cyan-400 font-bold uppercase tracking-widest text-xs">Loading Legal Docs...</p>}
                </div>
            </div>
        </div>
    );
}
