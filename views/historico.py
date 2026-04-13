import streamlit as st
import pandas as pd
from datetime import date, timedelta
from services.db_service import DBService
from services.pdf_service import gerar_pdf_bytes
from core.logger import get_logger

logger = get_logger(__name__)

_PAGE_SIZE = 15


def _strip_emoji(texto: str) -> str:
    """Remove o prefixo de emoji de um status. Ex: '✅ APROVADO' → 'APROVADO'."""
    partes = texto.split(" ", 1)
    # Se o primeiro "token" é um emoji (len <= 2 chars ou contém U+FE0F), descarta
    if len(partes) == 2 and len(partes[0]) <= 2:
        return partes[1]
    return texto


def _preparar_df(registros: list) -> pd.DataFrame:
    df = pd.DataFrame(registros)
    if "created_at" in df.columns:
        df["Data_Obj"] = pd.to_datetime(df["created_at"], utc=True)
        df["Data"] = df["Data_Obj"].dt.strftime("%d/%m/%Y %H:%M")
        df["Data_Date"] = df["Data_Obj"].dt.date
    else:
        df["Data_Obj"] = pd.NaT
        df["Data"] = "—"
        df["Data_Date"] = None

    df["Empresa"] = df.get("empresa", "—")
    df["CNPJ"] = df.get("cnpj", "—")
    df["Status"] = df.get("status", "—")
    df["Analista"] = df.get("usuario_nome", "—")
    df["Aluguel"] = pd.to_numeric(df.get("aluguel", 0), errors="coerce").fillna(0)
    return df


def _filtrar(df: pd.DataFrame, busca: str, status_sel: list, analista_sel: list,
             data_ini: date, data_fim: date) -> pd.DataFrame:
    mask = pd.Series([True] * len(df), index=df.index)

    if busca:
        mask &= (
            df["Empresa"].str.contains(busca, case=False, na=False)
            | df["CNPJ"].str.contains(busca, case=False, na=False)
        )
    if status_sel:
        mask &= df["Status"].isin(status_sel)
    if analista_sel:
        mask &= df["Analista"].isin(analista_sel)
    if df["Data_Date"].notna().any():
        mask &= df["Data_Date"].apply(
            lambda d: (d is not None) and (data_ini <= d <= data_fim)
        )

    return df[mask].copy()


def show_historico():
    st.markdown("""
    <h3 style="color:#FFFFFF; font-family:'Space Grotesk',sans-serif; font-weight:700; margin-bottom:4px;">
        Histórico de Análises
    </h3>
    <p style="color:#7F8C8D; font-size:14px; margin-bottom:20px;">
        Consulte, filtre, baixe PDFs ou gerencie as análises anteriores.
    </p>
    """, unsafe_allow_html=True)

    db = DBService()
    with st.spinner("Conectando ao banco de dados..."):
        registros = db.listar_analises(limite=500)

    if not registros:
        st.warning("Nenhuma análise encontrada ou falha na conexão.")
        return

    df = _preparar_df(registros)

    # ── FILTROS ───────────────────────────────────────────────────────────────
    with st.expander(
        "\u00a0\u00a0Filtros",  # espaço para o ícone BI renderizado via CSS no label
        expanded=True,
    ):
        # Ícone Bootstrap no título do expander via CSS injetado
        st.markdown("""
        <style>
            /* Substitui o ícone padrão do expander pelo BI funnel */
            details[data-testid="stExpander"] > summary::before {
                font-family: "bootstrap-icons" !important;
                content: "\\F3D0" !important;  /* bi-funnel */
                margin-right: 6px;
                font-size: 14px;
                color: #F47920;
                vertical-align: middle;
            }
            /* Remove o emoji 🔍 que ficaria duplicado */
            details[data-testid="stExpander"] > summary span {
                font-size: 14px;
                font-weight: 600;
                color: #C8D6E5;
            }
        </style>
        """, unsafe_allow_html=True)

        # Linha 1: Busca | Status | Analista — proporções equilibradas
        col_busca, col_status, col_analista = st.columns([2, 2, 2])

        with col_busca:
            busca = st.text_input(
                "Empresa ou CNPJ",
                placeholder="Digite para buscar...",
                label_visibility="collapsed",
            )

        with col_status:
            status_opcoes = sorted(df["Status"].dropna().unique().tolist())
            status_sel = st.multiselect(
                "Status",
                options=status_opcoes,
                default=status_opcoes,
                placeholder="Todos os status",
                # Exibe só o texto sem emoji na tag selecionada e no dropdown
                format_func=_strip_emoji,
            )

        with col_analista:
            analistas = sorted(df["Analista"].dropna().unique().tolist())
            analista_sel = st.multiselect(
                "Analista", options=analistas, default=[],
                placeholder="Todos os analistas",
            )

        col_d1, col_d2, col_reset = st.columns([2, 2, 1])
        data_min = df["Data_Date"].dropna().min() if df["Data_Date"].notna().any() else date.today() - timedelta(days=365)
        data_max = df["Data_Date"].dropna().max() if df["Data_Date"].notna().any() else date.today()

        with col_d1:
            data_ini = st.date_input(
                "De", value=data_min, min_value=data_min, max_value=data_max,
                format="DD/MM/YYYY",
            )
        with col_d2:
            data_fim = st.date_input(
                "Até", value=data_max, min_value=data_min, max_value=data_max,
                format="DD/MM/YYYY",
            )
        with col_reset:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Limpar", use_container_width=True):
                st.rerun()

    # ── FILTRAR + PAGINAR ─────────────────────────────────────────────────────
    df_filtrado = _filtrar(df, busca, status_sel, analista_sel, data_ini, data_fim)
    df_filtrado = df_filtrado.sort_values("Data_Obj", ascending=False)

    total_filtrado = len(df_filtrado)
    total_paginas = max(1, (total_filtrado + _PAGE_SIZE - 1) // _PAGE_SIZE)

    if "historico_pagina" not in st.session_state:
        st.session_state.historico_pagina = 1

    pagina_atual = min(st.session_state.historico_pagina, total_paginas)

    st.markdown(
        f'<span style="color:#7F8C8D; font-size:12px;">'
        f'{total_filtrado} análise(s) encontrada(s) · Página {pagina_atual}/{total_paginas}</span>',
        unsafe_allow_html=True,
    )

    inicio = (pagina_atual - 1) * _PAGE_SIZE
    fim = inicio + _PAGE_SIZE
    df_pagina = df_filtrado.iloc[inicio:fim]

    # ── GRID (multi-row selection) ────────────────────────────────────────────
    colunas_exibicao = ["Data", "Empresa", "CNPJ", "Analista", "Status"]
    event = st.dataframe(
        df_pagina[colunas_exibicao],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
    )

    # Paginação
    if total_paginas > 1:
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.button("← Anterior", disabled=pagina_atual <= 1):
                st.session_state.historico_pagina = pagina_atual - 1
                st.rerun()
        with col_info:
            nova_pag = st.number_input(
                "Ir para página", min_value=1, max_value=total_paginas,
                value=pagina_atual, step=1, label_visibility="collapsed",
            )
            if nova_pag != pagina_atual:
                st.session_state.historico_pagina = int(nova_pag)
                st.rerun()
        with col_next:
            if st.button("Próxima →", disabled=pagina_atual >= total_paginas):
                st.session_state.historico_pagina = pagina_atual + 1
                st.rerun()

    selected_rows = event.selection.get("rows", [])

    # ── EXCLUSÃO EM LOTE (multi-select) ───────────────────────────────────────
    if len(selected_rows) > 1:
        st.divider()
        n = len(selected_rows)
        st.markdown(
            f'<span style="color:#F1C40F; font-size:13px;">'
            f'<i class="bi bi-check2-square"></i>&nbsp;{n} análise(s) selecionada(s)</span>',
            unsafe_allow_html=True,
        )

        if st.button(
            f"🗑️ Excluir selecionados ({n})",
            type="secondary",
            use_container_width=False,
        ):
            st.session_state["_confirmar_exclusao_lote"] = [
                df_pagina.iloc[i].get("id", "") for i in selected_rows
            ]

        lote_ids = st.session_state.get("_confirmar_exclusao_lote", [])
        if lote_ids:
            st.warning(f"Confirmar exclusão de **{len(lote_ids)} análise(s)**? Esta ação é irreversível.")
            col_sim, col_nao = st.columns([1, 3])
            with col_sim:
                if st.button("✅ Confirmar exclusão", use_container_width=True):
                    erros = 0
                    for rid in lote_ids:
                        if rid and not db.excluir_analise(rid):
                            erros += 1
                    st.session_state.pop("_confirmar_exclusao_lote", None)
                    if erros == 0:
                        st.toast(f"{len(lote_ids)} análise(s) excluída(s) com sucesso.")
                    else:
                        st.error(f"{erros} exclusão(ões) falharam.")
                    st.rerun()
            with col_nao:
                if st.button("❌ Cancelar", use_container_width=False):
                    st.session_state.pop("_confirmar_exclusao_lote", None)
                    st.rerun()
        return  # não exibe detalhe individual quando há múltipla seleção

    # ── DETALHE DO REGISTRO SELECIONADO (seleção única) ───────────────────────
    if not selected_rows:
        return

    idx_na_pagina = selected_rows[0]
    registro_selecionado = df_pagina.iloc[idx_na_pagina]
    registro_real = df.loc[registro_selecionado.name]
    dados_json = registro_real.get("dados") or {}

    st.divider()
    st.markdown(f"### {registro_real['Empresa']}")

    col_det, col_acoes = st.columns([3, 1])

    with col_det:
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Status", registro_real["Status"])
        col_m2.metric("Analista", registro_real["Analista"])
        col_m3.metric("Data", registro_real["Data"])

        observacao = dados_json.get("parecer_oficial", "Sem parecer no registro.")
        st.markdown("**Parecer:**")
        st.info(observacao)

        checklist = dados_json.get("checklist_docs", {})
        if checklist:
            with st.expander("📚 Documentos Analisados"):
                for passo, arquivos in checklist.items():
                    if arquivos:
                        st.markdown(f"**✅ {passo}:**")
                        for arq in arquivos:
                            st.caption(f"- {arq}")

    with col_acoes:
        st.markdown("<br>", unsafe_allow_html=True)

        # Download PDF
        if st.button("📥 Baixar PDF", type="primary", use_container_width=True):
            with st.spinner("Gerando PDF..."):
                try:
                    pdf_bytes = gerar_pdf_bytes(dados_json, str(registro_real["Status"]))
                    st.download_button(
                        label="💾 Salvar PDF",
                        data=pdf_bytes,
                        file_name=f"Relatorio_{registro_real['Empresa']}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    logger.error("Erro ao gerar PDF do histórico: %s", e)
                    st.error(f"Erro ao gerar PDF: {e}")

        # Exclusão unitária
        st.markdown("<br>", unsafe_allow_html=True)
        registro_id = registro_real.get("id", "")

        if st.button("🗑️ Excluir", use_container_width=True):
            st.session_state["_confirmar_exclusao"] = registro_id

        if st.session_state.get("_confirmar_exclusao") == registro_id:
            st.warning("Confirmar exclusão?")
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button("✅ Sim", use_container_width=True):
                    sucesso = db.excluir_analise(registro_id)
                    if sucesso:
                        st.success("Registro excluído.")
                        st.session_state.pop("_confirmar_exclusao", None)
                        st.rerun()
                    else:
                        st.error("Erro ao excluir.")
            with col_nao:
                if st.button("❌ Não", use_container_width=True):
                    st.session_state.pop("_confirmar_exclusao", None)
                    st.rerun()
