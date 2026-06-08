import os
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================

load_dotenv()

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)

# ==============================================================================
# GOOGLE GEMINI
# ==============================================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise Exception("GOOGLE_API_KEY não encontrada.")

genai.configure(api_key=GOOGLE_API_KEY)

# ==============================================================================
# CHROMADB
# ==============================================================================

try:
    chroma_client = chromadb.PersistentClient(
        path="./chroma_db_estoque"
    )

    collection = chroma_client.get_or_create_collection(
        name="eletronicos"
    )

except Exception as e:
    print(f"Erro ao iniciar ChromaDB: {e}")
    raise

# ==============================================================================
# HOME
# ==============================================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "mensagem": "Backend Estoque IA funcionando"
    })

# ==============================================================================
# STATUS
# ==============================================================================

@app.route("/api/status", methods=["GET"])
def status():

    try:

        return jsonify({
            "status": "ok",
            "produtos": collection.count()
        })

    except Exception as e:

        return jsonify({
            "status": "erro",
            "mensagem": str(e)
        }), 500

# ==============================================================================
# CARREGAR DADOS
# ==============================================================================

def inicializar_banco_vetorial():

    try:

        total = collection.count()

        if total > 0:
            print(f"Banco já carregado ({total} registros).")
            return

        print("Iniciando vetorização...")

        if not os.path.exists("inventario_eletronicos.csv"):
            print("Arquivo inventario_eletronicos.csv não encontrado.")
            return

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

            embedding = genai.embed_content(
                model="models/gemini-embedding-001",
                content=texto_documento,
                task_type="retrieval_document"
            )

            collection.add(
                documents=[texto_documento],
                embeddings=[embedding["embedding"]],
                metadatas=[{
                    "id_produto": str(row["ID"])
                }],
                ids=[str(row["ID"])]
            )

        print(
            f"Vetorização concluída. Total: {collection.count()} produtos."
        )

    except Exception:
        traceback.print_exc()

# ==============================================================================
# INICIALIZAÇÃO
# ==============================================================================

with app.app_context():
    inicializar_banco_vetorial()

# ==============================================================================
# CHAT
# ==============================================================================

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:

        dados = request.get_json(silent=True)

        if not dados:
            return jsonify({
                "erro": "JSON inválido"
            }), 400

        pergunta_usuario = dados.get("mensagem")

        if not pergunta_usuario:
            return jsonify({
                "erro": "Mensagem não enviada"
            }), 400

        # ==========================================================
        # EMBEDDING DA PERGUNTA
        # ==========================================================

        query_embedding = genai.embed_content(
            model="models/gemini-embedding-001",
            content=pergunta_usuario,
            task_type="retrieval_query"
        )

        # ==========================================================
        # CONSULTA CHROMADB
        # ==========================================================

        resultados = collection.query(
            query_embeddings=[
                query_embedding["embedding"]
            ],
            n_results=3
        )

        documentos = resultados.get("documents", [])

        if not documentos or not documentos[0]:

            return jsonify({
                "resposta": "Nenhum produto relacionado foi encontrado."
            })

        contexto = "\n".join(documentos[0])

        # ==========================================================
        # PROMPT
        # ==========================================================

        prompt = f"""
Você é um assistente virtual especializado em estoque de eletrônicos.

Responda apenas usando as informações presentes no contexto.

Caso não encontre a informação, diga que ela não está disponível.

CONTEXTO:
{contexto}

PERGUNTA:
{pergunta_usuario}
"""

        # ==========================================================
        # GEMINI
        # ==========================================================

        model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )

        resposta = model.generate_content(prompt)

        texto = getattr(
            resposta,
            "text",
            "Não foi possível gerar resposta."
        )

        return jsonify({
            "resposta": texto
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "erro": str(e)
        }), 500

# ==============================================================================
# EXECUÇÃO
# ==============================================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )