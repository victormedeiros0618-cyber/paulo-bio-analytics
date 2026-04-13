import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.db_service import DBService
from core.config import COR_PRIMARIA
from utils.formatters import formatar_moeda_br

# ── Constantes ────────────────────────────────────────────────────────────────
_COLOR_MAP = {
    "✅ APROVADO": "#27AE60",
    "⚠️ APROVADO COM RESSALVA": "#F1C40F",
    "❌ REPROVADO": "#E74C3C",
}
_PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#C8D6E5", size=12),
    margin=dict(t=10, b=10, l=0, r=0),
)


def _preparar_df(registros: list) -> pd.DataFrame:
    df = pd.DataFrame(registros)
    df["Status"] = df.get("status", "—")
    df["Aluguel"] = pd.to_numeric(df.get("aluguel", 0), errors="coerce").fillna(0)
    df["Empresa"] = df.get("empresa", "—")
    df["Analista"] = df.get("usuario_nome", "—")

    if "created_at" in df.columns:
        df["Data_Obj"] = pd.to_datetime(df["created_at"], utc=True)
        df["Data"] = df["Data_Obj"].dt.strftime("%d/%m/%Y")
        df["Mes"] = df["Data_Obj"].dt.to_period("M").astype(str)
    else:
        df["Data_Obj"] = pd.NaT
        df["Data"] = "—"
        df["Mes"] = "—"

    return df


def _kpi_card(label: str, valor: str, cor: str = "", sub: str = "") -> str:
    classe = f"kpi-card {cor}" if cor else "kpi-card"
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="{classe}" style="{'border-left-color:' + COR_PRIMARIA + ';' if not cor else ''}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{valor}</div>
        {sub_html}
    </div>
    """


def _grafico_pizza(df: pd.DataFrame) -> go.Figure:
    counts = df["Status"].value_counts().reset_index()
    counts.columns = ["Status", "Quantidade"]
    fig = px.pie(
        counts, values="Quantidade", names="Status", hole=0.42,
        color="Status", color_discrete_map=_COLOR_MAP,
    )
    fig.update_layout(**_PLOTLY_LAYOUT, legend=dict(
        orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5
    ))
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def _grafico_tendencia(df: pd.DataFrame) -> go.Figure:
    """Linha de análises por mês, com série por status."""
    if "Mes" not in df.columns or df["Mes"].eq("—").all():
        return go.Figure()

    # Agrupa por mês e status
    tendencia = (
        df.groupby(["Mes", "Status"])
        .size()
        .reset_index(name="Qtd")
        .sort_values("Mes")
    )

    fig = px.line(
        tendencia, x="Mes", y="Qtd", color="Status",
        color_discrete_map=_COLOR_MAP,
        markers=True,
        labels={"Mes": "Mês", "Qtd": "Análises", "Status": ""},
    )
    fig.update_layout(
        **_PLOTLY_LAYOUT,
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
        xaxis=dict(tickangle=-30),
    )
    fig.update_traces(line=dict(width=2.5), marker=dict(size=7))
    return fig


def _grafico_vgl_status(df: pd.DataFrame) -> go.Figure:
    vgl = df.groupby("Status")["Aluguel"].sum().reset_index()
    fig = px.bar(
        vgl, x="Status", y="Aluguel",
        color="Status", color_discrete_map=_COLOR_MAP,
        text_auto=".2s",
        labels={"Aluguel": "VGL (R$)", "Status": ""},
    )
    fig.update_layout(**_PLOTLY_LAYOUT, showlegend=False)
    fig.update_traces(textposition="outside")
    return fig


def show_dashboard():
    st.markdown("""
    <h3 style="color:#FFFFFF; font-family:'Space Grotesk',sans-serif; font-weight:700; margin-bottom:4px;">
        Dashboard de Performance
    </h3>
    <p style="color:#7F8C8D; font-size:14px; margin-bottom:20px;">
        Visão executiva e financeira das análises de risco locatício.
    </p>
    """, unsafe_allow_html=True)

    db = DBService()
    with st.spinner("Carregando estatísticas..."):
        registros = db.listar_analises(limite=500)

    if not registros:
        st.warning("Nenhuma análise encontrada ou falha na conexão com o banco.")
        return

    df = _preparar_df(registros)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total = len(df)
    df_aprov = df[df["Status"].str.contains("APROVADO", na=False)]
    tx_aprov = (len(df_aprov) / total * 100) if total > 0 else 0
    vgl_total = df_aprov["Aluguel"].sum()
    ticket_medio = df["Aluguel"].mean() if total > 0 else 0
    analistas_ativos = df["Analista"].nunique()

    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(_kpi_card("Total de Análises", str(total)), unsafe_allow_html=True)
    with c2:
        cor = "verde" if tx_aprov >= 60 else ("amarelo" if tx_aprov >= 40 else "vermelho")
        st.markdown(_kpi_card("Taxa de Aprovação", f"{tx_aprov:.1f}%", cor), unsafe_allow_html=True)
    with c3:
        st.markdown(_kpi_card("VGL Aprovado", formatar_moeda_br(vgl_total), "verde"), unsafe_allow_html=True)
    with c4:
        st.markdown(_kpi_card("Ticket Médio (Aluguel)", formatar_moeda_br(ticket_medio)), unsafe_allow_html=True)
    with c5:
        st.markdown(_kpi_card("Analistas Ativos", str(analistas_ativos)), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ── GRÁFICOS — linha 1 ────────────────────────────────────────────────────
    col_pizza, col_vgl = st.columns([1, 2])

    with col_pizza:
        st.markdown("##### Proporção de Status")
        st.plotly_chart(_grafico_pizza(df), use_container_width=True)

    with col_vgl:
        st.markdown("##### VGL Aprovado por Status")
        st.plotly_chart(_grafico_vgl_status(df), use_container_width=True)

    st.divider()

    # ── GRÁFICO TENDÊNCIA ─────────────────────────────────────────────────────
    st.markdown("##### Tendência Mensal de Análises")
    fig_trend = _grafico_tendencia(df)
    if fig_trend.data:
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Dados insuficientes para exibir tendência mensal.")

    st.divider()

    # ── TABELA ÚLTIMAS ────────────────────────────────────────────────────────
    st.markdown("##### Últimas Análises Realizadas")
    df_ultimas = (
        df.sort_values("Data_Obj", ascending=False).head(10).copy()
        if "Data_Obj" in df.columns
        else df.head(10).copy()
    )
    df_ultimas["Valor (VGL)"] = df_ultimas["Aluguel"].apply(formatar_moeda_br)
    st.dataframe(
        df_ultimas[["Data", "Empresa", "Analista", "Valor (VGL)", "Status"]],
        use_container_width=True,
        hide_index=True,
    )
