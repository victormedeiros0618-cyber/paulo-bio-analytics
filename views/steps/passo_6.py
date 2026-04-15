import streamlit as st
from services.ai_service import AIService
from views.components.uicomponents import show_toast, ai_progress

def show_passo_6():
    d = st.session_state.dados
    ai = AIService()
    
    st.markdown("""
    <h3 style="font-weight: 700; margin-bottom: 20px;">
        <i class="bi bi-safe-fill" style="color: #F47920; margin-right: 8px;"></i> Garantia Física (IR Sócios)
    </h3>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.container(border=True):
            uploaded = st.file_uploader("Upload IR Sócios (Múltiplos PDFs)", type="pdf", accept_multiple_files=True, key="up6")
            if uploaded and st.button("Analisar Patrimônio"):
                with ai_progress("patrimonio", "Consolidando análise patrimonial..."):
                    res = ai.analisar_patrimonio_socios(uploaded, d)
                    if res:
                        st.session_state.dados.update(res)
                        st.session_state.dados["checklist_docs"]["Passo 6 (IR Sócios)"] = [f.name for f in uploaded]
                        show_toast("✅ Patrimônio dos sócios analisado!", "success")
                        st.rerun()
                    else:
                        st.error("Não foi possível analisar o patrimônio. Verifique se os PDFs são válidos e tente novamente.")
    with c2:
        with st.container(border=True):
            st.session_state.dados["conclusao_socio"] = st.text_area("Conclusão Patrimonial (Sócios) *", d.get("conclusao_socio", ""), height=150)
            st.session_state.dados["parecer_final"] = st.text_area("Pré-Parecer Jurídico Gerado *", d.get("parecer_final", ""), height=300)
            
            st.write("") 
            st.write("")
            c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
            with c_b1:
                if st.button("Voltar"): 
                    st.session_state.step = 5
                    show_toast("↩️ Retornando ao Passo 5", "info")
                    st.rerun()
            with c_b2:
                if st.button("Avançar"):
                    erros = []
                    if not st.session_state.dados.get("conclusao_socio", "").strip():
                        erros.append("Conclusão Patrimonial (Sócios)")
                    if not st.session_state.dados.get("parecer_final", "").strip():
                        erros.append("Pré-Parecer Jurídico Gerado")
                    if erros:
                        st.error(f"Preencha os campos obrigatórios: {', '.join(erros)}")
                    else:
                        st.session_state.step = 7
                        show_toast(":material/rate_review: Parecer Final — revise e emita o veredito", "info")
                        st.rerun()
