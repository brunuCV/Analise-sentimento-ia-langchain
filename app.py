import streamlit as st
import os
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# --- 1. CONFIGURAÇÕES INICIAIS ---
load_dotenv()
st.set_page_config(page_title="IA Analisadora de Feedback", layout="wide")

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

# --- 3. GERENCIAMENTO DE API KEY (Lógica Robusta) ---
api_key = None
try:
    # Tenta pegar dos Secrets do Streamlit ou do arquivo .env
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
except:
    api_key = os.getenv("GROQ_API_KEY")

# Se não achou em nenhum lugar, pede no Sidebar
if not api_key:
    st.sidebar.title("Configurações")
    api_key = st.sidebar.text_input("Insira sua Groq API Key manualmente:", type="password")
    if not api_key:
        st.info("👋 Bem-vindo! Por favor, insira sua API Key na barra lateral para começar.")
        st.stop()

# Inicializa os componentes da IA uma única vez
try:
    llm = ChatGroq(model="llama3-8b-8192", groq_api_key=api_key)
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