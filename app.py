import streamlit as st
import os
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# 1. CONFIGURAÇÃO INICIAL (DEVE SER A PRIMEIRA DE UI)
st.set_page_config(page_title="IA Analisadora de Feedback", layout="wide")
load_dotenv()

# 2. FUNÇÃO DE BUSCA DA CHAVE
def buscar_chave():
    key = None
    # 1. Tenta Secrets do Streamlit
    if "GROQ_API_KEY" in st.secrets:
        key = st.secrets["GROQ_API_KEY"]
    # 2. Tenta .env
    if not key:
        key = os.getenv("GROQ_API_KEY")
    
    # Remove espaços em branco, quebras de linha ou aspas extras
    if key:
        return key.strip().replace('"', '').replace("'", "")
    return None

api_key = buscar_chave()

# --- DEBUG NA BARRA LATERAL (APENAS PARA VOCÊ VERIFICAR) ---
if api_key:
    # Mostra apenas os 4 primeiros e 4 últimos caracteres para segurança
    st.sidebar.success(f"Chave detectada: {api_key[:4]}...{api_key[-4:]}")
else:
    st.sidebar.error("Nenhuma chave detectada automaticamente.")
    api_key = st.sidebar.text_input("Insira sua Groq API Key:", type="password")
    if api_key:
        api_key = api_key.strip() # Limpa a chave digitada manualmente também
    else:
        st.stop()

# --- 2. TEMPLATE DE IA ---
instrucoes = """
Você é um analista de dados especialista em CX (Customer Experience).
Analise o seguinte feedback de cliente e retorne APENAS um JSON com os campos:
- sentimento: (Positivo, Negativo ou Neutro)
- topico: (ex: Preço, Atendimento, Qualidade, Entrega)
- resumo: (Um resumo de 1 frase)
- sugestao: (Uma sugestão de resposta para o cliente)

Feedback: {feedback}
"""

# --- 3. GERENCIAMENTO DE API KEY (VERSÃO DEFINITIVA) ---
load_dotenv()

# Função para buscar a chave sem criar conflito de interface
def get_api_key():
    # 1. Tenta buscar nos Secrets do Streamlit (Nuvem)
    try:
        if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
            return st.secrets["GROQ_API_KEY"]
    except:
        pass
    
    # 2. Tenta buscar no .env ou Variáveis de Ambiente (Local)
    env_key = os.getenv("GROQ_API_KEY")
    if env_key:
        return env_key
    
    # 3. Se não achou em nada, aí sim pede no Sidebar
    st.sidebar.title("🔑 Configuração")
    user_key = st.sidebar.text_input("Groq API Key não detectada. Insira manualmente:", type="password")
    if user_key:
        return user_key
    
    return None

api_key = get_api_key()

if not api_key:
    st.info("👋 Bem-vindo! Por favor, configure sua API Key da Groq para começar.")
    st.markdown("""
    **Como configurar:**
    1. Crie um arquivo `.env` localmente com `GROQ_API_KEY=sua_chave`.
    2. Ou insira a chave na barra lateral esquerda.
    """)
    st.stop()

# Inicializa os componentes da IA
try:
    llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=api_key)
    prompt = ChatPromptTemplate.from_template(instrucoes)
    chain = prompt | llm | JsonOutputParser()
except Exception as e:
    st.error(f"Erro ao conectar com a IA: {e}")
    st.stop()

# --- 4. INTERFACE PRINCIPAL ---
st.title("📊 IA Analisadora de Feedbacks")
st.markdown("Transforme comentários brutos em insights estratégicos com IA Generativa.")

text_input = st.text_area("Cole aqui os feedbacks (um por linha):", 
                         placeholder="Exemplo: O produto chegou rápido mas a caixa estava amassada.",
                         height=150)

if st.button("Analisar Feedbacks"):
    feedbacks = [f.strip() for f in text_input.split('\n') if f.strip()]
    
    if not feedbacks:
        st.warning("Adicione pelo menos um feedback.")
    else:
        resultados = []
        
        with st.spinner('A IA está analisando os dados...'):
            for f in feedbacks:
                try:
                    res = chain.invoke({"feedback": f})
                    res['texto_original'] = f
                    resultados.append(res)
                except Exception as e:
                    st.error(f"Erro ao processar um dos comentários: {e}")

        if resultados:
            df = pd.DataFrame(resultados)

            # --- EXIBIÇÃO DOS RESULTADOS ---
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Distribuição de Sentimento")
                fig = px.pie(df, names='sentimento', color='sentimento',
                             color_discrete_map={'Positivo':'green', 'Negativo':'red', 'Neutro':'gray'})
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Tópicos mais citados")
                # Garante que a contagem seja visualmente limpa
                topicos_count = df['topico'].value_counts().reset_index()
                fig_bar = px.bar(topicos_count, x='topico', y='count', labels={'count': 'Quantidade', 'topico': 'Assunto'})
                st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("Análise Detalhada")
            st.table(df[['texto_original', 'sentimento', 'topico', 'sugestao']])

            # Botão para baixar resultados
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Relatório Completo (CSV)", csv, "analise_feedback_ia.csv", "text/csv")