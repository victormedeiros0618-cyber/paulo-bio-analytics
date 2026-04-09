import streamlit as st
from streamlit_option_menu import option_menu
from core.config import aplicar_estilo, COR_PRIMARIA
from views.components.header_context import render_dashboard_head

# Import dos Passos Modularizados
from views.steps.passo_0 import show_passo_0
from views.steps.passo_1 import show_passo_1
from views.steps.passo_2 import show_passo_2
from views.steps.passo_3 import show_passo_3
from views.steps.passo_4 import show_passo_4
from views.steps.passo_5 import show_passo_5
from views.steps.passo_6 import show_passo_6
from views.steps.passo_7 import show_passo_7

# --- 1. CONFIGURAÇÃO GLOBAL ---
st.set_page_config(
    page_title="Paulo Bio | Analytics",
    layout="wide",
    page_icon="logoOPB.png"
)
aplicar_estilo()

# --- 2. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    from views.login import show_login
    show_login()
    st.stop()

# --- 3. INICIALIZAÇÃO DE ESTADO ---
if 'step' not in st.session_state: st.session_state.step = 0
if 'dados' not in st.session_state:
    st.session_state.dados = {"checklist_docs": {}}
if 'tema_claro' not in st.session_state:
    st.session_state.tema_claro = st.query_params.get("tema") == "claro"
if 'usuario_logado' not in st.session_state: st.session_state.usuario_logado = "analista"
if 'email_usuario' not in st.session_state: st.session_state.email_usuario = ""



# --- 3. MENU LATERAL ---
with st.sidebar:
    # Centralização natural do Logo sem quebrar rotas estáticas
    colA, colB, colC = st.columns([1, 3, 1])
    with colB:
        st.image("logoOPB.png", use_container_width=True)

    tema_claro = st.session_state.get("tema_claro", False)
    
    # Cores dinâmicas para o Option Menu
    bg_nav = "#FFFFFF" if tema_claro else "#141E2B"
    text_nav = "#2C3E50" if tema_claro else "#C8D6E5"
    
    menu = option_menu(
        menu_title=None,
        options=["Dashboard", "Nova Análise", "Histórico", "Configurações"],
        icons=["bar-chart-fill", "file-earmark-text-fill", "clock-history", "gear-fill"],
        default_index=1,
        styles={
            "container": {"background-color": bg_nav},
            "nav-link": {"color": text_nav, "font-size": "14px", "border-radius": "2px"},
            "nav-link-selected": {"background-color": COR_PRIMARIA, "color": "#0F1923", "font-weight": "700"}
        }
    )

    # Toggle Tema Claro/Escuro
    st.markdown('<i class="bi bi-moon-stars" style="color:#F47920; margin-right:8px;"></i>**Visualização**', unsafe_allow_html=True)
    tema_novo = st.toggle("Modo Claro", value=tema_claro)
    if tema_novo != tema_claro:
        st.session_state.tema_claro = tema_novo
        st.query_params["tema"] = "claro" if tema_novo else "escuro"
        st.rerun()
    
    # Aplica CSS do tema com !important para sobrescrever config.py
    if tema_claro:
        st.markdown("""
        <style>
            /* Modo Claro - Alta Especificidade Total */
            
            /* Fundo principal e sidebar */
            section.main, div.block-container, div.stApp {
                background-color: #F5F6FA !important;
            }
            section[data-testid="stSidebar"], div[data-testid="stSidebarContent"] {
                background-color: #FFFFFF !important;
            }
            
            /* Forçar todos os textos a ficarem Pretos */
            h1, h2, h3, h4, h5, h6, 
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
            p, span, label, div, small, li, blockquote {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            
            /* Exceto botões que devem conter sua cor de texto nativa (geralmente branco ou preto dependendo do fundo) */
            .stButton>button div, .stButton>button span, .stButton>button p {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }

            /* Inputs, Textareas e SelectBoxes (Fundo CINZA e Borda LARANJA) */
            div[data-baseweb="input"] > div, 
            div[data-baseweb="textarea"] > div,
            div[data-baseweb="select"] > div,
            div[data-baseweb="base-input"] > div {
                background-color: #E2E8F0 !important; /* Cinza claro estilo campo */
                border: 1px solid #F47920 !important; /* Borda laranja */
                border-radius: 4px !important;
            }
            
            /* O texto digitado dentro do input */
            div[data-baseweb="input"] input, 
            div[data-baseweb="textarea"] textarea,
            div[data-baseweb="base-input"] input {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
                background-color: transparent !important;
            }

            /* File Uploader (Dropzone) - CINZA e BORDA LARANJA */
            [data-testid="stFileUploadDropzone"] {
                background-color: #D1D5DB !important; /* Cinza um pouco mais forte para destaque */
                border: 2px dashed #F47920 !important;
                border-radius: 4px !important;
            }
            [data-testid="stFileUploadDropzone"] div, 
            [data-testid="stFileUploadDropzone"] span,
            [data-testid="stFileUploadDropzone"] p {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            
            /* Ajuste para o widget de upload (texto de arquivos selecionados) */
            div[data-testid="stFileUploaderFileData"] span {
                color: #000000 !important;
            }
            
            /* Linhas Divisórias e Filetes Verticais */
            hr { border-color: #F47920 !important; }
            div[data-testid="stVerticalBlockBorderWrapper"] > div { 
                background-color: #FFFFFF !important; 
                border: 1px solid #F47920 !important; 
            }
            
            /* Stepper e Barras */
            .ctx-bar { 
                background-color: #FFFFFF !important; 
                border-bottom: 2px solid #F47920 !important; 
            }
            .ctx-val {
                color: #000000 !important;
            }
            .step-circle.active { 
                background-color: #FFFFFF !important; 
                color: #F47920 !important;
                border: 2px solid #F47920 !important;
            }
            .step-label.active {
                color: #000000 !important;
                font-weight: 700 !important;
            }
            .step-label.pending {
                color: #666666 !important;
            }
        </style>
        """, unsafe_allow_html=True)

    
    st.divider()

    nome_usuario = st.session_state.get("usuario_logado", "")
    st.markdown(f"""
    <style>
        .sidebar-action-btn button {{
            height: 32px !important;
            padding: 0 10px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            border-radius: 2px !important;
        }}
    </style>
    <div style="
        display:flex; align-items:center; gap:10px;
        background:rgba(244,121,32,0.08);
        border:1px solid rgba(244,121,32,0.25);
        border-radius:2px;
        padding:8px 10px;
        margin-bottom:8px;
    ">
        <div style="
            width:30px; height:30px; border-radius:2px;
            background:#F47920;
            display:flex; align-items:center; justify-content:center;
            flex-shrink:0;
        ">
            <i class="bi bi-person-fill" style="color:#0F1923; font-size:15px;"></i>
        </div>
        <div>
            <div style="font-size:12px; font-weight:600; color:#F47920; line-height:1.2;">{nome_usuario}</div>
            <div style="font-size:11px; color:#7F8C8D; line-height:1.2;">Analista</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_rst, col_sair = st.columns(2)
    with col_rst:
        st.markdown('<div class="sidebar-action-btn">', unsafe_allow_html=True)
        if st.button("Reiniciar", use_container_width=True):
            st.session_state.dados = {"checklist_docs": {}}
            st.session_state.step = 0
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col_sair:
        st.markdown('<div class="sidebar-action-btn">', unsafe_allow_html=True)
        if st.button("↪ Sair", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.usuario_logado = ""
            st.session_state.email_usuario = ""
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

from views.components.checklist import render_document_checklist

# --- 4. ROTEAMENTO DE CONTEÚDO ---
if menu == "Nova Análise":
    with st.sidebar:
        render_document_checklist()

    # ── STEPPER VISUAL ───────────────────────────────────────────
    PASSOS = [
        ("0", "Contrato"),
        ("1", "Proposta"),
        ("2", "Ficha"),
        ("3", "Serasa"),
        ("4", "Certidões"),
        ("5", "Contábil"),
        ("6", "IR"),
        ("7", "Parecer"),
    ]

    step_atual = st.session_state.step
    items_html = ""
    for i, (num, label) in enumerate(PASSOS):
        if i < step_atual:
            estado = "done"
            icon = "✔"
        elif i == step_atual:
            estado = "active"
            icon = num
        else:
            estado = "pending"
            icon = num

        items_html += f"""
        <div class="step-item">
            <div class="step-circle {estado}">{icon}</div>
            <span class="step-label {estado}">{label}</span>
        </div>"""

        # Linha conectora entre passos
        if i < len(PASSOS) - 1:
            conn_estado = "done" if i < step_atual else "pending"
            items_html += f'<div class="step-connector {conn_estado}"></div>'

    st.markdown(f'<div class="stepper">{items_html}</div>', unsafe_allow_html=True)

    # ── CONTEXT HEADER (Passo 2 em diante) ───────────────────────
    if step_atual >= 2:
        render_dashboard_head()

    # ── ROTEADOR DE PASSOS ────────────────────────────────────────
    roteador = {
        0: show_passo_0,
        1: show_passo_1,
        2: show_passo_2,
        3: show_passo_3,
        4: show_passo_4,
        5: show_passo_5,
        6: show_passo_6,
        7: show_passo_7,
    }

    if step_atual in roteador:
        roteador[step_atual]()
    else:
        st.error("Erro no roteamento: Passo não encontrado.")

elif menu == "Histórico":
    from views.historico import show_historico
    show_historico()

elif menu == "Dashboard":
    from views.dashboard import show_dashboard
    show_dashboard()

elif menu == "Configurações":
    st.title("Configurações")
    st.info("Em desenvolvimento.")