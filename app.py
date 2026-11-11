import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from openai import AzureOpenAI

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Painel Analítico e Suporte TI",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 2. CSS CUSTOMIZADO (CHAT FLUTUANTE ESTILO WHATSAPP)
# ==========================================
css_layout = """
<style>
/* Esconde o menu padrão e footer do Streamlit para ficar mais limpo */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Captura o bloco que contém a classe .chat-anchor e o transforma em uma janela flutuante no canto */
div[data-testid="stVerticalBlock"]:has(.chat-anchor) {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 380px;
    background-color: #1A1C23; /* Fundo escuro do chat */
    border-radius: 15px;
    padding: 15px 15px 5px 15px;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.5);
    z-index: 99999;
    border: 1px solid #333;
}

/* Estilização interna das mensagens simulando WhatsApp */
.msg-user {
    background-color: #005C4B;
    color: white;
    padding: 10px;
    border-radius: 10px 0px 10px 10px;
    margin: 5px 0 5px 40px;
    text-align: right;
    font-size: 14px;
}
.msg-bot {
    background-color: #2A2D37;
    color: white;
    padding: 10px;
    border-radius: 0px 10px 10px 10px;
    margin: 5px 40px 5px 0;
    text-align: left;
    font-size: 14px;
    border: 1px solid #3d404d;
}
</style>
"""
st.markdown(css_layout, unsafe_allow_html=True)

# Inicialização de variáveis de sessão
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Como posso ajudar você hoje com o suporte de TI?"}
    ]
if "conteudo_base" not in st.session_state:
    st.session_state.conteudo_base = ""

# ==========================================
# 3. BARRA LATERAL (MENU ESQUERDO)
# ==========================================
with st.sidebar:
    # Credenciais em Expander para não poluir
    with st.expander("⚙️ Credenciais Azure", expanded=False):
        end_ativo = st.text_input("Endpoint:", value=st.session_state.get("endpoint", ""), type="default")
        key_ativa = st.text_input("API Key:", value=st.session_state.get("api_key", ""), type="password")
        st.session_state.endpoint = end_ativo
        st.session_state.api_key = key_ativa

    mod_ativo = st.text_input("Deployment / Modelo:", value="gpt-4o-mini")
    st.session_state.modelo = mod_ativo
    
    st.divider()
    
    persona_padrao = "Forma ágil, clara e cordial. Consulte sempre a base anexada para orçamentos, procedimentos e SLAs."
    persona = st.text_area("Persona da IA:", value=persona_padrao, height=100)
    
    st.divider()
    
    arquivo_upload = st.file_uploader("Upload da Base (CSV para Dashboard + Chat):", type=["csv"])
    
    if st.button("🚀 Conectar IA", use_container_width=True, type="primary"):
        st.success("IA Conectada!")
        
    if st.button("🔄 Novo Chat", use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Como posso ajudar você hoje com o suporte de TI?"}]
        st.rerun()

# ==========================================
# 4. PROCESSAMENTO DE DADOS DO DASHBOARD
# ==========================================
@st.cache_data
def processar_dados(arquivo):
    if arquivo is not None:
        df = pd.read_csv(arquivo)
        st.session_state.conteudo_base = df.to_string(index=False) # Salva para o RAG
    else:
        # Dados simulados se nenhum arquivo for enviado (evita tela branca)
        np.random.seed(42)
        df = pd.DataFrame({
            'Categoria': np.random.choice(['Hardware', 'Software', 'Redes', 'Manutenção'], 150),
            'Custo_Total': np.random.uniform(50, 600, 150),
            'SLA_Horas': np.random.uniform(1, 24, 150)
        })
    return df

df_dash = processar_dados(arquivo_upload)

# ==========================================
# 5. TELA PRINCIPAL (DASHBOARD)
# ==========================================
st.title("📊 Painel Analítico de Manutenção e Serviços de TI")

# Cálculo dos KPIs
total_servicos = len(df_dash)
ticket_medio = df_dash['Custo_Total'].mean() if 'Custo_Total' in df_dash.columns else 0
sla_medio = df_dash['SLA_Horas'].mean() if 'SLA_Horas' in df_dash.columns else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total de Serviços", f"{total_servicos} itens")
col2.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
col3.metric("SLA Médio", f"{sla_medio:.1f} h")

st.divider()

# Gráficos iguais aos da imagem
col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.markdown("**Custo Total por Categoria (R$)**")
    if 'Categoria' in df_dash.columns and 'Custo_Total' in df_dash.columns:
        df_agrupado = df_dash.groupby('Categoria')['Custo_Total'].sum().reset_index()
        fig_bar = px.bar(df_agrupado, x='Categoria', y='Custo_Total', color='Categoria')
        fig_bar.update_layout(showlegend=False, margin=dict(t=10, b=0, l=0, r=0))
        st.plotly_chart(fig_bar, use_container_width=True)

with col_grafico2:
    st.markdown("**Distribuição de Valores**")
    if 'Categoria' in df_dash.columns and 'Custo_Total' in df_dash.columns:
        fig_pie = px.pie(df_agrupado, values='Custo_Total', names='Categoria', hole=0.4)
        fig_pie.update_layout(margin=dict(t=10, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# 6. CHAT FLUTUANTE (CANTO DIREITO)
# ==========================================
# Este container inteiro será movido para o canto da tela pelo CSS lá do topo
chat_container = st.container()

with chat_container:
    # A âncora invisível que o CSS usa para puxar o container
    st.markdown('<div class="chat-anchor"></div>', unsafe_allow_html=True)
    
    # Cabeçalho do Chat
    st.markdown("""
    <div style="display: flex; align-items: center; color: white; margin-bottom: 10px;">
        <h3 style="margin: 0; font-size: 18px;">🎧 Suporte de TI Online</h3>
    </div>
    <div style="color: #00E676; font-size: 12px; margin-top: -10px; margin-bottom: 15px;">🟢 online agora</div>
    """, unsafe_allow_html=True)

    # Área das mensagens de texto (Scrollable)
    area_scroll = st.container(height=300)
    with area_scroll:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="msg-bot">{msg["content"]}</div>', unsafe_allow_html=True)

    # Formulário de envio acoplado embaixo
    with st.form("form_envio", clear_on_submit=True):
        mensagem = st.text_input("Digite sua dúvida...", label_visibility="collapsed")
        enviado = st.form_submit_button("Enviar 🚀", use_container_width=True)
        
        if enviado and mensagem:
            # Salva usuário
            st.session_state.messages.append({"role": "user", "content": mensagem})
            
            # Checa chaves
            if not st.session_state.api_key or not st.session_state.endpoint:
                st.session_state.messages.append({"role": "assistant", "content": "⚠️ Por favor, insira as credenciais da Azure OpenAI na barra lateral."})
                st.rerun()
            else:
                # Chama API Azure
                try:
                    client = AzureOpenAI(
                        azure_endpoint=st.session_state.endpoint.strip(),
                        api_key=st.session_state.api_key.strip(),
                        api_version="2024-06-01"
                    )
                    
                    # Contexto RAG + Persona
                    sys_prompt = persona
                    if st.session_state.conteudo_base:
                        sys_prompt += f"\n\n--- DADOS DA PLANILHA ---\n{st.session_state.conteudo_base}"
                        
                    mensagens_api = [{"role": "system", "content": sys_prompt}]
                    for m in st.session_state.messages:
                        mensagens_api.append({"role": m["role"], "content": m["content"]})
                        
                    resposta = client.chat.completions.create(
                        model=st.session_state.modelo.strip(),
                        messages=mensagens_api,
                        temperature=0.3
                    )
                    
                    texto_ia = resposta.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": texto_ia})
                    st.rerun()
                    
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"Erro de conexão: {str(e)}"})
                    st.rerun()
