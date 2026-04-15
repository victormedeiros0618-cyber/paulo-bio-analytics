import streamlit as st
from services.ai_service import AIService
from views.components.uicomponents import show_toast, ai_progress, render_upload_status

# Mapeia risco para classe CSS e emoji
def _classe_risco(risco: str):
    r = risco.lower()
    if "baixo" in r: return "verde", "🟢"
    if "medio" in r or "médio" in r: return "amarelo", "🟡"
    if "alto" in r: return "vermelho", "🔴"
    return "", ""

def show_passo_3():
    d = st.session_state.dados
    ai = AIService()

    st.markdown("""
    <h3 style="color:#FFFFFF; font-family:'Space Grotesk',sans-serif; font-weight:700; margin-bottom:20px;">
        <i class="bi bi-shield-lock-fill" style="color:#F47920; margin-right:8px;"></i> Análise de Risco (Serasa)
    </h3>
    """, unsafe_allow_html=True)

    if d.get("alerta_divergencia_serasa"):
        st.error(f"🚨 **ALERTA DE DIVERGÊNCIA:** {d.get('alerta_divergencia_serasa')}")

    c1, c2 = st.columns([1, 2])

    # ── COLUNA UPLOAD ────────────────────────────────────────────
    with c1:
        with st.container(border=True):
            uploaded = st.file_uploader("Upload Serasa (Múltiplos PDFs)", type="pdf", accept_multiple_files=True, key="up3")
            res_up3 = st.session_state.get("_res_up3")
            if uploaded:
                render_upload_status(uploaded, res_up3)
            if uploaded and st.button("Mapear Pendências"):
                st.session_state.dados["checklist_docs"]["Passo 3 (Serasa)"] = [f.name for f in uploaded]
                with ai_progress("serasa", "Consolidando mapa de riscos..."):
                    res = ai.mapear_serasa(uploaded, d.get('empresa', ''), d.get('cnpj', ''))
                    if res:
                        st.session_state.dados.update(res)
                if res:
                    st.session_state["_res_up3"] = {f.name: True for f in uploaded}
                    score = st.session_state.dados.get("score_serasa", "")
                    risco = st.session_state.dados.get("risco_serasa", "")
                    partes = [p for p in [score and f"Score {score}", risco and f"Risco {risco}"] if p]
                    sufixo = " — " + " · ".join(partes) if partes else ""
                    show_toast(f"✅ Mapa de riscos Serasa consolidado{sufixo}!", "success")
                    st.rerun()
                else:
                    st.error("Não foi possível extrair os dados do Serasa. Verifique se os PDFs são válidos e tente novamente.")

    # ── COLUNA RESULTADOS ────────────────────────────────────────
    with c2:
        score = d.get("score_serasa", "")
        risco = d.get("risco_serasa", "")

        # Exibe KPI cards se já existe score extraído
        if score or risco:
            css_classe, emoji = _classe_risco(risco)
            st.markdown(f"""
            <div class="kpi-grid">
                <div class="kpi-card {css_classe}">
                    <div class="kpi-label">Score Serasa</div>
                    <div class="kpi-value">{score if score else "—"}</div>
                    <div class="kpi-sub">Pontuação de crédito</div>
                </div>
                <div class="kpi-card {css_classe}">
                    <div class="kpi-label">Nível de Risco</div>
                    <div class="kpi-value">{emoji} {risco if risco else "—"}</div>
                    <div class="kpi-sub">Classificação Serasa</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Campos de input manuais enquanto não houver extração
            with st.container(border=True):
                c_score, c_risco = st.columns(2)
                st.session_state.dados["score_serasa"] = c_score.text_input("Score Serasa *", d.get("score_serasa", ""))
                st.session_state.dados["risco_serasa"] = c_risco.text_input("Nível de Risco *", d.get("risco_serasa", ""))

        # Mapeamento de dividas sempre editável
        with st.container(border=True):
            st.session_state.dados["mapeamento_dividas"] = st.text_area(
                "Mapeamento de Riscos (Restrições)", d.get("mapeamento_dividas", ""), height=220
            )

        st.write("")
        c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])
        with c_b1:
            if st.button("Voltar"): 
                st.session_state.step = 2
                show_toast("↩️ Retornando ao Passo 2", "info")
                st.rerun()
        with c_b2:
            if st.button("Avançar"):
                erros = []
                if not st.session_state.dados.get("score_serasa", "").strip():
                    erros.append("Score Serasa")
                if not st.session_state.dados.get("risco_serasa", "").strip():
                    erros.append("Nível de Risco")
                if erros:
                    st.error(f"Preencha os campos obrigatórios: {', '.join(erros)}")
                else:
                    st.session_state.step = 4
                    show_toast(":material/gavel: Certidões jurídicas — carregue as certidões", "info")
                    st.rerun()
