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

# --- 1. CONFIGURAÇÃO E ESTILO (V5.3 - Layout & Operacional) ---
st.set_page_config(
    page_title="Paulo Bio | Analytics", 
    layout="wide", 
    page_icon="Logotipo.opb.png",
    initial_sidebar_state="expanded"
)

# Cores da Marca
COR_PRIMARIA = "#F47920"
COR_SECUNDARIA = "#2C3E50"

# CSS Personalizado (Aprimorado)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Outfit', sans-serif; }}
    .stButton>button {{
        background: {COR_PRIMARIA}; color: white; border-radius: 8px; border: none; height: 45px;
        font-weight: 600; text-transform: uppercase; width: 100%; transition: all 0.3s;
    }}
    .stButton>button:hover {{ background: #d66516; color: white; transform: translateY(-2px); }}
    .kpi-card {{
        background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid {COR_PRIMARIA}; text-align: center; margin-bottom: 15px;
    }}
    h1, h2, h3 {{ font-weight: 700; color: {COR_SECUNDARIA}; }}
    /* Ajuste visual para o farol */
    .status-aprovado {{ color: #27ae60; font-weight: bold; }}
    .status-reprovado {{ color: #c0392b; font-weight: bold; }}
    .status-analise {{ color: #f39c12; font-weight: bold; }}
</style>
""", unsafe_allow_html=True)

# --- 2. AUTENTICAÇÃO E CONEXÃO ---

def check_password():
    if st.session_state.get('logged_in'): return True
    
    st.write("")
    st.write("")
    
    # Colunas ajustadas: [4, 1, 4] espreme o logo no centro para ficar tamanho "ícone"
    col_vazia1, col_logo, col_vazia3 = st.columns([4, 1.5, 4])
    with col_logo:
        try:
            st.image("Logo branco.png", use_container_width=True)
        except:
            st.markdown("<h1 style='text-align: center; color: #F47920;'>🏢</h1>", unsafe_allow_html=True)
            
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
                else: st.error("Acesso negado. Verifique suas credenciais.")
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
    keys_to_keep = ['logged_in', 'user_name']
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]
    st.session_state.step = 0 
    st.session_state.dados = {}
    st.rerun()

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
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"CNPJ: {dados.get('cnpj', '-')}", ln=True)
    pdf.cell(0, 5, f"Capital Social: {dados.get('capital_social', '-')}", ln=True)
    pdf.cell(0, 5, f"Socios: {dados.get('socios', '-')}", ln=True)
    pdf.cell(0, 5, f"Responsavel: {dados.get('administrador', '-')}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "DADOS DA PROPOSTA", ln=True, fill=False)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Imovel: {dados.get('imovel', '-')}", ln=True)
    
    # Tratamento seguro para formatação de moeda (evita erro se vier string com vírgula)
    try: aluguel_float = float(str(dados.get('aluguel', 0)).replace(',', '.'))
    except: aluguel_float = 0.0
    pdf.cell(0, 5, f"Aluguel: R$ {aluguel_float:,.2f}", ln=True)
    
    pdf.cell(0, 5, f"Garantia: {dados.get('garantia', '-')}", ln=True)
    pdf.ln(5)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "1. ANALISE DE RISCO (SERASA)", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"Score: {dados.get('score', '-')} | Risco: {dados.get('risco', '-')}", ln=True)
    
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
                # Tratamento para garantir que a formatação não quebre se a IA mandar string
                r_val = float(str(receitas[i]).replace(',', '.'))
                l_val = float(str(lucros[i]).replace(',', '.'))
                r = f"R$ {r_val:,.2f}"
                l = f"R$ {l_val:,.2f}"
                pdf.cell(30, 6, p, 1)
                pdf.cell(60, 6, r, 1)
                pdf.cell(60, 6, l, 1)
                pdf.ln()
            except: pass
    else:
        pdf.cell(150, 6, "Sem dados contabeis estruturados", 1, ln=True)

    pdf.ln(5)
    if periodos and lucros:
        try:
            plt.figure(figsize=(6, 2.5))
            plt.bar(periodos, [float(str(x).replace(',', '.')) for x in lucros], color='#F47920')
            plt.title('Evolucao do Resultado (Lucro/Prejuizo)')
            plt.grid(axis='y', linestyle='--', alpha=0.5)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                plt.savefig(tmpfile.name, format='png', bbox_inches='tight')
                tmp_path = tmpfile.name
            plt.close()
            pdf.image(tmp_path, x=10, w=140)
            os.unlink(tmp_path)
        except: pass

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

# Sidebar Profissional
with st.sidebar:
    st.write("") # Dá um respiro no topo
    
    # Colunas para centralizar e diminuir o logo na sidebar
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        try:
            st.image("Logo branco.png", use_container_width=True)
        except:
            st.markdown("<h2 style='text-align: center; color: #F47920;'>🏢</h2>", unsafe_allow_html=True)
            
    st.markdown(f"<div style='text-align: center; color: gray; margin-bottom: 20px; margin-top: 10px;'>Operador: <b>{st.session_state.user_name.title()}</b></div>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("Navegação", ["Nova Análise", "Dashboard", "Histórico"])
    st.markdown("---")
    if st.button("🗑️ LIMPAR", type="primary"):
        limpar_analise()
    st.write("")
    if st.button("Sair do Sistema"):
        st.session_state.logged_in = False
        st.rerun()
#        
# TELA: NOVA ANÁLISE (FLUXO V5.3)
# 
if menu == "Nova Análise":
    passos = ["0. Contrato", "1. Proposta", "2. Serasa", "3. Contábil", "4. Decisão"]
    cols = st.columns(5)
    for i, col in enumerate(cols):
        cor = COR_PRIMARIA if i <= st.session_state.step else "#E0E0E0"
        texto = f"**{passos[i]}**" if i == st.session_state.step else passos[i]
        col.markdown(f"<div style='border-bottom: 4px solid {cor}; text-align: center; font-size: 0.9rem; padding-bottom: 5px;'>{texto}</div>", unsafe_allow_html=True)
    st.write("")

    # --- PASSO 0: CONTRATO SOCIAL ---
    if st.session_state.step == 0:
        st.markdown("### 📜 Extração Societária")
        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            with st.container(border=True):
                st.info("Faça o upload do Contrato Social ou Estatuto (PDF)")
                uploaded = st.file_uploader("Arquivo Societário", type="pdf", key="up0")
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
            with st.container(border=True):
                st.markdown("#### Dados Extraídos")
                d = st.session_state.dados
                empresa = st.text_input("Razão Social", d.get("empresa", ""))
                cnpj = st.text_input("CNPJ", d.get("cnpj", ""))
                socios = st.text_area("Sócios / QSA", d.get("socios", ""))
                capital = st.text_input("Capital Social", d.get("capital_social", ""))
                admin = st.text_input("Administrador / Assinante", d.get("administrador", ""))
                
                st.write("")
                if st.button("Avançar"):
                    st.session_state.dados.update({"empresa": empresa, "cnpj": cnpj, "socios": socios, "capital_social": capital, "administrador": admin})
                    st.session_state.step = 1
                    st.rerun()

    # --- PASSO 1: PROPOSTA ---
    elif st.session_state.step == 1:
        st.markdown("### 📝 Dados da Proposta")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            with st.container(border=True):
                uploaded = st.file_uploader("PDF Proposta", type="pdf", key="up1")
                if uploaded and st.button("Extrair Proposta"):
                    with st.spinner("Lendo..."):
                        try:
                            genai.configure(api_key=API_KEY)
                            model = genai.GenerativeModel('gemini-2.5-flash')
                            # Forçando string no aluguel para não perder zeros
                            prompt = """Extraia JSON: { "imovel": "", "aluguel": "Valor exato em texto (ex: 15000.00)", "tempo": "", "garantia": "" }"""
                            res = model.generate_content([{"mime_type": "application/pdf", "data": uploaded.getvalue()}, prompt])
                            text = res.text.replace("```json", "").replace("```", "").strip()
                            st.session_state.dados.update(json.loads(text[text.find('{'):text.rfind('}')+1]))
                            st.rerun()
                        except: st.warning("Leitura parcial.")
        with c2:
            with st.container(border=True):
                d = st.session_state.dados
                st.info(f"**Cliente:** {d.get('empresa', 'Não informado')}")
                imovel = st.text_input("Imóvel", d.get("imovel", ""))
                c_val, c_prazo = st.columns(2)
                aluguel = c_val.text_input("Aluguel (R$)", str(d.get("aluguel", "")))
                tempo = c_prazo.text_input("Prazo", d.get("tempo", ""))
                garantia = st.text_input("Garantia", d.get("garantia", ""))
                
                st.write("")
                c_b1, c_b2 = st.columns(2)
                if c_b1.button("Voltar"): st.session_state.step = 0; st.rerun()
                if c_b2.button("Avançar"):
                    st.session_state.dados.update({"imovel": imovel, "aluguel": aluguel, "tempo": tempo, "garantia": garantia})
                    st.session_state.step = 2
                    st.rerun()

    # --- PASSO 2: SERASA ---
    elif st.session_state.step == 2:
        st.markdown("### 🔍 Análise de Risco (Serasa)")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            with st.container(border=True):
                uploaded = st.file_uploader("PDF Serasa", type="pdf", key="up2")
                if uploaded and st.button("Analisar Risco"):
                    with st.spinner("Processando..."):
                        genai.configure(api_key=API_KEY)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        # Instrução rigorosa para não comer números
                        prompt = """
                        Extraia os dados EXATAMENTE como estão no documento. NÃO remova zeros.
                        Retorne JSON: { "score": "Valor exato em texto", "risco": "Baixo/Médio/Alto", "restricoes": "Resumo" }
                        """
                        res = model.generate_content([{"mime_type": "application/pdf", "data": uploaded.getvalue()}, prompt])
                        st.session_state.dados.update(json.loads(res.text.replace("```json","").replace("```","")))
                        st.rerun()
        with c2:
            with st.container(border=True):
                d = st.session_state.dados
                if "score" in d:
                    c_m1, c_m2 = st.columns(2)
                    c_m1.metric("Score Extraído", d.get("score"))
                    c_m2.metric("Nível de Risco", d.get("risco"))
                    st.info(f"**Restrições Localizadas:** {d.get('restricoes')}")
                
                st.write("")
                c_b1, c_b2 = st.columns(2)
                if c_b1.button("Voltar"): st.session_state.step = 1; st.rerun()
                if c_b2.button("Avançar"): st.session_state.step = 3; st.rerun()

    # --- PASSO 3: CONTÁBIL ---
    elif st.session_state.step == 3:
        st.markdown("### 📊 Auditoria Contábil Consolidada")
        
        with st.container(border=True):
            st.info("💡 **Dica:** Faça upload de Balanços Anuais E Balancetes Mensais juntos.")
            uploaded = st.file_uploader("PDFs Contábeis", accept_multiple_files=True, key="up3")
            
            if uploaded and st.button("Executar Auditoria Avançada"):
                with st.spinner("Lendo e consolidando arquivos..."):
                    try:
                        genai.configure(api_key=API_KEY)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        # Prompt blindado contra corte de zeros
                        prompt = f"""
                        Atue como Auditor Contábil Sênior. Analise TODOS os documentos.
                        
                        ATENÇÃO CRÍTICA: Extraia os valores numéricos EXATAMENTE como estão no documento. 
                        NÃO remova zeros à direita, NÃO arredonde. Mantenha os milhares exatos.
                        Retorne os valores financeiros obrigatoriamente como STRING no JSON (ex: "150000.00").
                        
                        TAREFA:
                        1. Identifique o PERÍODO de cada arquivo.
                        2. Extraia Receita e Lucro/Resultado.
                        3. Ordene cronologicamente.
                        
                        Retorne JSON:
                        {{
                            "periodos_contabeis": ["2023", "Mai/25"],
                            "receitas_contabeis": ["100000.00", "12000.00"],
                            "lucros_contabeis": ["10000.00", "1200.00"],
                            "nota_financeira": 85,
                            "analise_executiva": "Parecer detalhado."
                        }}
                        """
                        
                        parts = [{"mime_type": "application/pdf", "data": f.getvalue()} for f in uploaded]
                        parts.append(prompt)
                        
                        res = model.generate_content(parts)
                        text = res.text.replace("```json", "").replace("```", "").strip()
                        json_data = json.loads(text[text.find('{'):text.rfind('}')+1])
                        st.session_state.dados.update(json_data)
                        st.rerun()
                    except Exception as e: st.error(f"Erro na auditoria: {e}")

        d = st.session_state.dados
        if "periodos_contabeis" in d:
            c_tab, c_graf = st.columns([1, 1.5])
            with c_tab:
                df_fin = pd.DataFrame({
                    "Período": d.get("periodos_contabeis", []),
                    "Receita": d.get("receitas_contabeis", []),
                    "Lucro": d.get("lucros_contabeis", [])
                })
                st.dataframe(df_fin, use_container_width=True, hide_index=True)
            with c_graf:
                # Tratamento seguro para plotar strings
                try:
                    valores_grafico = [float(str(x).replace(',', '.')) for x in d.get("lucros_contabeis", [])]
                    st.bar_chart(pd.DataFrame({"Lucro": valores_grafico}, index=d.get("periodos_contabeis", [])), color=COR_PRIMARIA)
                except: pass
            
            with st.container(border=True):
                st.markdown("#### Parecer do Auditor IA")
                st.write(d.get("analise_executiva"))
            
        st.write("")
        c_b1, c_b2 = st.columns(2)
        if c_b1.button("Voltar"): st.session_state.step = 2; st.rerun()
        if c_b2.button("Avançar"): st.session_state.step = 4; st.rerun()

    # --- PASSO 4: DECISÃO ---
    elif st.session_state.step == 4:
        st.markdown("### 🏁 Decisão Final")
        d = st.session_state.dados
        
        try: score = float(str(d.get("score", 0)).replace(".","")) / 10
        except: score = 0
        prob = int((score * 0.3) + (d.get("nota_financeira",50) * 0.7))
        msg = "ALTA" if prob > 70 else "MÉDIA" if prob > 40 else "BAIXA"
        
        with st.container(border=True):
            st.markdown("#### Score de Aprovação")
            c1, c2 = st.columns([3, 1])
            c1.progress(prob/100)
            c1.caption(f"Probabilidade Calculada: {prob}% ({msg})")
            c2.metric("Score Geral", prob)

        st.write("")
        c_decisao, c_save = st.columns([1, 1])
        
        with c_decisao:
            with st.container(border=True):
                st.markdown("#### Emissão de Veredito")
                decisao = st.selectbox("Selecione o Veredito", ["APROVADO", "REPROVADO", "EM ANÁLISE"])
                
                # FAROL VISUAL NA TELA DE DECISÃO
                if decisao == "APROVADO": st.success("🟢 STATUS: APROVADO")
                elif decisao == "REPROVADO": st.error("🔴 STATUS: REPROVADO")
                else: st.warning("🟡 STATUS: EM ANÁLISE")
                
                obs = st.text_area("Justificativa / Observações Finais")
                
        with c_save:
            with st.container(border=True):
                st.markdown("#### Ações")
                if st.button("💾"):
                    if save_data(d.get("empresa"), decisao, json.dumps(d), obs):
                        st.success("Salvo com sucesso no Google Sheets!")
                        time.sleep(1.5)
                        limpar_analise()
                
                st.markdown("---")
                if st.button("📄Baixar PDF"):
                    try:
                        pdf = gerar_pdf_bytes(d, decisao, obs)
                        st.download_button("⬇️ Baixar Relatório Oficial", pdf, "Relatorio_Credito.pdf", "application/pdf")
                    except: st.error("Erro ao gerar PDF")
        
        st.write("")
        if st.button("Voltar"): st.session_state.step = 3; st.rerun()

# 
# TELA: DASHBOARD
# 
elif menu == "Dashboard":
    st.markdown("## 📊 Dashboard Gerencial")
    df = load_data()
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"""<div class="kpi-card"><p style="font-size: 2rem; font-weight: bold; margin: 0;">{len(df)}</p><p style="color: gray; margin: 0;">Total de Análises</p></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="kpi-card" style="border-left-color: #27ae60;"><p style="font-size: 2rem; font-weight: bold; margin: 0; color: #27ae60;">{len(df[df['status'].str.contains('APROVADO', na=False)])}</p><p style="color: gray; margin: 0;">Aprovados</p></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="kpi-card" style="border-left-color: #c0392b;"><p style="font-size: 2rem; font-weight: bold; margin: 0; color: #c0392b;">{len(df[df['status'] == 'REPROVADO'])}</p><p style="color: gray; margin: 0;">Reprovados</p></div>""", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.subheader("Distribuição de Vereditos")
            st.bar_chart(df['status'].value_counts(), color=COR_PRIMARIA)

# 
# TELA: HISTÓRICO (COM RESTAURAÇÃO DO PDF E FAROL)
# 
elif menu == "Histórico":
    st.markdown("## 🗂️ Histórico de Análises")
    df = load_data()
    
    if not df.empty:
        st.info("Selecione uma linha na tabela abaixo para visualizar os detalhes e baixar o PDF.")
        
        # Tabela com seleção ativada (Restauração da função)
        event = st.dataframe(
            df[['data_registro', 'cliente', 'status']], 
            selection_mode="single-row", 
            on_select="rerun", 
            use_container_width=True, 
            hide_index=True
        )
        
        # Lógica para quando uma linha é clicada
        if len(event.selection.rows) > 0:
            idx = event.selection.rows[0]
            registro = df.iloc[idx]
            
            with st.container(border=True):
                st.markdown(f"### 📄 Cliente: {registro['cliente']}")
                
                # FAROL VISUAL NO HISTÓRICO
                cor_farol = "🟢" if registro['status'] == 'APROVADO' else "🔴" if registro['status'] == 'REPROVADO' else "🟡"
                st.markdown(f"**Veredito:** {cor_farol} {registro['status']}")
                st.markdown(f"**Data:** {registro['data_registro']}")
                
                try:
                    dados_rec = json.loads(registro['dados_json'])
                    pdf = gerar_pdf_bytes(dados_rec, registro['status'], registro['obs_final'])
                    st.write("")
                    st.download_button("⬇️ Baixar PDF Desta Análise", pdf, f"Relatorio_{registro['cliente']}.pdf", "application/pdf", type="primary")
                except Exception as e: 
                    st.error(f"Erro ao processar dados antigos: {e}")
