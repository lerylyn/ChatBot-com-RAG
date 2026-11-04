import streamlit as st
from openai import AzureOpenAI
import PyPDF2
import pandas as pd

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E VARIÁVEIS
# ==========================================
st.set_page_config(page_title="ChatBot Catequese Rosa Mística", page_icon="🕊️", layout="centered")

# Inicializando variáveis de sessão (Memória do Streamlit)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_iniciado" not in st.session_state:
    st.session_state.chat_iniciado = False
if "contexto_arquivo" not in st.session_state:
    st.session_state.contexto_arquivo = ""

# ==========================================
# 2. FUNÇÕES DE PROCESSAMENTO DE ARQUIVOS
# ==========================================
def extrair_texto_arquivo(arquivo_upload):
    texto = ""
    if arquivo_upload is not None:
        try:
            if arquivo_upload.name.endswith(".pdf"):
                leitor_pdf = PyPDF2.PdfReader(arquivo_upload)
                for pagina in leitor_pdf.pages:
                    texto += pagina.extract_text() + "\n"
            elif arquivo_upload.name.endswith(".csv"):
                df = pd.read_csv(arquivo_upload)
                texto = df.to_string()
            elif arquivo_upload.name.endswith(".txt"):
                texto = arquivo_upload.read().decode("utf-8")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
    return texto

def novo_chat():
    st.session_state.messages = []
    # O estado de chat_iniciado e as credenciais são mantidos

# ==========================================
# 3. BARRA LATERAL (ENTRADAS E CONFIGURAÇÃO)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configurações da Azure")
    api_key = st.text_input("API Key", type="password", help="Insira sua chave da Azure OpenAI")
    azure_endpoint = st.text_input("End Point", placeholder="https://seu-recurso.openai.azure.com/")
    modelo = st.text_input("Modelo (Deployment Name)", placeholder="ex: gpt-35-turbo ou gpt-4")
    
    st.divider()
    
    st.header("🕊️ Configuração do Chat")
    persona_padrao = "Você é um assistente virtual da Catequese da Paróquia Rosa Mística. Seu objetivo é ajudar catequistas a preparar encontros e catequisandos a tirarem dúvidas sobre a fé católica, de forma acolhedora, clara e alinhada com os ensinamentos da Igreja."
    persona = st.text_area("Persona da IA", value=persona_padrao, height=150)
    
    arquivo = st.file_uploader("Upload de Arquivo (Base de Conhecimento)", type=["pdf", "csv", "txt"])
    if arquivo:
        st.session_state.contexto_arquivo = extrair_texto_arquivo(arquivo)
        st.success("Arquivo processado e pronto para uso!")

    if st.button("Iniciar Chat", use_container_width=True):
        if api_key and azure_endpoint and modelo:
            st.session_state.chat_iniciado = True
            st.success("Chat iniciado com sucesso!")
        else:
            st.error("Preencha a API, End Point e Modelo para iniciar.")

# ==========================================
# 4. ÁREA PRINCIPAL (INTERFACE DO CHAT)
# ==========================================
st.title("🕊️ ChatBot - Catequese Paróquia Rosa Mística")

if st.session_state.chat_iniciado:
    # Botão para Novo Chat (limpa mensagens, mantém conexão)
    col1, col2 = st.columns([4, 1])
    with col2:
        st.button("🔄 Novo Chat", on_click=novo_chat, use_container_width=True)

    # Exibir histórico de mensagens da sessão atual
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Entrada do usuário (O operador := é obrigatório aqui)
    if pergunta := st.chat_input("Digite sua pergunta..."):
        # Adicionar pergunta do usuário ao histórico e mostrar na tela
        st.session_state.messages.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        # Configurar o cliente da Azure OpenAI
        try:
            client = AzureOpenAI(
                api_key=api_key,
                api_version="2024-02-15-preview", # Versão padrão da API
                azure_endpoint=azure_endpoint
            )

            # Construir o prompt do sistema (Persona + Contexto do Arquivo)
            system_prompt = persona
            if st.session_state.contexto_arquivo:
                system_prompt += f"\n\nUtilize as seguintes informações de referência para basear sua resposta:\n{st.session_state.contexto_arquivo}"

            # Preparar as mensagens para enviar à API
            mensagens_api = [{"role": "system", "content": system_prompt}]
            mensagens_api.extend(st.session_state.messages)

            # Chamada à IA
            with st.chat_message("assistant"):
                placeholder = st.empty()
                resposta = client.chat.completions.create(
                    model=modelo,
                    messages=mensagens_api,
                    temperature=0.7
                )
                texto_resposta = resposta.choices[0].message.content
                placeholder.markdown(texto_resposta)
                
                # Salvar resposta no histórico
                st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
                
        except Exception as e:
            st.error(f"Erro ao conectar com a Azure OpenAI: Verifique suas credenciais. Detalhe técnico: {e}")
else:
    st.info("👈 Por favor, preencha as configurações de conexão na barra lateral e clique em 'Iniciar Chat'.")
