import streamlit as st
import pandas as pd
from services.ai_service import AIService
from views.components.uicomponents import show_toast

def _calcular_comprometimento(aluguel_raw, receita_list):
    """Calcula % de comprometimento da receita pelo aluguel."""
    try:
        aluguel_val = float(str(aluguel_raw).replace('R$', '').replace('.', '').replace(',', '.').strip())
        if not receita_list or receita_list[-1] in ["-", ""]:
            return None
        receita_val = float(str(receita_list[-1]).replace('R$', '').replace('.', '').replace(',', '.').strip())
        if receita_val <= 0:
            return None
        return round((aluguel_val / receita_val) * 100, 1)
    except Exception:
        return None

def _cor_comprometimento(pct):
    if pct is None: return "", "—"
    if pct <= 8: return "verde", f"{pct}%"
    if pct <= 15: return "amarelo", f"{pct}%"
    return "vermelho", f"{pct}%"

def show_passo_5():
    d = st.session_state.dados
    ai = AIService()

    st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <h3 style="font-family:'Space Grotesk',sans-serif; font-weight:700; margin-bottom:20px;">
        <i class="bi bi-bar-chart-fill" style="color:#F47920; margin-right:8px;"></i> Auditoria Contábil
    </h3>
    """, unsafe_allow_html=True)

    if d.get("alerta_divergencia_contabil"):
        st.error(f"🚨 **ALERTA DE DIVERGÊNCIA:** {d.get('alerta_divergencia_contabil')}")

    with st.container(border=True):
        uploaded = st.file_uploader("PDFs Contábeis (Balanços e DREs)", accept_multiple_files=True, key="up5")
        if uploaded and st.button("Executar Auditoria Avançada"):
            import time
            msgs = [
                "📄 Carregando Balanços e DREs...",
                "📊 Mapeando série histórica de receitas...",
                "🔢 Calculando indicadores (Solvência, Liquidez)...",
                "🧠 Elaborando parecer do auditor IA...",
            ]
            placeholder = st.empty()
            for msg in msgs:
                placeholder.info(msg)
                time.sleep(0.7)
            with placeholder.container():
                with st.spinner("Consolidando auditoria financeira..."):
                    res = ai.auditar_contabil(
                        uploaded,
                        d.get('empresa', ''),
                        d.get('cnpj', ''),
                        d.get('aluguel', 0),
                        d.get('iptu', 0)
                    )
                    st.session_state.dados.update(res)
                    st.session_state.dados["checklist_docs"]["Passo 5 (Contábil)"] = [f.name for f in uploaded]
            placeholder.empty()
            show_toast("✅ Auditoria contábil concluída!", "success")
            st.rerun()

    # ── VISUALIZAÇÃO FINANCEIRA (Matriz e Gráfico) ────────────────
    if "periodos" in d:
        periodos  = d.get("periodos", [])
        receitas  = d.get("receita_bruta", [])
        lucros    = d.get("resultado", [])

        # Normaliza listas
        if not isinstance(periodos, list): periodos = [periodos] if periodos else []
        if not isinstance(receitas, list): receitas = [receitas] if receitas else []
        if not isinstance(lucros,   list): lucros   = [lucros]   if lucros   else []

        max_len = max(len(periodos), len(receitas), len(lucros), 1)
        periodos += ["-"] * (max_len - len(periodos))
        receitas += ["-"] * (max_len - len(receitas))
        lucros   += ["-"] * (max_len - len(lucros))

        c1, c2 = st.columns([1, 1.5])

        with c1:
            st.markdown("#### Matriz Financeira")
            try:
                df_fin = pd.DataFrame({
                    "Período": periodos,
                    "Receita": receitas,
                    "Lucro":   lucros
                })
                st.dataframe(df_fin, use_container_width=True, hide_index=True)
            except Exception:
                st.warning("Dados financeiros desalinhados.")

        with c2:
            st.markdown("#### Evolução do Resultado")
            try:
                valores = []
                for x in lucros:
                    if x == "-":
                        valores.append(0.0)
                    else:
                        v = str(x).replace('R$', '').strip().replace('.', '').replace(',', '.')
                        v = ''.join([c for c in v if c.isdigit() or c in '.-'])
                        try:
                            valores.append(float(v) if v and v not in ['.', '-', '.-'] else 0.0)
                        except Exception:
                            valores.append(0.0)

                st.bar_chart(
                    pd.DataFrame({"Resultado (R$)": valores}, index=periodos),
                    color="#F47920"
                )
            except Exception:
                pass

        # Parecer dentro de expander
        st.write("")
        with st.container(border=True):
            st.markdown("#### Parecer do Auditor IA")
            st.write(d.get("analise_executiva", "Não disponível."))

        st.write("")
        c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])
        with c_b1:
            if st.button("Voltar"): 
                st.session_state.step = 4
                show_toast("↩️ Retornando ao Passo 4", "info")
                st.rerun()
        with c_b2:
            if st.button("Avançar"): 
                st.session_state.step = 6
                show_toast("Passo 6 - IR", "info")
                st.rerun()

    else:
        # Botões de nav mesmo quando ainda não há dados
        st.write("")
        c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])
        with c_b1:
            if st.button("Voltar"): 
                st.session_state.step = 4
                show_toast("↩️ Retornando ao Passo 4", "info")
                st.rerun()
        with c_b2:
            if st.button("Avançar"): 
                st.session_state.step = 6
                show_toast("Passo 6 - IR", "info")
                st.rerun()
