import streamlit as st
import pandas as pd
import plotly.express as px
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IA Analisadora de Feedback", layout="wide")

# --- BARRA LATERAL (CONFIGURAÇÃO DA API) ---
st.sidebar.title("Configurações")
api_key = st.sidebar.text_input("Insira sua Groq API Key", type="password")

# Inicializa o modelo
llm = ChatGroq(model="llama3-8b-8192", groq_api_key=api_key)

# --- PROMPT E PARSER ---
# Definimos que queremos a resposta estritamente em JSON para facilitar a análise
instrucoes = """
Você é um analista de dados especialista em CX (Customer Experience).
Analise o seguinte feedback de cliente e retorne APENAS um JSON com os campos:
- sentimento: (Positivo, Negativo ou Neutro)
- topico: (ex: Preço, Atendimento, Qualidade, Entrega)
- resumo: (Um resumo de 1 frase)
- sugestao: (Uma sugestão de resposta para o cliente)

Feedback: {feedback}
"""

prompt = ChatPromptTemplate.from_template(instrucoes)
chain = prompt | llm | JsonOutputParser()

# --- INTERFACE PRINCIPAL ---
st.title("📊 IA Analisadora de Feedbacks")
st.markdown("Transforme comentários brutos em insights estratégicos com IA Generativa.")

text_input = st.text_area("Cole aqui os feedbacks (um por linha):", height=150)

if st.button("Analisar Feedbacks"):
    feedbacks = [f.strip() for f in text_input.split('\n') if f.strip()]
    
    if not feedbacks:
        st.warning("Adicione pelo menos um feedback.")
    else:
        resultados = []
        
        with st.spinner('A IA está lendo os feedbacks...'):
            for f in feedbacks:
                try:
                    res = chain.invoke({"feedback": f})
                    res['texto_original'] = f
                    resultados.append(res)
                except Exception as e:
                    st.error(f"Erro ao processar um feedback: {e}")

        # Transforma em DataFrame
        df = pd.DataFrame(resultados)

        # --- EXIBIÇÃO DOS RESULTADOS ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Distribuição de Sentimento")
            fig = px.pie(df, names='sentimento', color='sentimento',
                         color_discrete_map={'Positivo':'green', 'Negativo':'red', 'Neutro':'gray'})
            st.plotly_chart(fig)

        with col2:
            st.subheader("Tópicos mais citados")
            fig_bar = px.bar(df['topico'].value_counts())
            st.plotly_chart(fig_bar)

        st.subheader("Análise Detalhada")
        st.table(df[['texto_original', 'sentimento', 'topico', 'sugestao']])

        # Botão para baixar resultados
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar Relatório Completo (CSV)", csv, "analise_ia.csv", "text/csv")