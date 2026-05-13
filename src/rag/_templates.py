"""Glacial Archive 前端模板"""
WEB_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DocQ — 智能文档问答</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #070c14;
    --surface: #0d1520;
    --surface2: #111b28;
    --surface3: #162030;
    --border: #1a2a3d;
    --border-light: #1f3248;
    --text: #edf2f9;
    --text-dim: #7b8ea8;
    --text-dim2: #4e617b;
    --accent: #5b9bd5;
    --accent-light: #7bb8e8;
    --accent-dim: rgba(91,155,213,0.10);
    --accent-glow: rgba(91,155,213,0.16);
    --accent-strong: rgba(91,155,213,0.25);
    --frost: rgba(140,180,220,0.06);
    --green: #4fc3f7;
    --green-dim: rgba(79,195,247,0.12);
    --radius: 14px;
    --radius-sm: 8px;
    --radius-xs: 5px;
    --font-body: 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: var(--font-body);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background-image:
      radial-gradient(ellipse at 45% 0%, rgba(91,155,213,0.06) 0%, transparent 55%),
      radial-gradient(ellipse at 85% 90%, rgba(79,195,247,0.04) 0%, transparent 50%),
      linear-gradient(180deg, rgba(91,155,213,0.015) 0%, transparent 30%);
  }
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(91,155,213,0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(91,155,213,0.025) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none;
    z-index: 0;
  }
  header {
    padding: 22px 40px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    position: relative;
    z-index: 1;
  }
  .logo {
    font-family: var(--font-mono);
    font-size: 20px;
    font-weight: 500;
    color: var(--text);
    letter-spacing: 2px;
  }
  .logo em {
    font-style: normal;
    color: var(--accent);
    font-weight: 600;
  }
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .status {
    display: flex; align-items: center; gap: 7px;
    font-size: 10px; color: var(--text-dim2);
    font-family: var(--font-mono);
    letter-spacing: 1px;
  }
  .status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px rgba(79,195,247,0.6);
    animation: pulse 3.5s infinite;
  }
  .btn-clear {
    font-size: 10px;
    font-family: var(--font-mono);
    color: var(--text-dim2);
    background: none;
    border: 1px solid var(--border);
    padding: 4px 10px;
    border-radius: 3px;
    cursor: pointer;
    letter-spacing: 1px;
    transition: all 0.2s;
  }
  .btn-clear:hover {
    color: var(--accent-light);
    border-color: var(--accent);
    background: var(--accent-dim);
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.35} }

  main {
    flex: 1;
    display: flex;
    flex-direction: column;
    max-width: 840px;
    width: 100%;
    margin: 0 auto;
    padding: 20px 24px 24px;
    overflow: hidden;
    position: relative;
    z-index: 1;
  }
  .chat-area {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 22px;
    padding-bottom: 14px;
    scroll-behavior: smooth;
  }
  .chat-area::-webkit-scrollbar { width: 3px; }
  .chat-area::-webkit-scrollbar-track { background: transparent; }
  .chat-area::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 2px; }

  /* Welcome */
  .welcome {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 48px 20px;
    gap: 16px;
  }
  .welcome-icon {
    width: 48px; height: 48px;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    color: var(--accent);
    opacity: 0.5;
    background: var(--frost);
    margin-bottom: 6px;
  }
  .welcome h2 {
    font-size: 24px;
    color: var(--text);
    font-weight: 400;
    letter-spacing: 0.5px;
  }
  .welcome h2 strong { font-weight: 600; color: var(--accent); }
  .welcome p {
    font-size: 13px;
    color: var(--text-dim);
    max-width: 440px;
    line-height: 1.8;
    font-weight: 300;
  }
  .welcome-files {
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
  }
  .file-badge {
    font-size: 10px;
    font-family: var(--font-mono);
    background: var(--surface2);
    border: 1px solid var(--border);
    padding: 4px 10px;
    border-radius: 3px;
    color: var(--text-dim);
    letter-spacing: 0.5px;
  }

  /* Messages */
  .msg {
    display: flex;
    gap: 12px;
    animation: fadeUp 0.35s ease;
  }
  @keyframes fadeUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
  .msg.user { flex-direction: row-reverse; }
  .msg-avatar {
    width: 32px; height: 32px;
    border-radius: var(--radius-xs);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px;
    flex-shrink: 0;
  }
  .msg.system .msg-avatar {
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid rgba(91,155,213,0.2);
  }
  .msg.user .msg-avatar {
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    color: var(--text-dim);
  }
  .msg-body {
    max-width: 82%;
    padding: 14px 16px;
    border-radius: var(--radius-sm);
    font-size: 13.5px;
    line-height: 1.75;
  }
  .msg.system .msg-body {
    background: var(--surface);
    border: 1px solid var(--border);
    border-top-left-radius: 3px;
  }
  .msg.user .msg-body {
    background: var(--accent-dim);
    border: 1px solid rgba(91,155,213,0.18);
    border-top-right-radius: 3px;
    color: #e4edf6;
  }
  .msg-label {
    font-size: 10px;
    color: var(--text-dim2);
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 500;
    font-family: var(--font-mono);
  }
  .msg-body p { margin: 0; }
  .msg-body p + p { margin-top: 10px; }
  .msg-body strong { color: var(--accent-light); font-weight: 600; }

  /* Streaming cursor */
  .streaming-cursor {
    display: inline-block;
    width: 7px; height: 14px;
    background: var(--accent);
    margin-left: 2px;
    animation: blink 0.8s infinite;
    vertical-align: text-bottom;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

  /* Progress Pipeline */
  .pipeline {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 10px 0 14px;
    margin-bottom: 4px;
  }
  .pipe-step { display: flex; align-items: center; gap: 0; }
  .pipe-dot {
    width: 22px; height: 22px;
    border-radius: 50%;
    border: 1.5px solid var(--border-light);
    background: var(--surface2);
    display: flex; align-items: center; justify-content: center;
    font-size: 9px;
    color: var(--text-dim2);
    transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    flex-shrink: 0;
  }
  .pipe-dot.done {
    border-color: var(--accent);
    background: var(--accent-dim);
    color: var(--accent-light);
    box-shadow: 0 0 12px var(--accent-dim);
  }
  .pipe-dot.active {
    border-color: var(--accent-light);
    background: var(--accent-strong);
    color: #fff;
    box-shadow: 0 0 18px var(--accent-glow), 0 0 4px rgba(91,155,213,0.4);
    animation: frostPulse 1s infinite alternate;
  }
  @keyframes frostPulse {
    from { box-shadow: 0 0 10px var(--accent-dim), 0 0 2px rgba(91,155,213,0.3); }
    to   { box-shadow: 0 0 22px var(--accent-glow), 0 0 8px rgba(91,155,213,0.5); }
  }
  .pipe-line {
    width: 28px; height: 1px;
    background: var(--border);
    transition: background 0.6s ease;
    flex-shrink: 0;
  }
  .pipe-line.lit { background: var(--accent); opacity: 0.4; }
  .pipe-label {
    font-size: 8px;
    color: var(--text-dim2);
    font-family: var(--font-mono);
    white-space: nowrap;
    margin-top: 4px;
    transition: color 0.5s ease;
    text-align: center;
    letter-spacing: 0.5px;
  }
  .pipe-label.done { color: var(--accent); }
  .pipe-label.active { color: var(--accent-light); }
  .pipe-step-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }

  /* Live indicator during streaming */
  .live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 10px;
    font-family: var(--font-mono);
    color: var(--accent);
    letter-spacing: 1px;
    margin-bottom: 8px;
    animation: livePulse 1.5s infinite;
  }
  .live-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--accent);
  }
  @keyframes livePulse {
    0%,100% { opacity: 0.5; }
    50% { opacity: 1; }
  }

  /* Evidence / Source Snippets */
  .evidence-section {
    margin-top: 14px;
    border-top: 1px solid var(--border);
    padding-top: 12px;
  }
  .evidence-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    cursor: pointer;
    user-select: none;
    padding: 4px 0;
  }
  .evidence-header:hover .evidence-title { color: var(--accent-light); }
  .evidence-title {
    font-size: 10px;
    font-family: var(--font-mono);
    color: var(--text-dim2);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    transition: color 0.2s;
  }
  .evidence-toggle {
    font-size: 9px;
    color: var(--text-dim2);
    transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    display: inline-block;
  }
  .evidence-toggle.open { transform: rotate(90deg); }
  .evidence-count {
    font-size: 10px;
    color: var(--text-dim2);
    font-family: var(--font-mono);
    margin-left: auto;
  }
  .snippet-cards {
    display: flex;
    flex-direction: column;
    gap: 7px;
    overflow: hidden;
    max-height: 0;
    transition: max-height 0.45s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
    opacity: 0;
  }
  .snippet-cards.open {
    max-height: 900px;
    opacity: 1;
  }
  .snippet-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 2px solid var(--accent);
    border-radius: 0 var(--radius-xs) var(--radius-xs) 0;
    padding: 10px 12px 10px 14px;
    animation: fadeUp 0.35s ease;
  }
  .snippet-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }
  .snippet-file {
    font-size: 10px;
    font-family: var(--font-mono);
    color: var(--accent-light);
    background: var(--accent-dim);
    padding: 2px 8px;
    border-radius: 2px;
    letter-spacing: 0.5px;
  }
  .snippet-relevance {
    font-size: 10px;
    color: var(--text-dim2);
    font-family: var(--font-mono);
    margin-left: auto;
  }
  .snippet-text {
    font-size: 12px;
    line-height: 1.7;
    color: var(--text-dim);
    font-family: var(--font-body);
    max-height: 78px;
    overflow-y: auto;
    padding-right: 4px;
    font-weight: 300;
  }
  .snippet-text::-webkit-scrollbar { width: 3px; }
  .snippet-text::-webkit-scrollbar-track { background: transparent; }
  .snippet-text::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
  .snippet-ellipsis {
    font-size: 10px;
    color: var(--text-dim2);
    font-family: var(--font-mono);
    margin-top: 4px;
    opacity: 0.7;
  }

  /* Input */
  .input-area {
    flex-shrink: 0;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 5px 5px 5px 8px;
    display: flex;
    align-items: flex-end;
    gap: 8px;
    transition: border-color 0.25s, box-shadow 0.25s;
  }
  .input-area:focus-within {
    border-color: rgba(91,155,213,0.45);
    box-shadow: 0 0 0 3px rgba(91,155,213,0.06), inset 0 0 20px rgba(91,155,213,0.02);
  }
  .input-area textarea {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-family: var(--font-body);
    font-size: 13.5px;
    resize: none;
    padding: 9px 6px;
    min-height: 22px;
    max-height: 150px;
    line-height: 1.6;
    font-weight: 300;
  }
  .input-area textarea::placeholder { color: var(--text-dim2); }
  .input-area button {
    background: var(--accent-dim);
    color: var(--accent-light);
    border: 1px solid rgba(91,155,213,0.25);
    width: 36px; height: 36px;
    border-radius: 50%;
    flex-shrink: 0;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.25s;
    margin-bottom: 1px;
  }
  .input-area button:hover {
    background: var(--accent-strong);
    border-color: var(--accent);
    color: #fff;
    box-shadow: 0 0 18px var(--accent-glow);
  }
  .input-area button:disabled { opacity: 0.2; transform: none; box-shadow: none; cursor: default; }
  .stop-btn {
    background: rgba(220,80,80,0.12) !important;
    color: #e07070 !important;
    border-color: rgba(220,80,80,0.3) !important;
  }
  .stop-btn:hover {
    background: rgba(220,80,80,0.25) !important;
    box-shadow: 0 0 14px rgba(220,80,80,0.2) !important;
  }

  footer {
    text-align: center;
    padding: 10px;
    font-size: 10px;
    color: var(--text-dim2);
    opacity: 0.5;
    flex-shrink: 0;
    font-family: var(--font-mono);
    letter-spacing: 1px;
    position: relative;
    z-index: 1;
  }
  .toast {
    position: fixed;
    top: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: #0f1a24;
    border: 1px solid #1e3548;
    color: #8ab4d6;
    padding: 11px 22px;
    border-radius: var(--radius-xs);
    font-size: 12px;
    z-index: 100;
    font-family: var(--font-body);
    animation: slideDown 0.3s ease;
  }
  @keyframes slideDown {
    from{opacity:0;transform:translateX(-50%) translateY(-10px)}
    to{opacity:1;transform:translateX(-50%) translateY(0)}
  }

  /* ── 对话侧边栏 ── */
  .app-shell { display: flex; height: 100vh; }
  .conv-sidebar {
    width: 280px; min-width: 280px;
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex; flex-direction: column;
    flex-shrink: 0;
  }
  .conv-sidebar-header {
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
  }
  .btn-new-chat {
    width: 100%; padding: 9px 0; border-radius: var(--radius-xs);
    border: 1px solid var(--border);
    background: var(--surface2);
    color: var(--accent-light);
    font-family: var(--font-mono); font-size: 11px;
    cursor: pointer; letter-spacing: 1px;
    transition: all 0.2s;
  }
  .btn-new-chat:hover {
    border-color: var(--accent);
    background: var(--accent-dim);
  }
  .conv-list {
    flex: 1; overflow-y: auto; padding: 6px;
    display: flex; flex-direction: column; gap: 3px;
  }
  .conv-list::-webkit-scrollbar { width: 2px; }
  .conv-list::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 1px; }
  .conv-item {
    padding: 9px 12px; border-radius: var(--radius-xs);
    cursor: pointer; transition: background 0.15s;
    border: 1px solid transparent; position: relative;
  }
  .conv-item:hover {
    background: var(--surface2);
    border-color: var(--border);
  }
  .conv-item.active {
    background: var(--surface2);
    border-color: var(--border-light);
  }
  .conv-item .cv-title {
    font-size: 12px; color: var(--text);
    line-height: 1.4; margin-bottom: 2px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    padding-right: 28px;
  }
  .conv-item .cv-meta {
    font-size: 10px; color: var(--text-dim2);
    font-family: var(--font-mono);
  }
  .conv-item .cv-del {
    position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
    width: 20px; height: 20px; border-radius: 3px;
    border: none; background: transparent;
    color: var(--text-dim2); cursor: pointer;
    font-size: 13px; line-height: 1;
    display: none; align-items: center; justify-content: center;
  }
  .conv-item:hover .cv-del { display: flex; }
  .conv-item .cv-del:hover {
    background: rgba(239,68,68,0.15);
    color: #ef4444;
  }
  .conv-empty {
    font-size: 11px; color: var(--text-dim2);
    text-align: center; padding: 32px 8px;
    font-family: var(--font-mono); line-height: 1.8;
  }
  .conv-loading {
    font-size: 10px; color: var(--text-dim2);
    text-align: center; padding: 16px;
  }
</style>
</head>
<body>
<div class="app-shell">
<div class="conv-sidebar" id="convSidebar">
  <div class="conv-sidebar-header">
    <button class="btn-new-chat" onclick="newConversation()">+ 新建对话</button>
  </div>
  <div class="conv-list" id="convList">
    <div class="conv-loading">加载中...</div>
  </div>
</div>
<div style="display:flex;flex-direction:column;flex:1;min-width:0;">
<header>
  <div class="logo">DOC<em>Q</em></div>
  <div class="header-right">
    <button class="btn-clear" onclick="clearCurrentConversation()" title="清空当前对话">CLEAR</button>
    <div class="status"><span class="status-dot"></span> DeepSeek</div>
  </div>
</header>
<main>
  <div class="chat-area" id="chatArea">
    <div class="welcome" id="welcomeBox">
      <div class="welcome-icon">&#9632;</div>
      <h2>Glacial <strong>Archive</strong></h2>
      <p>基于 DeepSeek 的本地文档智能问答系统。支持多轮对话与实时流式输出。</p>
      <div class="welcome-files" id="welcomeFiles"></div>
    </div>
  </div>
  <div class="input-area">
    <textarea id="queryInput" rows="1" placeholder="输入问题…"
      onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendQuery();}"
      oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,150)+'px';"
    ></textarea>
    <button id="sendBtn" onclick="sendQuery()" title="发送">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
    </button>
  </div>
</main>
<footer>archive — retrieval augmented generation</footer>
<script>
  const chatArea = document.getElementById('chatArea');
  const input = document.getElementById('queryInput');
  const sendBtn = document.getElementById('sendBtn');
  let waiting = false;
  let abortController = null;

  async function loadFiles() {
    try {
      const r = await fetch('/api/files');
      const data = await r.json();
      const el = document.getElementById('welcomeFiles');
      if (el && data.files && data.files.length) {
        el.innerHTML = data.files.map(f => '<span class="file-badge">'+f+'</span>').join('');
      }
    } catch(e) {}
  }
  loadFiles();

  /* --- Pipeline --- */
  const PIPELINE_STEPS = [
    { ico: '◆', label: '检索匹配' },
    { ico: '◇', label: '精排筛选' },
    { ico: '○', label: '阅读理解' },
    { ico: '●', label: '生成回答' },
  ];

  function buildPipeline() {
    const wrap = document.createElement('div');
    wrap.className = 'pipeline';
    PIPELINE_STEPS.forEach((s, i) => {
      const step = document.createElement('div');
      step.className = 'pipe-step';
      const inner = document.createElement('div');
      inner.className = 'pipe-step-inner';
      const dot = document.createElement('div');
      dot.className = 'pipe-dot';
      dot.textContent = s.ico;
      inner.appendChild(dot);
      const lbl = document.createElement('div');
      lbl.className = 'pipe-label';
      lbl.textContent = s.label;
      inner.appendChild(lbl);
      step.appendChild(inner);
      wrap.appendChild(step);
      if (i < PIPELINE_STEPS.length - 1) {
        const line = document.createElement('div');
        line.className = 'pipe-line';
        line.style.alignSelf = 'center';
        line.style.marginBottom = '16px';
        wrap.appendChild(line);
        step._line = line;
      }
      step._dot = dot;
      step._lbl = lbl;
    });
    return { wrap, steps: wrap.querySelectorAll('.pipe-step') };
  }

  function markPipelineStep(pipeEl, stepIdx) {
    const steps = pipeEl.steps;
    const lines = pipeEl.wrap.querySelectorAll('.pipe-line');
    for (let i = 0; i < stepIdx; i++) {
      steps[i]._dot.className = 'pipe-dot done';
      steps[i]._lbl.className = 'pipe-label done';
      if (lines[i]) lines[i].classList.add('lit');
    }
    if (stepIdx < steps.length) {
      steps[stepIdx]._dot.className = 'pipe-dot active';
      steps[stepIdx]._lbl.className = 'pipe-label active';
    }
  }

  function finishPipeline(pipeEl) {
    const steps = pipeEl.steps;
    const lines = pipeEl.wrap.querySelectorAll('.pipe-line');
    steps.forEach(s => {
      s._dot.className = 'pipe-dot done';
      s._lbl.className = 'pipe-label done';
    });
    lines.forEach(l => l.classList.add('lit'));
  }

  /* --- Source Snippets (Drawer) --- */
  function buildEvidence(snippets) {
    const section = document.createElement('div');
    section.className = 'evidence-section';
    const header = document.createElement('div');
    header.className = 'evidence-header';
    const toggle = document.createElement('span');
    toggle.className = 'evidence-toggle';
    toggle.textContent = '▶';
    const title = document.createElement('span');
    title.className = 'evidence-title';
    title.textContent = 'ARCHIVE REFERENCES';
    const count = document.createElement('span');
    count.className = 'evidence-count';
    count.textContent = snippets.length;
    header.appendChild(toggle);
    header.appendChild(title);
    header.appendChild(count);
    const cards = document.createElement('div');
    cards.className = 'snippet-cards';
    snippets.forEach((sn, idx) => {
      const card = document.createElement('div');
      card.className = 'snippet-card';
      card.style.animationDelay = (idx * 0.06) + 's';
      const ch = document.createElement('div');
      ch.className = 'snippet-card-header';
      const file = document.createElement('span');
      file.className = 'snippet-file';
      file.textContent = sn.file;
      const rel = document.createElement('span');
      rel.className = 'snippet-relevance';
      rel.textContent = '#' + (idx + 1);
      ch.appendChild(file);
      ch.appendChild(rel);
      const text = document.createElement('div');
      text.className = 'snippet-text';
      text.textContent = sn.text;
      card.appendChild(ch);
      card.appendChild(text);
      if (sn.text.length >= 600) {
        const dots = document.createElement('div');
        dots.className = 'snippet-ellipsis';
        dots.textContent = '… content truncated';
        card.appendChild(dots);
      }
      cards.appendChild(card);
    });
    header.addEventListener('click', () => {
      const isOpen = cards.classList.toggle('open');
      toggle.classList.toggle('open', isOpen);
    });
    section.appendChild(header);
    section.appendChild(cards);
    return section;
  }

  /* --- Messages --- */
  function addUserMsg(text) {
    const wb = document.getElementById('welcomeBox'); if (wb) wb.remove();
    const div = document.createElement('div');
    div.className = 'msg user';
    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = 'Q';
    const body = document.createElement('div');
    body.className = 'msg-body';
    const label = document.createElement('div');
    label.className = 'msg-label';
    label.textContent = 'query';
    body.appendChild(label);
    const p = document.createElement('p');
    p.textContent = text;
    body.appendChild(p);
    div.appendChild(avatar);
    div.appendChild(body);
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
    return div;
  }

  function createStreamingMsg() {
    const wb = document.getElementById('welcomeBox'); if (wb) wb.remove();
    const div = document.createElement('div');
    div.className = 'msg system';
    div.id = 'streamingMsg';
    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = 'A';
    const body = document.createElement('div');
    body.className = 'msg-body';
    // Label
    const label = document.createElement('div');
    label.className = 'msg-label';
    label.textContent = 'archive · streaming';
    body.appendChild(label);
    // Pipeline
    const pipe = buildPipeline();
    body.appendChild(pipe.wrap);
    // Live indicator
    const live = document.createElement('div');
    live.className = 'live-indicator';
    live.innerHTML = '<span class="live-dot"></span> LIVE';
    body.appendChild(live);
    // Answer container
    const answerEl = document.createElement('div');
    answerEl.className = 'streaming-answer';
    answerEl.style.minHeight = '20px';
    body.appendChild(answerEl);
    div.appendChild(avatar);
    div.appendChild(body);
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
    return { div, pipe, answerEl, live, body };
  }

  function finalizeStreamingMsg(msgObj, fullAnswer, snippets) {
    const { div, pipe, live, body, answerEl } = msgObj;
    div.removeAttribute('id');
    // Remove pipeline & live indicator
    pipe.wrap.remove();
    live.remove();
    // Set final answer
    const label = body.querySelector('.msg-label');
    label.textContent = 'archive';
    const paragraphs = fullAnswer.split(/\n\n+/);
    answerEl.innerHTML = '';
    paragraphs.forEach(pText => {
      const el = document.createElement('p');
      let html = pText.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/`([^`]+)`/g, '<code style="background:rgba(91,155,213,0.08);padding:1px 6px;border-radius:2px;font-family:JetBrains Mono,monospace;font-size:11.5px;color:#7bb8e8;">$1</code>');
      el.innerHTML = html;
      answerEl.appendChild(el);
    });
    // Add evidence
    if (snippets && snippets.length) {
      body.appendChild(buildEvidence(snippets));
    }
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(function() { toast.remove(); }, 3500);
  }

  /* --- SSE Stream Reader --- */
  async function readSSEStream(response, msgObj) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullAnswer = '';
    let snippets = [];

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6);
          try {
            const event = JSON.parse(jsonStr);
            if (event.type === 'retrieval_done') {
              // Mark first 2 steps done
              markPipelineStep(msgObj.pipe, 2);
              snippets = event.snippets || [];
            } else if (event.type === 'token') {
              fullAnswer += event.text;
              // Render markdown-like formatting on the fly
              let display = fullAnswer
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/`([^`]+)`/g, '<code style="background:rgba(91,155,213,0.08);padding:1px 6px;border-radius:2px;font-family:JetBrains Mono,monospace;font-size:11.5px;color:#7bb8e8;">$1</code>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>');
              msgObj.answerEl.innerHTML = '<p>' + display + '</p><span class="streaming-cursor"></span>';
              chatArea.scrollTop = chatArea.scrollHeight;
            } else if (event.type === 'done') {
              finishPipeline(msgObj.pipe);
            } else if (event.type === 'error') {
              showToast(event.message || '生成失败');
            }
          } catch (e) {
            // ignore malformed JSON in partial chunks
          }
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        showToast('流式连接中断');
      }
    }

    return { fullAnswer, snippets };
  }

  async function clearConversation() {
    try {
      await fetch('/api/conversation/clear', { method: 'POST' });
    } catch(e) {}
    // Reload to reset frontend state cleanly
    location.reload();
  }

  function setSendBtnStop() {
    sendBtn.classList.add('stop-btn');
    sendBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>';
    sendBtn.onclick = stopGeneration;
  }

  function setSendBtnSend() {
    sendBtn.classList.remove('stop-btn');
    sendBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    sendBtn.onclick = sendQuery;
  }

  function stopGeneration() {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    waiting = false;
    setSendBtnSend();
    sendBtn.disabled = false;
    input.focus();
  }

  async function sendQuery() {
    if (waiting) return;
    const query = input.value.trim();
    if (!query) return;
    waiting = true;
    sendBtn.disabled = false;
    setSendBtnStop();

    addUserMsg(query);
    input.value = '';
    input.style.height = 'auto';

    const msgObj = createStreamingMsg();

    abortController = new AbortController();
    try {
      const res = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query }),
        signal: abortController.signal
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        showToast(errData.error || '请求失败');
        msgObj.div.remove();
        waiting = false;
        setSendBtnSend();
        sendBtn.disabled = false;
        return;
      }

      const { fullAnswer, snippets } = await readSSEStream(res, msgObj);
      finalizeStreamingMsg(msgObj, fullAnswer, snippets);
    } catch (e) {
      if (e.name !== 'AbortError') {
        showToast('请求失败，请检查服务是否正常运行');
        msgObj.div.remove();
      }
    }

    abortController = null;
    waiting = false;
    setSendBtnSend();
    sendBtn.disabled = false;
    input.focus();
  }

  /* ── 对话管理逻辑 ── */
  let currentConvId = null;
  const convList = document.getElementById('convList');

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function formatTime(iso) {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      const now = new Date();
      const pad = n => String(n).padStart(2,'0');
      const time = pad(d.getHours()) + ':' + pad(d.getMinutes());
      if (d.toDateString() === now.toDateString()) return time;
      return (d.getMonth()+1) + '/' + d.getDate() + ' ' + time;
    } catch(e) { return ''; }
  }

  async function loadConversations() {
    try {
      const res = await fetch('/api/conversations');
      const data = await res.json();
      const convs = data.conversations || [];
      if (convs.length === 0) {
        convList.innerHTML = '<div class="conv-empty">暂无对话<br>点击上方按钮开始</div>';
        return;
      }
      convList.innerHTML = convs.map(c => {
        const active = c.id === currentConvId ? ' active' : '';
        return '<div class="conv-item' + active + '" data-id="' + c.id + '" onclick="switchConversation(\'' + c.id + '\')">' +
          '<div class="cv-title">' + escapeHtml(c.title || '新对话') + '</div>' +
          '<div class="cv-meta">' + c.message_count + ' 条消息 · ' + formatTime(c.updated_at) + '</div>' +
          '<button class="cv-del" onclick="event.stopPropagation();deleteConversation(\'' + c.id + '\')" title="删除">×</button>' +
          '</div>';
      }).join('');
    } catch(e) {
      convList.innerHTML = '<div class="conv-empty">加载失败</div>';
    }
  }

  async function newConversation() {
    try {
      const res = await fetch('/api/conversations', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title: '新对话'})
      });
      const data = await res.json();
      const conv = data.conversation;
      currentConvId = conv.id;
      // 清空聊天区
      document.getElementById('chatArea').innerHTML =
        '<div class="welcome" id="welcomeBox">' +
        '<div class="welcome-icon">&#9632;</div>' +
        '<h2>Glacial <strong>Archive</strong></h2>' +
        '<p>基于 DeepSeek 的本地文档智能问答系统。支持多轮对话与实时流式输出。</p>' +
        '<div class="welcome-files" id="welcomeFiles"></div>' +
        '</div>';
      loadFiles();
      await loadConversations();
    } catch(e) {
      showToast('创建对话失败');
    }
  }

  async function switchConversation(convId) {
    if (convId === currentConvId) return;
    currentConvId = convId;
    try {
      const res = await fetch('/api/conversations/' + convId);
      const data = await res.json();
      const conv = data.conversation;
      const chatArea = document.getElementById('chatArea');
      chatArea.innerHTML = '';
      if (conv && conv.messages && conv.messages.length > 0) {
        conv.messages.forEach(m => {
          if (m.role === 'user') addUserMsg(m.content);
          else if (m.role === 'assistant') addStaticAssistantMsg(m.content);
        });
      } else {
        chatArea.innerHTML =
          '<div class="welcome" id="welcomeBox">' +
          '<div class="welcome-icon">&#9632;</div>' +
          '<h2>Glacial <strong>Archive</strong></h2>' +
          '<p>基于 DeepSeek 的本地文档智能问答系统。</p>' +
          '</div>';
      }
      chatArea.scrollTop = chatArea.scrollHeight;
      await loadConversations();
    } catch(e) {
      showToast('加载对话失败');
    }
  }

  function addStaticAssistantMsg(text) {
    const div = document.createElement('div');
    div.className = 'msg system';
    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = 'A';
    const body = document.createElement('div');
    body.className = 'msg-body';
    const label = document.createElement('div');
    label.className = 'msg-label';
    label.textContent = 'archive';
    body.appendChild(label);
    const p = document.createElement('p');
    p.textContent = text;
    body.appendChild(p);
    div.appendChild(avatar);
    div.appendChild(body);
    const chatArea = document.getElementById('chatArea');
    chatArea.appendChild(div);
  }

  async function deleteConversation(convId) {
    if (!confirm('确定删除此对话？')) return;
    try {
      await fetch('/api/conversations/' + convId, {method: 'DELETE'});
      if (currentConvId === convId) {
        currentConvId = null;
        document.getElementById('chatArea').innerHTML =
          '<div class="welcome" id="welcomeBox">' +
          '<div class="welcome-icon">&#9632;</div>' +
          '<h2>Glacial <strong>Archive</strong></h2>' +
          '<p>基于 DeepSeek 的本地文档智能问答系统。</p>' +
          '</div>';
      }
      await loadConversations();
    } catch(e) {
      showToast('删除失败');
    }
  }

  async function clearCurrentConversation() {
    if (currentConvId) {
      await deleteConversation(currentConvId);
      await newConversation();
    }
  }

  // 重写 sendQuery，注入 conversation_id
  const origSendQuery = sendQuery;
  sendQuery = async function() {
    const query = input.value.trim();
    if (!query || waiting) return;

    // 如果没有当前对话，自动创建
    if (!currentConvId) {
      try {
        const res = await fetch('/api/conversations', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({title: query.substring(0, 30)})
        });
        const data = await res.json();
        currentConvId = data.conversation.id;
      } catch(e) {}
    }

    waiting = true;
    sendBtn.disabled = false;
    setSendBtnStop();
    addUserMsg(query);
    input.value = '';
    input.style.height = 'auto';

    const msgObj = createStreamingMsg();
    abortController = new AbortController();

    try {
      const res = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: query, conversation_id: currentConvId}),
        signal: abortController.signal
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        showToast(errData.error || '请求失败');
        msgObj.div.remove();
        waiting = false;
        setSendBtnSend();
        sendBtn.disabled = false;
        return;
      }

      const {fullAnswer, snippets} = await readSSEStream(res, msgObj);
      finalizeStreamingMsg(msgObj, fullAnswer, snippets);

      // 刷新侧边栏
      setTimeout(() => loadConversations(), 400);
    } catch(e) {
      if (e.name !== 'AbortError') {
        showToast('请求失败，请检查服务是否正常运行');
        msgObj.div.remove();
      }
    }

    abortController = null;
    waiting = false;
    setSendBtnSend();
    sendBtn.disabled = false;
    input.focus();
  };
  sendBtn.onclick = sendQuery;

  // 页面加载
  loadConversations();
</script>
</div><!-- end .app-shell inner -->
</div><!-- end .app-shell -->
</body>
</html>"""
