import React, { useState } from 'react';
import { ArrowRight, Check, Eye, EyeOff, ShieldCheck, Sparkles } from 'lucide-react';

export default function AuthPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [mode, setMode] = useState('login');
  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="hidden lg:flex w-[46%] bg-slate-950 text-white p-12 flex-col justify-between relative overflow-hidden">
        <div className="absolute inset-0 opacity-20 auth-grid" />
        <a href="/" className="relative text-xl font-bold">law<span className="text-slate-500">Shield</span></a>
        <div className="relative max-w-md">
          <div className="w-11 h-11 rounded-2xl bg-white/10 border border-white/10 flex items-center justify-center mb-7"><Sparkles size={19}/></div>
          <h1 className="text-4xl font-extrabold tracking-tight leading-tight mb-5">Your most capable legal colleague. Always on call.</h1>
          <p className="text-slate-400 leading-relaxed mb-8">Research, draft, and review with answers grounded in your documents and verified legal sources.</p>
          <div className="space-y-4">
            {['Private by design with automatic PII masking','Every citation checked before it reaches you','Built around real legal workflows'].map(x => <div key={x} className="flex items-center gap-3 text-sm text-slate-300"><span className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center"><Check size={11}/></span>{x}</div>)}
          </div>
        </div>
        <p className="relative text-xs text-slate-600">© 2026 lawShield, Inc.</p>
      </aside>
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <a href="/" className="lg:hidden block text-lg font-bold mb-12">law<span className="text-slate-400">Shield</span></a>
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1 mb-5"><ShieldCheck size={12}/> Secure workspace</div>
          <h2 className="text-3xl font-extrabold tracking-tight">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
          <p className="text-slate-500 mt-2 mb-8">{mode === 'login' ? 'Sign in to continue to your legal workspace.' : 'Start researching smarter in under a minute.'}</p>
          <button className="w-full border border-slate-200 bg-white rounded-xl py-3 text-sm font-semibold hover:bg-slate-50">Continue with Google</button>
          <div className="flex items-center gap-3 my-6 text-xs text-slate-400"><div className="h-px bg-slate-200 flex-1"/>or continue with email<div className="h-px bg-slate-200 flex-1"/></div>
          <form onSubmit={e => {e.preventDefault(); location.href='/app';}} className="space-y-4">
            {mode === 'signup' && <label className="block text-sm font-semibold">Full name<input required className="auth-input" placeholder="Alex Morgan"/></label>}
            <label className="block text-sm font-semibold">Work email<input required type="email" className="auth-input" placeholder="you@firm.com"/></label>
            <label className="block text-sm font-semibold">Password<div className="relative"><input required type={showPassword?'text':'password'} className="auth-input pr-11" placeholder="••••••••"/><button type="button" onClick={()=>setShowPassword(!showPassword)} className="absolute right-3 top-3.5 text-slate-400">{showPassword?<EyeOff size={16}/>:<Eye size={16}/>}</button></div></label>
            <button className="w-full bg-slate-900 text-white rounded-xl py-3 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-slate-700">{mode==='login'?'Sign in':'Create account'} <ArrowRight size={15}/></button>
          </form>
          <p className="text-center text-sm text-slate-500 mt-7">{mode==='login'?"New to lawShield?":"Already have an account?"} <button onClick={()=>setMode(mode==='login'?'signup':'login')} className="font-semibold text-slate-900">{mode==='login'?'Create an account':'Sign in'}</button></p>
        </div>
      </main>
    </div>
  );
}
