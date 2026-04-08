import streamlit as st
from services.ai_service import AIService
from views.components.uicomponents import show_toast, empty_state

def show_passo_0():
    d = st.session_state.dados
    ai = AIService()
    
    st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <h3 style="font-weight: 700; margin-bottom: 20px;">
        <i class="bi bi-file-earmark-person-fill" style="color: #F47920; margin-right: 8px;"></i> Contrato Social e Aditivos
    </h3>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.container(border=True):
            uploaded = st.file_uploader("Upload Contrato e Aditivos (PDFs)", type="pdf", accept_multiple_files=True, key="up0")
            if uploaded and st.button("Extrair Dados Societários"):
                st.session_state.dados["checklist_docs"]["Passo 0 (Contrato Social)"] = [f.name for f in uploaded]
                with st.spinner("Analisando Documentos..."):
                    res = ai.extrair_contrato(uploaded)
                    st.session_state.dados.update(res)
                    show_toast("✅ Dados extraídos com sucesso!", "success")
                    st.rerun()
    with c2:
        with st.container(border=True):
            if not d.get("empresa"):
                empty_state("📄", "Nenhum dado carregado", "Preencha os campos abaixo ou faça upload do contrato para auto-preenchimento.")
            st.session_state.dados["empresa"] = st.text_input("Razão Social", d.get("empresa", ""))
            st.session_state.dados["cnpj"] = st.text_input("CNPJ", d.get("cnpj", ""))
            
            c_ab, c_cap = st.columns(2)
            st.session_state.dados["data_abertura"] = c_ab.text_input("Data Abertura / Idade", d.get("data_abertura", ""))
            st.session_state.dados["capital_social"] = c_cap.text_input("Capital Social", d.get("capital_social", ""))
            
            st.session_state.dados["socios_participacao"] = st.text_area("Quadro Societário (%)", d.get("socios_participacao", ""))
            st.session_state.dados["administrador"] = st.text_input("Administrador", d.get("administrador", ""))
            st.session_state.dados["endereco_empresa"] = st.text_input("Endereço da Sede", d.get("endereco_empresa", ""))
            st.session_state.dados["informacoes_adicionais"] = st.text_area("Informações Adicionais (Resumo de Aditivos)", d.get("informacoes_adicionais", ""))
            
            st.write("") 
            st.write("")
            c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
            with c_b2:
                if st.button("Avançar"):
                    st.session_state.step = 1
                    show_toast("Passo 1 - Proposta", "info")
                    st.rerun()
