"""
skeletons.py
Funções de skeleton loading para Streamlit.

Padrão de uso:
    placeholder = st.empty()
    with placeholder.container():
        skeleton_historico()          # exibe placeholders
    dados = db.listar_analises()      # query real
    placeholder.empty()               # remove skeletons
    # renderiza conteúdo real abaixo
"""

import streamlit as st

# ── CSS compartilhado ─────────────────────────────────────────────────────────
_SKELETON_CSS = """
<style>
@keyframes pb-shimmer {
    0%   { background-position: -600px 0; }
    100% { background-position: 600px 0; }
}
.pb-skel {
    background: linear-gradient(90deg, #2C3E50 25%, #374f63 50%, #2C3E50 75%);
    background-size: 600px 100%;
    animation: pb-shimmer 1.4s infinite linear;
    border-radius: 6px;
    display: inline-block;
}
</style>
"""

_KPI_CARD_HTML = """
<div style="background:#1e2d3d;border-radius:10px;padding:18px 20px;margin-bottom:4px;">
    <div class="pb-skel" style="height:12px;width:55%;margin-bottom:10px;"></div>
    <div class="pb-skel" style="height:28px;width:40%;margin-bottom:6px;"></div>
    <div class="pb-skel" style="height:10px;width:70%;"></div>
</div>
"""

_TABLE_ROW_HTML = """
<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #2C3E50;">
    <div class="pb-skel" style="height:12px;width:14%;"></div>
    <div class="pb-skel" style="height:12px;width:22%;"></div>
    <div class="pb-skel" style="height:12px;width:18%;"></div>
    <div class="pb-skel" style="height:18px;width:12%;border-radius:20px;"></div>
    <div class="pb-skel" style="height:12px;width:14%;"></div>
    <div class="pb-skel" style="height:12px;width:10%;"></div>
</div>
"""

_CHART_CARD_HTML = """
<div style="background:#1e2d3d;border-radius:10px;padding:18px 20px;">
    <div class="pb-skel" style="height:14px;width:40%;margin-bottom:16px;"></div>
    <div class="pb-skel" style="height:{height}px;width:100%;border-radius:8px;"></div>
</div>
"""


def _inject_css() -> None:
    st.markdown(_SKELETON_CSS, unsafe_allow_html=True)


# ── Skeletons públicos ────────────────────────────────────────────────────────

def skeleton_historico() -> None:
    """Skeleton para a página de Histórico: filtros + tabela paginada."""
    _inject_css()

    # Filtros
    st.markdown(
        '<div class="pb-skel" style="height:38px;width:100%;margin-bottom:16px;"></div>',
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    for col in (col1, col2, col3, col4):
        with col:
            st.markdown(
                '<div class="pb-skel" style="height:38px;width:100%;"></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Header da tabela
    st.markdown(
        '<div class="pb-skel" style="height:14px;width:30%;margin-bottom:12px;"></div>',
        unsafe_allow_html=True,
    )

    # Linhas
    rows_html = _TABLE_ROW_HTML * 8
    st.markdown(
        f'<div style="background:#1e2d3d;border-radius:10px;padding:12px 16px;">'
        f'{rows_html}</div>',
        unsafe_allow_html=True,
    )

    # Paginação
    st.markdown("<br>", unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns([1, 3, 1])
    with col_p2:
        st.markdown(
            '<div class="pb-skel" style="height:36px;width:60%;margin:0 auto;border-radius:20px;"></div>',
            unsafe_allow_html=True,
        )


def skeleton_dashboard() -> None:
    """Skeleton para o Dashboard: 5 KPI cards + 2 gráficos."""
    _inject_css()

    # KPI cards — 5 colunas
    cols = st.columns(5)
    for col in cols:
        with col:
            st.markdown(_KPI_CARD_HTML, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Linha de gráficos — barras + pizza
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown(
            _CHART_CARD_HTML.format(height=220),
            unsafe_allow_html=True,
        )
    with col_right:
        st.markdown(
            _CHART_CARD_HTML.format(height=220),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Linha inferior — gráfico de linha largo
    st.markdown(
        _CHART_CARD_HTML.format(height=160),
        unsafe_allow_html=True,
    )
