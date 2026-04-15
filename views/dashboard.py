import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.db_service import DBService
from core.config import COR_PRIMARIA
from utils.formatters import formatar_moeda_br
from views.components.skeletons import skeleton_dashboard

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
    sub_html = f'<div class="kpi-sub" aria-label="Variação: {sub}">{sub}</div>' if sub else ""
    borda = f"border-left-color:{COR_PRIMARIA};" if not cor else ""
    style_card = f"{borda} min-height:80px;"
    return (
        f'<div class="{classe}" style="{style_card}" role="region" aria-label="Métrica: {label}">'
        f'<div class="kpi-label" aria-hidden="true">{label}</div>'
        f'<div class="kpi-value" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:22px;" '
        f'aria-label="{label}: {valor}">{valor}</div>'
        f'{sub_html}'
        f'</div>'
    )


def _calcular_tendencia_mes(df: pd.DataFrame) -> dict:
    """Calcula variação do mês atual vs anterior para KPIs."""
    if "Mes" not in df.columns or df["Mes"].eq("—").all():
        return {}

    meses = sorted(df["Mes"].unique())
    if len(meses) < 2:
        return {}

    mes_atual = meses[-1]
    mes_anterior = meses[-2]
    df_atual = df[df["Mes"] == mes_atual]
    df_anterior = df[df["Mes"] == mes_anterior]

    total_atual = len(df_atual)
    total_anterior = len(df_anterior)
    delta_total = total_atual - total_anterior

    aprov_atual = len(df_atual[df_atual["Status"].str.contains("APROVADO", na=False)])
    aprov_anterior = len(df_anterior[df_anterior["Status"].str.contains("APROVADO", na=False)])

    vgl_atual = df_atual[df_atual["Status"].str.contains("APROVADO", na=False)]["Aluguel"].sum()
    vgl_anterior = df_anterior[df_anterior["Status"].str.contains("APROVADO", na=False)]["Aluguel"].sum()

    def _seta(delta: float) -> str:
        if delta > 0:
            return f'<span style="color:#27AE60;">↑ +{int(delta)}</span>'
        elif delta < 0:
            return f'<span style="color:#E74C3C;">↓ {int(delta)}</span>'
        return '<span style="color:#7F8C8D;">= 0</span>'

    return {
        "total": _seta(delta_total),
        "vgl": _seta(vgl_atual - vgl_anterior),
        "aprovacoes": _seta(aprov_atual - aprov_anterior),
    }


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


def _section_header(titulo: str, icone: str = "") -> str:
    """Gera HTML de cabeçalho de seção com barra laranja lateral — padrão visual do relatório PDF."""
    icon_html = f'<i class="bi {icone}" style="margin-right:8px; font-size:14px; color:#F47920;"></i>' if icone else ""
    return f"""
    <div style="
        display:flex; align-items:center;
        border-left:3px solid #F47920;
        padding:6px 0 6px 12px;
        margin:8px 0 12px 0;
    ">
        {icon_html}
        <span style="
            font-family:'Space Grotesk',sans-serif;
            font-size:15px; font-weight:700;
            color:#FFFFFF !important;
            letter-spacing:-0.01em;
        ">{titulo}</span>
    </div>
    """


def _grafico_volume_mensal(df: pd.DataFrame) -> go.Figure:
    """Barras empilhadas de volume total por mês."""
    if "Mes" not in df.columns or df["Mes"].eq("—").all():
        return go.Figure()

    vol = (
        df.groupby(["Mes", "Status_Label"])
        .size()
        .reset_index(name="Qtd")
        .sort_values("Mes")
    )
    vol["Mes_Label"] = vol["Mes"].apply(_label_mes)

    fig = px.bar(
        vol, x="Mes_Label", y="Qtd", color="Status_Label",
        barmode="stack",
        color_discrete_map=_COLOR_MAP,
        labels={"Mes_Label": "Mês", "Qtd": "Análises", "Status_Label": ""},
        text="Qtd",
    )
    fig.update_layout(
        **_PLOTLY_LAYOUT,
        legend=dict(orientation="h", yanchor="bottom", y=-0.35,
                    xanchor="center", x=0.5, font=dict(size=11)),
        xaxis=dict(tickangle=-30, categoryorder="array",
                   categoryarray=vol["Mes_Label"].unique().tolist()),
    )
    fig.update_traces(textposition="inside", textfont_size=11)
    return fig


def _grafico_taxa_aprovacao_mensal(df: pd.DataFrame) -> go.Figure:
    """Linha de taxa de aprovação (%) por mês."""
    if "Mes" not in df.columns or df["Mes"].eq("—").all():
        return go.Figure()

    meses = sorted(df["Mes"].unique())
    dados = []
    for mes in meses:
        dfm = df[df["Mes"] == mes]
        total = len(dfm)
        if total == 0:
            continue
        aprovados = len(dfm[dfm["Status"].str.contains("APROVADO", na=False)])
        taxa = round(aprovados / total * 100, 1)
        dados.append({"Mes": mes, "Mes_Label": _label_mes(mes), "Taxa": taxa, "Total": total})

    if not dados:
        return go.Figure()

    dfp = pd.DataFrame(dados)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dfp["Mes_Label"], y=dfp["Taxa"],
        mode="lines+markers+text",
        text=dfp["Taxa"].apply(lambda v: f"{v}%"),
        textposition="top center",
        textfont=dict(size=11, color="#C8D6E5"),
        line=dict(color="#F47920", width=2.5),
        marker=dict(color="#F47920", size=8),
        name="Taxa de Aprovação",
    ))
    fig.add_hline(y=60, line_dash="dot", line_color="#27AE60",
                  annotation_text="Meta 60%", annotation_position="bottom right",
                  annotation_font_color="#27AE60")
    fig.update_layout(
        **_PLOTLY_LAYOUT,
        yaxis=dict(range=[0, 105], ticksuffix="%"),
        xaxis=dict(tickangle=-30),
        showlegend=False,
    )
    return fig


def _grafico_vgl_mensal(df: pd.DataFrame) -> go.Figure:
    """Barras de VGV (apenas análises aprovadas) por mês."""
    if "Mes" not in df.columns or df["Mes"].eq("—").all():
        return go.Figure()

    df_aprov = df[df["Status"].str.contains("APROVADO", na=False)].copy()
    if df_aprov.empty:
        return go.Figure()

    vgl_mes = (
        df_aprov.groupby("Mes")["Aluguel"]
        .sum()
        .reset_index()
        .sort_values("Mes")
    )
    vgl_mes["Mes_Label"] = vgl_mes["Mes"].apply(_label_mes)
    vgl_mes["VGL_Fmt"] = vgl_mes["Aluguel"].apply(
        lambda v: f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    fig = px.bar(
        vgl_mes, x="Mes_Label", y="Aluguel",
        text="VGL_Fmt",
        labels={"Mes_Label": "Mês", "Aluguel": "VGL Aprovado (R$)"},
        color_discrete_sequence=["#27AE60"],
    )
    fig.update_layout(
        **_PLOTLY_LAYOUT,
        showlegend=False,
        xaxis=dict(tickangle=-30, categoryorder="array",
                   categoryarray=vgl_mes["Mes_Label"].unique().tolist()),
    )
    fig.update_traces(textposition="outside", textfont_size=10)
    return fig


def _tabela_resumo_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Tabela resumo com total, aprovados, ressalvas, reprovados, taxa e VGL por mês."""
    if "Mes" not in df.columns or df["Mes"].eq("—").all():
        return pd.DataFrame()

    rows = []
    for mes in sorted(df["Mes"].unique()):
        dfm = df[df["Mes"] == mes]
        total = len(dfm)
        aprovados = len(dfm[dfm["Status"].str.contains("APROVADO", na=False) &
                             ~dfm["Status"].str.contains("RESSALVA", na=False)])
        ressalvas = len(dfm[dfm["Status"].str.contains("RESSALVA", na=False)])
        reprovados = len(dfm[dfm["Status"].str.contains("REPROVADO", na=False)])
        taxa = round((aprovados + ressalvas) / total * 100, 1) if total > 0 else 0
        vgl = dfm[dfm["Status"].str.contains("APROVADO", na=False)]["Aluguel"].sum()
        rows.append({
            "Mês": _label_mes(mes),
            "Total": total,
            "Aprovados": aprovados,
            "Ressalvas": ressalvas,
            "Reprovados": reprovados,
            "Taxa Aprov. (%)": f"{taxa}%",
            "VGL Aprovado": f"R$ {vgl:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."),
        })

    return pd.DataFrame(rows)


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
    _placeholder = st.empty()
    with _placeholder.container():
        skeleton_dashboard()
    registros = db.listar_analises(limite=500)
    _placeholder.empty()

    if not registros:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon"><i class="bi bi-graph-up"></i></div>
            <div class="empty-state-title">Nenhuma análise encontrada</div>
            <div class="empty-state-desc">
                Crie uma nova análise na aba "Nova Análise" para ver os indicadores aqui.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    df = _preparar_df(registros)

    # ── ABAS ──────────────────────────────────────────────────────────────────
    aba_visao, aba_mensal = st.tabs([
        ":material/speed: Visão Geral",
        ":material/calendar_month: Relatório Mensal",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 1 — Visão Geral (conteúdo original)
    # ══════════════════════════════════════════════════════════════════════════
    with aba_visao:
        # ── FILTRO DE PERÍODO ──────────────────────────────────────────────────
        meses_todos = sorted(df["Mes"].unique()) if "Mes" in df.columns else []
        df_vis = df.copy()  # df filtrado para a visão geral

        if meses_todos:
            col_fv1, col_fv2, col_fv_reset = st.columns([1, 1, 1])
            with col_fv1:
                mes_vis_ini = st.selectbox(
                    "De",
                    options=meses_todos,
                    index=0,
                    format_func=_label_mes,
                    key="visao_mes_ini",
                )
            with col_fv2:
                mes_vis_fim = st.selectbox(
                    "Até",
                    options=meses_todos,
                    index=len(meses_todos) - 1,
                    format_func=_label_mes,
                    key="visao_mes_fim",
                )
            with col_fv_reset:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Todos os períodos", use_container_width=True, key="visao_reset"):
                    st.session_state.visao_mes_ini = meses_todos[0]
                    st.session_state.visao_mes_fim = meses_todos[-1]
                    st.rerun()

            if mes_vis_ini <= mes_vis_fim:
                df_vis = df[(df["Mes"] >= mes_vis_ini) & (df["Mes"] <= mes_vis_fim)].copy()
            periodo_label = f"{_label_mes(mes_vis_ini)} → {_label_mes(mes_vis_fim)}"
            st.markdown(
                f'<p style="color:#7F8C8D; font-size:12px; margin:0 0 12px;">'
                f'Exibindo: <strong style="color:#F47920;">{periodo_label}</strong> · '
                f'{len(df_vis)} análise(s)</p>',
                unsafe_allow_html=True,
            )

        # ── KPIs ──────────────────────────────────────────────────────────────
        total = len(df_vis)
        df_aprov = df_vis[df_vis["Status"].str.contains("APROVADO", na=False)]
        tx_aprov = (len(df_aprov) / total * 100) if total > 0 else 0
        vgl_total = df_aprov["Aluguel"].sum()
        ticket_medio = df_vis["Aluguel"].mean() if total > 0 else 0
        analistas_ativos = df_vis["Analista"].nunique()

        tend = _calcular_tendencia_mes(df_vis)
        sub_total = f"vs mês anterior {tend['total']}" if tend.get("total") else ""
        sub_vgl = f"vs mês anterior {tend['vgl']}" if tend.get("vgl") else ""

        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(_kpi_card("Total de Análises", str(total), sub=sub_total), unsafe_allow_html=True)
        with c2:
            cor = "verde" if tx_aprov >= 60 else ("amarelo" if tx_aprov >= 40 else "vermelho")
            st.markdown(_kpi_card("Taxa de Aprovação", f"{tx_aprov:.1f}%", cor), unsafe_allow_html=True)
        with c3:
            st.markdown(_kpi_card("VGL Aprovado", formatar_moeda_br(vgl_total), "verde", sub=sub_vgl), unsafe_allow_html=True)
        with c4:
            st.markdown(_kpi_card("Ticket Médio (Aluguel)", formatar_moeda_br(ticket_medio)), unsafe_allow_html=True)
        with c5:
            st.markdown(_kpi_card("Analistas Ativos", str(analistas_ativos)), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # ── GRÁFICOS — linha 1 ────────────────────────────────────────────────
        col_pizza, col_vgl = st.columns([1, 2])
        with col_pizza:
            st.markdown(_section_header("Proporção de Status", "bi-pie-chart"), unsafe_allow_html=True)
            st.plotly_chart(_grafico_pizza(df_vis), use_container_width=True)
        with col_vgl:
            st.markdown(_section_header("VGL por Status", "bi-currency-dollar"), unsafe_allow_html=True)
            st.plotly_chart(_grafico_vgl_status(df_vis), use_container_width=True)

        st.divider()

        # ── GRÁFICO TENDÊNCIA ─────────────────────────────────────────────────
        st.markdown(_section_header("Análises por Mês e Status", "bi-bar-chart-line"), unsafe_allow_html=True)
        fig_trend = _grafico_tendencia(df_vis)
        if fig_trend.data:
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.markdown("""
            <div class="empty-state" style="padding:24px;">
                <div class="empty-state-icon" style="font-size:32px;"><i class="bi bi-bar-chart-line"></i></div>
                <div class="empty-state-desc">Dados insuficientes para exibir tendência mensal.</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # ── TABELA ÚLTIMAS ─────────────────────────────────────────────────────
        st.markdown(_section_header("Últimas Análises Realizadas", "bi-clock-history"), unsafe_allow_html=True)
        df_ultimas = (
            df_vis.sort_values("Data_Obj", ascending=False).head(10).copy()
            if "Data_Obj" in df_vis.columns
            else df_vis.head(10).copy()
        )
        df_ultimas["Valor (VGL)"] = df_ultimas["Aluguel"].apply(formatar_moeda_br)
        st.dataframe(
            df_ultimas[["Data", "Empresa", "Analista", "Valor (VGL)", "Status"]],
            use_container_width=True,
            hide_index=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 2 — Relatório Mensal
    # ══════════════════════════════════════════════════════════════════════════
    with aba_mensal:
        meses_disponiveis = sorted(df["Mes"].unique()) if "Mes" in df.columns else []

        if len(meses_disponiveis) == 0:
            st.info("Nenhum dado mensal disponível ainda.")
        else:
            # ── Filtro de período ─────────────────────────────────────────────
            col_f1, col_f2, _ = st.columns([1, 1, 2])
            with col_f1:
                mes_ini = st.selectbox(
                    "De",
                    options=meses_disponiveis,
                    index=0,
                    format_func=_label_mes,
                    key="relatorio_mes_ini",
                )
            with col_f2:
                mes_fim = st.selectbox(
                    "Até",
                    options=meses_disponiveis,
                    index=len(meses_disponiveis) - 1,
                    format_func=_label_mes,
                    key="relatorio_mes_fim",
                )

            df_filtrado = df[
                (df["Mes"] >= mes_ini) & (df["Mes"] <= mes_fim)
            ].copy() if mes_ini <= mes_fim else df.copy()

            # ── KPIs do período ───────────────────────────────────────────────
            total_p = len(df_filtrado)
            aprov_p = len(df_filtrado[df_filtrado["Status"].str.contains("APROVADO", na=False)])
            reprov_p = len(df_filtrado[df_filtrado["Status"].str.contains("REPROVADO", na=False)])
            ressalva_p = len(df_filtrado[df_filtrado["Status"].str.contains("RESSALVA", na=False)])
            taxa_p = round(aprov_p / total_p * 100, 1) if total_p > 0 else 0
            vgl_p = df_filtrado[df_filtrado["Status"].str.contains("APROVADO", na=False)]["Aluguel"].sum()
            n_meses = df_filtrado["Mes"].nunique() if "Mes" in df_filtrado.columns else 1
            media_mes = round(total_p / n_meses, 1) if n_meses > 0 else 0

            st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
            k1, k2, k3, k4, k5, k6 = st.columns(6)
            with k1:
                st.markdown(_kpi_card("Total no Período", str(total_p)), unsafe_allow_html=True)
            with k2:
                st.markdown(_kpi_card("Média / Mês", str(media_mes)), unsafe_allow_html=True)
            with k3:
                cor_taxa = "verde" if taxa_p >= 60 else ("amarelo" if taxa_p >= 40 else "vermelho")
                st.markdown(_kpi_card("Taxa de Aprovação", f"{taxa_p}%", cor_taxa), unsafe_allow_html=True)
            with k4:
                st.markdown(_kpi_card("Aprovados", str(aprov_p), "verde"), unsafe_allow_html=True)
            with k5:
                st.markdown(_kpi_card("Ressalvas", str(ressalva_p), "amarelo"), unsafe_allow_html=True)
            with k6:
                st.markdown(_kpi_card("Reprovados", str(reprov_p), "vermelho"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(
                f'<p style="color:#7F8C8D; font-size:12px; margin:4px 0 16px;">VGL total aprovado no período: '
                f'<strong style="color:#27AE60;">{formatar_moeda_br(vgl_p)}</strong></p>',
                unsafe_allow_html=True,
            )

            st.divider()

            # ── Gráficos mensais ──────────────────────────────────────────────
            col_vol, col_taxa = st.columns(2)

            with col_vol:
                st.markdown(_section_header("Volume Mensal por Status", "bi-bar-chart-steps"), unsafe_allow_html=True)
                fig_vol = _grafico_volume_mensal(df_filtrado)
                if fig_vol.data:
                    st.plotly_chart(fig_vol, use_container_width=True)
                else:
                    st.caption("Dados insuficientes.")

            with col_taxa:
                st.markdown(_section_header("Taxa de Aprovação Mensal", "bi-graph-up-arrow"), unsafe_allow_html=True)
                fig_taxa = _grafico_taxa_aprovacao_mensal(df_filtrado)
                if fig_taxa.data:
                    st.plotly_chart(fig_taxa, use_container_width=True)
                else:
                    st.caption("Dados insuficientes.")

            st.markdown(_section_header("VGL Aprovado por Mês", "bi-currency-dollar"), unsafe_allow_html=True)
            fig_vgl = _grafico_vgl_mensal(df_filtrado)
            if fig_vgl.data:
                st.plotly_chart(fig_vgl, use_container_width=True)
            else:
                st.caption("Nenhuma análise aprovada no período.")

            st.divider()

            # ── Tabela resumo ─────────────────────────────────────────────────
            st.markdown(_section_header("Resumo por Mês", "bi-table"), unsafe_allow_html=True)
            df_resumo = _tabela_resumo_mensal(df_filtrado)
            if not df_resumo.empty:
                st.dataframe(df_resumo, use_container_width=True, hide_index=True)
            else:
                st.caption("Sem dados para o período selecionado.")
