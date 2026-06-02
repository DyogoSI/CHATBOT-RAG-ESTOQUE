import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [mensagens, setMensagens] = useState([
    { remetente: 'bot', texto: 'Olá! Sou o assistente de estoque. Como posso ajudar você hoje?' }
  ]);
  const [carregando, setCarregando] = useState(false);
  const fimDasMensagensRef = useRef(null);

  // Faz o scroll automático para a última mensagem
  useEffect(() => {
    fimDasMensagensRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens]);

  const enviarMensagem = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const textoUsuario = input;
    setMensagens((prev) => [...prev, { remetente: 'usuario', texto: textoUsuario }]);
    setInput('');
    setCarregando(true);

    try {
      const response = await axios.post("http://localhost:5000/api/chat", {
        mensagem: textoUsuario
      });

      setMensagens((prev) => [...prev, { remetente: 'bot', texto: response.data.resposta }]);
    } catch (error) {
      console.error(error);
      setMensagens((prev) => [...prev, { remetente: 'bot', texto: 'Desculpe, ocorreu um erro ao conectar com o servidor.' }]);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="app-container">
      {/* Navbar Superior */}
      <nav className="navbar">
        <div className="logo-container">
          {/* Você pode trocar o emoji pela sua logo em imagem se preferir */}
          <span className="logo-icon">📦</span>
          <h1 className="logo-texto">Estoque.AI</h1>
        </div>
      </nav>

      {/* Container Principal do Chat */}
      <main className="chat-container">
        <div className="mensagens-area">
          {mensagens.map((msg, index) => (
            <div key={index} className={`linha-mensagem ${msg.remetente}`}>
              <div className={`balao-mensagem ${msg.remetente}`}>
                {msg.remetente === 'bot' ? (
                  <ReactMarkdown>{msg.texto}</ReactMarkdown>
                ) : (
                  msg.texto
                )}
              </div>
            </div>
          ))}
          {carregando && (
            <div className="linha-mensagem bot">
              <div className="balao-mensagem bot digitando">
                <span className="ponto">.</span><span className="ponto">.</span><span className="ponto">.</span>
              </div>
            </div>
          )}
          <div ref={fimDasMensagensRef} />
        </div>

        {/* Área de Input */}
        <form className="input-area" onSubmit={enviarMensagem}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Pergunte sobre os produtos..."
            disabled={carregando}
          />
          <button type="submit" disabled={carregando || !input.trim()}>
            Enviar
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;