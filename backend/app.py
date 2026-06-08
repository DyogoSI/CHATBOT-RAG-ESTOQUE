import os
import traceback
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ==============================================================================
# CONFIGURAÇÕES INICIAIS
# ==============================================================================

load_dotenv()

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)

# ==============================================================================
# CONFIGURAÇÃO DE APIs E BANCO DE DADOS
# ==============================================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY não encontrada nas variáveis de ambiente.")

client = genai.Client(api_key=GOOGLE_API_KEY)

chroma_client = chromadb.PersistentClient(path="./chroma_db_estoque")
collection = chroma_client.get_or_create_collection(name="eletronicos")

# Flag para indicar se o banco já está pronto
banco_pronto = False

# ==============================================================================
# MODELOS
# ==============================================================================

MODELO_EMBEDDING = "text-embedding-004"
MODELO_GERACAO   = "gemini-2.0-flash"

# ==============================================================================
# FUNÇÕES DE EMBEDDING E GERAÇÃO
# ==============================================================================

def get_embedding(texto, task_type="retrieval_document"):
    response = client.models.embed_content(
        model=MODELO_EMBEDDING,
        contents=texto,
        config=types.EmbedContentConfig(task_type=task_type)
    )
    return response.embeddings[0].values

def get_resposta_llm(prompt):
    response = client.models.generate_content(
        model=MODELO_GERACAO,
        contents=prompt
    )
    return response.text

# ==============================================================================
# ROTAS
# ==============================================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "mensagem": "Backend Estoque IA funcionando!",
        "banco_pronto": banco_pronto,
        "registros_chroma": collection.count()
    }), 200

@app.route("/api/debug", methods=["GET"])
def debug():
    chave_preview = (
        f"{GOOGLE_API_KEY[:6]}...{GOOGLE_API_KEY[-4:]}"
        if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10
        else "NÃO CONFIGURADA"
    )
    try:
        modelos = [m.name for m in client.models.list()]
        return jsonify({
            "status": "ok",
            "chave_preview": chave_preview,
            "banco_pronto": banco_pronto,
            "modelos_disponiveis": modelos,
            "registros_chroma": collection.count()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "erro",
            "chave_preview": chave_preview,
            "detalhe": str(e)
        }), 500

# ==============================================================================
# INICIALIZAÇÃO DO BANCO — roda em background para não bloquear o Gunicorn
# ==============================================================================

def inicializar_banco_vetorial():
    global banco_pronto
    try:
        if collection.count() == 0:
            print("Iniciando leitura do CSV e geração de embeddings...")

            df = pd.read_csv("inventario_eletronicos.csv")

            for _, row in df.iterrows():
                texto_documento = (
                    f"ID: {row['ID']} | "
                    f"Produto: {row['Nome_Produto']} | "
                    f"Categoria: {row['Categoria']} | "
                    f"Especificações: {row['Especificacoes_Tecnicas']} | "
                    f"Quantidade em Estoque: {row['Quantidade_Estoque']} | "
                    f"Nível Crítico: {row['Nivel_Critico']} | "
                    f"Preço: R${row['Preco_Unitario_BRL']} | "
                    f"Localização: {row['Localizacao_Corredor']} | "
                    f"Fornecedor: {row['Fornecedor']}"
                )

                vetor = get_embedding(texto_documento, "retrieval_document")

                collection.add(
                    documents=[texto_documento],
                    embeddings=[vetor],
                    metadatas=[{
                        "id_produto": str(row["ID"]),
                        "categoria": row["Categoria"]
                    }],
                    ids=[str(row["ID"])]
                )

            print(f"Sucesso! {collection.count()} produtos vetorizados.")
        else:
            print(f"ChromaDB já possui {collection.count()} registros. Pulando indexação.")

        banco_pronto = True
        print("Banco vetorial pronto.")

    except Exception as e:
        print(f"Erro ao inicializar banco vetorial: {str(e)}")
        print(traceback.format_exc())

# Inicia a indexação em thread separada — o Flask sobe imediatamente
thread_init = threading.Thread(target=inicializar_banco_vetorial, daemon=True)
thread_init.start()

# ==============================================================================
# ROTA PRINCIPAL DO CHATBOT (RAG)
# ==============================================================================

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    # Aguarda o banco estar pronto antes de responder
    if not banco_pronto:
        return jsonify({
            "erro": "O sistema ainda está inicializando. Aguarde alguns instantes e tente novamente."
        }), 503

    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Nenhum JSON enviado"}), 400

        pergunta_usuario = dados.get("mensagem")

        if not pergunta_usuario:
            return jsonify({"erro": "Nenhuma mensagem fornecida"}), 400

        # ----------------------------------------------------------
        # RETRIEVE
        # ----------------------------------------------------------

        query_embedding = get_embedding(pergunta_usuario, "retrieval_query")

        resultados_busca = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        contexto_recuperado = "\n".join(resultados_busca["documents"][0])

        # ----------------------------------------------------------
        # AUGMENT
        # ----------------------------------------------------------

        prompt = f"""
Você é o assistente virtual do sistema de gestão de estoque de eletrônicos.

Seja prestativo, profissional e objetivo.

Responda EXCLUSIVAMENTE com base nas informações do contexto.

Caso a informação não esteja disponível, informe que não possui essa informação no momento.

REGRA DE FORMATAÇÃO:
- Sempre utilize bullet points quando listar produtos.
- Coloque o nome do produto em negrito.
- Seja direto e organizado.

[CONTEXTO]
{contexto_recuperado}

[PERGUNTA]
{pergunta_usuario}

[RESPOSTA]
"""

        # ----------------------------------------------------------
        # GENERATE
        # ----------------------------------------------------------

        texto_resposta = get_resposta_llm(prompt)

        return jsonify({"resposta": texto_resposta})

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"erro": str(e)}), 500

# ==============================================================================
# EXECUÇÃO
# ==============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)