import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.db_service import DBService
from core.config import COR_PRIMARIA
from utils.formatters import formatar_moeda_br

# ── Constantes ────────────────────────────────────────────────────────────────
# Mapeamento limpo: status com emoji → label sem emoji para exibição
_LABEL_LIMPO = {
    "✅ APROVADO": "APROVADO",
    "⚠️ APROVADO COM RESSALVA": "APROVADO COM RESSALVA",
    "❌ REPROVADO": "REPROVADO",
}

# Color map usa labels limpos (sem emoji)
_COLOR_MAP = {
    "APROVADO": "#27AE60",
    "APROVADO COM RESSALVA": "#F1C40F",
    "REPROVADO": "#E74C3C",
}

_PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#C8D6E5", size=12),
    margin=dict(t=10, b=10, l=0, r=0),
)

# Meses em PT-BR para formatar eixo X (2026-04 → "Abr/2026")
_MESES_PT = {
    "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
    "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
    "09": "Set", "10": "Out", "11": "Nov", "12": "Dez",
}


def _label_mes(mes_str: str) -> str:
    """Converte '2026-04' → 'Abr/2026'."""
    try:
        ano, mes = mes_str.split("-")
        return f"{_MESES_PT.get(mes, mes)}/{ano}"
    except Exception:
        return mes_str


def _preparar_df(registros: list) -> pd.DataFrame:
    df = pd.DataFrame(registros)
    df["Status"] = df.get("status", "—")
    df["Aluguel"] = pd.to_numeric(df.get("aluguel", 0), errors="coerce").fillna(0)
    df["Empresa"] = df.get("empresa", "—")
    df["Analista"] = df.get("usuario_nome", "—")

    if "created_at" in df.columns:
        df["Data_Obj"] = pd.to_datetime(df["created_at"], utc=True)
        df["Data"] = df["Data_Obj"].dt.strftime("%d/%m/%Y")
        # Fix bug: usar strftime em vez de to_period().astype(str) que quebra com UTC
        df["Mes"] = df["Data_Obj"].dt.strftime("%Y-%m")
    else:
        df["Data_Obj"] = pd.NaT
        df["Data"] = "—"
        df["Mes"] = "—"

    # Coluna com labels limpos (sem emoji) para gráficos
    df["Status_Label"] = df["Status"].map(_LABEL_LIMPO).fillna(df["Status"])

    return df


def _kpi_card(label: str, valor: str, cor: str = "", sub: str = "") -> str:
    classe = f"kpi-card {cor}" if cor else "kpi-card"
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="{classe}" style="{'border-left-color:' + COR_PRIMARIA + ';' if not cor else ''}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: clamp(1.1rem, 2vw, 1.5rem);
        ">{valor}</div>
        {sub_html}
    </div>
    """


def _grafico_pizza(df: pd.DataFrame) -> go.Figure:
    counts = df["Status_Label"].value_counts().reset_index()
    counts.columns = ["Status", "Quantidade"]
    fig = px.pie(
        counts, values="Quantidade", names="Status", hole=0.42,
        color="Status", color_discrete_map=_COLOR_MAP,
    )
    fig.update_layout(
        **_PLOTLY_LAYOUT,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.30,
            xanchor="center", x=0.5,
            font=dict(size=11),
        ),
    )
    # Apenas % dentro da fatia, sem label
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        insidetextfont=dict(size=13, color="#FFFFFF"),
    )
    return fig


def _grafico_tendencia(df: pd.DataFrame) -> go.Figure:
    """Barras agrupadas de análises por mês × status."""
    if "Mes" not in df.columns or df["Mes"].eq("—").all():
        return go.Figure()

    # Agrupa por mês e status limpo
    tendencia = (
        df.groupby(["Mes", "Status_Label"])
        .size()
        .reset_index(name="Qtd")
        .sort_values("Mes")
    )

    if tendencia.empty:
        return go.Figure()

    # Labels PT-BR para eixo X
    tendencia["Mes_Label"] = tendencia["Mes"].apply(_label_mes)

    fig = px.bar(
        tendencia,
        x="Mes_Label",
        y="Qtd",
        color="Status_Label",
        barmode="group",
        color_discrete_map=_COLOR_MAP,
        labels={"Mes_Label": "Mês", "Qtd": "Análises", "Status_Label": ""},
        text="Qtd",
    )
    fig.update_layout(
        **_PLOTLY_LAYOUT,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.35,
            xanchor="center", x=0.5,
            font=dict(size=11),
        ),
        xaxis=dict(tickangle=-30, categoryorder="array",
                   categoryarray=tendencia["Mes_Label"].unique().tolist()),
        bargap=0.2,
        bargroupgap=0.05,
    )
    fig.update_traces(textposition="outside", textfont=dict(size=11))
    return fig


def _grafico_vgl_status(df: pd.DataFrame) -> go.Figure:
    vgl = df.groupby("Status_Label")["Aluguel"].sum().reset_index()
    fig = px.bar(
        vgl, x="Status_Label", y="Aluguel",
        color="Status_Label", color_discrete_map=_COLOR_MAP,
        text_auto=".2s",
        labels={"Aluguel": "VGL (R$)", "Status_Label": ""},
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
        st.markdown("##### VGL por Status")
        st.plotly_chart(_grafico_vgl_status(df), use_container_width=True)

    st.divider()

    # ── GRÁFICO TENDÊNCIA ─────────────────────────────────────────────────────
    st.markdown("##### Análises por Mês e Status")
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
