'use client';

import { useEffect, useState, useCallback } from 'react';
import { CopilotChat } from '@copilotkit/react-core/v2';

const PROMPTS = [
  { icon: '💰', label: 'Most expensive phone', text: 'What is the most expensive Samsung phone in the dataset?' },
  { icon: '⚡', label: 'Compare flagships',     text: 'Compare Samsung S24 Ultra vs S23 Ultra specs side by side' },
  { icon: '💸', label: 'Budget under $500',     text: 'Show me all Samsung phones available under $500' },
  { icon: '⭐', label: 'Highest rated',         text: 'Which Samsung phone has the highest customer rating?' },
  { icon: '🧠', label: 'Most RAM',              text: 'Which Samsung phone has the most RAM?' },
  { icon: '📷', label: 'Best for photography',  text: 'Which Samsung phone is best for camera and photography?' },
];

const STACK = ['LangGraph', 'CopilotKit', 'FastAPI', 'PostgreSQL', 'Groq', 'Next.js'];

const PIPELINE_STEPS = [
  {
    icon: '💬',
    title: 'Natural Language Input',
    subtitle: 'User Query',
    desc: 'Ask questions in plain English about Samsung phones — pricing, specs, comparisons, ratings',
    color: '#e75933',
    glow: 'rgba(231,89,51,0.35)',
  },
  {
    icon: '🧠',
    title: 'LangGraph Agent',
    subtitle: 'Groq LLM Processing',
    desc: 'Agent analyzes intent, plans SQL strategy, and orchestrates the query generation pipeline',
    color: '#8b5cf6',
    glow: 'rgba(139,92,246,0.35)',
  },
  {
    icon: '⚡',
    title: 'Text-to-SQL Generation',
    subtitle: 'PostgreSQL Query',
    desc: 'AI generates optimized SQL — SELECT with JOINs, WHERE clauses, aggregations, and ordering',
    color: '#3b82f6',
    glow: 'rgba(59,130,246,0.35)',
  },
  {
    icon: '🗄️',
    title: 'FastAPI Backend',
    subtitle: 'Database Execution',
    desc: 'Query runs against Samsung phone catalog via FastAPI endpoint with LangFuse observability',
    color: '#10b981',
    glow: 'rgba(16,185,129,0.35)',
  },
  {
    icon: '📊',
    title: 'CopilotKit Stream',
    subtitle: 'Structured Response',
    desc: 'Results formatted as natural language, streamed through CopilotKit to the chat interface',
    color: '#f59e0b',
    glow: 'rgba(245,158,11,0.35)',
  },
];

export default function Home() {
  const [theme, setTheme]     = useState<'dark' | 'light'>('dark');
  const [online, setOnline]   = useState<boolean | null>(null);
  const [flash,  setFlash]    = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('lv-theme') as 'dark' | 'light' | null;
    if (saved) setTheme(saved);
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('lv-theme', theme);
  }, [theme, mounted]);

  useEffect(() => {
    const ping = async () => {
      try {
        const r = await fetch('http://localhost:3050/health');
        const d = await r.json();
        setOnline(d?.status === 'ok');
      } catch { setOnline(false); }
    };
    ping();
    const t = setInterval(ping, 30_000);
    return () => clearInterval(t);
  }, []);

  const sendPrompt = useCallback((text: string) => {
    if (!text || !text.trim()) return;
    setFlash(text);
    setTimeout(() => setFlash(null), 900);

    const textarea = document.querySelector<HTMLTextAreaElement>(
      '.lv-chat-wrap textarea, [class*="copilot"] textarea, [class*="Copilot"] textarea'
    );
    
    if (textarea) {
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )?.set;
      
      if (nativeSetter) {
        nativeSetter.call(textarea, text);
      } else {
        textarea.value = text;
      }
      
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
      textarea.dispatchEvent(new Event('change', { bubbles: true }));
      
      setTimeout(() => {
        const sendBtn = document.querySelector<HTMLButtonElement>(
          '.lv-chat-wrap button[type="submit"], ' +
          '[class*="copilot"] button[type="submit"], ' +
          '[class*="Copilot"] button[type="submit"], ' +
          '.lv-chat-wrap [aria-label*="send" i], ' +
          '[class*="copilot"] [aria-label*="send" i], ' +
          '.lv-chat-wrap [aria-label*="Send" i], ' +
          '[class*="copilot"] [aria-label*="Send" i], ' +
          '.lv-chat-wrap button:has(svg), ' +
          '[class*="copilot"] button:has(svg)'
        );
        
        if (sendBtn) {
          sendBtn.click();
        } else {
          textarea.dispatchEvent(
            new KeyboardEvent('keydown', {
              key: 'Enter',
              code: 'Enter',
              keyCode: 13,
              which: 13,
              bubbles: true,
              cancelable: true,
            })
          );
        }
      }, 150);
    }
  }, []);

  const dark = theme === 'dark';

  if (!mounted) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: '#0d1829',
        color: '#e2e8f0',
        fontFamily: 'Inter, system-ui, sans-serif'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '24px', fontWeight: 800, marginBottom: '8px' }}>
            <span style={{ color: '#e75933' }}>Lumivya</span>
            <span style={{ color: '#6b7280', fontSize: '18px' }}> AI Studio</span>
          </div>
          <div style={{ fontSize: '13px', color: '#6b7280' }}>Loading...</div>
        </div>
      </div>
    );
  }

  const css = `
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; }

    body {
      background: ${dark ? '#0d1829' : '#f0f4f8'};
      color: ${dark ? '#e2e8f0' : '#111827'};
      transition: background 0.35s ease, color 0.25s ease;
      overflow: hidden;
    }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
      background: ${dark ? 'rgba(231,89,51,0.30)' : 'rgba(231,89,51,0.25)'};
      border-radius: 99px;
    }

    .orb {
      position: fixed; border-radius: 50%; pointer-events: none;
      filter: blur(100px); z-index: 0;
    }
    .orb-tl {
      width: 480px; height: 480px; top: -180px; left: -180px;
      background: ${dark ? 'rgba(23,37,84,0.65)' : 'rgba(231,89,51,0.06)'};
    }
    .orb-br {
      width: 520px; height: 520px; bottom: -200px; right: -200px;
      background: ${dark ? 'rgba(30,58,138,0.55)' : 'rgba(23,37,84,0.05)'};
    }
    .orb-accent {
      width: 220px; height: 220px; top: 35%; left: 55%;
      background: ${dark ? 'rgba(231,89,51,0.07)' : 'rgba(231,89,51,0.04)'};
    }

    .lv-header {
      position: relative; z-index: 30;
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 24px; flex-shrink: 0;
      background: ${dark ? 'rgba(13,24,41,0.85)' : 'rgba(255,255,255,0.90)'};
      border-bottom: 1px solid ${dark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.07)'};
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
    }
    .lv-wordmark { display: flex; align-items: center; gap: 10px; }
    .lv-wordmark-text { font-size: 18px; font-weight: 800; letter-spacing: -0.02em; }
    .lv-wordmark-text span.accent { color: #e75933; }
    .lv-wordmark-text span.muted  { color: ${dark ? '#6b7280' : '#9ca3af'}; font-size: 14px; font-weight: 500; }
    .lv-sub {
      font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase;
      color: ${dark ? '#6b7280' : '#9ca3af'}; margin-top: 1px;
    }

    .lv-header-right { display: flex; align-items: center; gap: 10px; }

    .lv-theme-btn {
      padding: 5px 14px; border-radius: 99px; font-size: 11px; font-weight: 600;
      border: 1px solid ${dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)'};
      background: ${dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'};
      color: ${dark ? '#e2e8f0' : '#374151'};
      cursor: pointer; letter-spacing: 0.02em;
      transition: border-color 0.2s, background 0.2s;
    }
    .lv-theme-btn:hover { border-color: #e75933; }

    .status-badge {
      display: flex; align-items: center; gap: 6px;
      padding: 5px 12px; border-radius: 99px; font-size: 11px; font-weight: 600;
      letter-spacing: 0.02em; border: 1px solid;
    }
    .status-ok     { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.25); color: #10b981; }
    .status-err    { background: rgba(239,68,68,0.08);  border-color: rgba(239,68,68,0.25);  color: #ef4444; }
    .status-wait   { background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.25); color: #f59e0b; }
    .status-dot {
      width: 6px; height: 6px; border-radius: 50%;
      animation: blink 2s ease infinite;
    }
    .dot-green { background: #10b981; }
    .dot-red   { background: #ef4444; animation: none; }
    .dot-amber { background: #f59e0b; }
    @keyframes blink {
      0%,100% { opacity:1; transform:scale(1); }
      50%      { opacity:0.4; transform:scale(0.75); }
    }

    .lv-app {
      display: flex; flex-direction: column;
      height: 100vh; width: 100vw;
      overflow: hidden;
    }

    .lv-body {
      position: relative; z-index: 10;
      display: flex; gap: 16px;
      padding: 16px 20px 16px;
      flex: 1; min-height: 0;
      overflow: hidden;
    }

    .lv-sidebar {
      width: 220px; flex-shrink: 0;
      display: flex; flex-direction: column; gap: 6px;
      overflow-y: auto; padding-right: 2px;
    }
    .sidebar-section-label {
      font-size: 9px; font-weight: 700; letter-spacing: 0.10em;
      text-transform: uppercase; color: ${dark ? '#6b7280' : '#9ca3af'};
      padding: 0 2px; margin-bottom: 4px;
    }
    .prompt-card {
      display: flex; align-items: center; gap: 9px;
      padding: 9px 11px; border-radius: 10px;
      background: ${dark ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.80)'};
      border: 1px solid ${dark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.07)'};
      cursor: pointer; transition: all 0.18s ease;
      color: ${dark ? '#cbd5e1' : '#374151'};
      font-family: inherit;
    }
    .prompt-card:hover {
      border-color: #e75933;
      background: ${dark ? 'rgba(231,89,51,0.08)' : 'rgba(231,89,51,0.06)'};
      transform: translateX(3px);
    }
    .prompt-card.active {
      border-color: #e75933;
      background: ${dark ? 'rgba(231,89,51,0.12)' : 'rgba(231,89,51,0.08)'};
    }
    .prompt-icon  { font-size: 14px; flex-shrink: 0; }
    .prompt-label { font-size: 12px; font-weight: 500; line-height: 1.3; }

    .sidebar-divider { height: 1px; background: ${dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'}; margin: 8px 0; }

    .stack-wrap { display: flex; flex-wrap: wrap; gap: 5px; }
    .stack-chip {
      font-size: 10px; font-weight: 600;
      padding: 3px 8px; border-radius: 99px;
      background: ${dark ? 'rgba(231,89,51,0.10)' : 'rgba(231,89,51,0.08)'};
      border: 1px solid ${dark ? 'rgba(231,89,51,0.25)' : 'rgba(231,89,51,0.22)'};
      color: #e75933;
      letter-spacing: 0.02em;
    }

    /* ── MAIN ── */
    .lv-main { 
      flex: 1; 
      display: flex; 
      flex-direction: column; 
      gap: 12px; 
      min-width: 0; 
      min-height: 0;
      overflow-y: auto;
      align-items: center;
      padding-bottom: 8px;
    }

    /* ── HERO (full width within centered column) ── */
    .lv-hero { text-align: center; padding: 4px 0; flex-shrink: 0; width: 100%; max-width: 800px; }
    .lv-eyebrow {
      display: inline-flex; align-items: center; gap: 6px;
      font-size: 10px; font-weight: 700; letter-spacing: 0.10em;
      text-transform: uppercase; color: #e75933;
      background: ${dark ? 'rgba(231,89,51,0.08)' : 'rgba(231,89,51,0.07)'};
      border: 1px solid ${dark ? 'rgba(231,89,51,0.22)' : 'rgba(231,89,51,0.18)'};
      padding: 4px 12px; border-radius: 99px; margin-bottom: 10px;
    }
    .lv-hero h1 {
      font-size: 22px; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 6px;
    }
    .lv-hero h1 .hl { color: #e75933; }
    .lv-hero p { font-size: 13px; color: ${dark ? '#94a3b8' : '#6b7280'}; }

    /* ── FEATURE STRIP (max-width to match chat) ── */
    .feature-strip { 
      display: grid; 
      grid-template-columns: repeat(4,1fr); 
      gap: 8px; 
      flex-shrink: 0;
      width: 100%;
      max-width: 800px;
    }
    .feature-card {
      display: flex; align-items: center; gap: 8px;
      padding: 9px 12px; border-radius: 10px; font-size: 12px; font-weight: 500;
      background: ${dark ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.85)'};
      border: 1px solid ${dark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.07)'};
      transition: border-color 0.2s;
      color: ${dark ? '#cbd5e1' : '#374151'};
    }
    .feature-card:hover { border-color: #e75933; }
    .feature-icon {
      width: 26px; height: 26px; border-radius: 6px; flex-shrink: 0;
      background: rgba(231,89,51,0.10); border: 1px solid rgba(231,89,51,0.20);
      display: flex; align-items: center; justify-content: center; font-size: 13px;
    }

    /* ══════════════════════════════════════════════════════════════════════════
       CHAT WRAPPER — CENTERED with max-width, both messages AND input centered
       ══════════════════════════════════════════════════════════════════════════ */

    .lv-chat-wrap {
      width: 100%;
      max-width: 800px;
      min-height: 380px;
      max-height: 420px;
      border-radius: 14px;
      overflow: hidden;
      flex-shrink: 0;
      margin-left: auto;
      margin-right: auto;
      background: ${dark ? 'rgba(13,24,41,0.65)' : 'rgba(255,255,255,0.88)'};
      border: 1px solid ${dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'};
      backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
      box-shadow: ${dark
        ? '0 12px 48px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.04)'
        : '0 4px 24px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.9)'};
    }

    /* CopilotKit root fills the wrapper */
    .lv-chat-wrap > div {
      width: 100% !important;
      height: 100% !important;
      display: flex !important;
      flex-direction: column !important;
    }

    /* ALL internal CopilotKit containers — full width */
    .lv-chat-wrap [class*="copilot"],
    .lv-chat-wrap [class*="Copilot"] {
      width: 100% !important;
      max-width: 100% !important;
    }

    /* Messages area — full width, scrollable */
    .lv-chat-wrap [class*="Messages"],
    .lv-chat-wrap [class*="messages"],
    .lv-chat-wrap [class*="ChatMessages"],
    .lv-chat-wrap [class*="chatMessages"],
    .lv-chat-wrap [class*="MessageList"],
    .lv-chat-wrap [class*="messageList"] {
      flex: 1 !important;
      width: 100% !important;
      max-width: 100% !important;
      overflow-y: auto !important;
      min-height: 0 !important;
    }

    /* Individual messages — full width so text fills naturally */
    .lv-chat-wrap [class*="Message"],
    .lv-chat-wrap [class*="message"],
    .lv-chat-wrap [class*="Bubble"],
    .lv-chat-wrap [class*="bubble"] {
      width: 100% !important;
      max-width: 100% !important;
    }

    /* Input area — full width, pinned to bottom */
    .lv-chat-wrap [class*="Input"],
    .lv-chat-wrap [class*="input"],
    .lv-chat-wrap [class*="ChatInput"],
    .lv-chat-wrap [class*="chatInput"],
    .lv-chat-wrap [class*="Footer"],
    .lv-chat-wrap [class*="footer"],
    .lv-chat-wrap [class*="Composer"],
    .lv-chat-wrap [class*="composer"],
    .lv-chat-wrap [class*="InputArea"],
    .lv-chat-wrap [class*="inputArea"] {
      width: 100% !important;
      max-width: 100% !important;
      flex-shrink: 0 !important;
    }

    /* Form inside input area */
    .lv-chat-wrap form,
    .lv-chat-wrap [class*="Form"],
    .lv-chat-wrap [class*="form"] {
      width: 100% !important;
      display: flex !important;
    }

    /* Textarea — full width */
    .lv-chat-wrap textarea,
    .lv-chat-wrap input[type="text"] {
      width: 100% !important;
      flex: 1 !important;
    }

    /* Send button */
    .lv-chat-wrap button[type="submit"],
    .lv-chat-wrap [class*="send"],
    .lv-chat-wrap [class*="Send"],
    .lv-chat-wrap [class*="SendButton"],
    .lv-chat-wrap [class*="sendButton"] {
      flex-shrink: 0 !important;
    }

    .copilot-fill {
      height: 95% !important;
      width:95% !important;
    }

    /* ══════════════════════════════════════════════════════════════════════════
       ARCHITECTURE SECTION — full width
       ══════════════════════════════════════════════════════════════════════════ */

    .arch-section {
      width: 100%;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .arch-header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 0 6px;
    }
    .arch-header-badge {
      padding: 5px 12px;
      border-radius: 99px;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      background: ${dark ? 'rgba(231,89,51,0.10)' : 'rgba(231,89,51,0.07)'};
      border: 1px solid ${dark ? 'rgba(231,89,51,0.25)' : 'rgba(231,89,51,0.20)'};
      color: #e75933;
    }
    .arch-header-line {
      flex: 1;
      height: 1px;
      background: ${dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'};
    }

    .arch-flow {
      display: flex;
      align-items: stretch;
      gap: 0;
      background: ${dark ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.60)'};
      border: 1px solid ${dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'};
      border-radius: 16px;
      overflow: hidden;
      position: relative;
      min-height: 160px;
    }

    .arch-step {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      gap: 10px;
      padding: 20px 12px 18px;
      position: relative;
      transition: background 0.25s;
      cursor: default;
    }
    .arch-step:hover {
      background: ${dark ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.50)'};
    }

    .arch-step::after {
      content: '';
      position: absolute;
      right: 0;
      top: 15%;
      height: 70%;
      width: 1px;
      background: ${dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)'};
    }
    .arch-step:last-child::after {
      display: none;
    }

    .arch-icon-wrap {
      width: 52px;
      height: 52px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      flex-shrink: 0;
      position: relative;
      transition: transform 0.25s, box-shadow 0.25s;
    }
    .arch-step:hover .arch-icon-wrap {
      transform: scale(1.08);
    }

    .arch-step-title {
      font-size: 14px;
      font-weight: 700;
      color: ${dark ? '#f1f5f9' : '#1e293b'};
      line-height: 1.2;
      letter-spacing: -0.01em;
    }
    .arch-step-subtitle {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      line-height: 1;
    }
    .arch-step-desc {
      font-size: 11px;
      color: ${dark ? '#94a3b8' : '#6b7280'};
      line-height: 1.5;
      max-width: 160px;
    }

    .arch-arrow {
      position: absolute;
      right: -10px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 16px;
      z-index: 2;
      color: ${dark ? '#475569' : '#cbd5d1'};
      pointer-events: none;
      opacity: 0.6;
    }
    .arch-step:last-child .arch-arrow {
      display: none;
    }

    .arch-stack-row {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      flex-wrap: wrap;
      padding: 4px 0;
    }
    .arch-stack-label {
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: ${dark ? '#64748b' : '#9ca3af'};
      margin-right: 2px;
    }
    .arch-stack-chip {
      font-size: 10px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 99px;
      background: ${dark ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.70)'};
      border: 1px solid ${dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'};
      color: ${dark ? '#cbd5e1' : '#374151'};
      letter-spacing: 0.02em;
    }

    @media (max-width: 900px) {
      .arch-flow {
        flex-wrap: wrap;
      }
      .arch-step {
        flex: 0 0 33.333%;
        min-width: 33.333%;
      }
      .arch-step::after { display: none; }
      .arch-arrow { display: none; }
    }
    @media (max-width: 600px) {
      .arch-step {
        flex: 0 0 50%;
        min-width: 50%;
      }
    }

    /* ══════════════════════════════════════════════════════════════════════════
       DARK MODE OVERRIDES
       ══════════════════════════════════════════════════════════════════════════ */

    .dark .lv-chat-wrap [class*="message"],
    .dark .lv-chat-wrap [class*="Message"],
    .dark .lv-chat-wrap [class*="bubble"],
    .dark .lv-chat-wrap [class*="Bubble"] {
      background: rgba(255,255,255,0.06) !important;
      color: #e2e8f0 !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
    }

    .dark .lv-chat-wrap [class*="user"] [class*="message"],
    .dark .lv-chat-wrap [class*="User"] [class*="Message"],
    .dark .lv-chat-wrap [class*="user"] [class*="bubble"],
    .dark .lv-chat-wrap [class*="User"] [class*="Bubble"] {
      background: rgba(231,89,51,0.15) !important;
      color: #fca5a5 !important;
      border: 1px solid rgba(231,89,51,0.25) !important;
    }

    .dark .lv-chat-wrap [class*="assistant"] [class*="message"],
    .dark .lv-chat-wrap [class*="Assistant"] [class*="Message"],
    .dark .lv-chat-wrap [class*="assistant"] [class*="bubble"],
    .dark .lv-chat-wrap [class*="Assistant"] [class*="Bubble"] {
      background: rgba(255,255,255,0.06) !important;
      color: #e2e8f0 !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
    }

    .dark .lv-chat-wrap [class*="bg-white"],
    .dark .lv-chat-wrap [style*="background: white"],
    .dark .lv-chat-wrap [style*="background: #fff"],
    .dark .lv-chat-wrap [style*="background-color: white"],
    .dark .lv-chat-wrap [style*="background-color: #fff"] {
      background: rgba(255,255,255,0.06) !important;
    }

    .dark .lv-chat-wrap [class*="text-black"],
    .dark .lv-chat-wrap [style*="color: black"],
    .dark .lv-chat-wrap [style*="color: #000"] {
      color: #e2e8f0 !important;
    }

    .dark .lv-chat-wrap [class*="text-gray-500"],
    .dark .lv-chat-wrap [class*="text-gray-600"],
    .dark .lv-chat-wrap [class*="text-gray-700"] {
      color: #94a3b8 !important;
    }

    .dark .lv-chat-wrap textarea,
    .dark .lv-chat-wrap input[type="text"] {
      background: rgba(255,255,255,0.06) !important;
      color: #e2e8f0 !important;
      border-color: rgba(255,255,255,0.12) !important;
    }
    .dark .lv-chat-wrap textarea::placeholder,
    .dark .lv-chat-wrap input::placeholder {
      color: #64748b !important;
    }

    .dark .lv-chat-wrap button[type="submit"],
    .dark .lv-chat-wrap [class*="send"],
    .dark .lv-chat-wrap [class*="Send"] {
      background: #e75933 !important;
      color: white !important;
    }

    .dark .lv-chat-wrap code,
    .dark .lv-chat-wrap pre {
      background: rgba(0,0,0,0.3) !important;
      color: #e2e8f0 !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
    }

    .dark .lv-chat-wrap a { color: #e75933 !important; }

    .dark .lv-chat-wrap table { border-color: rgba(255,255,255,0.12) !important; }
    .dark .lv-chat-wrap th {
      background: rgba(255,255,255,0.06) !important;
      color: #e2e8f0 !important;
      border-color: rgba(255,255,255,0.12) !important;
    }
    .dark .lv-chat-wrap td {
      background: rgba(255,255,255,0.03) !important;
      color: #cbd5e1 !important;
      border-color: rgba(255,255,255,0.08) !important;
    }

    /* ── FOOTER ── */
    .lv-footer {
      position: relative; z-index: 30;
      text-align: center; padding: 7px 16px;
      font-size: 10px; letter-spacing: 0.02em;
      color: ${dark ? '#6b7280' : '#9ca3af'};
      border-top: 1px solid ${dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'};
      background: ${dark ? 'rgba(13,24,41,0.85)' : 'rgba(255,255,255,0.90)'};
      backdrop-filter: blur(24px);
      flex-shrink: 0;
    }
    .lv-footer a { color: #e75933; text-decoration: none; }
    .lv-footer a:hover { text-decoration: underline; }

    .lv-cta {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 6px 16px; border-radius: 8px; font-size: 11px; font-weight: 700;
      background: #e75933; color: #fff; border: none; cursor: pointer;
      letter-spacing: 0.02em;
      box-shadow: 0 2px 12px rgba(231,89,51,0.35);
      transition: background 0.2s, transform 0.15s, box-shadow 0.2s;
    }
    .lv-cta:hover { background: #cf4e2a; transform: translateY(-1px); box-shadow: 0 4px 18px rgba(231,89,51,0.45); }

    @media (max-width: 768px) {
      .lv-sidebar    { display: none; }
      .feature-strip { grid-template-columns: repeat(2,1fr); }
      .lv-hero h1    { font-size: 17px; }
    }
  `;

  return (
    <div className="lv-app">
      <style dangerouslySetInnerHTML={{ __html: css }} />

      <div className="orb orb-tl" />
      <div className="orb orb-br" />
      <div className="orb orb-accent" />

      {/* ══ HEADER ════════════════════════════════════════════════════════════ */}
      <header className="lv-header">
        <div className="lv-wordmark">
          <div>
            <div className="lv-wordmark-text">
              <span className="accent">Lumivya</span>
              <span className="muted"> AI Studio</span>
            </div>
            <div className="lv-sub">Bootcamp · AI + Data Engineering + CopilotKit</div>
          </div>
        </div>

        <div className="lv-header-right">
          <button
            onClick={() => setTheme(dark ? 'light' : 'dark')}
            className="lv-theme-btn"
          >
            {dark ? '☀️ Light' : '🌙 Dark'}
          </button>

          <div className={`status-badge ${
            online === null ? 'status-wait' : online ? 'status-ok' : 'status-err'
          }`}>
            <span className={`status-dot ${
              online === null ? 'dot-amber' : online ? 'dot-green' : 'dot-red'
            }`} />
            {online === null ? 'Connecting…' : online ? 'Backend live' : 'Offline'}
          </div>

          <button className="lv-cta">
            Bootcamp 2026 ✦
          </button>
        </div>
      </header>

      {/* ══ BODY ══════════════════════════════════════════════════════════════ */}
      <div className="lv-body">

        {/* ── SIDEBAR ─────────────────────────────────────────────────────── */}
        <aside className="lv-sidebar">
          <div className="sidebar-section-label">Try asking</div>

          {PROMPTS.map((p) => (
            <button
              key={p.text}
              onClick={() => sendPrompt(p.text)}
              className={`prompt-card ${flash === p.text ? 'active' : ''}`}
              type="button"
            >
              <span className="prompt-icon">{p.icon}</span>
              <span className="prompt-label">{p.label}</span>
            </button>
          ))}

          <div className="sidebar-divider" />
          <div className="sidebar-section-label">Built with</div>
          <div className="stack-wrap">
            {STACK.map((s) => (
              <span key={s} className="stack-chip">{s}</span>
            ))}
          </div>
        </aside>

        {/* ── MAIN ────────────────────────────────────────────────────────── */}
        <main className="lv-main">

          <div className="lv-hero">
            <div className="lv-eyebrow">✦ Samsung Dataset · Text-to-SQL Agent</div>
            <h1>
              Empowering <span className="hl">Data Insights</span> Through AI
            </h1>
            <p>Ask any question in plain English — get instant, SQL-backed answers from the Samsung phone catalog</p>
          </div>

          <div className="feature-strip">
            {[
              { icon: '📊', label: 'Natural Language Queries' },
              { icon: '🧠', label: 'AI SQL Generation'        },
              { icon: '📱', label: 'Phone Spec Insights'      },
              { icon: '⚡', label: 'Instant Answers'          },
            ].map((f) => (
              <div key={f.label} className="feature-card">
                <div className="feature-icon">{f.icon}</div>
                {f.label}
              </div>
            ))}
          </div>

          {/* ── CHAT — centered via max-width + auto margins ──────────────── */}
          <div className="lv-chat-wrap">
            <CopilotChat
              className="copilot-fill"
              labels={{
                chatInputPlaceholder:
                  'Ask about Samsung phones ',
              }}
            />
          </div>

          {/* ── ARCHITECTURE ──────────────────────────────────────────────── */}
          <div className="arch-section">
            <div className="arch-header">
              <span className="arch-header-badge">System Architecture</span>
              <div className="arch-header-line" />
            </div>

            <div className="arch-flow">
              {PIPELINE_STEPS.map((step, i) => (
                <div key={i} className="arch-step">
                  {i < PIPELINE_STEPS.length - 1 && (
                    <span className="arch-arrow">▸</span>
                  )}

                  <div
                    className="arch-icon-wrap"
                    style={{
                      background: `${step.color}15`,
                      border: `1px solid ${step.color}35`,
                      boxShadow: `0 0 20px ${step.glow}, inset 0 1px 0 ${step.color}20`,
                    }}
                  >
                    {step.icon}
                  </div>

                  <div className="arch-step-title">{step.title}</div>
                  
                  <div
                    className="arch-step-subtitle"
                    style={{ color: step.color }}
                  >
                    {step.subtitle}
                  </div>

                  <div className="arch-step-desc">{step.desc}</div>
                </div>
              ))}
            </div>

            <div className="arch-stack-row">
              <span className="arch-stack-label">Powered by</span>
              {['LangGraph', 'CopilotKit', 'FastAPI', 'PostgreSQL', 'Groq', 'Next.js'].map((tech) => (
                <span key={tech} className="arch-stack-chip">{tech}</span>
              ))}
            </div>
          </div>

        </main>
      </div>

      {/* ══ FOOTER ════════════════════════════════════════════════════════════ */}
      <footer className="lv-footer">
        Built during&nbsp;
        <a href="https://lumivyatech.com" target="_blank" rel="noreferrer">
          Lumivya Technology Bootcamp 2026
        </a>
        &nbsp;· Empowering individuals and businesses through quality education and innovative digital solutions.
      </footer>
    </div>
  );
}