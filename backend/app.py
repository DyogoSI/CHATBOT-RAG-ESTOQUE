import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

# ==============================================================================
# CONFIGURAÇÕES INICIAIS
# ==============================================================================

load_dotenv()

app = Flask(__name__)

# CORS
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)

# ==============================================================================
# CONFIGURAÇÃO DE APIS E BANCO DE DADOS
# ==============================================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY não encontrada nas variáveis de ambiente.")

genai.configure(api_key=GOOGLE_API_KEY)

chroma_client = chromadb.PersistentClient(path="./chroma_db_estoque")
collection = chroma_client.get_or_create_collection(name="eletronicos")

# ==============================================================================
# ROTA DE TESTE
# ==============================================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "mensagem": "Backend Estoque IA funcionando!"
    }), 200

# ==============================================================================
# FUNÇÃO PARA CARREGAR DADOS E GERAR EMBEDDINGS
# ==============================================================================

def inicializar_banco_vetorial():
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

                # FIX: modelo de embedding atualizado
                embedding_response = genai.embed_content(
                    model="models/text-embedding-004",
                    content=texto_documento,
                    task_type="retrieval_document"
                )

                vetor = embedding_response["embedding"]

                collection.add(
                    documents=[texto_documento],
                    embeddings=[vetor],
                    metadatas=[{
                        "id_produto": str(row["ID"]),
                        "categoria": row["Categoria"]
                    }],
                    ids=[str(row["ID"])]
                )

            print(
                f"Sucesso! {collection.count()} produtos foram vetorizados."
            )

        else:
            print(
                f"ChromaDB já possui {collection.count()} registros."
            )

    except Exception as e:
        print(f"Erro ao inicializar banco vetorial: {str(e)}")

# ==============================================================================
# INICIALIZAÇÃO
# ==============================================================================

with app.app_context():
    inicializar_banco_vetorial()

# ==============================================================================
# ROTA PRINCIPAL DO CHATBOT (RAG)
# ==============================================================================

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():

    # Responde ao preflight do navegador
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:

        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Nenhum JSON enviado"
            }), 400

        pergunta_usuario = dados.get("mensagem")

        if not pergunta_usuario:
            return jsonify({
                "erro": "Nenhuma mensagem fornecida"
            }), 400

        # ==========================================================
        # RETRIEVE
        # ==========================================================

        # FIX: mesmo modelo de embedding usado no indexing
        query_embedding_response = genai.embed_content(
            model="models/text-embedding-004",
            content=pergunta_usuario,
            task_type="retrieval_query"
        )

        query_embedding = query_embedding_response["embedding"]

        resultados_busca = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        contexto_recuperado = "\n".join(
            resultados_busca["documents"][0]
        )

        # ==========================================================
        # AUGMENT
        # ==========================================================

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

        # ==========================================================
        # GENERATE
        # FIX: modelo atualizado de gemini-2.5-flash para gemini-2.0-flash
        # ==========================================================

        model = genai.GenerativeModel(
            "gemini-2.0-flash"
        )

        resposta_llm = model.generate_content(prompt)

        return jsonify({
            "resposta": resposta_llm.text
        })

    except Exception as e:

        import traceback
        print(f"Erro durante o processamento: {str(e)}")
        print(traceback.format_exc())

        return jsonify({
            "erro": str(e)
        }), 500

# ==============================================================================
# EXECUÇÃO
# ==============================================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )