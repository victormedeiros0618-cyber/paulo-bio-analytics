import streamlit as st
from services.pdf_service import gerar_pdf_bytes
from services.db_service import DBService
from views.components.uicomponents import show_toast

_VEREDITOS = {
    "✅ APROVADO": {
        "css": "aprovado",
        "icon": "bi-check-circle-fill",
        "sub": "Operação recomendada para prosseguimento."
    },
    "⚠️ APROVADO COM RESSALVA": {
        "css": "ressalva",
        "icon": "bi-exclamation-triangle-fill",
        "sub": "Aprovação condicionada às ressalvas descritas no parecer."
    },
    "❌ REPROVADO": {
        "css": "reprovado",
        "icon": "bi-x-circle-fill",
        "sub": "Operação não recomendada. Ver fundamentação no parecer."
    },
}

def show_passo_7():
    d = st.session_state.dados
    db = DBService()

    st.markdown("""
    <h3 style="font-family:'Space Grotesk',sans-serif; font-weight:700; margin-bottom:20px;">
        <i class="bi bi-file-earmark-check-fill" style="color:#F47920; margin-right:8px;"></i> Parecer e Veredito Final
    </h3>
    """, unsafe_allow_html=True)

    # Parecer gerado pela IA em destaque
    parecer_ia = d.get("parecer_final", "")
    if parecer_ia:
        with st.expander("📋 Pré-Parecer Gerado pela IA (Base)", expanded=False):
            st.info(parecer_ia)

    with st.container(border=True):
        st.markdown('<i class="bi bi-pencil-square" style="color:#F47920; margin-right:8px;"></i> **Parecer Jurídico Oficial** *', unsafe_allow_html=True)
        parecer_oficial = st.text_area(
            "Este campo será incluído no PDF",
            d.get("parecer_oficial", parecer_ia),
            height=200,
            label_visibility="collapsed"
        )
        st.session_state.dados["parecer_oficial"] = parecer_oficial

    # ── SOLUÇÃO COMPLEMENTAR ────────────────────────────────────────
    st.markdown("""
    <h4 style="font-family:'Space Grotesk',sans-serif; font-weight:600; margin-top:16px; margin-bottom:12px;">
        <i class="bi bi-lightbulb" style="color:#F47920; margin-right:8px;"></i> Solução Complementar
    </h4>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown('<span style="font-size:12px;">Sugira alternativas: aumento de garantia, fiador adicional, prazos especiais, etc.</span>', unsafe_allow_html=True)
        solucao_complementar = st.text_area(
            "Descreva a solução complementar sugerida",
            d.get("solucao_complementar", ""),
            height=100,
            label_visibility="collapsed",
            placeholder="Ex: Solicitar fiador adicional, aumentar depósito caução para 3 meses..."
        )
        st.session_state.dados["solucao_complementar"] = solucao_complementar

    st.divider()

    # ── SELEÇÃO DO VEREDITO ────────────────────────────────────────
    st.markdown("### Veredito da Operação")
    decisao = st.radio(
        "Selecione o Veredito",
        list(_VEREDITOS.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )

    # Card visual do veredito selecionado
    info = _VEREDITOS[decisao]
    st.markdown(f"""
    <div class="veredito-card {info['css']}">
        <div class="veredito-icon"><i class="bi {info['icon']}"></i></div>
        <div class="veredito-body">
            <div class="veredito-label">{decisao}</div>
            <div class="veredito-sub">{info['sub']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # ── AÇÃO FINAL ────────────────────────────────────────────────
    if st.button("📄 Finalizar Análise e Gerar Relatório", type="primary"):
        erros = []
        if not st.session_state.dados.get("parecer_oficial", "").strip():
            erros.append("Parecer Jurídico Oficial")
        if erros:
            st.error(f"Preencha os campos obrigatórios: {', '.join(erros)}")
        else:
            with st.spinner("Salvando e gerando PDF..."):
                pdf_data = None

                # 1. Tenta salvar no Supabase primeiro (independente do PDF)
                salvo = False
                try:
                    salvo = db.salvar_analise(d, decisao)
                    if salvo:
                        st.success("✅ Análise salva no histórico!")
                except Exception as e:
                    st.warning(f"⚠️ Erro ao salvar no histórico: {e}")

                # 2. Gera PDF
                try:
                    pdf_data = gerar_pdf_bytes(d, decisao)
                except Exception as e:
                    st.error(f"❌ Erro ao gerar PDF: {e}")
                    pdf_data = None

                # 3. Oferece download
                if pdf_data:
                    st.download_button(
                        label="📥 Baixar Relatório Executivo (PDF)",
                        data=pdf_data,
                        file_name=f"Relatorio_{d.get('empresa', 'Analise')}.pdf",
                        mime="application/pdf"
                    )
                    show_toast("✅ Relatório gerado com sucesso!", "success")
                else:
                    show_toast("⚠️ PDF não disponível, mas análise foi salva.", "warning")

    if st.button("Voltar"):
        st.session_state.step = 6
        show_toast("↩️ Retornando ao Passo 6", "info")
        st.rerun()
