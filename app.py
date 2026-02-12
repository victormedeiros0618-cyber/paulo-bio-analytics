import streamlit as st
import google.generativeai as genai
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

# --- 1. CONFIGURAÇÃO E ESTILO (V5.1) ---
st.set_page_config(
    page_title="Paulo Bio | Analytics", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# Cores da Marca
COR_PRIMARIA = "#F47920"
COR_SECUNDARIA = "#2C3E50"

# CSS Personalizado
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Outfit', sans-serif; }}
    .stButton>button {{
        background: {COR_PRIMARIA}; color: white; border-radius: 8px; border: none; height: 45px;
        font-weight: 600; text-transform: uppercase; width: 100%; transition: all 0.3s;
    }}
    .stButton>button:hover {{ background: #d66516; color: white; transform: translateY(-2px); }}
    .btn-outline {{ background: transparent; border: 2px solid {COR_SECUNDARIA}; color: {COR_SECUNDARIA}; }}
    .kpi-card {{
        background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid {COR_PRIMARIA}; text-align: center;
    }}
    h1, h2, h3 {{ font-weight: 700; color: {COR_SECUNDARIA}; }}
</style>
""", unsafe_allow_html=True)

# --- 2. AUTENTICAÇÃO E CONEXÃO ---

def check_password():
    if st.session_state.get('logged_in'): return True
    st.markdown("## 🔒 Acesso Restrito")
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.container(border=True):
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

# --- 3. FUNÇÕES AUXILIARES ---

def limpar_analise():
    """Reseta todo o estado da análise atual."""
    keys_to_keep = ['logged_in', 'user_name']
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]
    st.session_state.step = 0 # Começa do Contrato Social
    st.session_state.dados = {}
    st.rerun()

def gerar_pdf_bytes(dados, decisao, obs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(244, 121, 32)
    pdf.cell(0, 10, "PAULO BIO REAL ESTATE - RELATORIO DE CREDITO", ln=True, align='C')
    pdf.ln(5)
    
    # Dados da Empresa + Contrato Social
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"CLIENTE: {dados.get('empresa', 'N/A')}", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"CNPJ: {dados.get('cnpj', '-')}", ln=True)
    pdf.cell(0, 5, f"Capital Social: {dados.get('capital_social', '-')}", ln=True)
    pdf.cell(0, 5, f"Socios: {dados.get('socios', '-')}", ln=True)
    pdf.cell(0, 5, f"Responsavel: {dados.get('administrador', '-')}", ln=True)
    pdf.ln(5)
    
    # Proposta
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "DADOS DA PROPOSTA", ln=True, fill=False)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Imovel: {dados.get('imovel', '-')}", ln=True)
    pdf.cell(0, 5, f"Aluguel: R$ {dados.get('aluguel', 0):,.2f}", ln=True)
    pdf.cell(0, 5, f"Garantia: {dados.get('garantia', '-')}", ln=True)
    pdf.ln(5)

    # Serasa
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "1. ANALISE DE RISCO (SERASA)", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"Score: {dados.get('score', '-')} | Risco: {dados.get('risco', '-')}", ln=True)
    
    # Contábil
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "2. MATRIZ FINANCEIRA (CONSOLIDADA)", ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(30, 6, "PERIODO", 1)
    pdf.cell(60, 6, "RECEITA", 1)
    pdf.cell(60, 6, "LUCRO/RESULTADO", 1)
    pdf.ln()
    
    pdf.set_font("Arial", '', 9)
    periodos = dados.get("periodos_contabeis", [])
    receitas = dados.get("receitas_contabeis", [])
    lucros = dados.get("lucros_contabeis", [])
    
    if periodos:
        for i in range(len(periodos)):
            try:
                p = str(periodos[i])
                r = f"R$ {float(receitas[i]):,.2f}"
                l = f"R$ {float(lucros[i]):,.2f}"
                pdf.cell(30, 6, p, 1)
                pdf.cell(60, 6, r, 1)
                pdf.cell(60, 6, l, 1)
                pdf.ln()
            except: pass
    else:
        pdf.cell(150, 6, "Sem dados contabeis estruturados", 1, ln=True)

    # Gráfico
    pdf.ln(5)
    if periodos and lucros:
        try:
            plt.figure(figsize=(6, 2.5))
            plt.bar(periodos, [float(x) for x in lucros], color='#F47920')
            plt.title('Evolucao do Resultado (Lucro/Prejuizo)')
            plt.grid(axis='y', linestyle='--', alpha=0.5)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                plt.savefig(tmpfile.name, format='png', bbox_inches='tight')
                tmp_path = tmpfile.name
            plt.close()
            pdf.image(tmp_path, x=10, w=140)
            os.unlink(tmp_path)
        except: pass

    # Parecer
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "3. PARECER FINAL", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    analise = str(dados.get('analise_executiva', '')).encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, analise)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"VEREDITO: {decisao}", ln=True)
    pdf.set_font("Arial", 'I', 10)
    obs_clean = str(obs).encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, f"Obs: {obs_clean}")

    return pdf.output(dest='S').encode('latin-1')

# --- 4. FLUXO PRINCIPAL ---

if not check_password(): st.stop()

API_KEY = st.secrets["GOOGLE_API_KEY"]

if 'step' not in st.session_state: st.session_state.step = 0
if 'dados' not in st.session_state: st.session_state.dados = {}

# Sidebar
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_name.title()}")
    menu = st.radio("Menu", ["Nova Análise", "Dashboard", "Histórico"])
    st.markdown("---")
    if st.button("🗑️ LIMPAR / REINICIAR", type="primary"):
        limpar_analise()
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

# ==============================================================================
# TELA: NOVA ANÁLISE (FLUXO V5.1)
# ==============================================================================
if menu == "Nova Análise":
    passos = ["0. Contrato", "1. Proposta", "2. Serasa", "3. Contábil", "4. Decisão"]
    cols = st.columns(5)
    for i, col in enumerate(cols):
        cor = COR_PRIMARIA if i &lt;= st.session_state.step else "#E0E0E0"
        texto = f"**{passos[i]}**" if i == st.session_state.step else passos[i]
        col.markdown(f"<div style='border-bottom: 4px solid {cor}; text-align: center; font-size: 0.8rem;'>{texto}</div>", unsafe_allow_html=True)
    st.write("")

    # --- PASSO 0: CONTRATO SOCIAL (NOVO) ---
    if st.session_state.step == 0:
        st.markdown("### 📜 Contrato Social / Estatuto")
        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            st.info("Upload do Contrato Social (PDF)")
            uploaded = st.file_uploader("Arquivo", type="pdf", key="up0")
            if uploaded and st.button("Extrair Dados Societários"):
                with st.spinner("Lendo Contrato..."):
                    try:
                        genai.configure(api_key=API_KEY)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        prompt = """
                        Analise este Contrato Social. Extraia JSON:
                        {
                            "empresa": "Razão Social",
                            "cnpj": "CNPJ",
                            "socios": "Lista de nomes dos sócios",
                            "capital_social": "Valor do Capital Social (R$)",
                            "administrador": "Quem assina/responde pela empresa"
                        }
                        """
                        res = model.generate_content([{"mime_type": "application/pdf", "data": uploaded.getvalue()}, prompt])
                        text = res.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.dados.update(json.loads(text[text.find('{'):text.rfind('}')+1]))
                        st.rerun()
                    except: st.error("Erro na leitura.")
        
        with c2:
            d = st.session_state.dados
            empresa = st.text_input("Razão Social", d.get("empresa", ""))
            cnpj = st.text_input("CNPJ", d.get("cnpj", ""))
            socios = st.text_area("Sócios / QSA", d.get("socios", ""))
            capital = st.text_input("Capital Social", d.get("capital_social", ""))
            admin = st.text_input("Administrador / Assinante", d.get("administrador", ""))
            
            if st.button("Confirmar e Ir para Proposta >"):
                st.session_state.dados.update({"empresa": empresa, "cnpj": cnpj, "socios": socios, "capital_social": capital, "administrador": admin})
                st.session_state.step = 1
                st.rerun()

    # --- PASSO 1: PROPOSTA (Mantido) ---
    elif st.session_state.step == 1:
        st.markdown("### 📝 Dados da Proposta")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            uploaded = st.file_uploader("PDF Proposta", type="pdf", key="up1")
            if uploaded and st.button("Extrair Proposta"):
                with st.spinner("Lendo..."):
                    try:
                        genai.configure(api_key=API_KEY)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        prompt = """Extraia JSON: { "imovel": "", "aluguel": 0.0, "tempo": "", "garantia": "" }"""
                        res = model.generate_content([{"mime_type": "application/pdf", "data": uploaded.getvalue()}, prompt])
                        text = res.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.dados.update(json.loads(text[text.find('{'):text.rfind('}')+1]))
                        st.rerun()
                    except: st.warning("Leitura parcial.")
        with c2:
            d = st.session_state.dados
            st.info(f"Cliente: {d.get('empresa', 'Não informado')}")
            imovel = st.text_input("Imóvel", d.get("imovel", ""))
            c_val, c_prazo = st.columns(2)
            aluguel = c_val.number_input("Aluguel (R$)", float(d.get("aluguel") or 0.0))
            tempo = c_prazo.text_input("Prazo", d.get("tempo", ""))
            garantia = st.text_input("Garantia", d.get("garantia", ""))
            
            c_b1, c_b2 = st.columns(2)
            if c_b1.button("&lt; Voltar"): st.session_state.step = 0; st.rerun()
            if c_b2.button("Avançar >"):
                st.session_state.dados.update({"imovel": imovel, "aluguel": aluguel, "tempo": tempo, "garantia": garantia})
                st.session_state.step = 2
                st.rerun()

    # --- PASSO 2: SERASA (Mantido) ---
    elif st.session_state.step == 2:
        st.markdown("### 🔍 Serasa / Risco")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            uploaded = st.file_uploader("PDF Serasa", type="pdf", key="up2")
            if uploaded and st.button("Analisar Risco"):
                with st.spinner("Processando..."):
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt = """Extraia JSON: { "score": "", "risco": "Baixo/Médio/Alto", "restricoes": "Resumo" }"""
                    res = model.generate_content([{"mime_type": "application/pdf", "data": uploaded.getvalue()}, prompt])
                    st.session_state.dados.update(json.loads(res.text.replace("```json","").replace("```","")))
                    st.rerun()
        with c2:
            d = st.session_state.dados
            if "score" in d:
                c_m1, c_m2 = st.columns(2)
                c_m1.metric("Score", d.get("score"))
                c_m2.metric("Risco", d.get("risco"))
                st.write(f"**Restrições:** {d.get('restricoes')}")
            c_b1, c_b2 = st.columns(2)
            if c_b1.button("&lt; Voltar"): st.session_state.step = 1; st.rerun()
            if c_b2.button("Avançar >"): st.session_state.step = 3; st.rerun()

    # --- PASSO 3: CONTÁBIL (CORRIGIDO) ---
    elif st.session_state.step == 3:
        st.markdown("### 📊 Auditoria Contábil (Multi-Mês)")
        st.info("Dica: Faça upload de Balanços Anuais E Balancetes Mensais (ex: 05.2025) juntos.")
        
        uploaded = st.file_uploader("PDFs Contábeis", accept_multiple_files=True, key="up3")
        
        if uploaded and st.button("Executar Auditoria Avançada"):
            with st.spinner("Lendo cada arquivo individualmente e consolidando..."):
                try:
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    # Prompt Ninja para ler múltiplos arquivos
                    prompt = f"""
                    Atue como Auditor Contábil Sênior.
                    Analise TODOS os documentos fornecidos. Alguns podem ser anuais, outros mensais (balancetes).
                    
                    TAREFA:
                    1. Para CADA arquivo, identifique o PERÍODO (ex: "2023", "2024", "Mai/2025", "Jun/2025").
                    2. Se houver balancetes mensais, extraia o resultado daquele mês.
                    3. Se houver balanço anual, extraia o resultado do ano.
                    4. Ordene cronologicamente.
                    
                    Retorne JSON consolidado:
                    {{
                        "periodos_contabeis": ["2023", "2024", "Mai/25", "Jun/25"],
                        "receitas_contabeis": [100000.00, 150000.00, 12000.00, 13000.00],
                        "lucros_contabeis": [10000.00, 15000.00, 1200.00, 1300.00],
                        "nota_financeira": 85,
                        "analise_executiva": "Parecer detalhado sobre a evolução, citando os meses recentes de 2025 se houver."
                    }}
                    """
                    
                    parts = [{"mime_type": "application/pdf", "data": f.getvalue()} for f in uploaded]
                    parts.append(prompt)
                    
                    res = model.generate_content(parts)
                    # CORREÇÃO AQUI:
                    text = res.text.replace("```json", "").replace("```", "").strip()
                    json_data = json.loads(text[text.find('{'):text.rfind('}')+1])
                    st.session_state.dados.update(json_data)
                    st.rerun()
                except Exception as e: st.error(f"Erro na auditoria: {e}")

        d = st.session_state.dados
        if "periodos_contabeis" in d:
            df_fin = pd.DataFrame({
                "Período": d.get("periodos_contabeis", []),
                "Receita": d.get("receitas_contabeis", []),
                "Lucro": d.get("lucros_contabeis", [])
            })
            st.dataframe(df_fin, use_container_width=True, hide_index=True)
            st.bar_chart(df_fin.set_index("Período")["Lucro"], color=COR_PRIMARIA)
            st.write(d.get("analise_executiva"))
            
        c_b1, c_b2 = st.columns(2)
        if c_b1.button("&lt; Voltar"): st.session_state.step = 2; st.rerun()
        if c_b2.button("Conclusão >"): st.session_state.step = 4; st.rerun()

    # --- PASSO 4: DECISÃO (Mantido) ---
    elif st.session_state.step == 4:
        st.markdown("### 🏁 Decisão Final")
        d = st.session_state.dados
        
        # Termômetro
        try: score = float(str(d.get("score", 0)).replace(".","")) / 10
        except: score = 0
        prob = int((score * 0.3) + (d.get("nota_financeira",50) * 0.7))
        msg = "ALTA" if prob > 70 else "MÉDIA" if prob > 40 else "BAIXA"
        
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.progress(prob/100)
            c1.caption(f"Probabilidade de Aprovação: {prob}% ({msg})")
            c2.metric("Score Geral", prob)

        c_decisao, c_save = st.columns(2)
        with c_decisao:
            decisao = st.selectbox("Veredito", ["APROVADO", "REPROVADO", "EM ANÁLISE"])
            obs = st.text_area("Justificativa")
        with c_save:
            st.write("")
            if st.button("💾 Salvar Análise"):
                if save_data(d.get("empresa"), decisao, json.dumps(d), obs):
                    st.success("Salvo!")
                    time.sleep(1)
                    limpar_analise()
            if st.button("📄 Baixar PDF"):
                try:
                    pdf = gerar_pdf_bytes(d, decisao, obs)
                    st.download_button("⬇️ PDF", pdf, "Relatorio.pdf", "application/pdf")
                except: st.error("Erro PDF")
        
        if st.button("&lt; Voltar para Revisão"): st.session_state.step = 3; st.rerun()

# ==============================================================================
# TELA: DASHBOARD (Mantido)
# ==============================================================================
elif menu == "Dashboard":
    st.markdown("## 📊 Dashboard")
    df = load_data()
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total", len(df))
        c2.metric("Aprovados", len(df[df['status'].str.contains('APROVADO', na=False)]))
        c3.metric("Reprovados", len(df[df['status'] == 'REPROVADO']))
        st.bar_chart(df['status'].value_counts(), color=COR_PRIMARIA)

# ==============================================================================
# TELA: HISTÓRICO (Mantido)
# ==============================================================================
elif menu == "Histórico":
    st.markdown("## 🗂️ Histórico")
    df = load_data()
    if not df.empty:
        st.dataframe(df[['data_registro', 'cliente', 'status']], use_container_width=True)
