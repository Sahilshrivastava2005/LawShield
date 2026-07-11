import React, { useRef, useState, useContext, useEffect, useCallback } from 'react';
import {
  Routes, Route, NavLink, useNavigate, useSearchParams, Link,
} from 'react-router-dom';
import {
  LayoutDashboard, MessageSquare, Files, Settings, Search, Bell, Plus,
  Sparkles, ArrowUp, Paperclip, ShieldCheck, FileText, MoreHorizontal,
  ChevronRight, UploadCloud, CheckCircle2, BookOpen, Scale, Menu, X, LogOut,
} from 'lucide-react';
import { AuthContext } from '../context/AuthContext';

const API = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

const NAV_ITEMS = [
  { to: '/app',           end: true, label: 'Overview',        icon: LayoutDashboard },
  { to: '/app/chat',      end: false, label: 'Legal assistant', icon: MessageSquare },
  { to: '/app/documents', end: false, label: 'Documents',       icon: Files },
  { to: '/app/settings',  end: false, label: 'Settings',        icon: Settings },
];

// ── Utility ─────────────────────────────────────────────────────────────────────
function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

// ── Logo ─────────────────────────────────────────────────────────────────────────
function Logo() {
  return (
    <Link to="/" className="text-lg font-bold tracking-tight select-none">
      law<span className="text-slate-400">Shield</span>
    </Link>
  );
}

// ── Shell Layout ─────────────────────────────────────────────────────────────────
function Shell({ children, title, subtitle, action }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, token, logout } = useContext(AuthContext);
  const [threads, setThreads] = useState([]);
  const navigate = useNavigate();

  // Fetch thread list for sidebar
  useEffect(() => {
    if (!token) return;
    fetch(`${API}/threads`, { headers: authHeaders(token) })
      .then((r) => r.json())
      .then((data) => { if (Array.isArray(data)) setThreads(data); })
      .catch(console.error);
  }, [token]);

  const handleNewChat = async () => {
    setMobileOpen(false);
    navigate('/app/chat');
  };

  const initials = user?.name
    ? user.name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()
    : 'U';

  return (
    <div className="h-screen bg-slate-50 flex overflow-hidden">
      {/* ── Sidebar ── */}
      <aside
        className={`
          ${mobileOpen ? 'flex' : 'hidden'} md:flex
          fixed md:static inset-0 z-40
          w-full md:w-64 bg-white border-r border-slate-200
          flex-col p-4 shrink-0
        `}
      >
        {/* Header */}
        <div className="h-12 px-2 flex items-center justify-between">
          <Logo />
          <button className="md:hidden" onClick={() => setMobileOpen(false)} aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        {/* New matter button */}
        <button
          onClick={handleNewChat}
          className="mt-4 flex items-center justify-center gap-2 bg-slate-900 text-white text-sm font-semibold rounded-xl py-2.5 hover:bg-slate-700 transition"
        >
          <Plus size={15} /> New matter
        </button>

        {/* Nav links */}
        <nav className="mt-6 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              end={end}
              to={to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition
                 ${isActive ? 'bg-slate-100 text-slate-950' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Recent threads */}
        <div className="mt-7 px-3 text-[10px] uppercase tracking-widest font-bold text-slate-400">
          Recent matters
        </div>
        <div className="mt-2 space-y-0.5 overflow-y-auto flex-1">
          {threads.slice(0, 8).map((t) => (
            <NavLink
              key={t.id}
              to={`/app/chat?thread=${t.id}`}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `block truncate px-3 py-2 text-xs rounded-lg transition
                 ${isActive ? 'bg-slate-100 text-slate-900 font-medium' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'}`
              }
            >
              {t.title}
            </NavLink>
          ))}
          {threads.length === 0 && (
            <p className="px-3 py-2 text-xs text-slate-400 italic">No matters yet.</p>
          )}
        </div>

        {/* User / Logout */}
        <div className="mt-auto pt-4 border-t border-slate-100">
          <div className="rounded-xl border border-slate-200 p-3 mb-3">
            <div className="flex justify-between text-xs font-semibold">
              <span>Starter plan</span>
              <span>7 / 10</span>
            </div>
            <div className="h-1.5 bg-slate-100 rounded-full mt-2 overflow-hidden">
              <div className="h-full w-[70%] bg-slate-900 rounded-full" />
            </div>
            <p className="text-[10px] text-slate-400 mt-2">Prompts reset in 12 days</p>
          </div>

          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-2 py-2 rounded-xl hover:bg-slate-50 transition text-left"
          >
            <div className="w-8 h-8 rounded-lg bg-slate-900 text-white grid place-items-center text-xs font-bold shrink-0">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-semibold truncate">{user?.name || 'User'}</div>
              <div className="text-[10px] text-slate-400 truncate">{user?.email || ''}</div>
            </div>
            <LogOut size={14} className="text-slate-400 shrink-0" />
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/20 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* ── Main content ── */}
      <section className="flex-1 min-w-0 flex flex-col">
        <header className="h-16 bg-white/90 backdrop-blur border-b border-slate-200 px-4 md:px-7 flex items-center gap-4 shrink-0">
          <button className="md:hidden" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu size={20} />
          </button>
          <div className="min-w-0">
            <h1 className="text-sm font-bold truncate">{title}</h1>
            {subtitle && <p className="text-[11px] text-slate-400 truncate">{subtitle}</p>}
          </div>
          <div className="ml-auto flex items-center gap-2">
            {action}
            <button className="w-9 h-9 rounded-xl border border-slate-200 grid place-items-center text-slate-500 hover:bg-slate-50 transition">
              <Search size={15} />
            </button>
            <button className="w-9 h-9 rounded-xl border border-slate-200 grid place-items-center text-slate-500 hover:bg-slate-50 transition relative">
              <Bell size={15} />
              <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-amber-500 rounded-full" />
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-auto">{children}</main>
      </section>
    </div>
  );
}

// ── Overview Page ─────────────────────────────────────────────────────────────────
function Overview() {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [promptInput, setPromptInput] = useState('');

  const tools = [
    ['Ask legal AI',      'Research a question with verified sources',       MessageSquare, '/app/chat'],
    ['Analyze a document','Find risks, obligations, and key clauses',        FileText,      '/app/documents'],
    ['Research case law', 'Surface relevant judgments and statutes',         Scale,         '/app/chat'],
    ['Draft from scratch','Create a motion, brief, or legal notice',        BookOpen,      '/app/chat'],
  ];

  const handlePromptSubmit = () => {
    if (promptInput.trim()) {
      navigate('/app/chat', { state: { initialPrompt: promptInput.trim() } });
    }
  };

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <Shell
      title={`${greeting()}, ${user?.name?.split(' ')[0] || 'Counselor'}`}
      subtitle="Here's what's happening in your workspace."
    >
      <div className="max-w-6xl mx-auto p-5 md:p-8">
        {/* Hero */}
        <div className="relative overflow-hidden bg-slate-950 rounded-3xl p-7 md:p-9 text-white mb-7">
          <div className="absolute right-0 top-0 w-72 h-72 bg-white/5 rounded-full blur-3xl pointer-events-none" />
          <span className="inline-flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-400">
            <Sparkles size={12} /> Legal intelligence
          </span>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight mt-4 max-w-lg">
            What legal challenge can we solve today?
          </h2>
          <div className="mt-6 max-w-2xl flex bg-white rounded-2xl p-2 shadow-xl">
            <input
              value={promptInput}
              onChange={(e) => setPromptInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handlePromptSubmit()}
              className="flex-1 min-w-0 px-3 text-sm text-slate-900 outline-none bg-transparent"
              placeholder="Ask a legal question or describe a task…"
            />
            <button
              onClick={handlePromptSubmit}
              className="w-10 h-10 rounded-xl bg-slate-900 grid place-items-center hover:bg-slate-700 transition"
            >
              <ArrowUp size={16} />
            </button>
          </div>
          <p className="text-[10px] text-slate-500 mt-3 flex items-center gap-1.5">
            <ShieldCheck size={11} /> Sensitive details are automatically masked before processing.
          </p>
        </div>

        {/* Tools */}
        <h3 className="text-sm font-bold mb-3">Start with a tool</h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
          {tools.map(([t, d, I, to]) => (
            <button
              key={t}
              onClick={() => navigate(to)}
              className="text-left bg-white border border-slate-200 p-5 rounded-2xl hover:shadow-md hover:-translate-y-0.5 transition"
            >
              <div className="w-9 h-9 rounded-xl bg-slate-100 grid place-items-center mb-5">
                <I size={16} />
              </div>
              <div className="text-sm font-bold">{t}</div>
              <p className="text-xs text-slate-400 leading-relaxed mt-1">{d}</p>
            </button>
          ))}
        </div>
      </div>
    </Shell>
  );
}

// ── Chat Page ─────────────────────────────────────────────────────────────────────
function Chat() {
  const { token } = useContext(AuthContext);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useNavigate(); // keep for state
  const messagesEndRef = useRef(null);

  const [threadId, setThreadId] = useState(searchParams.get('thread'));
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Good morning. I'm ready to help with legal research, drafting, document analysis, or citation verification. What are you working on?",
      sources: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  // Load thread history when threadId changes
  useEffect(() => {
    if (!threadId || !token) return;

    fetch(`${API}/threads/${threadId}`, { headers: authHeaders(token) })
      .then((r) => {
        if (!r.ok) throw new Error('Thread not found');
        return r.json();
      })
      .then((data) => {
        if (data.messages && data.messages.length > 0) {
          setMessages(
            data.messages.map((m) => ({
              role:    m.role.toLowerCase(),
              content: m.content,
              sources: m.sources ? JSON.parse(m.sources) : [],
            }))
          );
        }
      })
      .catch((err) => {
        console.error('[Load thread]', err);
        setThreadId(null);
      });
  }, [threadId, token]);

  const send = useCallback(
    async (e) => {
      e?.preventDefault();
      const q = input.trim();
      if (!q || sending) return;

      setInput('');
      setSending(true);
      setMessages((prev) => [...prev, { role: 'user', content: q, sources: [] }]);

      try {
        let tid = threadId;

        // Create a new thread on the first message
        if (!tid) {
          const tRes = await fetch(`${API}/threads`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
            body:    JSON.stringify({ title: q.length > 40 ? q.slice(0, 40) + '…' : q }),
          });
          if (!tRes.ok) throw new Error('Failed to create thread');
          const tData = await tRes.json();
          tid = tData.id;
          setThreadId(tid);
          // Update URL without re-mounting
          window.history.replaceState({}, '', `/app/chat?thread=${tid}`);
        }

        const r = await fetch(`${API}/chat/`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
          body:    JSON.stringify({ threadId: tid, message: q }),
        });

        if (!r.ok) {
          const errData = await r.json().catch(() => ({}));
          throw new Error(errData.msg || 'Request failed');
        }

        const d = await r.json();
        setMessages((prev) => [
          ...prev,
          {
            role:    'assistant',
            content: d.content,
            sources: d.sources ? JSON.parse(d.sources) : [],
          },
        ]);
      } catch (err) {
        console.error('[Send message]', err);
        setMessages((prev) => [
          ...prev,
          {
            role:    'assistant',
            content: 'Sorry, there was a problem sending your message. Please check your connection and try again.',
            sources: [],
          },
        ]);
      } finally {
        setSending(false);
      }
    },
    [input, sending, threadId, token]
  );

  const startNewChat = () => {
    setThreadId(null);
    setMessages([
      {
        role: 'assistant',
        content: "Starting a new matter. What would you like to work on?",
        sources: [],
      },
    ]);
    window.history.replaceState({}, '', '/app/chat');
  };

  return (
    <Shell
      title="Legal assistant"
      subtitle="Private, source-grounded legal AI"
      action={
        <button
          onClick={startNewChat}
          className="hidden sm:flex items-center gap-2 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold hover:bg-slate-50 transition"
        >
          <Plus size={13} /> New chat
        </button>
      }
    >
      <div className="h-full flex flex-col bg-white">
        {/* Messages */}
        <div className="flex-1 overflow-auto">
          <div className="max-w-3xl mx-auto px-5 py-8 space-y-7">
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
                {m.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-xl bg-slate-900 text-white grid place-items-center shrink-0 mt-1">
                    <Sparkles size={13} />
                  </div>
                )}
                <div
                  className={`max-w-[85%] ${
                    m.role === 'user'
                      ? 'bg-slate-900 text-white rounded-2xl rounded-tr-sm px-4 py-3'
                      : 'pt-1'
                  }`}
                >
                  <p className="text-sm leading-7 whitespace-pre-wrap">{m.content}</p>
                  {m.sources?.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {m.sources.map((s, si) => (
                        <span
                          key={si}
                          className="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1 flex items-center gap-1"
                        >
                          <CheckCircle2 size={10} />
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {sending && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-xl bg-slate-900 text-white grid place-items-center shrink-0">
                  <Sparkles size={13} />
                </div>
                <div className="flex gap-1 pt-3">
                  {[0, 1, 2].map((x) => (
                    <i
                      key={x}
                      className="w-1.5 h-1.5 rounded-full bg-slate-300 animate-bounce not-italic"
                      style={{ animationDelay: `${x * 150}ms` }}
                    />
                  ))}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <form onSubmit={send} className="p-4 border-t border-slate-100">
          <div className="max-w-3xl mx-auto border border-slate-200 rounded-2xl bg-white shadow-lg p-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              rows={2}
              className="w-full resize-none outline-none px-3 py-2 text-sm"
              placeholder="Ask a legal question… (Shift+Enter for new line)"
            />
            <div className="flex items-center gap-2">
              <button type="button" className="p-2 text-slate-400 hover:text-slate-600 transition">
                <Paperclip size={17} />
              </button>
              <span className="text-[10px] text-slate-400 hidden sm:inline flex-1">
                Responses may require professional verification.
              </span>
              <button
                type="submit"
                disabled={!input.trim() || sending}
                className="ml-auto w-9 h-9 rounded-xl bg-slate-900 disabled:bg-slate-200 disabled:cursor-not-allowed text-white grid place-items-center transition"
              >
                <ArrowUp size={15} />
              </button>
            </div>
          </div>
        </form>
      </div>
    </Shell>
  );
}

// ── Documents Page ────────────────────────────────────────────────────────────────
function Documents() {
  const fileInputRef = useRef(null);
  const { token } = useContext(AuthContext);
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchDocs = useCallback(() => {
    if (!token) return;
    fetch(`${API}/documents`, { headers: authHeaders(token) })
      .then((r) => r.json())
      .then((data) => { if (Array.isArray(data)) setDocs(data); })
      .catch(console.error);
  }, [token]);

  useEffect(() => { fetchDocs(); }, [fetchDocs]);

  const upload = async (file) => {
    if (!file || uploading) return;
    setUploading(true);

    // Optimistic UI – add a processing placeholder
    const placeholder = {
      id:        `tmp-${Date.now()}`,
      filename:  file.name,
      fileType:  file.type,
      size:      `${(file.size / 1024 / 1024).toFixed(2)} MB`,
      status:    'Processing',
      createdAt: new Date().toISOString(),
    };
    setDocs((prev) => [placeholder, ...prev]);

    try {
      const fd = new FormData();
      fd.append('file', file);

      const r = await fetch(`${API}/documents/upload-and-ingest`, {
        method:  'POST',
        headers: authHeaders(token), // DO NOT set Content-Type – let browser set it with boundary
        body:    fd,
      });

      const data = await r.json();

      if (r.ok && data.document) {
        // Replace placeholder with real record
        setDocs((prev) => [data.document, ...prev.filter((d) => d.id !== placeholder.id)]);
      } else {
        // Update placeholder to failed
        setDocs((prev) =>
          prev.map((d) => (d.id === placeholder.id ? { ...d, status: 'Processing Failed' } : d))
        );
      }
    } catch (err) {
      console.error('[Upload]', err);
      setDocs((prev) =>
        prev.map((d) => (d.id === placeholder.id ? { ...d, status: 'Processing Failed' } : d))
      );
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const deleteDoc = async (id) => {
    try {
      await fetch(`${API}/documents/${id}`, {
        method:  'DELETE',
        headers: authHeaders(token),
      });
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error('[Delete doc]', err);
    }
  };

  const filtered = docs.filter((d) =>
    d.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Shell
      title="Documents"
      subtitle="Your private legal knowledge base"
      action={
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex items-center gap-2 bg-slate-900 text-white rounded-xl px-3 py-2 text-xs font-semibold hover:bg-slate-700 transition"
        >
          <UploadCloud size={13} /> Upload
        </button>
      }
    >
      <div className="max-w-6xl mx-auto p-5 md:p-8">
        <input
          ref={fileInputRef}
          className="hidden"
          type="file"
          accept=".pdf,.doc,.docx,.txt"
          onChange={(e) => upload(e.target.files[0])}
        />

        {/* Drop zone */}
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); upload(e.dataTransfer.files[0]); }}
          className="cursor-pointer bg-white border-2 border-dashed border-slate-200 hover:border-slate-400 rounded-2xl p-8 text-center transition"
        >
          <div className="w-11 h-11 bg-slate-100 rounded-2xl grid place-items-center mx-auto">
            <UploadCloud size={19} />
          </div>
          <h2 className="text-sm font-bold mt-4">
            {uploading ? 'Processing your document…' : 'Drop legal documents here or click to upload'}
          </h2>
          <p className="text-xs text-slate-400 mt-1">PDF, DOCX, DOC or TXT · Private and automatically indexed</p>
        </div>

        {/* Document list */}
        <div className="flex items-center justify-between mt-8 mb-3">
          <h2 className="text-sm font-bold">
            All documents{' '}
            <span className="text-slate-400 font-medium ml-1">{filtered.length}</span>
          </h2>
          <div className="relative">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-white border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-xs outline-none w-48"
              placeholder="Search documents"
            />
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
          <div className="hidden sm:grid grid-cols-[1fr_140px_90px_110px_36px] px-5 py-3 bg-slate-50 text-[10px] uppercase tracking-wider font-bold text-slate-400">
            <span>Name</span>
            <span>Type</span>
            <span>Size</span>
            <span>Added</span>
            <span />
          </div>

          {filtered.length === 0 && (
            <div className="px-5 py-10 text-center text-sm text-slate-400">
              {docs.length === 0 ? 'No documents uploaded yet.' : 'No documents match your search.'}
            </div>
          )}

          {filtered.map((d) => (
            <div
              key={d.id}
              className="grid sm:grid-cols-[1fr_140px_90px_110px_36px] items-center gap-2 px-5 py-4 border-t border-slate-100 first:border-t-0"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 bg-red-50 text-red-500 rounded-xl grid place-items-center shrink-0">
                  <FileText size={16} />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold truncate">{d.filename}</div>
                  <div
                    className={`text-[10px] flex items-center gap-1 ${
                      d.status === 'Ready'
                        ? 'text-emerald-600'
                        : d.status === 'Processing'
                        ? 'text-amber-600'
                        : 'text-red-500'
                    }`}
                  >
                    <CheckCircle2 size={9} />
                    {d.status}
                  </div>
                </div>
              </div>
              <span className="text-xs text-slate-500 truncate">{d.fileType}</span>
              <span className="text-xs text-slate-400">{d.size}</span>
              <span className="text-xs text-slate-400">
                {new Date(d.createdAt).toLocaleDateString()}
              </span>
              <button
                onClick={() => deleteDoc(d.id)}
                className="text-slate-400 hover:text-red-500 transition"
                title="Delete document"
              >
                <MoreHorizontal size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </Shell>
  );
}

// ── Settings Page ─────────────────────────────────────────────────────────────────
function SettingsPage() {
  const { user } = useContext(AuthContext);

  return (
    <Shell title="Settings" subtitle="Manage your workspace and preferences">
      <div className="max-w-3xl mx-auto p-5 md:p-8 space-y-5">
        {/* Profile */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6">
          <h2 className="text-base font-bold">Profile</h2>
          <p className="text-xs text-slate-400 mt-1 mb-6">Your personal information and workspace identity.</p>
          <div className="flex items-center gap-4 mb-6">
            <div className="w-14 h-14 rounded-2xl bg-slate-900 text-white grid place-items-center text-xl font-bold">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <label className="text-xs font-semibold block">
              Full name
              <input
                className="auth-input mt-1"
                defaultValue={user?.name || ''}
                readOnly
              />
            </label>
            <label className="text-xs font-semibold block">
              Email address
              <input
                className="auth-input mt-1"
                defaultValue={user?.email || ''}
                readOnly
              />
            </label>
          </div>
        </div>

        {/* AI Preferences */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6">
          <h2 className="text-base font-bold">AI preferences</h2>
          <p className="text-xs text-slate-400 mt-1 mb-6">Tune answers for your practice.</p>
          <div className="grid sm:grid-cols-2 gap-4">
            <label className="text-xs font-semibold block">
              Default jurisdiction
              <select className="auth-input mt-1">
                <option>India</option>
                <option>United States</option>
                <option>United Kingdom</option>
              </select>
            </label>
            <label className="text-xs font-semibold block">
              Response style
              <select className="auth-input mt-1">
                <option>Concise &amp; cited</option>
                <option>Detailed memorandum</option>
                <option>Plain English</option>
              </select>
            </label>
          </div>
        </div>
      </div>
    </Shell>
  );
}

// ── Root export ────────────────────────────────────────────────────────────────────
export default function WorkspacePage() {
  return (
    <Routes>
      <Route index element={<Overview />} />
      <Route path="chat" element={<Chat />} />
      <Route path="documents" element={<Documents />} />
      <Route path="settings" element={<SettingsPage />} />
    </Routes>
  );
}
