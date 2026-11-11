import streamlit as st
import pandas as pd
import plotly.express as px
from pypdf import PdfReader
from openai import AzureOpenAI

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Gestão e Atendimento - Tech Store",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do estado de sessão
if "chat_iniciado" not in st.session_state:
    st.session_state.chat_iniciado = False
if "messages" not in st.session_state:
    # Mensagem de boas-vindas típica de e-commerce
    st.session_state.messages = [{"role": "assistant", "content": "Olá! 👋 Sou o assistente virtual da loja. Como posso te ajudar hoje? Você pode me perguntar sobre peças, solicitar um orçamento de conserto ou ver o status do seu pedido."}]
if "conteudo_base" not in st.session_state:
    st.session_state.conteudo_base = ""

def extrair_texto_arquivo(uploaded_file) -> str:
    nome = uploaded_file.name.lower()
    try:
        if nome.endswith(".txt"):
            return uploaded_file.read().decode("utf-8", errors="ignore")
        elif nome.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            return df.to_string(index=False)
        elif nome.endswith(".pdf"):
            leitor = PdfReader(uploaded_file)
            texto = ""
            for pagina in leitor.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
            return texto
    except Exception as e:
        st.sidebar.error(f"Erro ao processar o arquivo: {e}")
        return ""
    return ""

# ==========================================
# BARRA LATERAL: Configurações da IA
# ==========================================
with st.sidebar:
    st.title("⚙️ Painel de Controle IA")
    
    with st.expander("🔑 Credenciais Azure OpenAI", expanded=False):
        endpoint = st.text_input("Endpoint Azure:", value=st.session_state.get("saved_endpoint", ""), type="default")
        api_key = st.text_input("API Key:", value=st.session_state.get("saved_key", ""), type="password")
        modelo = st.text_input("Modelo (Deployment):", value=st.session_state.get("saved_model", "gpt-4o-mini"))

    st.divider()

    # Persona ajustada para E-commerce / Assistência
    persona_padrao = (
        "Você é um assistente virtual de atendimento e vendas de uma loja de informática e assistência técnica. "
        "Seu tom é amigável, prestativo e comercial. Use emojis adequados. "
        "Seu objetivo é ajudar clientes a encontrar peças de hardware, licenças de software, e tirar dúvidas sobre orçamentos de conserto. "
        "Seja persuasivo, mas ético. Sempre que possível, guie o cliente para fechar um serviço ou compra. "
        "Se a dúvida for muito complexa, informe que um técnico humano assumirá o atendimento em breve."
    )
    persona = st.text_area("Persona do Bot (Prompt):", value=persona_padrao, height=150)
    
    arquivo_rag = st.file_uploader("Treinamento do Bot (RAG): Catálogo ou FAQs", type=["pdf", "txt", "csv"])
    if arquivo_rag is not None:
        st.session_state
