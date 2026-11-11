import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from openai import AzureOpenAI

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Dashboard Gerencial & Chat",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 2. CSS PARA O CHAT FLUTUANTE
# ==========================================
# Este CSS garante que APENAS o container do chat fique no canto inferior direito,
# sem quebrar ou esconder o resto do site.
css_chat_flutuante = """
<style>
/* Foca especificamente no bloco que contém a classe .marcador-chat */
div[data-testid="stVerticalBlock"]:has(> div.element-container .marcador-chat) {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 360px;
    background-color: #ffffff;
    border-radius: 12px;
    box-shadow: 0px 8px 24px rgba(0,0,0,0.2);
    border: 1px solid #e0e0e0;
    padding: 15px;
    z-index: 99999;
}
</style>
"""
st.markdown(css_chat_flutuante, unsafe_allow_html=True)

# Inicializa o histórico de mensagens do chat na sessão
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou o assistente de vendas da loja. Em que posso ajudar?"}]

# ==========================================
# 3. BARRA LATERAL (CONFIGURAÇÕES IA)
# ==========================================
with st.sidebar:
    st.title("⚙️ Configurações IA")
    st.caption("Insira as credenciais do Azure OpenAI para ativar o chatbot.")
    
    end_ativo = st.text_input("Endpoint Azure:", value=st.session_state.get("endpoint", ""), type="default")
    key_ativa = st.text_input("API Key:", value=st.session_state.get("api_key", ""), type="password")
    mod_ativo = st.text_input("Modelo:", value=st.session_state.get("modelo", "gpt-4o-mini"))
    
    if st.button("Salvar Chaves", use_container_width=True):
        st.session_state.endpoint = end_ativo
        st.session_state.api_key = key_ativa
        st.session_state.modelo = mod_ativo
        st.success("Configuração salva!")

# ==========================================
# 4. CARREGAMENTO DE DADOS (À PROVA DE FALHAS)
# ==========================================
@st.cache_data
def carregar_dados():
    arquivo = "dados_assistencia_tech.csv"
    # Se o CSV estiver na pasta, ele lê. Se não estiver, simula na hora para o Dashboard não quebrar.
    if os.path.exists(arquivo):
        df = pd.read_csv(arquivo)
        df['Data'] = pd.to_datetime(df['Data'])
    else:
        np.random.seed(42)
        datas = pd.date_range(start='2025-01-01', periods=1200, freq='D')
        df = pd.DataFrame({
            'Data': datas,
            'Categoria': np.random.choice(['Hardware', 'Software', 'Serviço', 'Reparo Misto'], 1200),
            'Item_Servico': ['Serviço / Peça Padrão'] * 1200,
            'Custo_Peca_R$': np.random.uniform(50, 600, 1200),
            'Valor_Servico_R$': np.random.uniform(100, 500, 1200),
            'Qtd_Vendas': np.random.randint(1, 6, 1200),
            'Orcamentos_Feitos': np.random.randint(2, 10, 1200),
            'Servicos_Atrasados': np.random.choice([0, 1, 2], 1200, p=[0.85, 0.10, 0.05])
        })
        
    df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')
    df['Receita_Total'] = (df['Custo_Peca_R$'] + df['Valor_Servico_R$']) * df['Qtd_Vendas']
    return df

df = carregar_dados()

# ==========================================
# 5. TELA PRINCIPAL: RESUMO GERENCIAL IMEDIATO
# ==========================================
st.title("📊 Resumo Gerencial - Assistência Técnica")
st.write("Acompanhamento financeiro e operacional em tempo real.")

# KPIs - Valores e Quantidades em Destaque
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

receita_bruta = df['Receita_Total'].sum()
total_vendas = df['Qtd_Vendas'].sum()
total_orcamentos = df['Orcamentos_Feitos'].sum()
total_atrasos = df['Servicos_Atrasados'].sum()

kpi1.metric("Faturamento Bruto Projetado", f"R$ {receita_bruta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
kpi2.metric("Quantidade de Vendas", f"{total_vendas:,}")
kpi3.metric("Orçamentos Emitidos", f"{total_orcamentos:,}")
kpi4.metric("Serviços em Atraso", f"{total_atrasos:,}", delta_color="inverse" if total_atrasos > 0 else "normal")

st.divider()

# Gráficos de Gestão
col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.subheader("Distribuição de Receita")
    df_cat = df.groupby('Categoria')['Receita_Total'].sum().reset_index()
    fig_rosca = px.pie(df_cat, values='Receita_Total', names='Categoria', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
    fig_rosca.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_rosca, use_container_width=True)

with col_grafico2:
    st.subheader("Evolução Mensal de Faturamento")
    df_mes = df.groupby('Mes_Ano')['Receita_Total'].sum().reset_index().sort_values('Mes_Ano')
    fig_linha = px.line(df_mes, x='Mes_Ano', y='Receita_Total', markers=True)
    fig_linha.update_traces(line_color='#0068c9', line_width=3)
    fig_linha.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_linha, use_container_width=True)

# ==========================================
# 6. WIDGET CHATBOT (CANTO DIREITO INFERIOR)
# ==========================================
# Este container é capturado pelo CSS criado no início do código
container_chat = st.container()

with container_chat:
    # A classe vazia abaixo serve apenas como "âncora" para o CSS puxar este container para o canto
    st.markdown('<div class="marcador-chat"></div>', unsafe_allow_html=True)
    
    st.markdown("#### 💬 Chat de Atendimento")
    
    # Área de rolagem para as mensagens (evita que o balão cresça infinitamente)
    area_mensagens = st.container(height=300)
    with area_mensagens:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.info(msg["content"], icon="👤")
            else:
                st.success(msg["content"], icon="🤖")

    # Formulário de envio de mensagem (compacto)
    with st.form("form_chat", clear_on_submit=True):
        col_input, col_btn = st.columns([4, 1])
        with col_input:
            mensagem_usuario = st.text_input("Msg", label_visibility="collapsed", placeholder="Digite sua dúvida...")
        with col_btn:
            btn_enviar = st.form_submit_button("➤")
            
        if btn_enviar and mensagem_usuario:
            # Adiciona a pergunta à tela
            st.session_state.messages.append({"role": "user", "content": mensagem_usuario})
            
            # Validação simples da API
            if not st.session_state.get("api_key") or not st.session_state.get("endpoint"):
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "⚠️ Chaves da API ausentes. Peça ao administrador para configurá-las na barra lateral esquerda."
                })
                st.rerun()
            else:
                try:
                    # Chamada Azure OpenAI
                    client = AzureOpenAI(
                        azure_endpoint=st.session_state.endpoint.strip(),
                        api_key=st.session_state.api_key.strip(),
                        api_version="2024-06-01"
                    )
                    
                    historico_api = [{"role": "system", "content": "Você é um simpático assistente virtual de vendas e suporte."}]
                    for m in st.session_state.messages:
                        historico_api.append({"role": m["role"], "content": m["content"]})
                        
                    response = client.chat.completions.create(
                        model=st.session_state.modelo.strip(),
                        messages=historico_api,
                        temperature=0.7
                    )
                    
                    resposta = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
                    st.rerun()
                    
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"❌ Erro na IA: {e}"})
                    st.rerun()
