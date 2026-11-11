import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np
from openai import AzureOpenAI

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Dashboard & Chat",
    page_icon="🛠️",
    layout="wide"
)

# ==========================================
# CSS PARA FIXAR O CHAT NO CANTO INFERIOR DIREITO
# ==========================================
# Injetamos CSS para transformar o botão padrão do Streamlit em um widget flutuante
css_flutuante = """
<style>
/* Oculta o rodapé padrão do Streamlit */
footer {visibility: hidden;}

/* Captura a caixa do popover e fixa no canto da tela */
div[data-testid="stPopover"] {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 9999;
}

/* Estiliza o botão para parecer um widget de site (redondo e flutuante) */
div[data-testid="stPopover"] > button {
    background-color: #0068c9 !important;
    color: white !important;
    border-radius: 40px !important;
    padding: 15px 30px !important;
    font-size: 16px !important;
    font-weight: bold !important;
    border: none !important;
    box-shadow: 0px 6px 15px rgba(0, 0, 0, 0.3) !important;
    transition: transform 0.2s;
}

div[data-testid="stPopover"] > button:hover {
    transform: scale(1.05);
    background-color: #0050a0 !important;
}
</style>
"""
st.markdown(css_flutuante, unsafe_allow_html=True)

# Inicializa o estado do chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Olá! 👋 Sou o assistente virtual da loja. Em que posso ajudar hoje?"}]

# ==========================================
# BARRA LATERAL: CONFIGURAÇÕES DE API (INVISÍVEL PARA O CLIENTE)
# ==========================================
with st.sidebar:
    st.title("⚙️ Painel Admin IA")
    st.caption("Configurações do Azure OpenAI")
    
    endpoint = st.text_input("Endpoint Azure:", value=st.session_state.get("endpoint", ""), type="default")
    api_key = st.text_input("API Key:", value=st.session_state.get("api_key", ""), type="password")
    modelo = st.text_input("Modelo:", value=st.session_state.get("modelo", "gpt-4o-mini"))
    
    if st.button("Salvar Chaves"):
        st.session_state.endpoint = endpoint
        st.session_state.api_key = api_key
        st.session_state.modelo = modelo
        st.success("Chaves salvas na sessão!")

# ==========================================
# TELA PRINCIPAL: DASHBOARD GERENCIAL (AUTO-LOAD)
# ==========================================
@st.cache_data
def carregar_dados():
    arquivo_csv = "dados_assistencia_tech.csv"
    
    # Tenta ler o CSV do repositório no GitHub. Se não existir, cria fallback.
    if os.path.exists(arquivo_csv):
        df = pd.read_csv(arquivo_csv)
    else:
        # Fallback de segurança para garantir que o Dashboard renderize sempre
        np.random.seed(42)
        datas = pd.date_range(start='2025-01-01', periods=150, freq='D')
        df = pd.DataFrame({
            'Data': datas,
            'Categoria': np.random.choice(['Hardware', 'Software', 'Serviço', 'Manutenção Mista'], 150),
            'Item_Servico': ['Item Simulado'] * 150,
            'Custo_Peca_R$': np.random.uniform(50, 800, 150),
            'Valor_Servico_R$': np.random.uniform(80, 400, 150),
            'Qtd_Vendas': np.random.randint(1, 8, 150),
            'Orcamentos_Feitos': np.random.randint(2, 12, 150),
            'Servicos_Atrasados': np.random.choice([0, 1, 2], 150, p=[0.85, 0.10, 0.05])
        })
        
    df['Data'] = pd.to_datetime(df['Data'])
    df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')
    df['Receita_Total'] = (df['Custo_Peca_R$'] + df['Valor_Servico_R$']) * df['Qtd_Vendas']
    return df

df = carregar_dados()

st.title("📊 Painel Gerencial de Vendas e Serviços")
st.write("Visão geral de faturamento, orçamentos e performance operacional da assistência.")

# Métricas Principais (KPIs)
receita_total = df['Receita_Total'].sum()
vendas = df['Qtd_Vendas'].sum()
orcamentos = df['Orcamentos_Feitos'].sum()
atrasos = df['Servicos_Atrasados'].sum()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Receita Bruta Projetada", f"R$ {receita_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
kpi2.metric("Total de Vendas", f"{vendas:,}")
kpi3.metric("Orçamentos Gerados", f"{orcamentos:,}")
kpi4.metric("Serviços em Atraso", f"{atrasos:,}", delta_color="inverse" if atrasos > 0 else "normal")

st.divider()

# Gráficos Visuais
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Receita por Categoria")
    df_cat = df.groupby('Categoria')['Receita_Total'].sum().reset_index()
    fig_pie = px.pie(df_cat, values='Receita_Total', names='Categoria', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_g2:
    st.subheader("Evolução Mensal do Faturamento")
    df_tempo = df.groupby('Mes_Ano')['Receita_Total'].sum().reset_index().sort_values('Mes_Ano')
    fig_line = px.line(df_tempo, x='Mes_Ano', y='Receita_Total', markers=True, line_shape='spline')
    fig_line.update_traces(line_color='#0068c9', line_width=3)
    fig_line.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_line, use_container_width=True)

# ==========================================
# WIDGET DO CHATBOT (CANTO DIREITO INFERIOR)
# ==========================================
# st.popover cria o botão e a janela expansível simulando o aplicativo
with st.popover("💬 Falar com Atendente"):
    st.markdown("#### 🛒 Chat da Loja")
    
    # Caixa com barra de rolagem contendo o histórico do chat
    caixa_chat = st.container(height=350)
    with caixa_chat:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"**👤 Você:** {msg['content']}")
            else:
                st.markdown(f"**🤖 IA:** {msg['content']}")
                
    # Formulário de digitação (evita que a tela pisque fora de contexto)
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([4, 1])
        with col_input:
            nova_mensagem = st.text_input("Escreva aqui...", label_visibility="collapsed", placeholder="Tire sua dúvida...")
        with col_btn:
            enviado = st.form_submit_button("Enviar")
            
        if enviado and nova_mensagem:
            # Salva mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": nova_mensagem})
            
            # Valida chaves da Azure antes de chamar
            key_ativa = st.session_state.get("api_key", "")
            end_ativo = st.session_state.get("endpoint", "")
            mod_ativo = st.session_state.get("modelo", "")
            
            if not key_ativa or not end_ativo:
                resposta_ia = "⚠️ Para que eu consiga responder, o administrador precisa configurar as chaves da Azure OpenAI na barra lateral esquerda."
                st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
                st.rerun()
            else:
                try:
                    # Configuração para o Azure OpenAI
                    client = AzureOpenAI(
                        azure_endpoint=end_ativo.strip(),
                        api_key=key_ativa.strip(),
                        api_version="2024-06-01"
                    )
                    
                    mensagens_api = [{"role": "system", "content": "Você é um assistente de vendas de tecnologia simpático e profissional."}]
                    for m in st.session_state.messages:
                        mensagens_api.append({"role": m["role"], "content": m["content"]})
                        
                    response = client.chat.completions.create(
                        model=mod_ativo.strip(),
                        messages=mensagens_api,
                        temperature=0.7
                    )
                    
                    resposta_ia = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
                    st.rerun()
                    
                except Exception as e:
                    erro = f"❌ Ocorreu um erro ao conectar com a IA: {e}"
                    st.session_state.messages.append({"role": "assistant", "content": erro})
                    st.rerun()
