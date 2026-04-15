import streamlit as st
import pandas as pd
from services.ai_service import AIService
from views.components.uicomponents import show_toast, ai_progress, render_upload_status

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
    <h3 style="font-family:'Space Grotesk',sans-serif; font-weight:700; margin-bottom:20px;">
        <i class="bi bi-bar-chart-fill" style="color:#F47920; margin-right:8px;"></i> Auditoria Contábil
    </h3>
    """, unsafe_allow_html=True)

    # Mensagens persistidas via session_state (sobrevivem ao st.rerun)
    if st.session_state.get('_contabil_erro'):
        st.error("Não foi possível realizar a auditoria contábil. Verifique se os PDFs são válidos e tente novamente.")
        del st.session_state['_contabil_erro']
    if st.session_state.get('_contabil_aviso'):
        st.warning(st.session_state['_contabil_aviso'])
        del st.session_state['_contabil_aviso']

    if d.get("alerta_divergencia_contabil"):
        st.error(f"🚨 **ALERTA DE DIVERGÊNCIA:** {d.get('alerta_divergencia_contabil')}")

    with st.container(border=True):
        uploaded = st.file_uploader("PDFs Contábeis (Balanços e DREs)", type="pdf", accept_multiple_files=True, key="up5")
        res_up5 = st.session_state.get("_res_up5")
        if uploaded:
            render_upload_status(uploaded, res_up5)
        if uploaded and st.button("Executar Auditoria Avançada"):
            with ai_progress("contabil", "Consolidando auditoria financeira..."):
                res = ai.auditar_contabil(
                    uploaded,
                    d.get('empresa', ''),
                    d.get('cnpj', ''),
                    d.get('aluguel', 0),
                    d.get('iptu', 0)
                )
                if res:
                    st.session_state.dados.update(res)
                    st.session_state.dados["checklist_docs"]["Passo 5 (Contábil)"] = [f.name for f in uploaded]
                    st.session_state["_res_up5"] = {f.name: True for f in uploaded}
                    if not (res.get("receita_bruta") or res.get("analise_executiva")):
                        st.session_state['_contabil_aviso'] = "Análise concluída, mas alguns dados financeiros não foram identificados nos documentos. Verifique se os PDFs contêm Balanço e DRE."
            if res:
                periodos_ext = st.session_state.dados.get("periodos", [])
                receitas_ext = st.session_state.dados.get("receita_bruta", [])
                n_per = len(periodos_ext)
                msg_contabil = f"✅ Auditoria contábil concluída — {n_per} período(s) processado(s)" if n_per else "✅ Auditoria contábil concluída!"
                if receitas_ext:
                    msg_contabil += f" · Receita {receitas_ext[-1]}"
                show_toast(msg_contabil, "success")
                st.rerun()
            else:
                st.session_state['_contabil_erro'] = True
                st.rerun()

    # ── VISUALIZAÇÃO FINANCEIRA (Matriz e Gráfico) ────────────────
    if "periodos" in d or d.get("receita_bruta") or d.get("analise_executiva"):
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
                erros = []
                rb = st.session_state.dados.get("receita_bruta", "")
                if (isinstance(rb, list) and len(rb) == 0) or (not isinstance(rb, list) and not str(rb).strip()):
                    erros.append("Receita Bruta")
                res_val = st.session_state.dados.get("resultado", "")
                if (isinstance(res_val, list) and len(res_val) == 0) or (not isinstance(res_val, list) and not str(res_val).strip()):
                    erros.append("Resultado")
                if erros:
                    st.error(f"Preencha os campos obrigatórios: {', '.join(erros)}")
                else:
                    st.session_state.step = 6
                    show_toast(":material/receipt_long: IR dos Sócios — carregue as declarações", "info")
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
                erros = []
                rb = st.session_state.dados.get("receita_bruta", "")
                if (isinstance(rb, list) and len(rb) == 0) or (not isinstance(rb, list) and not str(rb).strip()):
                    erros.append("Receita Bruta")
                res_val = st.session_state.dados.get("resultado", "")
                if (isinstance(res_val, list) and len(res_val) == 0) or (not isinstance(res_val, list) and not str(res_val).strip()):
                    erros.append("Resultado")
                if erros:
                    st.error(f"Preencha os campos obrigatórios: {', '.join(erros)}")
                else:
                    st.session_state.step = 6
                    show_toast(":material/receipt_long: IR dos Sócios — carregue as declarações", "info")
                    st.rerun()
