import streamlit as st
from google import genai
from google.genai import types
import json
import pandas as pd
from datetime import datetime
import time
from fpdf import FPDF
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
        except: st.markdown("<h1 style='text-align: center; color: #F47920;'>🏢</h1>", unsafe_allow_html=True)
            
    st.markdown("<h3 style='text-align: center; color: #2C3E50;'>Portal de Análise de Crédito</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        with st.container(border=True):
            st.markdown("#### 🔒 Acesso Restrito")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                # Verifica se o usuário existe e a senha bate
                if usuario in st.secrets["passwords"] and senha == st.secrets["passwords"][usuario]:
                    st.session_state.logged_in = True
                    
                    # --- A MÁGICA ACONTECE AQUI ---
                    # Busca o nome e email nos secrets. Se não achar, usa um padrão.
                    st.session_state.usuario_logado = st.secrets.get("usuarios_nomes", {}).get(usuario, usuario.title())
                    st.session_state.email_usuario = st.secrets.get("usuarios_emails", {}).get(usuario, f"{usuario}@paulobio.com.br")
                    
                    st.rerun()
                else: 
                    st.error("Acesso negado. Verifique usuário e senha.")
    return False

@st.cache_resource
def salvar_dados_planilha(dados, decisao):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        
        planilha = client.open("banco_locacao_paulo_bio").sheet1 
        
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        empresa = dados.get("empresa", dados.get("pretendente", "Não informado"))
        dados_json = json.dumps(dados) 
        
        planilha.append_row([data_atual, empresa, decisao, dados_json, ""])
        return True
    except Exception as e:
        raise e

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

def formatar_valor_contabil(valor):
    """Converte valores em parênteses (15000) para formato negativo - 15000"""
    v_str = str(valor).strip()
    if v_str.startswith('(') and v_str.endswith(')'):
        numero_limpo = v_str[1:-1].strip()
        return f"- {numero_limpo}"
    return v_str

def gerar_pdf_bytes(dados, decisao):
    def limpa(texto):
        # Ignora emojis e limpa espaços
        return str(texto).encode('latin-1', 'ignore').decode('latin-1').strip()

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
    
    def check_space(space_needed):
        if pdf.get_y() + space_needed > 277:
            pdf.add_page()

    # ==========================================
    # PÁGINA 1: CAPA DINÂMICA PREMIUM
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
    
    # Lógica da Capa Dinâmica (O quadrado estica conforme o texto)
    empresa_nome = dados.get('empresa', dados.get('pretendente', 'Não informado'))
    imovel_nome = dados.get('imovel', 'Não informado')
    
    pdf.set_font("Arial", 'B', 14)
    w_empresa = pdf.get_string_width(limpa(empresa_nome))
    pdf.set_font("Arial", '', 10)
    w_imovel = pdf.get_string_width(limpa(f"Imóvel: {imovel_nome}"))
    
    max_w = max(w_empresa, w_imovel) + 40 # 40mm de margem interna
    if max_w > 170: max_w = 170 # Trava na largura máxima da página A4
    x_rect = (210 - max_w) / 2
    
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(x_rect, pdf.get_y(), max_w, 25, 'F')
    pdf.set_y(pdf.get_y() + 5)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, limpa(empresa_nome), ln=True, align='C')
    
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, limpa(f"Imóvel: {imovel_nome}"), ln=True, align='C')
    
    pdf.set_y(-40)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, limpa(f"São Paulo - SP, {datetime.now().strftime('%d/%m/%Y')}"), ln=True, align='C')

    # ==========================================
    # PÁGINA 2: CONTEÚDO
    # ==========================================
    pdf.add_page()
    
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
        pdf.multi_cell(0, 6, limpa(value), align='J') # Adicionado Justificado ABNT

    # --- 1. RESUMO DO NEGÓCIO ---
    title("1. Resumo do Negócio", 60)
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
    
    # Inclusão das Condições e Informações Gerais
    condicoes = dados.get('condicoes_gerais', '')
    info_gerais = dados.get('info_gerais_manuais', '')
    
    if condicoes and condicoes.lower() != 'não informado':
        pdf.ln(2)
        row("Condições Gerais:", condicoes)
    if info_gerais and info_gerais.lower() != 'não informado':
        pdf.ln(2)
        row("Informações Gerais:", info_gerais)

    # --- 2. DADOS CADASTRAIS ---
    title("2. Qualificação Societária e Restrições", 50)
    row("Razão Social:", dados.get('empresa', '-'))
    row("CNPJ:", dados.get('cnpj', '-'))
    row("Abertura (Idade):", dados.get('data_abertura', '-'))
    row("Capital Social:", dados.get('capital_social', '-'))
    row("Quadro Societário:", dados.get('socios_participacao', '-'))
    pdf.ln(3)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 6, limpa("Apontamentos e Restrições (Serasa):"), ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Puxa as chaves exatas geradas no Passo 3 (ajuste os nomes das chaves se no seu código estiver diferente)
    score = str(dados.get('score_serasa', 'Não informado'))
    risco = str(dados.get('risco_serasa', 'Não informado'))
    mapeamento = str(dados.get('mapeamento_dividas', dados.get('resumo_serasa', 'Nada consta.')))
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(30, 5, limpa("Score Serasa:"), border=0)
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, limpa(score), border=0, ln=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(30, 5, limpa("Risco Serasa:"), border=0)
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, limpa(risco), border=0, ln=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, limpa("Mapeamento de Riscos (Restrições):"), border=0, ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 5, limpa(mapeamento), align='J')

      # --- 3. AUDITORIA FINANCEIRA ---
    title("3. Auditoria Financeira", 60)
    periodos = dados.get("periodos", [])
    receitas = dados.get("receita_bruta", [])
    lucros = dados.get("resultado", [])

    # FUNÇÃO INJETADA: Trata os parênteses contábeis antes de converter para float
    def trata_negativo_contabil(v):
        v_str = str(v).strip()
        if v_str.startswith('(') and v_str.endswith(')'):
            return "-" + v_str[1:-1].strip()
        return v_str

    if periodos and len(periodos) > 0:
        # Tabela Original Mantida
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(30, 6, limpa("PERÍODO"), 0, 0)
        pdf.cell(60, 6, limpa("RECEITA BRUTA"), 0, 0)
        pdf.cell(60, 6, limpa("RESULTADO LÍQUIDO"), 0, 1)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(2)

        # Aplica a regra no max_val para o gráfico de barras não quebrar
        max_val = max([safe_float(trata_negativo_contabil(r)) for r in receitas] + [1])

        pdf.set_font("Arial", '', 9)
        for i in range(len(periodos)):
            try:
                # APLICAÇÃO DA REGRA: Limpa os parênteses antes do safe_float
                rec_val = safe_float(trata_negativo_contabil(receitas[i]))
                luc_val = safe_float(trata_negativo_contabil(lucros[i]))

                pdf.set_xy(20, pdf.get_y() + 2)
                y_linha = pdf.get_y()
                pdf.cell(30, 6, limpa(periodos[i]), 0, 0)
                
                pdf.cell(60, 6, limpa(f"R$ {rec_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")), 0, 0)
                
                # Se for negativo, a cor fica vermelha automaticamente pelo seu código original!
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

        # NOVA MATRIZ DE BALANÇO PATRIMONIAL
        pdf.ln(8)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(0, 6, limpa("MATRIZ DE BALANÇO PATRIMONIAL"), ln=True)
        pdf.set_font("Arial", 'B', 8)

        largura_col = 170 / (len(periodos) + 1)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(largura_col, 6, limpa("INDICADOR"), border=1, align='C', fill=True)
        for p in periodos:
            pdf.cell(largura_col, 6, limpa(str(p)), border=1, align='C', fill=True)
        pdf.ln()

        indicadores = [
            ("Patrimônio Líquido", "patrimonio_liquido"),
            ("Ativo Circulante", "ativo_circulante"),
            ("Ativo Não Circulante", "ativo_nao_circulante"),
            ("Passivo Circulante", "passivo_circulante"),
            ("Passivo Não Circulante", "passivo_nao_circulante"),
            ("Imobilizado", "imobilizado")
        ]

        pdf.set_font("Arial", '', 8)
        for nome_ind, chave_ind in indicadores:
            pdf.cell(largura_col, 6, limpa(nome_ind), border=1)
            valores = dados.get(chave_ind, [])
            for i in range(len(periodos)):
                val = valores[i] if i < len(valores) else "Não encontrado"
                if val and val != "Não encontrado" and val != "-" and str(val).strip() != "":
                    try:
                        # APLICAÇÃO DA REGRA NA MATRIZ
                        val_limpo = trata_negativo_contabil(val)
                        val_f = safe_float(val_limpo)
                        val_str = f"R$ {val_f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        
                        # Deixa o texto vermelho na matriz se for negativo
                        if val_f < 0:
                            pdf.set_text_color(200, 0, 0)
                        else:
                            pdf.set_text_color(0, 0, 0)
                    except:
                        val_str = str(val)
                        pdf.set_text_color(0, 0, 0)
                else:
                    val_str = "Não encontrado"
                    pdf.set_text_color(0, 0, 0)
                    
                pdf.cell(largura_col, 6, limpa(val_str), border=1, align='C')
                pdf.set_text_color(0, 0, 0) # Reseta a cor para a próxima célula
            pdf.ln()

    pdf.ln(5)
    row("Comprometimento:", f"{dados.get('comprometimento_renda', '0')}% (Aluguel+IPTU sobre Receita)")

    # --- 4. CAPACIDADE DE GARANTIA ---
    garantia_tipo = str(dados.get('garantia', '')).lower()

    # Lógica Condicional Correta: Puxa a matriz certa baseada na garantia
    if "fiador" in garantia_tipo:
        title("4. Capacidade de Garantia (Fiador)", 40)
        matriz = dados.get("matriz_fiadores", {})
        conclusao = dados.get("conclusao_fiador", "")
    else:
        title("4. Capacidade de Garantia (Sócios)", 40)
        matriz = dados.get("matriz_socios", {})
        conclusao = dados.get("conclusao_socio", "")

    if matriz and isinstance(matriz, dict) and "nomes" in matriz:
        nomes = matriz.get("nomes", [])
        
        # AJUSTE DE LARGURA: Reduzido para 170mm total (igual ao item 3)
        largura_total = 170
        largura_indicador = 55
        largura_dados = (largura_total - largura_indicador) / len(nomes) if len(nomes) > 0 else 40
        
        pdf.set_font("Arial", 'B', 8)
        pdf.set_fill_color(240, 240, 240)
        
        # --- CABEÇALHO ---
        pdf.set_x(20) # Indentação para alinhar com o resto do documento
        pdf.cell(largura_indicador, 6, limpa("Indicador"), 1, 0, 'L', fill=True)
        for nome in nomes:
            pdf.cell(largura_dados, 6, limpa(nome), 1, 0, 'C', fill=True)
        pdf.ln()
        
        # --- LINHAS DE DADOS ---
        pdf.set_font("Arial", '', 8)
        linhas = [
            ("Rendimentos tributáveis (IRPF)", matriz.get("rendimentos_tributaveis", [])),
            ("Rendimentos não tributáveis (IRPF)", matriz.get("rendimentos_nao_tributaveis", [])),
            ("Renda mensal média oficial", matriz.get("renda_mensal_media", [])),
            ("Renda mensal atual", matriz.get("renda_mensal_atual", [])),
            ("Patrimônio declarado", matriz.get("patrimonio", []))
        ]
        
        for titulo_linha, valores in linhas:
            pdf.set_x(20) # Mantém a indentação em todas as linhas
            pdf.cell(largura_indicador, 6, limpa(titulo_linha), 1, 0, 'L')
            for i in range(len(nomes)):
                val = valores[i] if i < len(valores) else "-"
                pdf.cell(largura_dados, 6, limpa(str(val)), 1, 0, 'C')
            pdf.ln()
            
        # Linha extra do Aluguel Pretendido
        aluguel_str = f"R$ {dados.get('aluguel', '0')}"
        pdf.set_x(20)
        pdf.cell(largura_indicador, 6, limpa("Aluguel pretendido"), 1, 0, 'L')
        for i in range(len(nomes) - 1):
            pdf.cell(largura_dados, 6, "-", 1, 0, 'C')
        pdf.cell(largura_dados, 6, limpa(aluguel_str), 1, 1, 'C')
        
        pdf.ln(5)
        
        # --- CONCLUSÃO ---
        if conclusao:
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(0, 5, limpa("Conclusão Prática:"), border=0, ln=True)
            pdf.set_font("Arial", '', 9)
            pdf.multi_cell(0, 5, limpa(conclusao), align='J')
            
    else:
        # Fallback de segurança
        pdf.set_font("Arial", '', 10)
        texto_fallback = dados.get('parecer_fiador', dados.get('resumo_patrimonial', 'Análise não informada.'))
        pdf.multi_cell(0, 5, limpa(texto_fallback), align='J')

    # --- 5. CHECKLIST DE DOCUMENTAÇÃO ANALISADA ---
    title("5. Checklist de Documentação Analisada", 60)

    # Recupera o checklist salvo no session_state (ou um dicionário vazio se não houver)
    checklist = dados.get("checklist_docs", {})

    # Lista oficial de todos os passos da esteira
    passos_oficiais = [
        "Passo 0 (Contrato Social)",
        "Passo 1 (Proposta)",
        "Passo 1 (Fiador)",
        "Passo 2 (Ficha Cadastral)",
        "Passo 3 (Serasa)",
        "Passo 4 (Certidões)",
        "Passo 5 (Contábil)",
        "Passo 6 (IR Sócios)"
    ]

    pdf.set_font("Arial", '', 9)

    for passo in passos_oficiais:
        arquivos = checklist.get(passo, [])
        
        if arquivos:
            # Tem arquivo: Colchete com X (Verde)
            pdf.set_text_color(46, 204, 113) # Verde
            pdf.cell(10, 5, "[ X ]", border=0)
            pdf.set_text_color(0, 0, 0) # Volta pro preto
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(0, 5, limpa(passo) + ":", border=0, ln=True)
            
            # Lista os nomes dos arquivos
            pdf.set_font("Arial", 'I', 8)
            pdf.set_text_color(100, 100, 100) # Cinza escuro
            for arq in arquivos:
                pdf.cell(10, 4, "", border=0) # Espaçamento (identação)
                pdf.cell(0, 4, "- " + limpa(arq), border=0, ln=True)
            pdf.set_text_color(0, 0, 0) # Volta pro preto
            pdf.set_font("Arial", '', 9)
            
        else:
            # Não tem arquivo: Colchete vazio (Vermelho/Cinza)
            pdf.set_text_color(231, 76, 60) # Vermelho
            pdf.cell(10, 5, "[   ]", border=0)
            pdf.set_text_color(0, 0, 0) # Volta pro preto
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(0, 5, limpa(passo) + ":", border=0, ln=True)
            
            # Mensagem de ausência
            pdf.set_font("Arial", 'I', 8)
            pdf.set_text_color(150, 150, 150) # Cinza claro
            pdf.cell(10, 4, "", border=0) # Espaçamento
            pdf.cell(0, 4, limpa("- Nenhum documento anexado nesta etapa."), border=0, ln=True)
            pdf.set_text_color(0, 0, 0) # Volta pro preto
            pdf.set_font("Arial", '', 9)
            
        pdf.ln(2) # Espaçinho entre os passos
        
    pdf.ln(5) # Espaço antes do próximo grande bloco

    # --- 5. PARECER JURÍDICO ---
    title("6. Parecer Jurídico", 70) 
    pdf.set_font("Arial", '', 10)
    parecer = dados.get('parecer_oficial', 'Parecer não gerado.')
    pdf.multi_cell(0, 5, limpa(parecer), align='J') # ABNT
    pdf.ln(10)
    
    check_space(40)
    
    # Remove emojis na hora de imprimir o veredito
    decisao_limpa = decisao.replace("🟢", "").replace("🟠", "").replace("🔴", "").strip()
    
    is_aprovado = "APROVADO" in decisao_limpa.upper()
    is_reprovado = "REPROVADO" in decisao_limpa.upper()
    
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
    pdf.cell(170, 10, limpa(decisao_limpa.upper()), align='C', ln=True)
    
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(80, 80, 80)

    return pdf.output(dest='S').encode('latin-1')

# --- 4. FLUXO PRINCIPAL ---
if not check_password(): st.stop()
API_KEY = st.secrets["GOOGLE_API_KEY"]

gemini_client = genai.Client(api_key=API_KEY)

if 'step' not in st.session_state: st.session_state.step = 0
if 'dados' not in st.session_state: st.session_state.dados = {}
if "checklist_docs" not in st.session_state.dados:
    st.session_state.dados["checklist_docs"] = {}

# --- SIDEBAR COM OPTION MENU (O SEGREDO DO SAAS) ---
with st.sidebar:
    # Removido o st.write("") do topo para ganhar espaço
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        try: st.image("logoOPB.png", width="stretch") 
        except: st.markdown("<h2 style='text-align: center; color: #F47920;'>🏢</h2>", unsafe_allow_html=True)

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
             
    # Linha divisória fina
    st.divider()
    
    # 1. BOTÃO REINICIAR (Agora alinhado corretamente com o st.sidebar)
    if st.button("Reiniciar Análise", width="stretch"):
        # Limpa apenas os dados da análise e volta pro passo 1
        st.session_state.dados = {}
        st.session_state.step = 1 
        st.rerun()

    # 2. ÁREA LOGADA (Totalmente fora do botão reiniciar)
    nome_completo = st.session_state.get('usuario_logado', 'Usuário')
    email_usuario = st.session_state.get('email_usuario', 'usuario@paulobio.com.br')
    primeiro_nome = nome_completo.split()[0] if nome_completo else "Usuário"
    
    with st.popover(f":material/account_circle: {primeiro_nome}", width="stretch"):
        st.markdown(f"""
        <div style="text-align: center; padding-top: 5px; padding-bottom: 5px;">
            <p style="color: #2C3E50; font-weight: 700; font-size: 18px; margin: 0;">{nome_completo}</p>
            <p style="color: #7F8C8D; font-size: 14px; margin: 0;">{email_usuario}</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider() 
        
        # Botão de Sair
        if st.button(":material/logout: Sair", key="btn_logout", width="stretch"):
            st.session_state.logged_in = False  # Usa a mesma chave do check_password
            st.session_state.dados = {}
            st.session_state.step = 1
            st.rerun()

    # --- ÁREA DE DESENVOLVEDOR (TESTE MOCK) ---
    st.divider()
    st.caption("🛠️ Modo Desenvolvedor")
    if st.button("🧪 Injetar Dados de Teste (Mock)", width="stretch"):
        st.session_state.dados = {
            # Passo 0 (Contrato Social + Aditivos)
            "empresa": "TechNova Soluções em TI LTDA",
            "cnpj": "12.345.678/0001-99",
            "endereco_empresa": "Av. Paulista, 1000, Conj 50, São Paulo - SP",
            "data_abertura": "5 Anos e 3 Meses",
            "capital_social": "R$ 500.000,00",
            "socios_participacao": "João Silva (60%), Maria Souza (40%)",
            "administrador": "João Silva",
            "informacoes_adicionais": "Alteração Contratual 01 (2021): Entrada da sócia Maria Souza. Alteração 02 (2023): Aumento de capital social de R$ 100k para R$ 500k.",
            
            # Passo 1 (Proposta)
            "pretendente": "TechNova Soluções em TI LTDA",
            "atividade": "Desenvolvimento de Software",
            "imovel": "Galpão Logístico - Módulo 3 - Condomínio Alpha",
            "prazo": "36 meses",
            "data_inicio": "01/05/2026",
            "carencia": "3 meses (Isenção de aluguel, paga apenas IPTU)",
            "aluguel": "15000.00",
            "iptu": "1200.00",
            "garantia": "Fiador",
            "condicoes_gerais": "Reajuste anual pelo IPCA. Multa rescisória de 3 aluguéis proporcionais. Seguro incêndio obrigatório.",
            "info_gerais_manuais": "Cliente solicitou autorização para instalação de mezanino metálico. Proprietário de acordo, desde que com ART.",
            "parecer_fiador": "O fiador apresentado (Sr. Roberto Carlos) possui renda mensal comprovada de R$ 45.000,00 e 3 imóveis quitados na capital que somam R$ 3.500.000,00. Capacidade financeira excelente e totalmente compatível para garantir a locação de R$ 15.000,00.",
            
            # Passo 2 (Ficha Cadastral)
            "ref_locaticias": "Paga aluguel atual de R$ 8.000 na Imobiliária XYZ sem atrasos.",
            "ref_comerciais": "Dell Computadores - (11) 4000-1111 / Kalunga - (11) 3333-2222",
            "ref_bancarias": "Itaú - Ag 1234 - Gerente Carlos (11) 99999-8888",
            
            # Passo 3 e 4 (Serasa e Certidões)
            "score": "850",
            "risco": "Baixo",
            "resumo_serasa": "1. PENDÊNCIAS FINANCEIRAS: Nenhuma pendência financeira, protesto ou dívida vencida registrada para a PJ.\n2. ANÁLISE CRUZADA: Sócios não apresentam apontamentos que ofereçam risco de contágio.\n3. PARTICIPAÇÕES: Empresa não possui participação em outras sociedades.",
            "resumo_certidoes": "Certidões Negativas de Débitos (CND) Federal, Estadual e Municipal válidas. Nada consta na Justiça do Trabalho.",
            "resumo_apontamentos": "Nada consta no Serasa para a PJ. Sócios sem restrições. Certidões negativas estaduais e federais válidas.",
            
            # Passo 5 (Contábil + Matriz Financeira)
            "periodos": ["2021", "2022", "2023"],
            "receita_bruta": ["1200000.00", "1800000.00", "2500000.00"],
            "resultado": ["150000.00", "280000.00", "450000.00"],
            "patrimonio_liquido": ["500000.00", "780000.00", "1230000.00"],
            "ativo_circulante": ["300000.00", "450000.00", "800000.00"],
            "ativo_nao_circulante": ["250000.00", "380000.00", "500000.00"],
            "passivo_circulante": ["50000.00", "50000.00", "70000.00"],
            "passivo_nao_circulante": ["0.00", "0.00", "0.00"],
            "imobilizado": ["200000.00", "300000.00", "400000.00"],
            "evolucao_yoy": "Crescimento contínuo e expressivo. A receita bruta cresceu 50% em 2022 e 38% em 2023. O lucro líquido acompanhou a escalada, crescendo 86% e 60% respectivamente.",
            "analise_executiva": "Empresa apresenta balanço extremamente saudável, com alta liquidez (Ativo Circulante cobre o Passivo Circulante em mais de 10 vezes). O comprometimento da renda com a locação pretendida é de apenas 7.7%, indicando risco financeiro quase nulo.",
            "comprometimento_renda": "7.7",
            
            # Passo 6 (IR Sócios)
            "resumo_patrimonial": "1. Sócio João Silva: Renda declarada de R$ 350.000/ano. Evolução patrimonial positiva, passando de R$ 1.2M (2022) para R$ 1.5M (2023), justificada pela renda. Possui 2 imóveis quitados.\n2. Sócia Maria Souza: Renda declarada de R$ 200.000/ano. Evolução estável, com R$ 500k em aplicações financeiras de alta liquidez.\nCONSOLIDADO GLOBAL: Patrimônio forte e líquido, garantindo conforto adicional à operação.",
            
            # Passo 7 (Parecer IA e Oficial)
            "parecer_final": "A empresa apresenta excelente saúde financeira, com crescimento de receita contínuo nos últimos 3 anos e margem de lucro sólida. O comprometimento de renda para a locação é inferior a 8%, o que representa baixíssimo risco. A garantia apresentada (Fiador) foi validada e possui lastro patrimonial superior a 200 vezes o valor do aluguel. Recomenda-se a aprovação integral da operação.",
            "parecer_oficial": "A empresa apresenta excelente saúde financeira, com crescimento de receita contínuo nos últimos 3 anos e margem de lucro sólida. O comprometimento de renda para a locação é inferior a 8%, o que representa baixíssimo risco. A garantia apresentada (Fiador) foi validada e possui lastro patrimonial superior a 200 vezes o valor do aluguel. Recomenda-se a aprovação integral da operação."
        }
        # Pula direto para o Passo 7 (Veredito Final) para você já ver o PDF
        st.session_state.step = 7
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
        d = st.session_state.dados # Atalho para facilitar
        
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-file-earmark-person-fill" style="color: #F47920; margin-right: 8px;"></i> Contrato Social e Aditivos
        </h3>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                # AJUSTE 1: accept_multiple_files=True
                uploaded = st.file_uploader("Upload Contrato e Aditivos (PDFs)", type="pdf", accept_multiple_files=True, key="up0")
                if uploaded and st.button("Extrair Dados Societários"):
                    
                    # CORREÇÃO: Usando a variável 'uploaded' que foi definida acima
                    st.session_state.dados["checklist_docs"]["Passo 0 (Contrato Social)"] = [f.name for f in uploaded]
                    
                    with st.spinner("Analisando Documentos..."):
                        try:
                            # AJUSTE 2: Prompt atualizado para aditivos
                            prompt = """Analise os documentos societários (Contrato Social e eventuais Aditivos) em ordem cronológica.
                            Extraia o quadro societário ATUALIZADO e um resumo das alterações.
                            Extraia APENAS JSON válido, valores exatos como texto: 
                            { 
                                "empresa": "", 
                                "cnpj": "", 
                                "endereco_empresa": "Extrair o endereço completo da sede da empresa. Se não achar, retorne 'Não informado'",
                                "data_abertura": "", 
                                "capital_social": "", 
                                "socios_participacao": "Quadro societário final/atualizado", É ESTRITAMENTE PROIBIDO retornar arrays [ ] ou objetos { } neste campo,
                                "administrador": "",
                                "informacoes_adicionais": "Breve resumo cronológico das alterações contratuais (ex: entrada/saída de sócios, aumento de capital). Se não houver aditivos, escreva 'Documento original sem aditivos identificados.'"
                            }"""
                            parts = [types.Part.from_bytes(data=f.getvalue(), mime_type='application/pdf') for f in uploaded]
                            parts.append(prompt)
                            
                            res = gemini_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=parts
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
                foto_sede = st.text_input("Endereço da Sede", d.get("foto_sede", d.get("endereco_empresa", "")))
                
                # AJUSTE 2: Novo campo na UI
                info_adicionais = st.text_area("Informações Adicionais (Resumo de Aditivos)", d.get("informacoes_adicionais", ""))
                st.session_state.dados["informacoes_adicionais"] = info_adicionais
                
                st.write("") 
                st.write("") 
                
                c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])
                with c_b2:
                    if st.button("Avançar"): 
                        st.session_state.step = 1
                        st.rerun()

    # --- PASSO 1: PROPOSTA ---
    elif st.session_state.step == 1:
        d = st.session_state.dados
        
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
                    
                    # CORREÇÃO: 'uploaded' é um arquivo único, então usamos [uploaded.name]
                    st.session_state.dados["checklist_docs"]["Passo 1 (Proposta)"] = [uploaded.name]
                    
                    with st.spinner("Lendo..."):
                        try:
                            # AJUSTE 3: Novos campos no prompt
                            prompt = """Analise a proposta de locação e extraia os dados solicitados.
                            REGRA CRÍTICA: Você DEVE retornar um JSON válido contendo EXATAMENTE todas as chaves abaixo. Se uma informação não existir no documento, preencha o valor com 'Não informado'. NUNCA omita nenhuma chave.
                            REGRA CRÍTICA DE ESCALONAMENTO: Se a proposta apresentar valores de aluguel progressivos (ex: 1º ano X, 2º ano Y, 3º ano Z), você DEVE extrair APENAS o valor referente ao último ano (o valor mais alto e final) para o campo 'aluguel'.
                            { 
                                "pretendente": "Nome da empresa ou pessoa", 
                                "atividade": "Ramo de atividade", 
                                "imovel": "Extrair EXATAMENTE o endereço do imóvel objeto da locação. REGRA CRÍTICA: NUNCA preencha com o endereço da própria empresa pretendente.", 
                                "prazo": "Prazo total do contrato", 
                                "data_inicio": "Data de início da locação",
                                "carencia": "Período de carência ou isenção",
                                "aluguel": "Valor exato", 
                                "iptu": "REGRA CRÍTICA: Se o texto disser '10 parcelas de R$1000' ou '10x de 1000', extraia APENAS o valor da parcela mensal (ex: '1000.00').", 
                                "garantia": "Tipo de garantia (ex: Fiador, Seguro Fiança, Caução)",
                                "condicoes_gerais": "Resumo de índices de reajuste, multas ou condições especiais. PROIBIDO usar formatação Markdown (asteriscos, hashtags). Escreva em texto corrido limpo. Se não houver, escreva 'Não informado'."
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
                st.session_state.dados["pretendente"] = pretendente
                
                atividade = st.text_input("Atividade a ser realizada", d.get("atividade", ""))
                st.session_state.dados["atividade"] = atividade
                
                imovel = st.text_input("Endereço do Imóvel", d.get("imovel", ""))
                st.session_state.dados["imovel"] = imovel
                
                c_p1, c_p2, c_p3 = st.columns(3)
                prazo = c_p1.text_input("Prazo", d.get("prazo", ""))
                st.session_state.dados["prazo"] = prazo
                
                data_inicio = c_p2.text_input("Data de Início", d.get("data_inicio", ""))
                st.session_state.dados["data_inicio"] = data_inicio
                
                carencia = c_p3.text_input("Carência", d.get("carencia", ""))
                st.session_state.dados["carencia"] = carencia
                
                c_val1, c_val2 = st.columns(2)
                aluguel = c_val1.text_input("Aluguel (R$)", d.get("aluguel", "0"))
                st.session_state.dados["aluguel"] = aluguel
                
                iptu = c_val2.text_input("IPTU (R$)", d.get("iptu", "0"))
                st.session_state.dados["iptu"] = iptu
                
                garantia = st.text_input("Garantia Proposta", d.get("garantia", ""))
                st.session_state.dados["garantia"] = garantia
                
                condicoes = st.text_area("Condições Gerais (Reajustes/Multas)", d.get("condicoes_gerais", ""))
                st.session_state.dados["condicoes_gerais"] = condicoes
                
                # AJUSTE 3: Campo manual livre
                info_gerais = st.text_area("Informações Gerais (Anotações Livres)", d.get("info_gerais_manuais", ""))
                st.session_state.dados["info_gerais_manuais"] = info_gerais

        # AJUSTE 4: Lógica dinâmica do Fiador
        if "fiador" in str(d.get("garantia", "")).lower():
            st.write("")
            st.markdown("""
            <h4 style="color: #2C3E50; font-weight: 600; margin-bottom: 10px;">
                <i class="bi bi-person-bounding-box" style="color: #F47920; margin-right: 8px;"></i> Análise do Fiador
            </h4>
            """, unsafe_allow_html=True)
            
            cf1, cf2 = st.columns([1, 2])
            with cf1:
                with st.container(border=True):
                    up_fiador = st.file_uploader("Upload Docs do Fiador (IR, Matrícula)", type="pdf", accept_multiple_files=True, key="up_fiador")
                    if up_fiador and st.button("Analisar Capacidade do Fiador"):
                        
                        # NOVO: Adicionando os documentos do Fiador no checklist
                        st.session_state.dados["checklist_docs"]["Passo 1 (Fiador)"] = [f.name for f in up_fiador]
                        
                        with st.spinner("Analisando Fiador..."):
                            try:
                                prompt_fiador = f"""
                                Atue como Analista de Crédito Sênior e Especialista em Garantias Locatícias.
                                Analise os documentos anexados referentes ao(s) fiador(es) ou sócio(s). 
                                O aluguel pretendido é R$ {st.session_state.dados.get('aluguel', '0')}.

                                Siga RIGOROSAMENTE as seguintes regras de extração para montar uma matriz comparativa:
                                1. Identifique todos os indivíduos.
                                2. Extraia os Rendimentos Tributáveis anuais do último IRPF.
                                3. Extraia os Rendimentos Não Tributáveis anuais do último IRPF.
                                4. Calcule a Renda Mensal Média Oficial (soma dos rendimentos anuais dividida por 12).
                                5. Identifique a Renda Mensal Atual (se houver holerites/prolabores recentes anexados, caso contrário use '-').
                                6. Extraia o Patrimônio Total declarado no último IRPF.
                                7. Na última posição dos arrays de valores, SEMPRE coloque a SOMA (Combinado) de todos os indivíduos.

                                Para a conclusão, siga EXATAMENTE este formato e tom de voz (adaptando os valores):
                                "Patrimonialmente, [sim/não], eles demonstram força para atuar como fiadores, porque o patrimônio conjunto de R$ [X] é [expressivo/insuficiente] em relação ao aluguel proposto.
                                Sob a ótica de renda mensal, a situação é [apertada/confortável/inviável]. A renda combinada fica em aproximadamente [X]x o aluguel, o que indica capacidade de pagamento [existente com folga limitada / excelente / insuficiente]."

                                Retorne APENAS um JSON válido no formato exato abaixo:
                                {{
                                    "matriz_fiadores": {{
                                        "nomes": ["Nome 1", "Nome 2", "Combinado"],
                                        "rendimentos_tributaveis": ["R$ X", "R$ Y", "R$ Soma"],
                                        "rendimentos_nao_tributaveis": ["R$ X", "R$ Y", "R$ Soma"],
                                        "renda_mensal_media": ["R$ X", "R$ Y", "R$ Soma"],
                                        "renda_mensal_atual": ["R$ X", "-", "R$ Soma"],
                                        "patrimonio": ["R$ X", "R$ Y", "R$ Soma"]
                                    }},
                                    "conclusao_fiador": "Texto da conclusão nos moldes solicitados."
                                }}
                                """
                                parts = [types.Part.from_bytes(data=f.getvalue(), mime_type='application/pdf') for f in up_fiador]
                                parts.append(prompt_fiador)
                                res_fiador = gemini_client.models.generate_content(model='gemini-2.5-flash', contents=parts)
                                st.session_state.dados.update(extrair_json_seguro(res_fiador.text))
                                st.rerun()
                            except Exception as e: st.error(f"Erro: {e}")
            with cf2:
                with st.container(border=True):
                    parecer_fiador = st.text_area("Parecer sobre o Fiador", d.get("conclusao_fiador", ""), height=150)
                    st.session_state.dados["conclusão_fiador"] = parecer_fiador

        st.write("") 
        st.write("")                
        c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
        with c_b1:
            if st.button("Voltar"): 
                st.session_state.step = 0 
                st.rerun()         
        with c_b2:
            if st.button("Avançar"): 
                st.session_state.step = 2 
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
                    st.session_state.dados["checklist_docs"]["Passo 2 (Ficha Cadastral)"] = [uploaded.name]
                    with st.spinner("Lendo..."):
                        try:
                            prompt = """Extraia APENAS JSON válido resumindo as referências: 
                            { 
                                "ref_locaticias": "Paga aluguel? Onde? Valor? Proprietário? Se estiver em branco ou não existir, retorne EXATAMENTE 'Não encontrado'.", 
                                "ref_comerciais": "Extrair as referências comerciais OBRIGATORIAMENTE no formato: 'Nome da Empresa - Telefone'. Ex: 'Fornecedor X - (11) 9999-9999'. Se estiver em branco ou não existir, retorne EXATAMENTE 'Não encontrado'.", 
                                "ref_bancarias": "Extrair as referências bancárias OBRIGATORIAMENTE no formato: 'Banco - Agência - Telefone/Contato do Gerente'. Se estiver em branco ou não existir, retorne EXATAMENTE 'Não encontrado'." 
                            }"""
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
        d = st.session_state.dados
        
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-shield-lock-fill" style="color: #F47920; margin-right: 8px;"></i> Análise de Risco (Serasa)
        </h3>
        """, unsafe_allow_html=True)
        
        # AJUSTE 5: Trava de Divergência Visual
        if d.get("alerta_divergencia_serasa"):
            st.error(f"🚨 **ALERTA DE DIVERGÊNCIA DE DADOS:** {d.get('alerta_divergencia_serasa')}")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                uploaded = st.file_uploader("Upload Serasa (Múltiplos PDFs)", accept_multiple_files=True, key="up3")
                if uploaded and st.button("Mapear Pendências"):
                    st.session_state.dados["checklist_docs"]["Passo 3 (Serasa)"] = [f.name for f in uploaded]
                    with st.spinner("Analisando riscos e contágio..."):
                        try:
                            # AJUSTE 5: Prompt de Compliance
                            prompt = f"""
                            Atue como Analista de Risco. 
                            REGRA DE COMPLIANCE: Estes documentos devem pertencer à empresa '{d.get('empresa', '')}' (CNPJ: {d.get('cnpj', '')}) ou a seus sócios. Se os documentos principais forem de uma empresa totalmente diferente, preencha o campo 'alerta_divergencia_serasa' informando o erro. Se estiver correto, deixe vazio.

                            INSTRUÇÕES DE ANÁLISE (Use isso como base mental para elaborar o resumo):
                            1. PENDÊNCIAS FINANCEIRAS: Verifique se possui pendências. Se sim, detalhe o tipo (Protesto, Pefin, Refin, etc.), credores, valores exatos e datas.
                            2. ANÁLISE CRUZADA: 
                               - Se o documento for PJ: Analise o quadro de sócios. Existe alguma sinalização de pendência para os sócios? (Se sim, recomende puxar o Serasa PF do sócio).
                               - Se o documento for PF: Verifique se há pendências nas empresas em que a pessoa é sócia (Se sim, recomende puxar o Serasa PJ).
                            3. PARTICIPAÇÕES SOCIETÁRIAS: Indique a existência de outras empresas em que a PJ principal for sócia, ou se os sócios possuem participação em outras empresas.

                            REGRA DE FORMATAÇÃO CRÍTICA PARA O RESUMO:
                            O campo 'mapeamento_dividas' DEVE ser um resumo executivo em TEXTO CORRIDO (parágrafo único) sintetizando todas as informações analisadas acima. 
                            É ESTRITAMENTE PROIBIDO usar formato de perguntas e respostas, tópicos, quebras de linha ou formatação Markdown (asteriscos, traços). Seja direto e profissional.

                            Retorne APENAS um JSON válido no seguinte formato exato:
                            {{
                                "alerta_divergencia_serasa": "",
                                "score_serasa": "Valor exato do score",
                                "risco_serasa": "Baixo/Médio/Alto",
                                "mapeamento_dividas": "Texto corrido em parágrafo único contendo a síntese executiva das pendências, análise cruzada e participações societárias."
                            }}
                            """
                            parts = [types.Part.from_bytes(data=f.getvalue(), mime_type='application/pdf') for f in uploaded]
                            parts.append(prompt)
                            res = gemini_client.models.generate_content(model='gemini-2.5-flash', contents=parts)
                            st.session_state.dados.update(extrair_json_seguro(res.text))
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao processar Serasa: {e}")
        with c2:
            with st.container(border=True):
                c_m1, c_m2 = st.columns(2)
                score_val = c_m1.text_input("Score Extraído", d.get("score_serasa", ""))
                risco_val = c_m2.text_input("Nível de Risco", d.get("risco_serasa", ""))
                resumo_serasa = st.text_area("Mapeamento de Riscos (Restrições)", d.get("mapeamento_dividas", ""), height=250)
                
                st.write("") 
                st.write("")               
                c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
                with c_b1:
                    if st.button("Voltar"): 
                        st.session_state.step = 2 
                        st.rerun()         
                with c_b2:
                    if st.button("Avançar"): 
                        st.session_state.step = 4 
                        st.rerun()

   # --- PASSO 4: CERTIDÕES ---
    elif st.session_state.step == 4:
        d = st.session_state.dados
        
        st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <h3 style="color: #2C3E50; font-weight: 700; margin-bottom: 20px;">
            <i class="bi bi-scales" style="color: #F47920; margin-right: 8px;"></i> Certidões Jurídicas
        </h3>
        """, unsafe_allow_html=True)
        
        # AJUSTE 5: Trava de Divergência Visual
        if d.get("alerta_divergencia_certidoes"):
            st.error(f"🚨 **ALERTA DE DIVERGÊNCIA DE DADOS:** {d.get('alerta_divergencia_certidoes')}")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                uploaded = st.file_uploader("Upload Lote de Certidões (Múltiplos PDFs)", accept_multiple_files=True, key="up4")
                if uploaded and st.button("Auditar Certidões"):
                    st.session_state.dados["checklist_docs"]["Passo 4 (Certidões)"] = [f.name for f in uploaded]
                    with st.spinner("Lendo certidões..."):
                        try:
                            prompt = f"""Atue como Advogado. 
                            REGRA DE COMPLIANCE: Verifique se as certidões pertencem à empresa '{d.get('empresa', '')}' (CNPJ: {d.get('cnpj', '')}). Se forem de terceiros não relacionados, preencha 'alerta_divergencia_certidoes'.
                            PROIBIDO usar formatação Markdown (asteriscos, hashtags, traços). Escreva em texto corrido, formato executivo e parágrafos limpos.
                            
                            Extraia APENAS JSON válido: 
                            {{ 
                                "alerta_divergencia_certidoes": "",
                                "resumo_certidoes": "Texto resumindo apontamentos: Cível, Trabalhista, Federal, etc. Cite natureza, valor, data e se é polo ativo/passivo. Se não houver nada, escreva 'Nada Consta'." 
                            }}"""
                            parts = [types.Part.from_bytes(data=f.getvalue(), mime_type='application/pdf') for f in uploaded]
                            parts.append(prompt)
                            res = gemini_client.models.generate_content(model='gemini-2.5-flash', contents=parts)
                            st.session_state.dados.update(extrair_json_seguro(res.text))
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao ler certidões: {e}")
        with c2:
            with st.container(border=True):
                resumo_certidoes = st.text_area("Apontamentos Jurídicos", d.get("resumo_certidoes", ""), height=150)
                
                st.write("") 
                st.write("")               
                c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
                with c_b1:
                    if st.button("Voltar"): 
                        st.session_state.step = 3 
                        st.rerun()         
                with c_b2:
                    if st.button("Avançar"): 
                        st.session_state.step = 5 
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
        
        # AJUSTE 5: Trava de Divergência Visual
        if d.get("alerta_divergencia_contabil"):
            st.error(f"🚨 **ALERTA DE DIVERGÊNCIA DE DADOS:** {d.get('alerta_divergencia_contabil')}")

        with st.container(border=True):
            st.info("💡 **Dica:** Faça upload de Balanços Anuais E Balancetes Mensais juntos.")
            uploaded = st.file_uploader("PDFs Contábeis (Últimos 3 anos)", accept_multiple_files=True, key="up5")
            
            if uploaded and st.button("Executar Auditoria Avançada"):
                with st.spinner("Consolidando finanças..."):
                    try:
                        # Resgatando os valores da proposta para a IA calcular o comprometimento
                        aluguel_proposto = st.session_state.dados.get("aluguel", "0")
                        iptu_proposto = st.session_state.dados.get("iptu", "0")
                        
                        # Prompt blindado unindo sua lógica com a estrutura JSON necessária
                        prompt = f"""
                        Atue como um analista financeiro sênior e Auditor Contábil. Em anexo, estão os Balanços Patrimoniais e as DREs de 2024 e 2025 da empresa.
                        O aluguel pretendido é R$ {aluguel_proposto} e o IPTU é R$ {iptu_proposto}.
                        A empresa analisada deve ser '{d.get('empresa', '')}' (CNPJ: {d.get('cnpj', '')}). Se for diferente, preencha o campo 'alerta_divergencia_contabil'.

                        Sua tarefa é extrair os dados contábeis e elaborar um resumo financeiro. Siga rigorosamente o passo a passo abaixo:

                        Parte 1: Extração de Dados
                        Busque os dados cruzando as informações da DRE e do Balanço Patrimonial. Extraia os valores exatos para 2024 e 2025 das seguintes linhas:
                        Receita Bruta, EBITDA, Resultado do Exercício (Lucro/Prejuízo), Patrimônio Líquido, Ativo Circulante, Ativo Não Circulante, Passivo Circulante, Passivo Não Circulante, Imobilizado.
                        Calcule o comprometimento da renda: ((Aluguel + IPTU) / (Receita Bruta Anual 2025 / 12)) * 100.

                        Parte 2: Parecer do Auditor IA (analise_executiva)
                        Escreva dois parágrafos de análise respondendo: Considerando a série histórica da empresa, qual o resultado acumulado atual (lucro ou prejuízo)?
                        Para escrever esta análise, aplique obrigatoriamente a seguinte lógica interpretativa:
                        - Identifique e cite que em 2024 a empresa possuía um expressivo 'Prejuízo Acumulado' (cite o valor exato do Balanço), o que deixou o Patrimônio Líquido negativo.
                        - Identifique e cite que em 2025 houve uma reversão, gerando um 'Lucro' alto no Resultado do Exercício (cite o valor exato da DRE/Balanço).
                        - Conclua a redação explicando a matemática financeira ocorrida: explique que o lucro de 2025 foi suficiente para absorver todo o prejuízo histórico, zerando o déficit e fazendo com que o Patrimônio Líquido de 2025 fechasse positivo, refletindo exatamente o valor do Capital Social integralizado.

                        Retorne APENAS um JSON válido no formato exato abaixo. É ESTRITAMENTE PROIBIDO retornar qualquer texto fora do JSON.
                        {{
                            "alerta_divergencia_contabil": "Motivo da divergência de CNPJ/Empresa ou vazio se estiver ok",
                            "periodos": ["2024", "2025"],
                            "receita_bruta": ["Valor 2024", "Valor 2025"],
                            "ebitda": ["Valor 2024", "Valor 2025"],
                            "resultado": ["Valor 2024", "Valor 2025"],
                            "patrimonio_liquido": ["Valor 2024", "Valor 2025"],
                            "ativo_circulante": ["Valor 2024", "Valor 2025"],
                            "ativo_nao_circulante": ["Valor 2024", "Valor 2025"],
                            "passivo_circulante": ["Valor 2024", "Valor 2025"],
                            "passivo_nao_circulante": ["Valor 2024", "Valor 2025"],
                            "imobilizado": ["Valor 2024", "Valor 2025"],
                            "evolucao_yoy": "Texto executivo sobre crescimento/queda ano a ano",
                            "analise_executiva": "Os dois parágrafos da Parte 2 (Análise do Resultado Acumulado Histórico) seguindo a lógica interpretativa exigida.",
                            "comprometimento_renda": "Apenas o número do cálculo de comprometimento (ex: 15.5)"
                        }}
                        """
                        parts = [types.Part.from_bytes(data=f.getvalue(), mime_type='application/pdf') for f in uploaded]
                        parts.append(prompt)
                        
                        res = gemini_client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=parts
                        )
                        st.session_state.dados.update(extrair_json_seguro(res.text))
                        
                        # Checklist atualizado SOMENTE se a extração der certo!
                        st.session_state.dados["checklist_docs"]["Passo 5 (Contábil)"] = [f.name for f in uploaded]
                        
                        st.rerun()
                    except Exception as e: st.error(f"Erro na auditoria: {e}")

        d = st.session_state.dados
        
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
                    with st.spinner("Analisando declarações e gerando parecer final..."):
                        try:
                            prompt = f"""
                            Atue como Analista de Crédito Sênior e Especialista em Garantias Locatícias.
                            Analise as Declarações de Imposto de Renda (IRPF) anexadas referentes aos sócios da empresa.
                            
                            DADOS GLOBAIS DA OPERAÇÃO JÁ COLETADOS:
                            - Aluguel pretendido: R$ {st.session_state.dados.get('aluguel', '0')}
                            - Score Serasa da Empresa: {st.session_state.dados.get('score_serasa', 'Não informado')}
                            - Risco Serasa: {st.session_state.dados.get('risco_serasa', 'Não informado')}
                            - Comprometimento da Renda (Auditoria Contábil): {st.session_state.dados.get('comprometimento_renda', '0')}%
                            
                            Siga RIGOROSAMENTE as seguintes regras de extração para montar uma matriz comparativa:
                            1. Identifique todos os indivíduos (sócios).
                            2. Extraia os Rendimentos Tributáveis e Não Tributáveis anuais do último IRPF.
                            3. Calcule a Renda Mensal Média Oficial (soma dos rendimentos anuais dividida por 12).
                            4. Identifique a Renda Mensal Atual (se houver prolabores recentes, caso contrário use '-').
                            5. Extraia o Patrimônio Total declarado no último IRPF (Bens e Direitos).
                            6. Na última posição dos arrays, SEMPRE coloque a SOMA (Combinado).

                            PRÉ-PARECER JURÍDICO GLOBAL (parecer_final):
                            Com base nos DADOS GLOBAIS fornecidos acima E na análise atual dos sócios, escreva um parecer final recomendando explicitamente: APROVADO, APROVADO COM RESSALVA ou REPROVADO. Justifique com base no Serasa, saúde contábil e força patrimonial.

                            Retorne APENAS um JSON válido no formato exato abaixo:
                            {{
                                "matriz_socios": {{
                                    "nomes": ["Nome Sócio 1", "Nome Sócio 2", "Combinado"],
                                    "rendimentos_tributaveis": ["R$ X", "R$ Y", "R$ Soma"],
                                    "rendimentos_nao_tributaveis": ["R$ X", "R$ Y", "R$ Soma"],
                                    "renda_mensal_media": ["R$ X", "R$ Y", "R$ Soma"],
                                    "renda_mensal_atual": ["R$ X", "-", "R$ Soma"],
                                    "patrimonio": ["R$ X", "R$ Y", "R$ Soma"]
                                }},
                                "conclusao_socio": "Texto da conclusão sobre os sócios.",
                                "parecer_final": "Veredito global (Aprovado/Reprovado) unindo Serasa, Contábil e Sócios."
                            }}
                            """
                            parts = [types.Part.from_bytes(data=f.getvalue(), mime_type='application/pdf') for f in uploaded]
                            parts.append(prompt)
                            
                            res = gemini_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=parts
                            )
                            
                            # Atualiza os dados com as duas novas chaves (resumo_patrimonial e parecer_final)
                            dados_extraidos = extrair_json_seguro(res.text)
                            st.session_state.dados.update(dados_extraidos)
                            st.session_state.dados["checklist_docs"]["Passo 6 (IR Sócios)"] = [f.name for f in uploaded]
                            
                            # Já deixa o parecer oficial pré-preenchido com o rascunho da IA para o Passo 7
                            if "parecer_final" in dados_extraidos:
                                st.session_state.dados["parecer_final"] = dados_extraidos["parecer_final"]
                                
                            # AJUSTE: Checklist atualizado SOMENTE se a extração der certo e com a nomenclatura exata do PDF
                            st.session_state.dados["checklist_docs"]["IR Sócios"] = [f.name for f in uploaded]
                                
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao ler IR e gerar parecer: {e}")
        with c2:
            with st.container(border=True):
                # Puxando a chave correta: "conclusao_analise"
                conclusao_analise = st.text_area("Conclusão da Análise (Sócios)", st.session_state.dados.get("conclusao_socio", ""), height=150)
                st.session_state.dados["conclusao_socio"] = conclusao_analise
                
                # Puxando a chave correta: "parecer_final"
                parecer_final = st.text_area("Pré-Parecer Jurídico Gerado", st.session_state.dados.get("parecer_final", ""), height=300)
                st.session_state.dados["parecer_final"] = parecer_final
                
                st.write("") # Respiro visual
                st.write("") # Respiro visual extra                
                
                # Coluna 1 (Voltar), Coluna 2 (Espaço vazio gigante), Coluna 3 (Avançar)
                c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
                with c_b1:
                    if st.button("Voltar"): 
                        st.session_state.step = 5 # Volta para o Contábil
                        st.rerun()         
                with c_b2:
                    if st.button("Avançar"): 
                        # Avança para o Passo 7
                        st.session_state.step = 7 
                        st.rerun()

    elif st.session_state.step == 7:
        st.subheader("Passo 7: Parecer e Veredito Final")

        # 1. Rascunho da IA (Apenas leitura)
        st.markdown("Análise Gerada pela IA")
        st.info(st.session_state.dados.get("parecer_final", "Parecer não gerado."))

        # 2. Campo Oficial do Advogado (Editável, vai pro PDF)
        st.markdown("Parecer Jurídico")
        st.caption("Copie trechos da IA acima ou escreva seu parecer final aqui. ⚠️ **DICA:** Após editar, clique fora da caixa de texto para o sistema registrar a alteração antes de gerar o PDF.")
        
        # Correção: Gerenciamento de estado blindado para o Text Area
        if "input_parecer" not in st.session_state:
            st.session_state.input_parecer = st.session_state.dados.get("parecer_oficial", st.session_state.dados.get("parecer_final", ""))

        st.text_area(
            "Texto do Parecer", 
            height=300,
            label_visibility="collapsed",
            key="input_parecer"
        )
        
        # Garante que o dicionário receba o texto atualizado do widget instantaneamente
        st.session_state.dados["parecer_oficial"] = st.session_state.input_parecer

        st.divider()

        # 3. Veredito (Horizontal para não cortar)
        st.markdown("Veredito da Operação")
        decisao = st.radio(
            "Selecione o veredito final:",
            options=["🟢 APROVADO", "🟠 APROVADO COM RESSALVAS", "🔴 REPROVADO"],
            horizontal=True,
            label_visibility="collapsed"
        )

        st.divider()
        
        # 4. Botões de Ação
        c_b1, c_b2 = st.columns([1, 4])
        with c_b1:
            if st.button("Voltar"): 
                st.session_state.step = 6
                st.rerun()
        with c_b2:
            pdf_bytes = gerar_pdf_bytes(st.session_state.dados, decisao)
            
            st.download_button(
                label="GERAR RELATÓRIO EXECUTIVO (PDF)",
                data=pdf_bytes,
                file_name=f"Relatorio_Risco_{st.session_state.dados.get('empresa', 'Cliente')}.pdf",
                mime="application/pdf",
                type="primary",
                width="stretch"
            )
            
        st.write("") # Respiro
        
        # Botão para salvar na planilha (Alimenta o Dashboard Global)
        if st.button("Salvar Análise no Histórico", width="stretch"):
            with st.spinner("Salvando dados de forma segura no Google Sheets..."):
                try:
                    salvar_dados_planilha(st.session_state.dados, decisao)
                    st.cache_data.clear()
                    st.success("✅ Análise salva com sucesso no histórico! O Dashboard foi atualizado.")
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")

# 
# PÁGINA: DASHBOARD EXECUTIVO
# 
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
                    
                    if isinstance(valor, (int, float)): return float(valor)
                    
                    valor_str = str(valor).upper().replace('R$', '').strip()
                    
                    if '.' in valor_str and ',' in valor_str:
                        valor_str = valor_str.replace('.', '').replace(',', '.')
                    elif ',' in valor_str:
                        valor_str = valor_str.replace(',', '.')
                    
                    valor_limpo = re.sub(r'[^\d.]', '', valor_str)
                    return float(valor_limpo) if valor_limpo else 0.0
                except:
                    return 0.0 
            
            df['Valor_Aluguel'] = df['dados_json'].apply(extrair_aluguel)
            
            # 1.3 Tratamento de Data (Inteligente: aceita BR e US)
            df['Data_Limpa'] = df['Data'].astype(str).str.split(' ').str[0]
            
            def converter_data_segura(data_str):
                try:
                    if '-' in data_str:
                        return pd.to_datetime(data_str, format='%Y-%m-%d')
                    else:
                        return pd.to_datetime(data_str, format='%d/%m/%Y')
                except:
                    return pd.NaT
                    
            df['Data'] = df['Data_Limpa'].apply(converter_data_segura)
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
        # 2. FILTRO GLOBAL (Com Calendário Interativo)
        st.markdown(f"""
        <div style='display: flex; align-items: center; margin-bottom: 10px;'>
            <i class="bi bi-calendar-event-fill" style="color: {COR_PRIMARIA}; font-size: 1.2rem; margin-right: 8px;"></i>
            <span style="color: white; font-size: 1.1rem; font-weight: 500;">Filtrar por Período</span>
        </div>
        """, unsafe_allow_html=True)

        c_opt, c_cal, _ = st.columns([1.5, 1.5, 2])
        
        with c_opt:
            # Botão de rádio horizontal elegante
            tipo_filtro = st.radio("Filtro", ["Todos os Períodos", "Mês Específico"], horizontal=True, label_visibility="collapsed")
            
        with c_cal:
            if tipo_filtro == "Mês Específico":
                # Abre o calendário nativo. O usuário escolhe qualquer dia do mês desejado.
                data_selecionada = st.date_input("Selecione uma data do mês desejado:", format="DD/MM/YYYY", label_visibility="collapsed")
                # O código converte a data escolhida (ex: 15/03/2026) para o formato do nosso filtro (03/2026)
                periodo_selecionado = data_selecionada.strftime('%m/%Y')
            else:
                periodo_selecionado = "Todos os Períodos"

        # Aplica o filtro na base de dados
        if periodo_selecionado != "Todos os Períodos":
            df_filtrado = df[df['Mês/Ano'] == periodo_selecionado]
        else:
            df_filtrado = df

        # 3. MÉTRICAS FINANCEIRAS (CORRIGIDO: Ignorando emojis na matemática)
        total_analises = len(df_filtrado)
        
        # Cria uma coluna limpa temporária só para a matemática funcionar perfeitamente
        status_limpo = df_filtrado['Status'].astype(str).str.replace('🟢', '').str.replace('🟠', '').str.replace('🔴', '').str.strip().str.upper()
        
        # Considera tanto APROVADO quanto APROVADO COM RESSALVAS para o VGV
        df_aprovados = df_filtrado[status_limpo.isin(['APROVADO', 'APROVADO COM RESSALVAS'])]
        df_reprovados = df_filtrado[status_limpo == 'REPROVADO']

        taxa_aprovacao = (len(df_aprovados) / total_analises * 100) if total_analises > 0 else 0
        vgv_aprovado = df_aprovados['Valor_Aluguel'].sum()
        risco_evitado = df_reprovados['Valor_Aluguel'].sum()

        # 4. CARDS EXECUTIVOS
        st.write("")
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #3498DB;">
                <p style="color: #AAB7B8; margin-bottom: 5px; font-size: 14px;"><i class="bi bi-clipboard-data"></i> Total de Análises</p>
                <h3 style="color: white; margin: 0; font-size: 24px;">{total_analises}</h3>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #9B59B6;">
                <p style="color: #AAB7B8; margin-bottom: 5px; font-size: 14px;"><i class="bi bi-percent"></i> Taxa de Aprovação</p>
                <h3 style="color: white; margin: 0; font-size: 24px;">{taxa_aprovacao:.1f}%</h3>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #2ECC71;">
                <p style="color: #AAB7B8; margin-bottom: 5px; font-size: 14px;"><i class="bi bi-cash-coin" style="color: #2ECC71;"></i> VGL Aprovado</p>
                <h3 style="color: white; margin: 0; font-size: 24px;">R$ {vgv_aprovado:,.2f}</h3>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #E74C3C;">
                <p style="color: #AAB7B8; margin-bottom: 5px; font-size: 14px;"><i class="bi bi-shield-fill-x" style="color: #E74C3C;"></i> Risco Evitado</p>
                <h3 style="color: white; margin: 0; font-size: 24px;">R$ {risco_evitado:,.2f}</h3>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

        st.divider()

        # 5. GRÁFICOS
        import plotly.express as px 
        cg1, cg2 = st.columns([1, 2])

        # Adicionado APROVADO COM RESSALVAS no mapa de cores
        color_map = {
            "APROVADO": COR_PRIMARIA, 
            "APROVADO COM RESSALVAS": "#F39C12", 
            "REPROVADO": COR_SECUNDARIA, 
            "EM ANÁLISE": COR_TERCIARIA
        }

        with cg1:
            st.markdown("**Proporção de Status**")
            if total_analises > 0:
                df_filtrado_grafico = df_filtrado.copy()
                # Limpa os emojis para o gráfico reconhecer as cores exatas do color_map
                df_filtrado_grafico['Status'] = df_filtrado_grafico['Status'].astype(str).str.replace('🟢', '').str.replace('🟠', '').str.replace('🔴', '').str.strip().str.upper()
                
                fig_pie = px.pie(df_filtrado_grafico, names='Status', color='Status', color_discrete_map=color_map, hole=0.4)
                fig_pie.update_layout(
                    margin=dict(t=0, b=0, l=0, r=0), 
                    showlegend=True, 
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',  
                    font=dict(color='white')       
                )
                st.plotly_chart(fig_pie, width="stretch")
            else:
                st.info("Sem dados para este período.")

        with cg2:
            st.markdown("**VGL Aprovado por Mês (R$)**")
            
            meses_oficiais = ['mar/26', 'abr/26', 'mai/26', 'jun/26', 'jul/26', 'ago/26', 'set/26', 'out/26', 'nov/26', 'dez/26']
            
            mapa_meses = {
                '03/2026': 'mar/26', '04/2026': 'abr/26', '05/2026': 'mai/26', 
                '06/2026': 'jun/26', '07/2026': 'jul/26', '08/2026': 'ago/26', 
                '09/2026': 'set/26', '10/2026': 'out/26', '11/2026': 'nov/26', 
                '12/2026': 'dez/26'
            }

            if len(df_aprovados) > 0:
                df_mensal = df_aprovados.groupby('Mês/Ano')['Valor_Aluguel'].sum().reset_index()
                
                df_mensal['Mês_Formatado'] = df_mensal['Mês/Ano'].map(mapa_meses)
                df_mensal = df_mensal.dropna(subset=['Mês_Formatado'])
                
                df_completo = pd.DataFrame({'Mês_Formatado': meses_oficiais})
                df_final = pd.merge(df_completo, df_mensal, on='Mês_Formatado', how='left').fillna(0)
                
                fig_bar = px.bar(df_final, x='Mês_Formatado', y='Valor_Aluguel', text_auto='.2s', color_discrete_sequence=[COR_PRIMARIA])
                fig_bar.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
                fig_bar.update_layout(
                    margin=dict(t=0, b=0, l=0, r=0), 
                    xaxis_title="", 
                    yaxis_title="Valor (R$)", 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',  
                    font=dict(color='white')       
                )
                fig_bar.update_xaxes(type='category', categoryorder='array', categoryarray=meses_oficiais, showgrid=False)
                fig_bar.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig_bar, width="stretch")
            else:
                df_vazio = pd.DataFrame({'Mês_Formatado': meses_oficiais, 'Valor_Aluguel': [0]*10})
                fig_bar = px.bar(df_vazio, x='Mês_Formatado', y='Valor_Aluguel', color_discrete_sequence=[COR_PRIMARIA])
                fig_bar.update_layout(
                    margin=dict(t=0, b=0, l=0, r=0), xaxis_title="", yaxis_title="Valor (R$)", 
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white')
                )
                fig_bar.update_xaxes(type='category', categoryorder='array', categoryarray=meses_oficiais, showgrid=False)
                fig_bar.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig_bar, width="stretch")

        # 6. TABELA DE ÚLTIMAS MOVIMENTAÇÕES
        st.write("")
        st.markdown("**Últimas Análises Realizadas**")
        df_display = df_filtrado.sort_values('Data', ascending=False).head(10).copy()
        df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
        df_display['Valor_Aluguel'] = df_display['Valor_Aluguel'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        styled_df = df_display[['Data', 'Empresa', 'Valor_Aluguel', 'Status']].style.set_properties(**{
            'background-color': COR_TERCIARIA,
            'color': 'white',
            'border-color': 'rgba(255,255,255,0.1)'
        })
        
        st.dataframe(styled_df, width="stretch", hide_index=True)

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

    # 1. CONEXÃO E MAPEAMENTO (Retorna APENAS os dados, sem o client para não quebrar o cache)
    @st.cache_data(ttl=60)
    def carregar_dados_historico():
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
            client = gspread.authorize(creds)
            
            planilha = client.open("banco_locacao_paulo_bio").sheet1 
            dados = planilha.get_all_records()
            
            if not dados:
                return pd.DataFrame()
                
            df = pd.DataFrame(dados)
            
            df['linha_planilha'] = range(2, len(df) + 2)
            
            df = df.rename(columns={
                'data_registro': 'Data',
                'cliente': 'Empresa',
                'status': 'Status'
            })
            
            return df
        except Exception as e:
            st.error(f"Erro ao conectar com o Google Sheets: {e}")
            return pd.DataFrame()

    df_hist = carregar_dados_historico()

    if df_hist.empty:
        st.info("Nenhum registro encontrado no histórico.")
    else:
        # 2. PAINEL DE BUSCA E FILTROS
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
        st.markdown("**Selecione uma ou mais análises na tabela abaixo para ver opções:**")
        
        df_exibicao = df_filtrado[['linha_planilha', 'Data', 'Empresa', 'Status', 'obs_final', 'dados_json']].copy()
        
        evento_selecao = st.dataframe(
            df_exibicao[['Data', 'Empresa', 'Status', 'obs_final']], 
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row"
        )

        # 4. PAINEL DE DETALHES E AÇÕES
        linhas_selecionadas = evento_selecao.selection.rows
        
        # SELECIONOU APENAS 1 ITEM
        if len(linhas_selecionadas) == 1:
            st.divider()
            
            indice_real = linhas_selecionadas[0]
            linha_dados = df_exibicao.iloc[indice_real]
            
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
                # --- NOVO: EXIBIÇÃO DO CHECKLIST DE DOCUMENTOS ---
                import json
                dados_sessao_recuperados = json.loads(linha_dados['dados_json'])
                checklist = dados_sessao_recuperados.get("checklist_docs", {})
                
                if checklist:
                    st.write("")
                    with st.expander("📚 Documentos Analisados (Checklist)", expanded=False):
                        for passo, arquivos in checklist.items():
                            if arquivos:
                                st.markdown(f"**✅ {passo}:**")
                                for arq in arquivos:
                                    st.markdown(f"- <span style='color:#7F8C8D; font-size: 0.9em;'>{arq}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"**❌ {passo}:** <span style='color:#7F8C8D; font-size: 0.9em;'>Nenhum documento anexado.</span>", unsafe_allow_html=True)
            
            with c_acoes:
                try:
                    import json
                    dados_sessao_recuperados = json.loads(linha_dados['dados_json'])
                    
                    # 1. Pega o status (decisão) que está salvo na linha da tabela
                    decisao_recuperada = str(linha_dados['Status'])
                    
                    # 2. Chama a função com o nome CORRETO e passando os DOIS parâmetros
                    pdf_bytes = gerar_pdf_bytes(dados_sessao_recuperados, decisao_recuperada)
                    
                    st.download_button(
                        label="Baixar PDF Executivo",
                        data=pdf_bytes,
                        file_name=f"Relatorio_{linha_dados['Empresa']}.pdf",
                        mime="application/pdf",
                        width="stretch",
                        type="primary",
                        icon=":material/download:"
                    )
                except Exception as e:
                    # Adicionei o {e} para mostrar o erro exato caso aconteça de novo
                    st.error(f"Erro ao recuperar PDF. Detalhe: {e}")
                
                st.write("")
                
                if "confirmar_exclusao" not in st.session_state:
                    st.session_state.confirmar_exclusao = False
                    
                if not st.session_state.confirmar_exclusao:
                    if st.button("Excluir Registro", width="stretch", icon=":material/delete:"):
                        st.session_state.confirmar_exclusao = True
                        st.rerun()
                else:
                    st.warning("Tem certeza? Esta ação não pode ser desfeita.")
                    c_sim, c_nao = st.columns(2)
                    with c_sim:
                        if st.button("Sim, excluir", width="stretch", icon=":material/check_circle:"):
                            try:
                                # Abre uma conexão FRESCA e segura para excluir
                                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                                creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
                                fresh_client = gspread.authorize(creds)
                                planilha = fresh_client.open("banco_locacao_paulo_bio").sheet1
                                
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
                        if st.button("Cancelar", width="stretch", icon=":material/cancel:"):
                            st.session_state.confirmar_exclusao = False
                            st.rerun()

        # SELECIONOU MÚLTIPLOS ITENS (Bulk Delete)
        elif len(linhas_selecionadas) > 1:
            st.divider()
            
            st.markdown(f"""
            <h4 style='color: {COR_SECUNDARIA}; margin-bottom: 15px;'>
                <i class="bi bi-trash-fill" style="color: #E74C3C; margin-right: 8px;"></i> 
                Exclusão em Massa ({len(linhas_selecionadas)} itens selecionados)
            </h4>
            """, unsafe_allow_html=True)
            
            if "confirmar_exclusao_multipla" not in st.session_state:
                st.session_state.confirmar_exclusao_multipla = False
                
            if not st.session_state.confirmar_exclusao_multipla:
                if st.button(f"Excluir {len(linhas_selecionadas)} Registros", width="stretch", icon=":material/delete:"):
                    st.session_state.confirmar_exclusao_multipla = True
                    st.rerun()
            else:
                st.warning("Tem certeza? Esta ação excluirá TODOS os registros selecionados e não pode ser desfeita.")
                c_sim, c_nao = st.columns(2)
                with c_sim:
                    if st.button("Sim, excluir todos", width="stretch", icon=":material/check_circle:"):
                        with st.spinner("Excluindo registros..."):
                            try:
                                # Abre uma conexão FRESCA e segura para excluir
                                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                                creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
                                fresh_client = gspread.authorize(creds)
                                planilha = fresh_client.open("banco_locacao_paulo_bio").sheet1
                                
                                # Pega as linhas reais e ordena de trás pra frente
                                linhas_reais = df_exibicao.iloc[linhas_selecionadas]['linha_planilha'].tolist()
                                linhas_reais.sort(reverse=True)
                                
                                for linha in linhas_reais:
                                    planilha.delete_rows(int(linha))
                                    
                                st.cache_data.clear()
                                st.session_state.confirmar_exclusao_multipla = False
                                st.success(f"{len(linhas_reais)} registros excluídos com sucesso!")
                                import time
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir: {e}")
                with c_nao:
                    if st.button("Cancelar", width="stretch", icon=":material/cancel:"):
                        st.session_state.confirmar_exclusao_multipla = False
                        st.rerun()

# --- TELA: CONFIGURAÇÕES ---
elif menu == "Configurações":
    st.markdown("## ⚙️ Configurações do Sistema")
    with st.container(border=True):
        st.markdown("Módulo em desenvolvimento. Aqui você poderá ajustar parâmetros da IA e limites de crédito no futuro.")
