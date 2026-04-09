import streamlit as st
from services.ai_service import AIService
from views.components.uicomponents import show_toast

def show_passo_2():
    d = st.session_state.dados
    ai = AIService()
    
    st.markdown("""
    <h3 style="font-weight: 700; margin-bottom: 20px;">
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
                    res = ai.extrair_referencias(uploaded)
                    if res:
                        st.session_state.dados.update(res)
                        show_toast("✅ Referências extraídas!", "success")
                        st.rerun()
                    else:
                        st.error("Não foi possível extrair as referências. Verifique se o PDF é válido e tente novamente.")
    with c2:
        with st.container(border=True):
            st.session_state.dados["ref_locaticias"] = st.text_area("Referências Locatícias", d.get("ref_locaticias", ""))
            st.session_state.dados["ref_comerciais"] = st.text_area("Referências Comerciais", d.get("ref_comerciais", ""))
            st.session_state.dados["ref_bancarias"] = st.text_area("Referências Bancárias", d.get("ref_bancarias", ""))
            
            st.write("") 
            st.write("")
            c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
            with c_b1:
                if st.button("Voltar"): 
                    st.session_state.step = 1
                    show_toast("↩️ Retornando ao Passo 1", "info")
                    st.rerun()
            with c_b2:
                if st.button("Avançar"): 
                    st.session_state.step = 3
                    show_toast("Passo 3 - Serasa", "info")
                    st.rerun()
