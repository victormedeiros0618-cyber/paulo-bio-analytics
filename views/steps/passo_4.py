import streamlit as st
from services.ai_service import AIService
from views.components.uicomponents import show_toast

def show_passo_4():
    d = st.session_state.dados
    ai = AIService()
    
    st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <h3 style="font-weight: 700; margin-bottom: 20px;">
        <i class="bi bi-scales" style="color: #F47920; margin-right: 8px;"></i> Certidões Jurídicas
    </h3>
    """, unsafe_allow_html=True)
    
    if d.get("alerta_divergencia_certidoes"):
        st.error(f"🚨 **ALERTA DE DIVERGÊNCIA:** {d.get('alerta_divergencia_certidoes')}")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.container(border=True):
            uploaded = st.file_uploader("Upload Lote de Certidões", accept_multiple_files=True, key="up4")
            if uploaded and st.button("Auditar Certidões"):
                st.session_state.dados["checklist_docs"]["Passo 4 (Certidões)"] = [f.name for f in uploaded]
                with st.spinner("Lendo certidões..."):
                    res = ai.auditar_certidoes(uploaded, d.get('empresa', ''), d.get('cnpj', ''))
                    st.session_state.dados.update(res)
                    show_toast("✅ Certidões auditadas!", "success")
                    st.rerun()
    with c2:
        with st.container(border=True):
            st.session_state.dados["resumo_certidoes"] = st.text_area("Apontamentos Jurídicos", d.get("resumo_certidoes", ""), height=250)
            
            st.write("") 
            st.write("")
            c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
            with c_b1:
                if st.button("Voltar"): 
                    st.session_state.step = 3
                    show_toast("↩️ Retornando ao Passo 3", "info")
                    st.rerun()
            with c_b2:
                if st.button("Avançar"): 
                    st.session_state.step = 5
                    show_toast("Passo 5 - Contábil", "info")
                    st.rerun()
