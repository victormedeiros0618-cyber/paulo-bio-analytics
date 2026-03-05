import streamlit as st
from google import genai
from google.genai import types
import json
import pandas as pd
from datetime import datetime
import time
from fpdf import FPDF
import matplotlib.pyplot as plt
import tempfile
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_option_menu import option_menu  
from datetime import datetime
import base64
import plotly.express as px

class PDFExecutivo(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_fill_color(244, 121, 32)
            self.rect(0, 0, 210, 4, 'F')
            self.ln(5)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_fill_color(244, 121, 32)
            self.rect(0, 293, 210, 4, 'F')
            self.set_font('Arial', 'I', 9)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'R')

# --- 2. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(
    page_title="Paulo Bio | Analytics", 
    layout="wide", 
    page_icon="logo.png",
    initial_sidebar_state="expanded"
)

COR_PRIMARIA = "#F47920"
COR_SECUNDARIA = "#2C3E50"
COR_TERCIARIA = "#7F8C8D"

# CSS Personalizado (Fundo Escuro + Sidebar Chumbo + Forms Claros)
st.markdown(f"""
<style>
    /* ==========================================
       1. FONTES E OCULTAÇÃO DE ELEMENTOS NATIVOS
       ========================================== */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Roboto', sans-serif; }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    [data-testid="stHeader"] {{ background-color: transparent !important; visibility: visible !important; }}
    [data-testid="stToolbar"] {{ visibility: hidden !important; display: none !important; }}

        /* ==========================================
       2. CORES DE FUNDO (TELA ESCURA + SIDEBAR CHUMBO)
       ========================================== */
    /* Fundo principal da tela */
    .stApp, .main, .block-container {{ 
        background-color: #3E5771 !important; 
    }}
    
    /* Pinta TODAS as camadas possíveis do Sidebar de Cinza Chumbo 
       Isso mata o "quadrado preto" atrás do menu */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"],
    section[data-testid="stSidebar"] div {{ 
        background-color: #2C3E50 !important; 
    }}
    
    [data-testid="stSidebar"] {{
        border-right: 2px solid #FF3D00 !important;
        box-shadow: 3px 0 10px rgba(255, 61, 0, 0.15) !important;
    }}
    /* ==========================================
       3. BOTÃO DE RECOLHER/EXPANDIR SIDEBAR
       ========================================== */
    [data-testid="stHeader"] button, 
    [data-testid="collapsedControl"] {{
        visibility: visible !important;
        display: inline-flex !important;
        background-color: #2C3E50 !important; 
        border-radius: 8px !important;
        z-index: 999999 !important; 
        margin-top: 10px !important;
        margin-left: 10px !important;
        opacity: 1 !important;
    }}
    
    [data-testid="stHeader"] button svg, 
    [data-testid="collapsedControl"] svg {{ fill: #FFFFFF !important; color: #FFFFFF !important; }}

    [data-testid="stSidebarHeader"] button,
    [data-testid="stSidebarCollapseButton"] {{
        visibility: visible !important;
        display: inline-flex !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        opacity: 1 !important;
    }}

    [data-testid="stSidebarHeader"] button svg,
    [data-testid="stSidebarCollapseButton"] svg {{ fill: #FFFFFF !important; color: #FFFFFF !important; }}

    /* ==========================================
       4. TIPOGRAFIA (TEXTOS BRANCOS NO FUNDO ESCURO)
       ========================================== */
    /* Títulos e textos gerais ficam brancos para contrastar com o fundo #3E5771 */
    h1, h2, h3, h4, h5, h6 {{ 
        font-weight: 700 !important; 
        color: #FFFFFF !important; 
        letter-spacing: -0.5px; 
        margin-bottom: 25px !important;
        margin-top: 0px !important;
    }}
    
    [data-testid="stMarkdownContainer"] p, 
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    [data-testid="stFileUploadDropzone"] p,
    [data-testid="stFileUploadDropzone"] span {{
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }}

    /* ==========================================
       5. CARDS E CONTAINERS (GLASSMORPHISM)
       ========================================== */
    /* Caixas com leve transparência para combinar com o fundo escuro */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        padding: 25px !important;
    }}
    hr {{ border-bottom: 1px solid rgba(255, 255, 255, 0.2) !important; }}

    /* ==========================================
       6. INPUTS DE FORMULÁRIO (FUNDO CLARO, TEXTO ESCURO)
       ========================================== */
    /* As caixas onde o usuário digita ficam claras com texto escuro */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, 
    .stSelectbox > div > div > div {{
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        padding: 12px 16px;
        background-color: #FAFAFA !important;
        color: #2C3E50 !important; 
    }}
    .stTextInput > div > div > input:focus {{ 
        border-color: {COR_PRIMARIA}; 
        box-shadow: inset 0 0 0 1px {COR_PRIMARIA}; 
    }}

    /* ==========================================
       7. BOTÕES
       ========================================== */
    .stButton>button {{
        background-color: #F47920 !important; 
        color: white !important; 
        border-radius: 100px !important; 
        border: none !important; 
        height: 48px !important;
        font-weight: 500 !important; 
        text-transform: uppercase !important; 
        letter-spacing: 0.5px !important;
        width: 100% !important; 
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px 0 rgba(0,0,0,0.3) !important;
    }}
    .stButton>button p {{ color: white !important; }}
    .stButton>button:hover {{ 
        background-color: #d66516 !important; 
        box-shadow: 0 4px 8px 3px rgba(0,0,0,0.15) !important; 
        transform: translateY(-1px) !important;
    }}
    
    /* --- AJUSTE DOS BOTÕES DO SIDEBAR (REINICIAR E PERFIL) --- */
    button[kind="secondary"] {{
        background-color: transparent !important; /* Tira o fundo laranja e deixa transparente */
        border: 1px solid rgba(255, 255, 255, 0.2) !important; /* Linha branca bem fina e discreta */
        border-radius: 12px !important;
    }}
    
    /* Garante que o texto e os ícones dentro do botão fiquem brancos */
    button[kind="secondary"] p, 
    button[kind="secondary"] div,
    button[kind="secondary"] span {{ 
        color: #FFFFFF !important; 
    }}
    
    /* Efeito ao passar o mouse (Hover) */
    button[kind="secondary"]:hover {{ 
        background-color: rgba(255, 255, 255, 0.05) !important; /* Leve brilho no fundo */
        border: 1px solid #F47920 !important; /* A linha acende na cor laranja primária */
    }}
    button[kind="secondary"]:hover p,
    button[kind="secondary"]:hover div,
    button[kind="secondary"]:hover span {{
        color: #F47920 !important; /* O texto também fica laranja ao passar o mouse */
    }}
    /* ==========================================
       8. PERFIL E MENU
       ========================================== */
    .block-container {{ padding-top: 2rem !important; }}
    [data-testid="column"] {{ display: flex; flex-direction: column; justify-content: flex-start; }}
    
    [data-testid="stSidebarUserContent"] {{ padding-top: 1rem !important; padding-bottom: 0rem !important; }}
    [data-testid="stSidebarUserContent"] > div {{ gap: 0.2rem !important; }}
    [data-testid="stSidebar"] hr {{ margin-top: 5px !important; margin-bottom: 5px !important; border-bottom: 1px solid rgba(255,255,255,0.1) !important; }}
    
    [data-testid="stVerticalBlock"] {{ gap: 0.5rem !important; }}
    [data-testid="stWidgetLabel"] {{ padding-bottom: 2px !important; min-height: auto !important; }}
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {{ padding-top: 8px !important; padding-bottom: 8px !important; }}
    
    /* Perfil do Usuário no Sidebar */
    .user-profile-card {{
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
    }}
    .user-profile-card p {{ color: #FFFFFF !important; font-weight: 600 !important; margin-top: 10px; margin-bottom: 0px; font-size: 14px; }}
    
    /* KPI Cards */
    .kpi-card {{
        background: rgba(255, 255, 255, 0.05); 
        border-radius: 12px; 
        padding: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-left: 5px solid {COR_PRIMARIA}; 
        text-align: center; 
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}

        /* ==========================================
       9. ÁREA DE UPLOAD DE ARQUIVOS (DRAG & DROP)
       ========================================== */
    /* Remove o fundo cinza padrão e deixa da cor da tela */
    [data-testid="stFileUploadDropzone"] {{
        background-color: transparent !important; /* Deixa o fundo transparente para puxar a cor da tela */
        border: 2px dashed rgba(255, 255, 255, 0.3) !important; /* Borda tracejada branca e elegante */
        border-radius: 12px !important;
    }}
    
    /* Quando o usuário arrastar o arquivo por cima (Hover) */
    [data-testid="stFileUploadDropzone"]:hover {{
        background-color: rgba(255, 255, 255, 0.05) !important; /* Dá um leve brilho ao passar o mouse */
        border-color: #F47920 !important; /* A borda fica laranja (sua cor primária) */
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. AUTENTICAÇÃO E CONEXÃO ---
def check_password():
    if st.session_state.get('logged_in'): return True
    st.write(""); st.write("")
    col_vazia1, col_logo, col_vazia3 = st.columns([4, 1.5, 4])
    with col_logo:
        try: st.image("logoOPB.png", width="stretch")
        except: st.markdown(f"<h1 style='text-align: center; color: {COR_PRIMARIA};'>🏢</h1>", unsafe_allow_html=True)
            
    st.markdown("<h3 style='text-align: center; color: #2C3E50;'>Portal de Análise de Crédito</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        with st.container(border=True):
            st.markdown("#### 🔒 Acesso Restrito")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                if usuario in st.secrets["passwords"] and senha == st.secrets["passwords"][usuario]:
                    st.session_state.logged_in = True
                    st.session_state.user_name = usuario
                    st.rerun()
                else: st.error("Acesso negado.")
    return False

@st.cache_resource
def get_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
    client = gspread.authorize(creds)
    return client.open(st.secrets["SHEET_NAME"]).sheet1

def load_data():
    try: return pd.DataFrame(get_google_sheet().get_all_records())
    except: return pd.DataFrame()

def save_data(cliente, status, dados_json, obs):
    try:
        get_google_sheet().append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cliente, status, dados_json, obs])
        return True
    except: return False

def limpar_analise():
    keys_to_keep = ['logged_in', 'user_name']
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep: del st.session_state[key]
    st.session_state.step = 0 
    st.session_state.dados = {}
    st.rerun()

def extrair_json_seguro(texto):
    try:
        inicio = texto.find('{')
        fim = texto.rfind('}') + 1
        if inicio != -1 and fim != -1: return json.loads(texto[inicio:fim])
    except: pass
    return {}

def str_to_float(val):
    try: return float(str(val).replace('R$', '').replace('.', '').replace(',', '.').strip())
    except: return 0.0

def gerar_pdf_bytes(dados, decisao, obs):
    def limpa(texto):
        return str(texto).encode('latin-1', 'replace').decode('latin-1')

    def safe_float(valor):
        try:
            if isinstance(valor, (int, float)): return float(valor)
            v = str(valor).upper().replace('R$', '').strip()
            if '.' in v and ',' in v: v = v.replace('.', '').replace(',', '.')
            elif ',' in v: v = v.replace(',', '.')
            import re
            v = re.sub(r'[^\d.-]', '', v)
            return float(v) if v else 0.0
        except:
            return 0.0

    pdf = PDFExecutivo(orientation='P', unit='mm', format='A4')
    pdf.set_margins(left=20, top=20, right=20)
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # --- INTELIGÊNCIA ESPACIAL ---
    def check_space(space_needed):
        # Altura A4 (297mm) - Margem Inferior (20mm) = 277mm de área útil
        # Se a posição atual + o espaço que o bloco precisa passar do limite, quebra a página
        if pdf.get_y() + space_needed > 277:
            pdf.add_page()

    # ==========================================
    # PÁGINA 1: CAPA MODERNA
    # ==========================================
    pdf.add_page()
    pdf.ln(60)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, limpa("RELATÓRIO EXECUTIVO · " + str(datetime.now().year)), ln=True, align='C')
    
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(244, 121, 32)
    pdf.cell(0, 15, limpa("Análise de Risco Locatício"), ln=True, align='C')
    pdf.ln(15)
    
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(40, pdf.get_y(), 130, 35, 'F')
    pdf.set_y(pdf.get_y() + 8)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    empresa_nome = dados.get('empresa', dados.get('pretendente', 'Não informado'))
    pdf.cell(0, 8, limpa(empresa_nome), ln=True, align='C')
    
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(80, 80, 80)
    imovel_nome = dados.get('imovel', 'Não informado')
    pdf.cell(0, 6, limpa(f"Imóvel: {imovel_nome}"), ln=True, align='C')
    
    pdf.set_y(-40)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, limpa(f"São Paulo - SP, {datetime.now().strftime('%d/%m/%Y')}"), ln=True, align='C')

    # ==========================================
    # PÁGINA 2: CONTEÚDO
    # ==========================================
    pdf.add_page()
    
    # O título agora exige pelo menos 35mm de espaço livre abaixo dele
    def title(txt, space_needed=35):
        check_space(space_needed)
        pdf.ln(8)
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 8, limpa(txt), ln=True)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(4)
        pdf.set_text_color(0, 0, 0)
        
    def row(label, value):
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(45, 6, limpa(label))
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 6, limpa(value))

    # --- 1. RESUMO DO NEGÓCIO ---
    title("1. Resumo do Negócio", 60) # Exige 60mm por causa dos cards
    row("Pretendente:", dados.get('pretendente', '-'))
    row("Atividade:", dados.get('atividade', '-'))
    row("Imóvel:", dados.get('imovel', '-'))
    row("Garantia:", dados.get('garantia', '-'))
    pdf.ln(5)
    
    y_cards = pdf.get_y()
    pdf.set_fill_color(245, 245, 245)
    
    pdf.rect(20, y_cards, 50, 20, 'F')
    pdf.set_xy(20, y_cards + 4)
    pdf.set_font("Arial", '', 8); pdf.set_text_color(100, 100, 100); pdf.cell(50, 4, limpa("PRAZO"), align='C', ln=True)
    pdf.set_xy(20, y_cards + 9)
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 0, 0); pdf.cell(50, 6, limpa(dados.get('prazo', '-')), align='C')

    pdf.rect(80, y_cards, 50, 20, 'F')
    pdf.set_xy(80, y_cards + 4)
    pdf.set_font("Arial", '', 8); pdf.set_text_color(100, 100, 100); pdf.cell(50, 4, limpa("ALUGUEL MENSAL"), align='C', ln=True)
    pdf.set_xy(80, y_cards + 9)
    val_aluguel = safe_float(dados.get('aluguel', 0))
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 0, 0); pdf.cell(50, 6, limpa(f"R$ {val_aluguel:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")), align='C')

    pdf.rect(140, y_cards, 50, 20, 'F')
    pdf.set_xy(140, y_cards + 4)
    pdf.set_font("Arial", '', 8); pdf.set_text_color(100, 100, 100); pdf.cell(50, 4, limpa("IPTU MENSAL"), align='C', ln=True)
    pdf.set_xy(140, y_cards + 9)
    val_iptu = safe_float(dados.get('iptu', 0))
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 0, 0); pdf.cell(50, 6, limpa(f"R$ {val_iptu:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")), align='C')
    
    pdf.set_y(y_cards + 25)

    # --- 2. DADOS CADASTRAIS ---
    title("2. Qualificação Societária e Restrições", 50)
    row("Razão Social:", dados.get('empresa', '-'))
    row("CNPJ:", dados.get('cnpj', '-'))
    row("Abertura (Idade):", dados.get('data_abertura', '-'))
    row("Capital Social:", dados.get('capital_social', '-'))
    row("Quadro Societário:", dados.get('socios_participacao', '-'))
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, limpa("Apontamentos (Serasa e Certidões):"), ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, limpa(dados.get('resumo_apontamentos', 'Nada consta.')), align='J')

    # --- 3. AUDITORIA FINANCEIRA ---
    title("3. Auditoria Financeira", 60) # Exige espaço para a tabela/gráfico
    periodos = dados.get("periodos", [])
    receitas = dados.get("receita_bruta", [])
    lucros = dados.get("resultado", [])
    
    if periodos and len(periodos) > 0:
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(30, 6, limpa("PERÍODO"), 0, 0)
        pdf.cell(60, 6, limpa("RECEITA BRUTA"), 0, 0)
        pdf.cell(60, 6, limpa("RESULTADO LÍQUIDO"), 0, 1)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(2)
        
        max_val = max([safe_float(r) for r in receitas] + [1]) 
        
        pdf.set_font("Arial", '', 9)
        for i in range(len(periodos)):
            try:
                rec_val = safe_float(receitas[i])
                luc_val = safe_float(lucros[i])
                
                pdf.set_xy(20, pdf.get_y() + 2)
                y_linha = pdf.get_y()
                pdf.cell(30, 6, limpa(periodos[i]), 0, 0)
                pdf.cell(60, 6, limpa(f"R$ {rec_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")), 0, 0)
                if luc_val < 0: pdf.set_text_color(200, 0, 0)
                pdf.cell(60, 6, limpa(f"R$ {luc_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")), 0, 1)
                pdf.set_text_color(0, 0, 0)
                
                largura_rec = (rec_val / max_val) * 50 if max_val > 0 else 0
                largura_luc = (abs(luc_val) / max_val) * 50 if max_val > 0 else 0
                
                pdf.set_fill_color(173, 216, 230)
                pdf.rect(50, y_linha + 6, largura_rec, 2, 'F')
                
                if luc_val >= 0: pdf.set_fill_color(144, 238, 144)
                else: pdf.set_fill_color(255, 182, 193)
                pdf.rect(110, y_linha + 6, largura_luc, 2, 'F')
                
                pdf.ln(4)
            except: pass
            
    pdf.ln(5)
    row("Comprometimento:", f"{dados.get('comprometimento_renda', '0')}% (Aluguel+IPTU sobre Receita)")

    # --- 4. CAPACIDADE DE GARANTIA ---
    title("4. Capacidade de Garantia (Sócios)", 40)
    row("Renda Anual (IR):", dados.get('renda_anual', '-'))
    row("Aplicações:", dados.get('aplicacoes_financeiras', '-'))
    row("Bens Imóveis:", dados.get('bens_imoveis', '-'))

    # --- 5. PARECER E VEREDITO ---
    # Exige 70mm de espaço livre para não cortar o banner no meio
    title("5. Parecer Jurídico", 70) 
    pdf.set_font("Arial", '', 10)
    parecer = dados.get('parecer_final', 'Parecer não gerado.')
    pdf.multi_cell(0, 5, limpa(parecer), align='J')
    pdf.ln(10)
    
    # Verifica se sobrou espaço para o banner gigante, senão joga pra próxima página
    check_space(40)
    
    is_aprovado = "APROVADO" in decisao.upper()
    is_reprovado = "REPROVADO" in decisao.upper()
    
    if is_aprovado: 
        cor_fundo = (230, 245, 230); cor_texto = (0, 120, 0)
    elif is_reprovado: 
        cor_fundo = (250, 230, 230); cor_texto = (180, 0, 0)
    else: 
        cor_fundo = (255, 240, 220); cor_texto = (200, 100, 0)

    y_banner = pdf.get_y()
    pdf.set_fill_color(*cor_fundo)
    pdf.rect(20, y_banner, 170, 35, 'F')
    
    pdf.set_xy(20, y_banner + 5)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(*cor_texto)
    pdf.cell(170, 6, limpa("RESULTADO DA ANÁLISE"), align='C', ln=True)
    
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(170, 10, limpa(decisao.upper()), align='C', ln=True)
    
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(80, 80, 80)
    obs_texto = obs if obs else "Análise concluída com base nos dados apresentados."
    pdf.cell(170, 8, limpa(f"Obs: {obs_texto}"), align='C', ln=True)

    return pdf.output(dest='S').encode('latin-1')

# --- 4. FLUXO PRINCIPAL ---
if not check_password(): st.stop()
API_KEY = st.secrets["GOOGLE_API_KEY"]

gemini_client = genai.Client(api_key=API_KEY)

if 'step' not in st.session_state: st.session_state.step = 0
if 'dados' not in st.session_state: st.session_state.dados = {}

# --- SIDEBAR COM OPTION MENU (O SEGREDO DO SAAS) ---
with st.sidebar:
    # Removido o st.write("") do topo para ganhar espaço
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        try: st.image("logoOPB.png", width="stretch") 
        except: st.markdown(f"<h2 style='text-align: center; color: {COR_PRIMARIA};'>🏢</h2>", unsafe_allow_html=True)

    # O Novo Menu Robusto
    menu = option_menu(
        menu_title=None, 
        options=["Dashboard", "Nova Análise", "Histórico", "Configurações"],
        icons=["bar-chart-fill", "file-earmark-text", "clock-history", "gear"], 
        menu_icon="cast",
        default_index=1,
        styles={
            "container": {"padding": "0!important", "background-color": "#2C3E50"}, 
            "icon": {"color": "#F47920", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "15px", "text-align": "left", "margin":"5px", 
                "--hover-color": "rgba(255,255,255,0.1)", "border-radius": "8px",
                "color": "white"
            },
            "nav-link-selected": {
                "background-color": "#FFF3E0", "color": "#FF3D00", 
                "font-weight": "bold", "border-left": "4px solid #FF3D00"
            },
        }
    )
        
    st.markdown("<div style='min-height: 200px;'></div>", unsafe_allow_html=True)
             
    # Linha divisória fina (compactada pelo CSS)
    st.divider()
    st.write("")
    st.write("")
    
        # 3. BOTÃO DE REINICIAR (Agrupado com a área logada)
    if st.button(":material/refresh: Reiniciar", key="btn_reiniciar_global"):
        st.session_state.clear() # Ou sua função limpar_analise()
        st.rerun()

    # 2. ÁREA LOGADA (Movida para baixo)
    nome_usuario = st.session_state.get('usuario_logado', 'Victor Padilha')
    email_usuario = "padilha@engenharia.ai" 
    
    with st.popover(f":material/account_circle: {nome_usuario}", width="stretch"):
        st.markdown(f"""
        <div style="text-align: center; padding-top: 5px; padding-bottom: 5px;">
            <p style="color: #2C3E50; font-weight: 700; font-size: 18px; margin: 0;">{nome_usuario}</p>
            <p style="color: #7F8C8D; font-size: 14px; margin: 0;">{email_usuario}</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider() 
        if st.button(":material/logout: Sair", key="btn_logout", width="stretch"):
            st.session_state.logado = False
            st.rerun()
            
# --- ROTEAMENTO DE TELAS ---
d = st.session_state.dados

if menu == "Nova Análise":
    passos = ["0. Contrato", "1. Proposta", "2. Ficha", "3. Serasa", "4. Certidões", "5. Contábil", "6. IR", "7. Parecer"]
    cols = st.columns(len(passos))
    for i, col in enumerate(cols):
        cor = COR_PRIMARIA if i <= st.session_state.step else "#E0E0E0"
        peso = "bold" if i == st.session_state.step else "normal"
        col.markdown(f"<div style='font-size: 0.75rem; text-align: center; padding-bottom: 5px; border-bottom: 4px solid {cor}; font-weight: {peso};'>{passos[i]}</div>", unsafe_allow_html=True)
    st.write("")

      # --- PASSO 0: CONTRATO SOCIAL ---
    if st.session_state.step == 0:
        
        # Título padronizado com Bootstrap Icons
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-file-earmark-person-fill" style="color: #F47920; margin-right: 8px;"></i> Contrato Social
        </h3>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                uploaded = st.file_uploader("Upload Contrato Social (PDF)", type="pdf", key="up0")
                if uploaded and st.button("Extrair Dados Societários"):
                    with st.spinner("Analisando Contrato..."):
                        try:
                            prompt = """Extraia APENAS JSON válido: 
                            { 
                            "empresa": "Razão Social", 
                            "cnpj": "CNPJ", 
                            "data_abertura": "Data ou Idade", 
                            "capital_social": "Valor em R$", 
                            "socios_participacao": "Nomes e % de cada um", 
                            "administrador": "Nome do administrador", 
                            "endereco_empresa": "Varra o documento inteiro com extrema atenção até localizar o endereço completo da sede da empresa. Geralmente fica na qualificação inicial dos sócios ou na cláusula 'Da Sede'. Retorne apenas se tiver certeza. Se realmente não constar no documento, retorne '-'"
                            }"""
                            res = gemini_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=[types.Part.from_bytes(data=uploaded.getvalue(), mime_type='application/pdf'), prompt]
                            )
                            st.session_state.dados.update(extrair_json_seguro(res.text))
                            st.rerun()
                        except Exception as e: st.error(f"Erro na leitura: {e}")
        with c2:
            with st.container(border=True):
                empresa = st.text_input("Razão Social", d.get("empresa", ""))
                cnpj = st.text_input("CNPJ", d.get("cnpj", ""))
                c_ab, c_cap = st.columns(2)
                abertura = c_ab.text_input("Data Abertura / Idade", d.get("data_abertura", ""))
                capital = c_cap.text_input("Capital Social", d.get("capital_social", ""))
                socios = st.text_area("Quadro Societário (%)", d.get("socios_participacao", ""))
                admin = st.text_input("Administrador", d.get("administrador", ""))
                
                # Label preparado para a integração com a API do Google Street View
                foto_sede = st.text_input("Endereço da Sede", d.get("foto_sede", ""))
                
                st.write("") # Respiro visual
                st.write("") # Respiro visual extra
                
                # Coluna 1 (Vazia), Coluna 2 (Espaço gigante), Coluna 3 (Avançar)
                c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])
                
                # A c_b1 fica sem nada dentro
                
                with c_b2:
                    # Removido o use_container_width (o CSS fará o trabalho)
                    if st.button("Avançar"): 
                        st.session_state.step = 1
                        st.rerun()

       # --- PASSO 1: PROPOSTA ---
    elif st.session_state.step == 1:
        
        # Importa a mesma biblioteca de ícones do menu lateral e cria o título moderno
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-briefcase-fill" style="color: #F47920; margin-right: 8px;"></i> Proposta
        </h3>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                uploaded = st.file_uploader("Upload Proposta (PDF)", type="pdf", key="up1")
                if uploaded and st.button("Extrair Proposta"):
                    with st.spinner("Lendo..."):
                        try:
                            prompt = """Extraia APENAS JSON válido, valores exatos como texto: 
                            { 
                                "pretendente": "", 
                                "atividade": "", 
                                "imovel": "Extrair EXATAMENTE o endereço do imóvel objeto da locação/negócio. REGRA CRÍTICA: NUNCA preencha com o endereço da própria empresa pretendente. Se o endereço do imóvel a ser alugado estiver em branco ou não for mencionado na proposta, retorne OBRIGATORIAMENTE a frase 'NÃO INFORMADO'.", 
                                "prazo": "", 
                                "aluguel": "Valor exato", 
                                "iptu": "Valor exato", 
                                "garantia": "" 
                            }"""
                            res = gemini_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=[types.Part.from_bytes(data=uploaded.getvalue(), mime_type='application/pdf'), prompt]
                            )
                            dados_extraidos = extrair_json_seguro(res.text)
                            if dados_extraidos:
                                st.session_state.dados.update(dados_extraidos)
                                st.rerun()
                        except Exception as e: st.error(f"Erro na leitura: {e}")
        with c2:
            with st.container(border=True):
                pretendente = st.text_input("Pretendente", d.get("pretendente", d.get("empresa", "")))
                atividade = st.text_input("Atividade a ser realizada", d.get("atividade", ""))
                imovel = st.text_input("Endereço do Imóvel", d.get("imovel", ""))
                prazo = st.text_input("Prazo", d.get("prazo", ""))
                c_val1, c_val2 = st.columns(2)
                aluguel = c_val1.text_input("Aluguel (R$)", d.get("aluguel", "0"))
                iptu = c_val2.text_input("IPTU (R$)", d.get("iptu", "0"))
                garantia = st.text_input("Garantia Proposta", d.get("garantia", ""))
                
                st.write("") # Respiro visual
                st.write("") # Respiro visual extra                
                # Coluna 1 (Voltar), Coluna 2 (Espaço vazio gigante), Coluna 3 (Avançar)
                c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
                with c_b1:
                    if st.button("Voltar"): 
                        st.session_state.step = 0 # Altere para o passo anterior correto
                        st.rerun()         
                with c_b2:
                    if st.button("Avançar"): 
                        st.session_state.step = 2 # Altere para o próximo passo correto
                        st.rerun()

    # --- PASSO 2: FICHA CADASTRAL ---
    elif st.session_state.step == 2:
        
        # Título padronizado com Bootstrap Icons
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-card-checklist" style="color: #F47920; margin-right: 8px;"></i> Ficha Cadastral
        </h3>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                uploaded = st.file_uploader("Upload Ficha Cadastral (PDF)", type="pdf", key="up2")
                if uploaded and st.button("Extrair Referências"):
                    with st.spinner("Lendo..."):
                        try:
                            prompt = """Extraia APENAS JSON válido resumindo as referências: { "ref_locaticias": "Paga aluguel? Onde? Valor? Proprietário?", "ref_comerciais": "Extrair as referências comerciais OBRIGATORIAMENTE no formato: 'Nome da Empresa - Telefone'. Ex: 'Fornecedor X - (11) 9999-9999'", "ref_bancarias": "Extrair as referências bancárias OBRIGATORIAMENTE no formato: 'Banco - Agência - Telefone/Contato do Gerente'" }"""
                            res = gemini_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=[types.Part.from_bytes(data=uploaded.getvalue(), mime_type='application/pdf'), prompt]
                            )
                            st.session_state.dados.update(extrair_json_seguro(res.text))
                            st.rerun()
                        except: st.warning("Leitura parcial, preencha manualmente.")
        with c2:
            with st.container(border=True):
                ref_loc = st.text_area("Referências Locatícias", d.get("ref_locaticias", ""))
                ref_com = st.text_area("Referências Comerciais", d.get("ref_comerciais", ""))
                ref_ban = st.text_area("Referências Bancárias", d.get("ref_bancarias", ""))
                
                st.write("") # Respiro visual
                st.write("") # Respiro visual extra                
                # Coluna 1 (Voltar), Coluna 2 (Espaço vazio gigante), Coluna 3 (Avançar)
                c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
                with c_b1:
                    if st.button("Voltar"): 
                        st.session_state.step = 1 # Altere para o passo anterior correto
                        st.rerun()         
                with c_b2:
                    if st.button("Avançar"): 
                        st.session_state.step = 3 # Altere para o próximo passo correto
                        st.rerun()

    # --- PASSO 3: SERASA ---
    elif st.session_state.step == 3:
        
        # Título padronizado com Bootstrap Icons
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-shield-lock-fill" style="color: #F47920; margin-right: 8px;"></i> Análise de Risco (Serasa)
        </h3>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                uploaded = st.file_uploader("Upload Serasa (Múltiplos PDFs)", accept_multiple_files=True, key="up3")
                if uploaded and st.button("Mapear Pendências"):
                    with st.spinner("Analisando riscos e contágio..."):
                        try:
                            # Prompt blindado contra o "sumiço dos zeros"
                            prompt = """
                            Atue como Analista de Risco. Analise os Serasas.
                            ATENÇÃO CRÍTICA: Extraia os valores financeiros EXATAMENTE como estão no documento. NÃO remova zeros à direita e não arredonde.

                            Sua tarefa é extrair o Score, o Risco e criar um Resumo Analítico padronizado e estruturado.

                            O campo "resumo_serasa" deve ser um texto claro e estruturado contendo obrigatoriamente os seguintes tópicos:

                            1. PENDÊNCIAS FINANCEIRAS:
                            - Possui pendências? (Sim/Não)
                            - Que tipo e natureza? (Ex: Protesto, Cheque sem fundo, Pefin, Refin, Dívida Vencida, Falência)
                            - Quais são os credores?
                            - Qual o valor exato envolvido em cada pendência?
                            - Qual a data de cada pendência?

                            2. ANÁLISE CRUZADA (SÓCIOS E EMPRESAS):
                            - Se o documento for PJ: Analise o quadro de sócios. Existe alguma sinalização de pendência apontada para os sócios? (Se sim, emita um alerta recomendando puxar o Serasa PF do sócio específico).
                            - Se o documento for PF: Verifique se há sinalização de pendências nas empresas em que a pessoa figura como sócia (Se sim, emita um alerta recomendando puxar o Serasa PJ da empresa específica).

                            3. PARTICIPAÇÕES SOCIETÁRIAS:
                            - Indique a existência de eventuais outras empresas em que a PJ principal for sócia.
                            - Indique se os sócios (PF ou PJ) possuem participação em outras empresas listadas no documento.

                            Retorne APENAS um JSON válido no seguinte formato:
                            {
                                "score": "Valor exato do score em texto",
                                "risco": "Baixo/Médio/Alto",
                                "resumo_serasa": "Texto estruturado seguindo rigorosamente os 3 tópicos acima. Use quebras de linha (\\n) para separar os tópicos e criar um padrão visual limpo para todas as análises."
                            }
                            """
                            parts = [types.Part.from_bytes(data=f.getvalue(), mime_type='application/pdf') for f in uploaded]
                            parts.append(prompt)
                            res = gemini_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=parts
                            )
                            st.session_state.dados.update(extrair_json_seguro(res.text))
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao processar Serasa: {e}")
        with c2:
            with st.container(border=True):
                c_m1, c_m2 = st.columns(2)
                score_val = c_m1.text_input("Score Extraído", d.get("score", ""))
                risco_val = c_m2.text_input("Nível de Risco", d.get("risco", ""))
                resumo_serasa = st.text_area("Mapeamento de Riscos (Restrições)", d.get("resumo_serasa", ""), height=150)
                
                st.write("") # Respiro visual
                st.write("") # Respiro visual extra                
                # Coluna 1 (Voltar), Coluna 2 (Espaço vazio gigante), Coluna 3 (Avançar)
                c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
                with c_b1:
                    if st.button("Voltar"): 
                        st.session_state.step = 2 # Altere para o passo anterior correto
                        st.rerun()         
                with c_b2:
                    if st.button("Avançar"): 
                        st.session_state.step = 4 # Altere para o próximo passo correto
                        st.rerun()

    # --- PASSO 4: CERTIDÕES ---
    elif st.session_state.step == 4:
        
        # Título padronizado com Bootstrap Icons
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-scales" style="color: #F47920; margin-right: 8px;"></i> Certidões Jurídicas
        </h3>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                uploaded = st.file_uploader("Upload Lote de Certidões (Múltiplos PDFs)", accept_multiple_files=True, key="up4")
                if uploaded and st.button("Auditar Certidões"):
                    with st.spinner("Lendo certidões..."):
                        try:
                            prompt = """Atue como Advogado. Analise as certidões. Extraia APENAS JSON válido: { "resumo_certidoes": "Texto resumindo apontamentos: Cível, Trabalhista, Federal, etc. Cite natureza, valor, data e se é polo ativo/passivo. Se não houver nada, escreva 'Nada Consta'." }"""
                            parts = [types.Part.from_bytes(data=f.getvalue(), mime_type='application/pdf') for f in uploaded]
                            parts.append(prompt)
                            res = gemini_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=parts
                            )
                            st.session_state.dados.update(extrair_json_seguro(res.text))
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao ler certidões: {e}")
        with c2:
            with st.container(border=True):
                resumo_certidoes = st.text_area("Apontamentos Jurídicos", d.get("resumo_certidoes", ""), height=150)
                
                st.write("") # Respiro visual
                st.write("") # Respiro visual extra                
                # Coluna 1 (Voltar), Coluna 2 (Espaço vazio gigante), Coluna 3 (Avançar)
                c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
                with c_b1:
                    if st.button("Voltar"): 
                        st.session_state.step = 3 # Altere para o passo anterior correto
                        st.rerun()         
                with c_b2:
                    if st.button("Avançar"): 
                        st.session_state.step = 5 # Altere para o próximo passo correto
                        st.rerun()

       # --- PASSO 5: CONTÁBIL ---
    elif st.session_state.step == 5:
        
        # Título padronizado com Bootstrap Icons
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-bar-chart-fill" style="color: #F47920; margin-right: 8px;"></i> Auditoria Contábil
        </h3>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            st.info("💡 **Dica:** Faça upload de Balanços Anuais E Balancetes Mensais juntos.")
            uploaded = st.file_uploader("PDFs Contábeis (Últimos 3 anos)", accept_multiple_files=True, key="up5")
            
            if uploaded and st.button("Executar Auditoria Avançada"):
                with st.spinner("Consolidando finanças..."):
                    try:
                        # Resgatando os valores da proposta para a IA calcular o comprometimento
                        aluguel_proposto = st.session_state.dados.get("aluguel", "0")
                        iptu_proposto = st.session_state.dados.get("iptu", "0")
                        
                        # Prompt blindado e robusto para Auditoria Contábil
                        prompt = f"""
                        Atue como Auditor Contábil Sênior. Analise TODOS os documentos financeiros fornecidos (Balanço Patrimonial e DRE, preferencialmente SPED Fiscal) referentes aos últimos 03 anos (sendo 02 anos anteriores fechados + ano atual, ainda que parcial).
                        
                        ATENÇÃO CRÍTICA: Extraia os valores numéricos EXATAMENTE como estão no documento. 
                        NÃO remova zeros à direita, NÃO arredonde. Mantenha os milhares exatos.
                        Retorne os valores financeiros obrigatoriamente como STRING no JSON (ex: "150000.00").
                        
                        TAREFA 1 - EXTRAÇÃO DE DADOS (Ordene cronologicamente do mais antigo para o mais recente):
                        Extraia os seguintes dados para cada período encontrado:
                        - Receita Bruta
                        - Resultado (Lucro ou Prejuízo)
                        - Patrimônio Líquido (Capital Social + Resultado)
                        - Ativo Circulante
                        - Ativo Não Circulante
                        - Passivo Circulante
                        - Passivo Não Circulante
                        - Imobilizado
                        obs: trazer uma tabela com uma demonstração clara e executiva das informações acima (imprescindível).
                        
                        TAREFA 2 - ANÁLISE DO RESULTADO ACUMULADO:
                        Considerando a série histórica da empresa, avalie o Patrimônio Líquido e informe qual o resultado acumulado atual (Lucro ou Prejuízo) e o seu valor.
                        
                        TAREFA 3 - CÁLCULO DE COMPROMETIMENTO:
                        - Valor do Aluguel Proposto: R$ {aluguel_proposto}
                        - Valor do IPTU Proposto: R$ {iptu_proposto}
                        Calcule a Receita Bruta Mensal Média (baseada no último ano/período mais recente).
                        Calcule o percentual de comprometimento usando a relação: ((Aluguel + IPTU) / Receita Bruta Mensal Média) * 100.
                        
                        Retorne APENAS JSON válido no formato exato abaixo:
                        {{
                            "periodos": ["2022", "2023", "2024"],
                            "receita_bruta": ["100000.00", "120000.00", "150000.00"],
                            "resultado": ["10000.00", "-5000.00", "12000.00"],
                            "patrimonio_liquido": ["50000.00", "45000.00", "57000.00"],
                            "ativo_circulante": ["...", "...", "..."],
                            "ativo_nao_circulante": ["...", "...", "..."],
                            "passivo_circulante": ["...", "...", "..."],
                            "passivo_nao_circulante": ["...", "...", "..."],
                            "imobilizado": ["...", "...", "..."],
                            "resultado_acumulado_historico": "Texto descritivo informando se o resultado acumulado atual da série histórica é de lucro ou prejuízo, com base no PL.",
                            "analise_executiva": "Resumo objetivo e conciso da saúde financeira da empresa. OBRIGATÓRIO incluir o cálculo de comprometimento da renda de forma clara."
                        }}
                        """
                        parts = [types.Part.from_bytes(data=f.getvalue(), mime_type='application/pdf') for f in uploaded]
                        parts.append(prompt)
                        
                        res = gemini_client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=parts
                        )
                        st.session_state.dados.update(extrair_json_seguro(res.text))
                        st.rerun()
                    except Exception as e: st.error(f"Erro na auditoria: {e}")

        d = st.session_state.dados
        
        # Correção 1: Ajustadas as chaves para baterem com o JSON do prompt
        if "periodos" in d:
            c_tab, c_graf = st.columns([1, 1.5])
            with c_tab:
                df_fin = pd.DataFrame({
                    "Período": d.get("periodos", []),
                    "Receita": d.get("receita_bruta", []),
                    "Lucro": d.get("resultado", [])
                })
                st.dataframe(df_fin, width="stretch", hide_index=True)
            with c_graf:
                try:
                    valores_grafico = [float(str(x).replace(',', '.')) for x in d.get("resultado", [])]
                    st.bar_chart(pd.DataFrame({"Lucro": valores_grafico}, index=d.get("periodos", [])), color="#F47920")
                except: pass
            
            with st.container(border=True):
                st.markdown("#### Parecer do Auditor IA")
                st.write(d.get("analise_executiva"))
        
        # Correção 2: Os botões foram "desindentados" para fora do IF. Agora aparecem sempre!
        st.write("") # Respiro visual
        st.write("") # Respiro visual extra                
        
        # Coluna 1 (Voltar), Coluna 2 (Espaço vazio gigante), Coluna 3 (Avançar)
        c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
        with c_b1:
            if st.button("Voltar"): 
                st.session_state.step = 4 
                st.rerun()         
        with c_b2:
            if st.button("Avançar"): 
                st.session_state.step = 6 
                st.rerun()

    # --- PASSO 6: IR SÓCIOS ---
    elif st.session_state.step == 6:
        
        # Título padronizado com Bootstrap Icons
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-safe-fill" style="color: #F47920; margin-right: 8px;"></i> Garantia Física (IR Sócios)
        </h3>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                st.info("💡 **Dica:** Faça o upload do IR de TODOS os sócios de uma vez.")
                uploaded = st.file_uploader("Upload IR Sócios (Múltiplos PDFs)", type="pdf", accept_multiple_files=True, key="up6")
                
                if uploaded and st.button("Analisar e Consolidar Patrimônio"):
                    with st.spinner("Analisando declarações e consolidando garantias..."):
                        try:
                            # Prompt robusto para mapear múltiplos sócios e gerar um dossiê único
                            prompt = """
                            Atue como Analista de Crédito Sênior. Analise as Declarações de Imposto de Renda (IR) enviadas.
                            
                            ATENÇÃO CRÍTICA: Extraia os valores numéricos EXATAMENTE como estão no documento. NÃO remova zeros à direita.
                            
                            Sua tarefa é ler todos os arquivos e criar um dossiê patrimonial único e estruturado.
                            1. Identifique o nome de cada titular (sócio).
                            2. Para CADA sócio, liste de forma resumida: Renda Anual, Principais Aplicações Financeiras e Principais Bens Imóveis.
                            3. Ao final, crie uma seção "CONSOLIDADO GLOBAL" somando a renda de todos os sócios e resumindo a força do patrimônio total que servirá como garantia.
                            
                            Retorne APENAS JSON válido no formato: 
                            { 
                                "resumo_patrimonial": "Texto bem estruturado com quebras de linha (\\n), detalhando cada sócio individualmente e finalizando com o Consolidado Global." 
                            }
                            """
                            parts = [types.Part.from_bytes(data=f.getvalue(), mime_type='application/pdf') for f in uploaded]
                            parts.append(prompt)
                            
                            res = gemini_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=parts
                            )
                            st.session_state.dados.update(extrair_json_seguro(res.text))
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao ler IR: {e}")
        with c2:
            with st.container(border=True):
                # Um único campo de texto robusto e alto para receber o dossiê completo
                resumo_patrimonial = st.text_area("Dossiê Patrimonial Consolidado (Todos os Sócios)", d.get("resumo_patrimonial", ""), height=300)
                
                st.write("") # Respiro visual
                st.write("") # Respiro visual extra                
                # Coluna 1 (Voltar), Coluna 2 (Espaço vazio gigante), Coluna 3 (Avançar)
                c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
                with c_b1:
                    if st.button("Voltar"): 
                        st.session_state.step = 5 # Altere para o passo anterior correto
                        st.rerun()         
                with c_b2:
                    if st.button("Avançar"): 
                        st.session_state.step = 7 # Altere para o próximo passo correto
                        st.rerun()

    # --- PASSO 7: PARECER JURÍDICO ---
    elif st.session_state.step == 7:
        
        # Título padronizado com Bootstrap Icons
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-file-earmark-check-fill" style="color: #F47920; margin-right: 8px;"></i> Parecer Final e Veredito
        </h3>
        """, unsafe_allow_html=True)
        
        d = st.session_state.dados # Garantindo que 'd' está acessível
        
        with st.container(border=True):
            if st.button("Gerar Parecer Automático com IA", type="primary"):
                with st.spinner("Advogado IA redigindo parecer cruzando todos os dados do dossiê..."):
                    try:
                        # Prompt atualizado para considerar a nova estrutura de garantias consolidadas
                        import json
                        prompt = f"""Atue como Advogado Sênior de Real Estate e Analista de Risco. 
                        Escreva um Parecer Jurídico de Análise Cadastral para locação baseado estritamente nestes dados consolidados: {json.dumps(d)}. 
                        Discorra com fluidez sobre a empresa, o comprometimento de renda, os apontamentos (Serasa/Certidões) e a força das garantias (IR dos sócios). 
                        Traga insights relevantes e conclua sugerindo APROVADO, REPROVADO ou PENDENTE, justificando o motivo de forma técnica e clara."""
                        
                        res = gemini_client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt
                        )
                        st.session_state.dados["parecer_final"] = res.text
                        st.rerun()
                    except Exception as e: 
                        st.error(f"Erro ao gerar parecer: {e}")
            
            parecer = st.text_area("Edição do Parecer Oficial", d.get("parecer_final", ""), height=300)
            # Salva as edições manuais em tempo real no session_state
            st.session_state.dados["parecer_final"] = parecer
        
        with st.container(border=True):
            c_decisao, c_save = st.columns([1, 1])
            
            with c_decisao:
                decisao = st.selectbox("Veredito Oficial", ["APROVADO", "REPROVADO", "EM ANÁLISE"])
                if decisao == "APROVADO": st.success("🟢 STATUS: APROVADO")
                elif decisao == "REPROVADO": st.error("🔴 STATUS: REPROVADO")
                else: st.warning("🟡 STATUS: EM ANÁLISE")
                
                obs = st.text_input("Observação Curta (Opcional)")
                
                # Salvando a decisão para o PDF
                st.session_state.dados["veredito_final"] = decisao
                st.session_state.dados["recomendacao_final"] = obs
            
            with c_save:
                st.write("")
                st.write("") # Alinhamento vertical com o selectbox
                
                # Botão de Salvar no Banco/Histórico
                if st.button("Salvar no Histórico", width="stretch"):
                    if save_data(d.get("razao_social", "Sem Nome"), decisao, json.dumps(d), obs):
                        st.toast("Salvo com sucesso no histórico!", icon="✅")
                        import time
                        time.sleep(1.5)
                        # limpar_analise() # Descomente se quiser limpar a tela logo após salvar
                
                # Botão de Download do PDF
                st.write("") # Respiro antes do botão de PDF
                try:
                    # 1. Chama a função FPDF correta, passando os 3 argumentos que ela exige!
                    pdf_bytes = gerar_pdf_bytes(st.session_state.dados, decisao, obs)
                    
                    st.download_button(
                        label="Baixar PDF Executivo",
                        data=pdf_bytes,
                        file_name=f"Relatorio_Risco_{d.get('razao_social', 'Empresa')}.pdf",
                        mime="application/pdf",
                        width="stretch",
                        type="primary"
                    )
                except Exception as e: 
                    # 2. Mensagem de erro limpa, sem o fantasma do wkhtmltopdf!
                    st.error(f"Erro ao compilar PDF: {e}")
        
        st.write("") # Respiro visual
        st.write("") # Respiro visual extra
        
        # Coluna 1 (Voltar), Coluna 2 (Espaço gigante), Coluna 3 (Vazia)
        c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])
        
        with c_b1:
            # Botão de voltar alinhado à esquerda
            if st.button("Voltar"): 
                st.session_state.step = 6
                st.rerun()

# ==========================================
# PÁGINA: DASHBOARD EXECUTIVO
# ==========================================
if menu == "Dashboard":
    
    st.markdown(f"""
    <h2 style='color: {COR_SECUNDARIA}; font-weight: 700; margin-bottom: 0px;'>
        <i class="bi bi-bar-chart-fill" style="color: {COR_PRIMARIA};"></i> Dashboard de Performance
    </h2>
    <p style='color: #7F8C8D; margin-bottom: 20px;'>Visão executiva e financeira das análises de risco locatício.</p>
    """, unsafe_allow_html=True)

    # 1. CONEXÃO COM GOOGLE SHEETS E EXTRAÇÃO DE JSON
    @st.cache_data(ttl=300)
    def carregar_dados_reais():
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
            client = gspread.authorize(creds)
            
            planilha = client.open("banco_locacao_paulo_bio").sheet1 
            dados = planilha.get_all_records()
            
            if not dados:
                return pd.DataFrame()
                
            df = pd.DataFrame(dados)
            
            # 1.1 Renomeando as colunas da planilha
            df = df.rename(columns={
                'data_registro': 'Data',
                'cliente': 'Empresa',
                'status': 'Status'
            })
            
            # 1.2 Função BLINDADA para extrair o Aluguel
            import json
            import re
            def extrair_aluguel(json_str):
                try:
                    if not json_str: return 0.0
                    dicionario = json.loads(json_str)
                    valor = dicionario.get('aluguel', 0)
                    
                    # Se já for número, retorna direto
                    if isinstance(valor, (int, float)): return float(valor)
                    
                    # Limpeza inteligente da string
                    valor_str = str(valor).upper().replace('R$', '').strip()
                    
                    # Se tem ponto E vírgula (ex: 1.500,00) -> Padrão BR
                    if '.' in valor_str and ',' in valor_str:
                        valor_str = valor_str.replace('.', '').replace(',', '.')
                    # Se tem SÓ vírgula (ex: 1500,00) -> Padrão BR sem milhar
                    elif ',' in valor_str:
                        valor_str = valor_str.replace(',', '.')
                    # Se tem SÓ ponto (ex: 1500.00) -> Padrão US (deixa como está)
                    
                    # Remove qualquer outro caractere que não seja número ou ponto
                    valor_limpo = re.sub(r'[^\d.]', '', valor_str)
                    return float(valor_limpo) if valor_limpo else 0.0
                except:
                    return 0.0 
            
            df['Valor_Aluguel'] = df['dados_json'].apply(extrair_aluguel)
            
            # 1.3 Tratamento de Data
            df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
            df['Mês_Num'] = df['Data'].dt.to_period('M')
            
            return df
        except Exception as e:
            st.error(f"Erro ao conectar com o Google Sheets: {e}")
            return pd.DataFrame()

    df = carregar_dados_reais()

    if df.empty:
        st.warning("Nenhum dado encontrado na planilha ou erro de conexão.")
    else:
        # 2. FILTRO GLOBAL
        # Ordena cronologicamente do mais recente para o mais antigo
        meses_disponiveis = df.sort_values('Mês_Num', ascending=False)['Mês/Ano'].unique().tolist()
        meses_disponiveis.insert(0, "Todos os Períodos")

        col_filtro, _ = st.columns([1, 3])
        with col_filtro:
            periodo_selecionado = st.selectbox("📅 Filtrar por Período:", meses_disponiveis)

        if periodo_selecionado != "Todos os Períodos":
            df_filtrado = df[df['Mês/Ano'] == periodo_selecionado]
        else:
            df_filtrado = df

        # 3. MÉTRICAS FINANCEIRAS
        total_analises = len(df_filtrado)
        df_aprovados = df_filtrado[df_filtrado['Status'].astype(str).str.upper() == 'APROVADO']
        df_reprovados = df_filtrado[df_filtrado['Status'].astype(str).str.upper() == 'REPROVADO']

        taxa_aprovacao = (len(df_aprovados) / total_analises * 100) if total_analises > 0 else 0
        vgv_aprovado = df_aprovados['Valor_Aluguel'].sum()
        risco_evitado = df_reprovados['Valor_Aluguel'].sum()

        # 4. CARDS EXECUTIVOS
        st.write("")
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.container(border=True).metric("Total de Análises", f"{total_analises}", "Volume bruto")
        with c2:
            st.container(border=True).metric("Taxa de Aprovação", f"{taxa_aprovacao:.1f}%", "Conversão", delta_color="normal")
        with c3:
            st.container(border=True).metric("💰 VGV Aprovado", f"R$ {vgv_aprovado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), "Receita Potencial")
        with c4:
            st.container(border=True).metric("🛡️ Risco Evitado", f"R$ {risco_evitado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), "Reprovações", delta_color="inverse")

        st.divider()

        # 5. GRÁFICOS
        import plotly.express as px # Garantindo o import
        cg1, cg2 = st.columns([1, 2])

        color_map = {
            "APROVADO": COR_PRIMARIA, 
            "REPROVADO": COR_SECUNDARIA, 
            "EM ANÁLISE": COR_TERCIARIA
        }

        with cg1:
            st.markdown("**Proporção de Status**")
            if total_analises > 0:
                df_filtrado_grafico = df_filtrado.copy()
                df_filtrado_grafico['Status'] = df_filtrado_grafico['Status'].astype(str).str.upper()
                
                fig_pie = px.pie(df_filtrado_grafico, names='Status', color='Status', color_discrete_map=color_map, hole=0.4)
                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                st.plotly_chart(fig_pie, width="stretch")
            else:
                st.info("Sem dados para este período.")

        with cg2:
            st.markdown("**VGV Aprovado por Mês (R$)**")
            if len(df_aprovados) > 0:
                # CORREÇÃO CRÍTICA DO PLOTLY: Agrupa, ordena cronologicamente e converte para string
                df_mensal = df_aprovados.groupby('Mês_Num')['Valor_Aluguel'].sum().reset_index()
                df_mensal = df_mensal.sort_values('Mês_Num') 
                df_mensal['Mês'] = df_mensal['Mês_Num'].astype(str) # Evita o erro de JSON serializable do Plotly
                
                fig_bar = px.bar(df_mensal, x='Mês', y='Valor_Aluguel', text_auto='.2s', color_discrete_sequence=[COR_PRIMARIA])
                fig_bar.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
                fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0), xaxis_title="", yaxis_title="Valor (R$)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_bar, width="stretch")
            else:
                st.info("Sem aprovações neste período.")

        # 6. TABELA DE ÚLTIMAS MOVIMENTAÇÕES
        st.write("")
        st.markdown("**Últimas Análises Realizadas**")
        df_display = df_filtrado.sort_values('Data', ascending=False).head(10).copy()
        df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
        df_display['Valor_Aluguel'] = df_display['Valor_Aluguel'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.dataframe(df_display[['Data', 'Empresa', 'Valor_Aluguel', 'Status']], width="stretch", hide_index=True)

# ==========================================
# PÁGINA: HISTÓRICO DE ANÁLISES
# ==========================================
elif menu == "Histórico":
    
    st.markdown(f"""
    <h2 style='color: {COR_SECUNDARIA}; font-weight: 700; margin-bottom: 0px;'>
        <i class="bi bi-clock-history" style="color: {COR_PRIMARIA};"></i> Histórico de Análises
    </h2>
    <p style='color: #7F8C8D; margin-bottom: 20px;'>Consulte, baixe PDFs ou gerencie as análises anteriores.</p>
    """, unsafe_allow_html=True)

    # 1. CONEXÃO E MAPEAMENTO DE LINHAS PARA EXCLUSÃO SEGURA
    @st.cache_data(ttl=60)
    def carregar_dados_historico():
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
            client = gspread.authorize(creds)
            
            planilha = client.open("banco_locacao_paulo_bio").sheet1 
            dados = planilha.get_all_records()
            
            if not dados:
                return pd.DataFrame(), None
                
            df = pd.DataFrame(dados)
            
            df['linha_planilha'] = range(2, len(df) + 2)
            
            df = df.rename(columns={
                'data_registro': 'Data',
                'cliente': 'Empresa',
                'status': 'Status'
            })
            
            return df, client
        except Exception as e:
            st.error(f"Erro ao conectar com o Google Sheets: {e}")
            return pd.DataFrame(), None

    df_hist, gsheets_client = carregar_dados_historico()

    if df_hist.empty:
        st.info("Nenhum registro encontrado no histórico.")
    else:
        # 2. PAINEL DE BUSCA E FILTROS (Sem emojis, visual limpo)
        c_busca, c_filtro = st.columns([2, 1])
        with c_busca:
            termo_busca = st.text_input("Buscar por Empresa/Cliente:", "")
        with c_filtro:
            status_opcoes = df_hist['Status'].unique().tolist()
            filtro_status = st.multiselect("Filtrar por Status:", status_opcoes, default=status_opcoes)

        # Aplicando filtros
        df_filtrado = df_hist[df_hist['Status'].isin(filtro_status)]
        if termo_busca:
            df_filtrado = df_filtrado[df_filtrado['Empresa'].str.contains(termo_busca, case=False, na=False)]

        st.write("")

        # 3. DATA GRID INTERATIVO
        st.markdown("**Selecione uma análise na tabela abaixo para ver opções:**")
        
        df_exibicao = df_filtrado[['linha_planilha', 'Data', 'Empresa', 'Status', 'obs_final', 'dados_json']].copy()
        
        evento_selecao = st.dataframe(
            df_exibicao[['Data', 'Empresa', 'Status', 'obs_final']], 
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        # 4. PAINEL DE DETALHES E AÇÕES
        linhas_selecionadas = evento_selecao.selection.rows
        
        if len(linhas_selecionadas) > 0:
            st.divider()
            
            indice_real = linhas_selecionadas[0]
            linha_dados = df_exibicao.iloc[indice_real]
            
            # Título com Bootstrap Icon
            st.markdown(f"""
            <h4 style='color: {COR_SECUNDARIA}; margin-bottom: 15px;'>
                <i class="bi bi-file-earmark-text" style="color: {COR_PRIMARIA}; margin-right: 8px;"></i> 
                Detalhes: {linha_dados['Empresa']}
            </h4>
            """, unsafe_allow_html=True)
            
            c_info, c_acoes = st.columns([2, 1])
            
            with c_info:
                st.write(f"**Data da Análise:** {linha_dados['Data']}")
                st.write(f"**Veredito:** {linha_dados['Status']}")
                st.write(f"**Observação:** {linha_dados['obs_final']}")
            
            with c_acoes:
                # AÇÃO 1: GERAR PDF (Usando ícone Material nativo do Streamlit)
                try:
                    import json
                    dados_sessao_recuperados = json.loads(linha_dados['dados_json'])
                    pdf_bytes = gerar_pdf_executivo(dados_sessao_recuperados)
                    
                    st.download_button(
                        label="Baixar PDF Executivo",
                        data=pdf_bytes,
                        file_name=f"Relatorio_{linha_dados['Empresa']}.pdf",
                        mime="application/pdf",
                        width="stretch",
                        type="primary",
                        icon=":material/download:" # Ícone moderno do Google
                    )
                except Exception as e:
                    st.error("Erro ao recuperar PDF. Os dados podem estar incompletos.")
                
                st.write("")
                
                # AÇÃO 2: EXCLUIR COM CONFIRMAÇÃO
                if "confirmar_exclusao" not in st.session_state:
                    st.session_state.confirmar_exclusao = False
                    
                if not st.session_state.confirmar_exclusao:
                    # Botão de excluir com ícone de lixeira do Google
                    if st.button("Excluir Registro", width="stretch", icon=":material/delete:"):
                        st.session_state.confirmar_exclusao = True
                        st.rerun()
                else:
                    st.warning("Tem certeza? Esta ação não pode ser desfeita.")
                    c_sim, c_nao = st.columns(2)
                    with c_sim:
                        # Ícone de check
                        if st.button("Sim, excluir", width="stretch", icon=":material/check_circle:"):
                            try:
                                planilha = gsheets_client.open("banco_locacao_paulo_bio").sheet1
                                planilha.delete_rows(int(linha_dados['linha_planilha']))
                                
                                st.cache_data.clear()
                                st.session_state.confirmar_exclusao = False
                                st.success("Registro excluído com sucesso!")
                                import time
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir: {e}")
                    with c_nao:
                        # Ícone de cancelar
                        if st.button("Cancelar", width="stretch", icon=":material/cancel:"):
                            st.session_state.confirmar_exclusao = False
                            st.rerun()

# --- TELA: CONFIGURAÇÕES ---
elif menu == "Configurações":
    st.markdown("## ⚙️ Configurações do Sistema")
    with st.container(border=True):
        st.markdown("Módulo em desenvolvimento. Aqui você poderá ajustar parâmetros da IA e limites de crédito no futuro.")
