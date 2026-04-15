import difflib
import streamlit as st
from services.pdf_service import gerar_pdf_bytes
from services.db_service import DBService
from views.components.uicomponents import show_toast


def _render_diff(texto_original: str, texto_editado: str) -> str:
    """
    Gera HTML com diff inline: adições em verde, remoções em vermelho.
    Compara palavra a palavra para granularidade fina.
    """
    palavras_orig = texto_original.split()
    palavras_edit = texto_editado.split()
    matcher = difflib.SequenceMatcher(None, palavras_orig, palavras_edit, autojunk=False)

    partes_orig: list[str] = []
    partes_edit: list[str] = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        orig_chunk = " ".join(palavras_orig[i1:i2])
        edit_chunk = " ".join(palavras_edit[j1:j2])
        if op == "equal":
            partes_orig.append(orig_chunk)
            partes_edit.append(edit_chunk)
        elif op == "replace":
            partes_orig.append(f'<span style="background:rgba(231,76,60,0.25);color:#E74C3C;border-radius:2px;padding:0 2px;">{orig_chunk}</span>')
            partes_edit.append(f'<span style="background:rgba(39,174,96,0.25);color:#27AE60;border-radius:2px;padding:0 2px;">{edit_chunk}</span>')
        elif op == "delete":
            partes_orig.append(f'<span style="background:rgba(231,76,60,0.25);color:#E74C3C;border-radius:2px;padding:0 2px;">{orig_chunk}</span>')
        elif op == "insert":
            partes_edit.append(f'<span style="background:rgba(39,174,96,0.25);color:#27AE60;border-radius:2px;padding:0 2px;">{edit_chunk}</span>')

    html_orig = " ".join(partes_orig)
    html_edit = " ".join(partes_edit)

    # Calcula % de similaridade
    ratio = round(matcher.ratio() * 100, 1)
    cor_ratio = "#27AE60" if ratio >= 80 else ("#F1C40F" if ratio >= 50 else "#E74C3C")

    return f"""
    <div style="margin-top:12px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:11px; color:#7F8C8D; text-transform:uppercase; letter-spacing:.06em;">
                Comparação Parecer IA × Editado
            </span>
            <span style="font-size:11px; color:{cor_ratio}; font-weight:600;">
                {ratio}% de similaridade
            </span>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
            <div style="background:#1A2636; border:1px solid rgba(231,76,60,0.3); border-radius:2px; padding:12px;">
                <div style="font-size:10px; color:#E74C3C; font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-bottom:8px;">
                    ← Versão IA
                </div>
                <div style="font-size:12px; color:#C8D6E5; line-height:1.6;">{html_orig}</div>
            </div>
            <div style="background:#1A2636; border:1px solid rgba(39,174,96,0.3); border-radius:2px; padding:12px;">
                <div style="font-size:10px; color:#27AE60; font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-bottom:8px;">
                    Versão Editada →
                </div>
                <div style="font-size:12px; color:#C8D6E5; line-height:1.6;">{html_edit}</div>
            </div>
        </div>
    </div>
    """

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

    # Parecer gerado pela IA — guardar versão original para diff
    parecer_ia = d.get("parecer_final", "")
    # Preserva a versão original da IA na primeira vez que o passo é exibido
    if parecer_ia and "_parecer_ia_original" not in st.session_state:
        st.session_state["_parecer_ia_original"] = parecer_ia

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

        # ── DIFF VISUAL IA × EDITADO ────────────────────────────────────────
        parecer_orig = st.session_state.get("_parecer_ia_original", "")
        if parecer_orig and parecer_oficial and parecer_orig.strip() != parecer_oficial.strip():
            with st.expander(":material/compare: Ver diferenças em relação ao parecer da IA", expanded=False):
                st.markdown(
                    _render_diff(parecer_orig, parecer_oficial),
                    unsafe_allow_html=True,
                )

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
    <article class="veredito-card {info['css']}" role="region" aria-label="Veredito da análise: {decisao}">
        <div class="veredito-icon" aria-hidden="true"><i class="bi {info['icon']}"></i></div>
        <div class="veredito-body">
            <h2 class="veredito-label">{decisao}</h2>
            <p class="veredito-sub">{info['sub']}</p>
        </div>
    </article>
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
                    cfg_usr = st.session_state.get("config_usuario", {})
                    pdf_data = gerar_pdf_bytes(d, decisao, config_usuario=cfg_usr)
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
