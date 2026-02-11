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

# --- 1. CONFIGURAÇÃO E ESTILO (V4.0 CLOUD) ---
st.set_page_config(
    page_title="Paulo Bio | Analytics", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="collapsed"
)

# Cores da Marca
COR_PRIMARIA = "#F47920"
COR_PRIMARIA_HOVER = "#d66516"
COR_SECUNDARIA = "#2C3E50"
COR_FUNDO_GERAL = "#F8F9FA"

# CSS V3.4 (Mantido)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Outfit', sans-serif; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 3rem; max_width: 1200px; }}
    .stButton>button {{
        background: linear-gradient(90deg, {COR_PRIMARIA} 0%, {COR_PRIMARIA_HOVER} 100%);
        color: white !important;
        border-radius: 8px; border: none; height: 50px;
        font-weight: 600; text-transform: uppercase; width: 100%;
        box-shadow: 0 4px 6px rgba(244, 121, 32, 0.2);
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); color: white !important; }}
    div[data-testid="column"] > div > div > div > div > div > button:contains("&lt; Voltar") {{
        background: transparent; border: 2px solid {COR_SECUNDARIA}; color: {COR_SECUNDARIA} !important;
    }}
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {{
        border-radius: 8px; border: 1px solid #E0E0E0; padding: 10px;
        background-color: #FFFFFF !important; color: #000000 !important;
    }}
    .stTextInput>div>div>input:focus {{ border-color: {COR_PRIMARIA}; box-shadow: 0 0 0 1px {COR_PRIMARIA}; }}
    div[data-testid="stVerticalBlock"] > div[style*="border"] {{
        background-color: white; border-radius: 12px; border: 1px solid #EAEAEA;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03); padding: 20px;
    }}
    h1, h2, h3 {{ font-weight: 700; }}
    .kpi-card {{
        background-color: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid {COR_PRIMARIA}; text-align: center;
    }}
    .kpi-value {{ font-size: 2.5rem; font-weight: 700; color: {COR_SECUNDARIA}; margin: 0; }}
    .kpi-label {{ font-size: 0.9rem; color: #7F8C8D; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. AUTENTICAÇÃO E CONEXÃO GOOGLE SHEETS ---

# Função de Login
def check_password():
    """Retorna True se o usuário estiver logado corretamente."""
    if st.session_state.get('logged_in'):
        return True
        
    st.markdown("## 🔒 Acesso Restrito - Paulo Bio Analytics")
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.container(border=True):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            
            if st.button("Entrar"):
                # Verifica no secrets.toml
                if usuario in st.secrets["passwords"] and senha == st.secrets["passwords"][usuario]:
                    st.session_state.logged_in = True
                    st.session_state.user_name = usuario
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    return False

# Função de Conexão com Google Sheets
@st.cache_resource
def get_google_sheet():
    """Conecta ao Google Sheets usando as credenciais do secrets."""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # Carrega credenciais do secrets.toml
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Abre a planilha pelo nome
    sheet = client.open(st.secrets["SHEET_NAME"]).sheet1
    return sheet

# Função para Ler Dados
def load_data():
    try:
        sheet = get_google_sheet()
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao conectar no banco de dados: {e}")
        return pd.DataFrame()

# Função para Salvar Dados
def save_data(cliente, status, dados_json, obs):
    try:
        sheet = get_google_sheet()
        # Data atual
        data_reg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Adiciona linha
        sheet.append_row([data_reg, cliente, status, dados_json, obs])
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- 3. FLUXO PRINCIPAL ---

if not check_password():
    st.stop() # Para a execução se não estiver logado

# Se passou do login:
API_KEY = st.secrets["GOOGLE_API_KEY"]

# Função PDF (Mantida V3.4)
def gerar_pdf_bytes(dados, decisao, obs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(244, 121, 32)
    pdf.cell(0, 10, "PAULO BIO REAL ESTATE - RELATORIO DE CREDITO", ln=True, align='C')
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"CLIENTE: {dados.get('empresa', 'N/A')}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, f"CNPJ: {dados.get('cnpj', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"Aluguel Proposto: R$ {dados.get('aluguel', 0):,.2f}", ln=True)
    pdf.cell(0, 6, f"Garantia: {dados.get('garantia', 'N/A')}", ln=True)
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "1. ANALISE DE RISCO (SERASA)", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, f"Score: {dados.get('score', '-')} | Risco: {dados.get('risco', '-')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "2. MATRIZ FINANCEIRA", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 8, "ANO", 1)
    pdf.cell(60, 8, "RECEITA BRUTA", 1)
    pdf.cell(60, 8, "LUCRO LIQUIDO", 1)
    pdf.ln()
    pdf.set_font("Arial", '', 10)
    anos = dados.get("anos", [])
    receitas = dados.get("receita_bruta", [])
    lucros = dados.get("lucro_liquido", [])
    if anos:
        for i in range(len(anos)):
            try:
                ano = str(anos[i])
                rec = f"R$ {float(receitas[i]):,.2f}"
                luc = f"R$ {float(lucros[i]):,.2f}"
                pdf.cell(30, 8, ano, 1)
                pdf.cell(60, 8, rec, 1)
                pdf.cell(60, 8, luc, 1)
                pdf.ln()
            except: pass
    else:
        pdf.cell(150, 8, "Dados contabeis nao disponiveis", 1, ln=True)
    pdf.ln(5)
    if anos and lucros:
        try:
            plt.figure(figsize=(6, 3))
            plt.bar(anos, [float(x) for x in lucros], color='#F47920')
            plt.title('Evolucao do Lucro Liquido')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                plt.savefig(tmpfile.name, format='png', bbox_inches='tight')
                tmp_path = tmpfile.name
            plt.close()
            pdf.image(tmp_path, x=10, w=140)
            os.unlink(tmp_path)
        except: pass
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "3. PARECER FINAL", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    analise = str(dados.get('analise_executiva', '')).encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, analise)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"VEREDITO: {decisao}", ln=True)
    pdf.set_font("Arial", 'I', 11)
    obs_clean = str(obs).encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, f"Obs: {obs_clean}")
    return pdf.output(dest='S').encode('latin-1')

# --- NAVEGAÇÃO ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'dados' not in st.session_state: st.session_state.dados = {}

with st.sidebar:
    st.markdown(f"### 👤 Olá, {st.session_state.user_name.title()}")
    menu = st.radio("Menu", ["Dashboard", "Nova Análise", "Histórico"])
    st.markdown("---")
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

# ==============================================================================
# TELA: DASHBOARD
# ==============================================================================
if menu == "Dashboard":
    st.markdown("## 📊 Visão Geral da Carteira")
    
    df = load_data() # Carrega do Google Sheets
    
    if df.empty:
        st.warning("Conexão com Banco de Dados estabelecida, mas sem registros ainda.")
    else:
        total = len(df)
        aprovados = len(df[df['status'].astype(str).str.contains('APROVADO', na=False)])
        reprovados = len(df[df['status'] == 'REPROVADO'])
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="kpi-card"><p class="kpi-value">{total}</p><p class="kpi-label">Total Analisado</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="kpi-card" style="border-left-color: #27ae60;"><p class="kpi-value" style="color: #27ae60;">{aprovados}</p><p class="kpi-label">Aprovados</p></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="kpi-card" style="border-left-color: #c0392b;"><p class="kpi-value" style="color: #c0392b;">{reprovados}</p><p class="kpi-label">Reprovados</p></div>""", unsafe_allow_html=True)
        
        st.write("")
        c_chart1, c_chart2 = st.columns([2, 1])
        with c_chart1:
            with st.container(border=True):
                st.subheader("Evolução Temporal")
                try:
                    df['data_dt'] = pd.to_datetime(df['data_registro'])
                    chart_data = df.groupby(df['data_dt'].dt.date).size()
                    st.line_chart(chart_data, color=COR_PRIMARIA)
                except: st.caption("Dados insuficientes.")
        with c_chart2:
            with st.container(border=True):
                st.subheader("Proporção")
                st.bar_chart(df['status'].value_counts(), color=COR_PRIMARIA)

# ==============================================================================
# TELA: NOVA ANÁLISE
# ==============================================================================
elif menu == "Nova Análise":
    st.markdown("#### 🚀 Nova Análise de Crédito")
    passos = ["1. Proposta", "2. Serasa", "3. Contábil", "4. Decisão"]
    cols = st.columns(4)
    for i, col in enumerate(cols):
        cor = COR_PRIMARIA if (i + 1) <= st.session_state.step else "#E0E0E0"
        texto = f"**{passos[i]}**" if (i + 1) == st.session_state.step else passos[i]
        col.markdown(f"<div style='border-bottom: 4px solid {cor}; padding-bottom: 5px; text-align: center;'>{texto}</div>", unsafe_allow_html=True)
    st.write("") 

       # --- PASSO 1: PROPOSTA (CORREÇÃO DO ERRO FALSO-POSITIVO) ---
    if st.session_state.step == 1:
        st.markdown("### 📝 Dados da Proposta")
        
        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            st.info("Faça upload da Proposta ou Ficha Cadastral")
            uploaded = st.file_uploader("PDF da Proposta", type="pdf", key="up1")
            
            if uploaded and st.button("Extrair Dados com IA"):
                if not API_KEY: 
                    st.error("⚠️ API Key não configurada.")
                else:
                    with st.spinner("🤖 Lendo Proposta..."):
                        try:
                            genai.configure(api_key=API_KEY)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            prompt = """
                            Analise este documento.
                            Extraia e retorne APENAS um JSON válido (sem markdown```json):
                            { 
                                "empresa": "Nome do Cliente", 
                                "cnpj": "CNPJ apenas números e pontuação", 
                                "imovel": "Endereço completo", 
                                "aluguel": 0.0, 
                                "tempo": "Prazo em meses",
                                "garantia": "Tipo de garantia"
                            }
                            """
                            
                            res = model.generate_content([
                                {"mime_type": "application/pdf", "data": uploaded.getvalue()},
                                prompt
                            ])
                            
                            # Limpeza Power (Remove tudo que não é JSON)
                            texto = res.text
                            inicio = texto.find('{')
                            fim = texto.rfind('}') + 1
                            
                            if inicio != -1 and fim != -1:
                                json_str = texto[inicio:fim]
                                dados_extraidos = json.loads(json_str)
                                st.session_state.dados.update(dados_extraidos)
                                st.rerun() # Recarrega a página para mostrar os dados
                            else:
                                st.warning("A IA leu, mas o formato veio estranho. Verifique os campos ao lado.")
                                
                        except Exception as e:
                            # Se os dados foram preenchidos, ignora o erro visual
                            if st.session_state.dados.get('empresa'):
                                st.rerun()
                            else:
                                st.error(f"Erro na leitura: {e}")
        
        with c2:
            st.write("Preencha ou corrija os dados:")
            d = st.session_state.dados
            
            # Formulário
            empresa = st.text_input("Cliente / Empresa", d.get("empresa", ""))
            cnpj = st.text_input("CNPJ / CPF", d.get("cnpj", ""))
            imovel = st.text_input("Imóvel de Interesse", d.get("imovel", ""))
            
            col_val, col_prazo = st.columns(2)
            aluguel = col_val.number_input("Aluguel Mensal (R$)", float(d.get("aluguel") or 0.0))
            tempo = col_prazo.text_input("Tempo de Contrato", d.get("tempo", ""))
            
            garantia = st.text_input("Garantia Oferecida", d.get("garantia", ""))
            
            if st.button("Confirmar e Avançar >", type="primary"):
                st.session_state.dados.update({
                    "empresa": empresa, 
                    "cnpj": cnpj, 
                    "imovel": imovel,
                    "aluguel": aluguel,
                    "tempo": tempo,
                    "garantia": garantia
                })
                st.session_state.step = 2
                st.rerun()

    elif st.session_state.step == 2:
        with st.container(border=True):
            st.subheader("🔍 Análise de Risco (Serasa)")
            c1, c2 = st.columns([1, 1.5])
            with c1:
                uploaded = st.file_uploader("PDF Serasa", type="pdf", key="up2")
                if uploaded and st.button("Processar Risco"):
                    with st.spinner("Calculando Score..."):
                        genai.configure(api_key=API_KEY)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        prompt = """Extraia JSON: { "score": "", "risco": "Baixo/Médio/Alto", "restricoes": "Resumo" }"""
                        res = model.generate_content([{"mime_type": "application/pdf", "data": uploaded.getvalue()}, prompt])
                        st.session_state.dados.update(json.loads(res.text.replace("```json","").replace("```","")))
                        st.rerun()
            with c2:
                d = st.session_state.dados
                if "score" in d:
                    c_met1, c_met2 = st.columns(2)
                    c_met1.metric("Score Serasa", d.get("score"))
                    c_met2.metric("Nível de Risco", d.get("risco"))
                    st.markdown(f"**Restrições:** {d.get('restricoes')}")
                col_b1, col_b2 = st.columns(2)
                if col_b1.button("&lt; Voltar"): st.session_state.step = 1; st.rerun()
                if col_b2.button("Próximo >"): st.session_state.step = 3; st.rerun()

    elif st.session_state.step == 3:
        with st.container(border=True):
            st.subheader("📊 Auditoria Contábil")
            uploaded = st.file_uploader("PDFs Contábeis", accept_multiple_files=True, key="up3")
            if uploaded and st.button("Executar Auditoria"):
                with st.spinner("Auditando..."):
                    try:
                        genai.configure(api_key=API_KEY)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        safety_settings = [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
                        aluguel = st.session_state.dados.get('aluguel', 0)
                        garantia = st.session_state.dados.get('garantia', 'Não informada')
                        prompt = f"""Atue como Auditor. Aluguel: {aluguel}. Garantia: {garantia}. 
                        Extraia anos, receita, lucro. Calcule notas (0-100) financeira e garantia. PT-BR.
                        JSON: {{ "anos": [], "receita_bruta": [], "lucro_liquido": [], "nota_financeira": 0, "nota_garantia": 0, "analise_executiva": "texto" }}"""
                        parts = [{"mime_type": "application/pdf", "data": f.getvalue()} for f in uploaded]
                        parts.append(prompt)
                        res = model.generate_content(parts, safety_settings=safety_settings)
                        text = res.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.dados.update(json.loads(text[text.find('{'):text.rfind('}')+1]))
                        st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")
            d = st.session_state.dados
            if "receita_bruta" in d:
                df_fin = pd.DataFrame({"Ano": d.get("anos",[]), "Receita": d.get("receita_bruta",[]), "Lucro": d.get("lucro_liquido",[])})
                st.dataframe(df_fin, use_container_width=True, hide_index=True)
                st.bar_chart(df_fin.set_index("Ano")["Lucro"], color=COR_PRIMARIA)
                st.write(d.get("analise_executiva"))
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("&lt; Voltar"): st.session_state.step = 2; st.rerun()
            if col_b2.button("Conclusão >"): st.session_state.step = 4; st.rerun()

    elif st.session_state.step == 4:
        st.subheader("🏁 Consolidação")
        d = st.session_state.dados
        try:
            score_raw = float(str(d.get("score", 0)).replace(".",""))
            nota_serasa = min(score_raw / 10, 100)
        except: nota_serasa = 0
        prob = int((nota_serasa * 0.3) + (d.get("nota_financeira",50) * 0.5) + (d.get("nota_garantia",50) * 0.2))
        msg = "ALTA" if prob > 75 else "MÉDIA" if prob > 50 else "BAIXA"
        
        with st.container(border=True):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"### 🌡️ Probabilidade: {prob}% ({msg})")
                st.progress(prob/100)
            with c2: st.metric("Score Calculado", prob)
        
        st.write("")
        c_decisao, c_save = st.columns(2)
        with c_decisao:
            decisao = st.selectbox("Veredito", ["APROVADO", "REPROVADO", "EM ANÁLISE"])
            obs = st.text_area("Justificativa")
        with c_save:
            st.write("")
            st.write("")
            if st.button("💾 Salvar na Nuvem"):
                if save_data(d.get("empresa"), decisao, json.dumps(d), obs):
                    st.success("Salvo no Google Sheets!")
                    time.sleep(1)
                    st.session_state.step = 1
                    st.session_state.dados = {}
                    st.rerun()
            if st.button("📄 PDF"):
                try:
                    pdf = gerar_pdf_bytes(d, decisao, obs)
                    st.download_button("⬇️ Baixar", pdf, f"Analise.pdf", "application/pdf")
                except: st.error("Erro PDF")

# ==============================================================================
# TELA: HISTÓRICO (AGORA LÊ DO GOOGLE SHEETS)
# ==============================================================================
elif menu == "Histórico":
    st.markdown("## 🗂️ Arquivo de Análises (Google Sheets)")
    
    df = load_data()
    
    if not df.empty:
        c1, c2 = st.columns(2)
        filtro_nome = c1.text_input("🔎 Buscar")
        filtro_status = c2.selectbox("Status", ["Todos", "APROVADO", "REPROVADO", "EM ANÁLISE"])
        
        if filtro_nome: df = df[df['cliente'].astype(str).str.contains(filtro_nome, case=False, na=False)]
        if filtro_status != "Todos": df = df[df['status'] == filtro_status]
        
        event = st.dataframe(df[['data_registro', 'cliente', 'status']], selection_mode="single-row", on_select="rerun", use_container_width=True, hide_index=True)
        
        if len(event.selection.rows) > 0:
            idx = event.selection.rows[0]
            registro = df.iloc[idx]
            with st.container(border=True):
                st.markdown(f"### {registro['cliente']}")
                try:
                    dados_rec = json.loads(registro['dados_json'])
                    pdf = gerar_pdf_bytes(dados_rec, registro['status'], registro['obs_final'])
                    st.download_button("📄 Re-gerar PDF", pdf, f"Relatorio.pdf", "application/pdf")
                except: st.error("Erro ao processar dados antigos.")
