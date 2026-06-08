import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const API_URL = "https://backend-estoque-ia.onrender.com/api/chat";

const sugestoes = [
  { icon: "📦", texto: "Quais produtos estão abaixo do nível crítico?" },
  { icon: "🔍", texto: "Mostre todos os produtos da categoria Smartphones" },
  { icon: "💰", texto: "Qual produto tem o maior preço unitário?" },
  { icon: "📍", texto: "Quais produtos ficam no corredor A?" },
];

function GeminiIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 2C14 8.627 8.627 14 2 14C8.627 14 14 19.373 14 26C14 19.373 19.373 14 26 14C19.373 14 14 8.627 14 2Z"
        fill="url(#gemini_grad)"/>
      <defs>
        <linearGradient id="gemini_grad" x1="2" y1="2" x2="26" y2="26" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4285F4"/>
          <stop offset="0.5" stopColor="#9B72CB"/>
          <stop offset="1" stopColor="#D96570"/>
        </linearGradient>
      </defs>
    </svg>
  );
}

function UserIcon() {
  return (
    <div style={{
      width: 32, height: 32, borderRadius: '50%',
      background: 'linear-gradient(135deg, #4285F4, #9B72CB)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: 14, color: 'white', fontWeight: 600, flexShrink: 0
    }}>U</div>
  );
}

function SendIcon({ disabled }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
      <path d="M12 20V4M12 4L6 10M12 4L18 10"
        stroke={disabled ? "#5f6368" : "#e8eaed"}
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function TypingDots() {
  return (
    <div className="typing-dots">
      <span /><span /><span />
    </div>
  );
}

export default function App() {
  const [input, setInput] = useState('');
  const [mensagens, setMensagens] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [iniciado, setIniciado] = useState(false);
  const fimRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens, carregando]);

  const enviar = async (texto) => {
    const msg = texto || input;
    if (!msg.trim() || carregando) return;

    setIniciado(true);
    setMensagens(prev => [...prev, { remetente: 'usuario', texto: msg }]);
    setInput('');
    setCarregando(true);

    try {
      const response = await axios.post(API_URL, { mensagem: msg });
      setMensagens(prev => [...prev, { remetente: 'bot', texto: response.data.resposta }]);
    } catch {
      setMensagens(prev => [...prev, {
        remetente: 'bot',
        texto: 'Ocorreu um erro ao conectar com o servidor. Tente novamente.'
      }]);
    } finally {
      setCarregando(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  };

  return (
    <>
      <style>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          background: #131314;
          color: #e8eaed;
          font-family: "Google Sans", "Roboto", sans-serif;
          height: 100vh;
          overflow: hidden;
        }

        .layout {
          display: flex;
          height: 100vh;
        }

        /* ── SIDEBAR ── */
        .sidebar {
          width: 256px;
          background: #1e1f20;
          display: flex;
          flex-direction: column;
          padding: 16px 12px;
          gap: 8px;
          flex-shrink: 0;
        }

        .sidebar-logo {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 8px 12px;
          margin-bottom: 8px;
        }

        .sidebar-logo span {
          font-size: 1.25rem;
          font-weight: 500;
          background: linear-gradient(90deg, #4285F4, #9B72CB, #D96570);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .btn-novo-chat {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 16px;
          border-radius: 24px;
          border: none;
          background: transparent;
          color: #e8eaed;
          cursor: pointer;
          font-size: 0.9rem;
          font-family: inherit;
          transition: background 0.15s;
          text-align: left;
          width: 100%;
        }

        .btn-novo-chat:hover {
          background: rgba(255,255,255,0.08);
        }

        .btn-novo-chat svg {
          flex-shrink: 0;
        }

        .sidebar-section-label {
          font-size: 0.75rem;
          color: #9aa0a6;
          padding: 16px 16px 8px;
          letter-spacing: 0.02em;
        }

        .sidebar-item {
          padding: 10px 16px;
          border-radius: 8px;
          font-size: 0.875rem;
          color: #c4c7c5;
          cursor: pointer;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          transition: background 0.15s;
        }

        .sidebar-item:hover {
          background: rgba(255,255,255,0.08);
        }

        /* ── MAIN ── */
        .main {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          position: relative;
        }

        /* ── TELA INICIAL ── */
        .welcome-screen {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px 24px;
          gap: 32px;
        }

        .welcome-title {
          font-size: 2.5rem;
          font-weight: 400;
          text-align: center;
          background: linear-gradient(90deg, #4285F4 0%, #9B72CB 40%, #D96570 70%, #F29900 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .sugestoes-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          max-width: 640px;
          width: 100%;
        }

        .sugestao-card {
          background: #1e1f20;
          border: 1px solid #3c4043;
          border-radius: 16px;
          padding: 16px;
          cursor: pointer;
          transition: background 0.15s, border-color 0.15s;
          text-align: left;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .sugestao-card:hover {
          background: #2d2e30;
          border-color: #5f6368;
        }

        .sugestao-icon { font-size: 1.25rem; }

        .sugestao-texto {
          font-size: 0.875rem;
          color: #c4c7c5;
          line-height: 1.4;
        }

        /* ── MENSAGENS ── */
        .chat-scroll {
          flex: 1;
          overflow-y: auto;
          padding: 24px 0 120px;
          scroll-behavior: smooth;
        }

        .chat-scroll::-webkit-scrollbar { width: 6px; }
        .chat-scroll::-webkit-scrollbar-thumb {
          background: rgba(255,255,255,0.1);
          border-radius: 3px;
        }

        .mensagem-wrapper {
          max-width: 720px;
          margin: 0 auto;
          padding: 0 24px;
        }

        .mensagem-row {
          display: flex;
          gap: 16px;
          padding: 16px 0;
          align-items: flex-start;
        }

        .mensagem-row.usuario {
          flex-direction: row-reverse;
        }

        .avatar {
          flex-shrink: 0;
          margin-top: 2px;
        }

        .bubble {
          flex: 1;
          min-width: 0;
        }

        .bubble-usuario {
          background: #2d2e30;
          border-radius: 20px 20px 4px 20px;
          padding: 12px 18px;
          font-size: 0.95rem;
          line-height: 1.6;
          max-width: fit-content;
          margin-left: auto;
        }

        .bubble-bot {
          font-size: 0.95rem;
          line-height: 1.7;
          color: #e8eaed;
          padding-top: 4px;
        }

        .bubble-bot p { margin-bottom: 12px; }
        .bubble-bot p:last-child { margin-bottom: 0; }
        .bubble-bot ul { padding-left: 20px; margin: 8px 0; }
        .bubble-bot li { margin-bottom: 6px; }
        .bubble-bot strong { color: #fff; font-weight: 600; }
        .bubble-bot code {
          background: #2d2e30;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 0.875em;
        }

        /* ── TYPING ── */
        .typing-dots {
          display: flex;
          gap: 4px;
          align-items: center;
          padding: 8px 0;
        }

        .typing-dots span {
          width: 8px; height: 8px;
          border-radius: 50%;
          background: #9aa0a6;
          animation: bounce 1.4s infinite ease-in-out;
        }
        .typing-dots span:nth-child(1) { animation-delay: 0s; }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-6px); opacity: 1; }
        }

        /* ── INPUT ── */
        .input-wrapper {
          position: absolute;
          bottom: 0; left: 0; right: 0;
          padding: 16px 24px 24px;
          background: linear-gradient(to top, #131314 70%, transparent);
        }

        .input-box {
          max-width: 720px;
          margin: 0 auto;
          background: #1e1f20;
          border: 1px solid #3c4043;
          border-radius: 24px;
          display: flex;
          align-items: flex-end;
          gap: 8px;
          padding: 12px 12px 12px 20px;
          transition: border-color 0.2s;
        }

        .input-box:focus-within {
          border-color: #8ab4f8;
        }

        .input-box textarea {
          flex: 1;
          background: transparent;
          border: none;
          outline: none;
          color: #e8eaed;
          font-size: 0.975rem;
          font-family: inherit;
          line-height: 1.5;
          resize: none;
          max-height: 200px;
          overflow-y: auto;
        }

        .input-box textarea::placeholder { color: #5f6368; }

        .send-btn {
          width: 40px; height: 40px;
          border-radius: 50%;
          border: none;
          background: transparent;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.15s;
          flex-shrink: 0;
        }

        .send-btn:hover:not(:disabled) {
          background: rgba(255,255,255,0.1);
        }

        .send-btn:disabled { cursor: default; }

        .send-btn.active {
          background: #4285F4;
        }

        .send-btn.active:hover {
          background: #5a95f5;
        }

        .input-disclaimer {
          text-align: center;
          font-size: 0.75rem;
          color: #5f6368;
          margin-top: 10px;
        }

        /* ── RESPONSIVO ── */
        @media (max-width: 768px) {
          .sidebar { display: none; }
          .sugestoes-grid { grid-template-columns: 1fr; }
          .welcome-title { font-size: 1.8rem; }
        }
      `}</style>

      <div className="layout">
        {/* SIDEBAR */}
        <aside className="sidebar">
          <div className="sidebar-logo">
            <GeminiIcon />
            <span>Estoque.AI</span>
          </div>

          <button className="btn-novo-chat" onClick={() => { setMensagens([]); setIniciado(false); }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 5v14M5 12h14" stroke="#e8eaed" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Novo chat
          </button>

          {mensagens.length > 0 && (
            <>
              <div className="sidebar-section-label">Hoje</div>
              <div className="sidebar-item">
                {mensagens.find(m => m.remetente === 'usuario')?.texto?.slice(0, 40) || 'Chat'}...
              </div>
            </>
          )}
        </aside>

        {/* MAIN */}
        <main className="main">
          {!iniciado ? (
            /* TELA DE BOAS-VINDAS */
            <div className="welcome-screen">
              <h1 className="welcome-title">Como posso ajudar?</h1>

              <div className="sugestoes-grid">
                {sugestoes.map((s, i) => (
                  <button key={i} className="sugestao-card" onClick={() => enviar(s.texto)}>
                    <span className="sugestao-icon">{s.icon}</span>
                    <span className="sugestao-texto">{s.texto}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* CHAT */
            <div className="chat-scroll">
              <div className="mensagem-wrapper">
                {mensagens.map((msg, i) => (
                  <div key={i} className={`mensagem-row ${msg.remetente}`}>
                    <div className="avatar">
                      {msg.remetente === 'bot' ? <GeminiIcon /> : <UserIcon />}
                    </div>
                    <div className="bubble">
                      {msg.remetente === 'bot' ? (
                        <div className="bubble-bot">
                          <ReactMarkdown>{msg.texto}</ReactMarkdown>
                        </div>
                      ) : (
                        <div className="bubble-usuario">{msg.texto}</div>
                      )}
                    </div>
                  </div>
                ))}

                {carregando && (
                  <div className="mensagem-row bot">
                    <div className="avatar"><GeminiIcon /></div>
                    <div className="bubble">
                      <TypingDots />
                    </div>
                  </div>
                )}
                <div ref={fimRef} />
              </div>
            </div>
          )}

          {/* INPUT FLUTUANTE */}
          <div className="input-wrapper">
            <div className="input-box">
              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                onChange={e => {
                  setInput(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
                onKeyDown={handleKey}
                placeholder="Pergunte sobre o estoque..."
                disabled={carregando}
              />
              <button
                className={`send-btn ${input.trim() && !carregando ? 'active' : ''}`}
                onClick={() => enviar()}
                disabled={!input.trim() || carregando}
              >
                <SendIcon disabled={!input.trim() || carregando} />
              </button>
            </div>
            <p className="input-disclaimer">
              Estoque.AI pode cometer erros. Verifique as informações importantes.
            </p>
          </div>
        </main>
      </div>
    </>
  );
}