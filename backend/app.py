import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ==============================================================================
# CONFIGURAÇÃO DE APIS E BANCO DE DADOS
# ==============================================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

chroma_client = chromadb.PersistentClient(path="./chroma_db_estoque")
collection = chroma_client.get_or_create_collection(name="eletronicos")

# ==============================================================================
# FUNÇÃO PARA CARREGAR DADOS E GERAR EMBEDDINGS
# ==============================================================================
def inicializar_banco_vetorial():
    if collection.count() == 0:
        print("Iniciando leitura do CSV e geração de embeddings...")
        try:
            df = pd.read_csv("inventario_eletronicos.csv")
            
            for index, row in df.iterrows():
                texto_documento = (
                    f"ID: {row['ID']} | Produto: {row['Nome_Produto']} | "
                    f"Categoria: {row['Categoria']} | Especificações: {row['Especificacoes_Tecnicas']} | "
                    f"Quantidade em Estoque: {row['Quantidade_Estoque']} | Nível Crítico: {row['Nivel_Critico']} | "
                    f"Preço: R${row['Preco_Unitario_BRL']} | Localização: {row['Localizacao_Corredor']} | "
                    f"Fornecedor: {row['Fornecedor']}"
                )
                
                embedding_response = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=texto_documento,
                    task_type="retrieval_document"
                )
                vetor = embedding_response['embedding']

                collection.add(
                    documents=[texto_documento],
                    embeddings=[vetor],
                    metadatas=[{"id_produto": str(row['ID']), "categoria": row['Categoria']}],
                    ids=[str(row['ID'])]
                )
            print(f"Sucesso! {collection.count()} produtos foram vetorizados no ChromaDB.")
        except Exception as e:
            print(f"Erro ao carregar o CSV: {e}")
    else:
        print(f"ChromaDB já está carregado com {collection.count()} registros de produtos.")

with app.app_context():
    inicializar_banco_vetorial()

# ==============================================================================
# ROTA PRINCIPAL DO CHATBOT (RAG)
# ==============================================================================
@app.route('/api/chat', methods=['POST'])
def chat():
    dados = request.json
    pergunta_usuario = dados.get('mensagem')

    if not pergunta_usuario:
        return jsonify({"erro": "Nenhuma mensagem fornecida"}), 400

    try:
        # 1. RETRIEVE
        query_embedding_response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=pergunta_usuario,
            task_type="retrieval_query"
        )
        query_embedding = query_embedding_response['embedding']

        resultados_busca = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        contexto_recuperado = "\n".join(resultados_busca['documents'][0])

        # 2. AUGMENT (Com regras estritas de formatação visual)
        prompt = f"""Você é o assistente virtual do sistema de gestão de estoque de eletrônicos.
        Seja prestativo, profissional e conciso. Responda à pergunta do usuário baseando-se EXCLUSIVAMENTE nas informações de contexto fornecidas abaixo.
        Se a informação não estiver no contexto, diga gentilmente que você não possui essa informação no momento.
        
        REGRA DE FORMATAÇÃO: Sempre que for listar produtos ou opções, utilize tópicos (bullet points). Coloque o nome do produto em **negrito** e resuma as informações de forma limpa e direta.
        
        [CONTEXTO DO ESTOQUE]:
        {contexto_recuperado}
        
        [PERGUNTA DO USUÁRIO]: 
        {pergunta_usuario}
        
        Resposta:"""

        # 3. GENERATE 
        model = genai.GenerativeModel('gemini-3.0-flash-preview')
        resposta_llm = model.generate_content(prompt)

        return jsonify({"resposta": resposta_llm.text})

    except Exception as e:
        print(f"Erro durante o processamento do chat: {e}")
        return jsonify({"erro": "Erro interno no servidor"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)