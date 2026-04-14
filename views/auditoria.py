"""
views/auditoria.py
Tela de trilha de auditoria — exibe eventos da tabela audit_log do Supabase.
Paginação manual, filtros por ação, usuário e período.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from services.db_service import DBService
from core.logger import get_logger

logger = get_logger(__name__)

_PAGE_SIZE = 30

# ── Labels e cores por ação ───────────────────────────────────────────────────

_ACAO_LABELS = {
    "ANALISE_CRIADA":   "Análise criada",
    "ANALISE_EXCLUIDA": "Análise excluída",
}

_ACAO_CORES = {
    "ANALISE_CRIADA":   "#27AE60",
    "ANALISE_EXCLUIDA": "#E74C3C",
}


def _badge_acao(acao: str) -> str:
    label = _ACAO_LABELS.get(acao, acao)
    cor = _ACAO_CORES.get(acao, "#7F8C8D")
    return (
        f'<span style="background:{cor}22; color:{cor}; border:1px solid {cor}55; '
        f'border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600;">'
        f'{label}</span>'
    )


# ── Busca no Supabase ─────────────────────────────────────────────────────────

def _listar_eventos(db: DBService, limite: int = 500) -> list:
    """Busca eventos da tabela audit_log ordenados por timestamp desc."""
    try:
        headers = {
            "apikey": db.supabase_key,
            "Authorization": f"Bearer {db.supabase_key}",
            "Content-Type": "application/json",
        }
        import requests
        url = (
            f"{db.supabase_url}/rest/v1/audit_log"
            f"?select=*&order=timestamp.desc&limit={limite}"
        )
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
        logger.warning("audit_log retornou status %d", res.status_code)
        return []
    except Exception as e:
        logger.error("Erro ao buscar audit_log: %s", e)
        return []


# ── Preparação do DataFrame ───────────────────────────────────────────────────

def _preparar_df(eventos: list) -> pd.DataFrame:
    df = pd.DataFrame(eventos)
    if df.empty:
        return df

    if "timestamp" in df.columns:
        df["Data_Obj"] = pd.to_datetime(df["timestamp"], utc=True)
        df["Data"] = df["Data_Obj"].dt.strftime("%d/%m/%Y %H:%M")
        df["Data_Date"] = df["Data_Obj"].dt.date
    else:
        df["Data_Obj"] = pd.NaT
        df["Data"] = "—"
        df["Data_Date"] = None

    df["Acao_Label"] = df["acao"].map(_ACAO_LABELS).fillna(df["acao"])
    df["Usuario"] = df.get("usuario", "—")
    df["Entidade_ID"] = df.get("entidade_id", "—")
    df["Detalhe"] = df.get("detalhe", "—")
    return df


def _filtrar(
    df: pd.DataFrame,
    acoes_sel: list,
    usuarios_sel: list,
    data_ini: date,
    data_fim: date,
) -> pd.DataFrame:
    mask = pd.Series([True] * len(df), index=df.index)

    if acoes_sel:
        mask &= df["acao"].isin(acoes_sel)
    if usuarios_sel:
        mask &= df["Usuario"].isin(usuarios_sel)
    if df["Data_Date"].notna().any():
        mask &= df["Data_Date"].apply(
            lambda d: d is not None and data_ini <= d <= data_fim
        )
    return df[mask].copy()


# ── View principal ────────────────────────────────────────────────────────────

def show_auditoria():
    st.markdown("""
    <h3 style="color:#FFFFFF; font-family:'Space Grotesk',sans-serif; font-weight:700; margin-bottom:4px;">
        Trilha de Auditoria
    </h3>
    <p style="color:#7F8C8D; font-size:14px; margin-bottom:20px;">
        Registro imutável de todas as ações realizadas no sistema.
    </p>
    """, unsafe_allow_html=True)

    db = DBService()
    with st.spinner("Carregando eventos..."):
        eventos = _listar_eventos(db, limite=500)

    if not eventos:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon"><i class="bi bi-shield-check"></i></div>
            <div class="empty-state-title">Nenhum evento registrado ainda</div>
            <div class="empty-state-desc">
                Os eventos aparecem aqui conforme as ações são realizadas no sistema.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    df = _preparar_df(eventos)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total = len(df)
    criadas = len(df[df["acao"] == "ANALISE_CRIADA"])
    excluidas = len(df[df["acao"] == "ANALISE_EXCLUIDA"])
    usuarios_ativos = df["Usuario"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Eventos", total)
    c2.metric("Análises Criadas", criadas)
    c3.metric("Análises Excluídas", excluidas)
    c4.metric("Usuários Ativos", usuarios_ativos)

    st.divider()

    # ── Filtros ───────────────────────────────────────────────────────────────
    with st.expander("\u00a0\u00a0Filtros", expanded=False):
        col_acao, col_usuario = st.columns(2)

        with col_acao:
            acoes_disponiveis = sorted(df["acao"].unique().tolist())
            acoes_sel = st.multiselect(
                "Ação",
                options=acoes_disponiveis,
                default=[],
                format_func=lambda a: _ACAO_LABELS.get(a, a),
                placeholder="Todas as ações",
            )

        with col_usuario:
            usuarios = sorted(df["Usuario"].dropna().unique().tolist())
            usuarios_sel = st.multiselect(
                "Usuário",
                options=usuarios,
                default=[],
                placeholder="Todos os usuários",
            )

        col_d1, col_d2, col_reset = st.columns([2, 2, 1])
        data_min = df["Data_Date"].dropna().min() if df["Data_Date"].notna().any() else date.today() - timedelta(days=90)
        data_max = df["Data_Date"].dropna().max() if df["Data_Date"].notna().any() else date.today()

        with col_d1:
            data_ini = st.date_input("De", value=data_min, min_value=data_min, max_value=data_max, format="DD/MM/YYYY")
        with col_d2:
            data_fim = st.date_input("Até", value=data_max, min_value=data_min, max_value=data_max, format="DD/MM/YYYY")
        with col_reset:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Limpar", use_container_width=True):
                st.rerun()

    # ── Filtrar e paginar ─────────────────────────────────────────────────────
    df_filtrado = _filtrar(df, acoes_sel, usuarios_sel, data_ini, data_fim)
    df_filtrado = df_filtrado.sort_values("Data_Obj", ascending=False)

    total_filtrado = len(df_filtrado)
    total_paginas = max(1, (total_filtrado + _PAGE_SIZE - 1) // _PAGE_SIZE)

    if "auditoria_pagina" not in st.session_state:
        st.session_state.auditoria_pagina = 1

    pagina_atual = min(st.session_state.auditoria_pagina, total_paginas)

    st.markdown(
        f'<span style="color:#7F8C8D; font-size:12px;">'
        f'{total_filtrado} evento(s) · Página {pagina_atual}/{total_paginas}</span>',
        unsafe_allow_html=True,
    )

    inicio = (pagina_atual - 1) * _PAGE_SIZE
    df_pagina = df_filtrado.iloc[inicio: inicio + _PAGE_SIZE]

    # ── Tabela de eventos ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    for _, row in df_pagina.iterrows():
        col_data, col_acao, col_detalhe, col_usuario = st.columns([1.5, 1.5, 4, 2])

        with col_data:
            st.markdown(
                f'<span style="color:#7F8C8D; font-size:12px;">{row["Data"]}</span>',
                unsafe_allow_html=True,
            )
        with col_acao:
            st.markdown(_badge_acao(row["acao"]), unsafe_allow_html=True)
        with col_detalhe:
            st.markdown(
                f'<span style="font-size:13px; color:#C8D6E5;">{row["Detalhe"]}</span>',
                unsafe_allow_html=True,
            )
        with col_usuario:
            st.markdown(
                f'<span style="color:#7F8C8D; font-size:12px;">{row["Usuario"]}</span>',
                unsafe_allow_html=True,
            )

    # ── Paginação ─────────────────────────────────────────────────────────────
    if total_paginas > 1:
        st.divider()
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.button("← Anterior", disabled=pagina_atual <= 1):
                st.session_state.auditoria_pagina = pagina_atual - 1
                st.rerun()
        with col_info:
            nova_pag = st.number_input(
                "Ir para página", min_value=1, max_value=total_paginas,
                value=pagina_atual, step=1, label_visibility="collapsed",
            )
            if nova_pag != pagina_atual:
                st.session_state.auditoria_pagina = int(nova_pag)
                st.rerun()
        with col_next:
            if st.button("Próxima →", disabled=pagina_atual >= total_paginas):
                st.session_state.auditoria_pagina = pagina_atual + 1
                st.rerun()
