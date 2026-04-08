import streamlit as st
import pandas as pd
import plotly.express as px
from services.db_service import DBService
from core.config import COR_PRIMARIA

def show_dashboard():
    st.markdown("""
    <h3 style="color:#FFFFFF; font-family:'Space Grotesk',sans-serif; font-weight:700; margin-bottom:10px;">
        Dashboard de Performance
    </h3>
    <p style="color:#7F8C8D; font-size:14px; margin-bottom:20px;">
        Visão executiva e financeira das análises de risco locatício.
    </p>
    """, unsafe_allow_html=True)

    db = DBService()
    with st.spinner("Carregando estatísticas..."):
        registros = db.listar_analises()

    if not registros:
        st.warning("Estatísticas não disponíveis no momento ou banco vazio.")
        return

    df = pd.DataFrame(registros)
    
    # Prepara tipagem e status
    df["Status"] = df.get("status", "—")
    df["Aluguel"] = pd.to_numeric(df.get("aluguel", 0), errors='coerce').fillna(0)
    if "created_at" in df.columns:
        df["Data_Obj"] = pd.to_datetime(df["created_at"])
        df["Data"] = df["Data_Obj"].dt.strftime("%d/%m/%Y")
    else:
        df["Data"] = "—"
    df["Empresa"] = df.get("empresa", "—")

    # Cálculos Globais
    total_analises = len(df)
    df_aprovados = df[df["Status"].str.contains("APROVADO", na=False)]
    tx_aprovacao = (len(df_aprovados) / total_analises) * 100 if total_analises > 0 else 0
    vgl_aprovado = df_aprovados["Aluguel"].sum()
    ticket_medio = df["Aluguel"].mean() if total_analises > 0 else 0

    def fmt_moeda(val):
        return f"R$ {val:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

    # Renderiza KPIs Topo
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'''
        <div class="kpi-card" style="border-left-color: {COR_PRIMARIA};">
            <div class="kpi-label" style="color: {COR_PRIMARIA} !important;">Total de Análises</div>
            <div class="kpi-value">{total_analises}</div>
        </div>
        ''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''
        <div class="kpi-card verde">
            <div class="kpi-label">Taxa de Aprovação</div>
            <div class="kpi-value">{tx_aprovacao:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    with c3:
        st.markdown(f'''
        <div class="kpi-card verde">
            <div class="kpi-label">VGL Aprovado</div>
            <div class="kpi-value">{fmt_moeda(vgl_aprovado)}</div>
        </div>
        ''', unsafe_allow_html=True)
    with c4:
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Ticket Médio (Aluguel)</div>
            <div class="kpi-value">{fmt_moeda(ticket_medio)}</div>
        </div>
        ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()

    # GRÁFICOS
    col_chart1, col_chart2 = st.columns([1, 2])
    
    with col_chart1:
        st.markdown("##### Proporção de Status")
        status_counts = df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Quantidade"]
        
        # Mapeia cores hardcoded pelo nome
        color_discrete_map = {
            "✅ APROVADO": "#27AE60",
            "⚠️ APROVADO COM RESSALVA": "#F1C40F",
            "❌ REPROVADO": "#E74C3C"
        }
        
        fig1 = px.pie(status_counts, values="Quantidade", names="Status", hole=0.4, 
                      color="Status", color_discrete_map=color_discrete_map)
        fig1.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#C8D6E5'),
            margin=dict(t=0, b=0, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        st.markdown("##### VGL Aprovado por Status")
        vgl_por_status = df.groupby("Status")["Aluguel"].sum().reset_index()
        fig2 = px.bar(vgl_por_status, x="Status", y="Aluguel", color="Status", color_discrete_map=color_discrete_map, text_auto=".2s")
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#C8D6E5'),
            margin=dict(t=0, b=0, l=0, r=0),
            showlegend=False,
            xaxis_title="",
            yaxis_title="VGL (R$)"
        )
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    
    # Tabela Inferior
    st.markdown("##### Últimas Análises Realizadas")
    df_ultimas = df.sort_values(by="Data_Obj", ascending=False).head(10).copy() if "Data_Obj" in df.columns else df.head(10)
    
    # Formata a coluna aluguel só pra exibição limitando as colunas visiveis
    df_ultimas["Valor (VGL)"] = df_ultimas["Aluguel"].apply(lambda x: fmt_moeda(x))
    
    colunas_visiveis = ["Data", "Empresa", "Valor (VGL)", "Status"]
    st.dataframe(df_ultimas[colunas_visiveis], use_container_width=True, hide_index=True)
