import streamlit as st
import pandas as pd
from services.db_service import DBService
from services.pdf_service import gerar_pdf_bytes

def show_historico():
    st.markdown("""
    <h3 style="color:#FFFFFF; font-family:'Space Grotesk',sans-serif; font-weight:700; margin-bottom:10px;">
        Histórico de Análises
    </h3>
    <p style="color:#7F8C8D; font-size:14px; margin-bottom:20px;">
        Consulte, baixe PDFs ou gerencie as análises anteriores.
    </p>
    """, unsafe_allow_html=True)
    
    db = DBService()
    
    with st.spinner("Conectando ao banco de dados..."):
        registros = db.listar_analises()
        
    if not registros:
        st.warning("Nenhuma análise encontrada no histórico ou falha na conexão.")
        return

    # Preparar DataFrame para exibição
    df = pd.DataFrame(registros)
    
    # Processa datas
    if "created_at" in df.columns:
        df["Data"] = pd.to_datetime(df["created_at"]).dt.strftime("%d/%m/%Y %H:%M:%S")
    else:
        df["Data"] = "—"
        
    df["Empresa"] = df.get("empresa", "—")
    df["Status"] = df.get("status", "—")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        busca = st.text_input("Buscar por Empresa/Cliente", placeholder="Digite o nome da empresa...")
    with col2:
        st.markdown("<div style='margin-top:2px;'></div>", unsafe_allow_html=True)
        status_filter = st.multiselect("Filtrar por Status", options=df["Status"].unique(), default=df["Status"].unique())

    # Filtros
    mask = df["Status"].isin(status_filter)
    if busca:
        mask = mask & df["Empresa"].str.contains(busca, case=False, na=False)
        
    df_filtrado = df[mask].copy()
    
    colunas_exibicao = ["Data", "Empresa", "Status"]
    
    # Exibi a grid com seleção de linha    
    st.markdown('<span style="color:#7F8C8D; font-size:12px;">Selecione uma análise abaixo para ver opções:</span>', unsafe_allow_html=True)

    event = st.dataframe(
        df_filtrado[colunas_exibicao], 
        use_container_width=True, 
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    selected_rows = event.selection.get("rows", [])
    
    if selected_rows:
        idx_selecionado = selected_rows[0]
        # Pega a linha real baseada no df_filtrado
        registro_selecionado = df_filtrado.iloc[idx_selecionado] 
        
        # Como o df_filtrado perde a ref do dict orginal "dados" que vem do json completo, vou pegar do ref original:
        real_idx_original = registro_selecionado.name # O nome da index é a row original no df principal
        registro_real = df.iloc[real_idx_original]
        
        dados_json = registro_real.get("dados", {})
        
        st.divider()
        st.markdown(f"### Detalhes: {registro_real['Empresa']}")
        col_det1, col_det2 = st.columns([2, 1])
        
        with col_det1:
            st.markdown(f"**Data de Análise:** {registro_real['Data']}")
            st.markdown(f"**Veredito:** {registro_real['Status']}")
            observacao = dados_json.get("parecer_oficial", "Sem observação no registro.")
            st.markdown("**Observação:**")
            st.info(observacao)
            
            checklist = dados_json.get("checklist_docs", {})
            if checklist:
                with st.expander("📚 Documentos Analisados (Checklist)", expanded=True):
                    for passo, arquivos in checklist.items():
                        if arquivos:
                            st.markdown(f"**✅ {passo}:**")
                            for arq in arquivos:
                                st.caption(f"- {arq}")
                
        with col_det2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📥 Baixar PDF Executivo", type="primary", use_container_width=True):
                with st.spinner("Montando Relatório PDF..."):
                    try:
                        pdf_bytes = gerar_pdf_bytes(dados_json, str(registro_real['Status']))
                        st.download_button(
                            label="Clique para Salvar",
                            data=pdf_bytes,
                            file_name=f"Relatorio_{registro_real['Empresa']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar PDF desta memória antiga: {e}")
            
            if st.button("🗑️ Excluir Registro", use_container_width=True):
                st.warning("Função de exclusão será implementada em breve.")
