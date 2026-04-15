import streamlit as st
from services.ai_service import AIService
from views.components.uicomponents import show_toast, ai_progress
from utils.formatters import safe_float

def show_passo_1():
    d = st.session_state.dados
    ai = AIService()
    
    st.markdown("""
    <h3 style="font-weight: 700; margin-bottom: 20px;">
        <i class="bi bi-briefcase-fill" style="color: #F47920; margin-right: 8px;"></i> Proposta
    </h3>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.container(border=True):
            uploaded = st.file_uploader("Upload Proposta (PDF)", type="pdf", key="up1")
            if uploaded and st.button("Extrair Proposta"):
                st.session_state.dados["checklist_docs"]["Passo 1 (Proposta)"] = [uploaded.name]
                with ai_progress("proposta", "Consolidando dados da proposta..."):
                    res = ai.extrair_proposta(uploaded)
                    if res:
                        st.session_state.dados.update(res)
                        aluguel = st.session_state.dados.get("aluguel", "")
                        imovel = st.session_state.dados.get("imovel", "")
                        msg = f"✅ Proposta consolidada — {imovel}" if imovel else "✅ Proposta de locação extraída!"
                        if aluguel:
                            msg += f" · R$ {aluguel}"
                        show_toast(msg, "success")
                        st.rerun()
                    else:
                        st.error("Não foi possível extrair os dados. Verifique se o PDF é válido e tente novamente.")
    with c2:
        with st.container(border=True):
            # Restaurando TODOS os campos da proposta e o controle de estado
            st.session_state.dados["pretendente"] = st.text_input("Pretendente", d.get("pretendente", d.get("empresa", "")))
            st.session_state.dados["atividade"] = st.text_input("Atividade a ser realizada", d.get("atividade", ""))
            st.session_state.dados["imovel"] = st.text_input("Endereço do Imóvel *", d.get("imovel", ""))

            c_p1, c_p2, c_p3 = st.columns(3)
            st.session_state.dados["prazo"] = c_p1.text_input("Prazo *", d.get("prazo", ""))
            st.session_state.dados["data_inicio"] = c_p2.text_input("Data de Início", d.get("data_inicio", ""))
            st.session_state.dados["carencia"] = c_p3.text_input("Carência", d.get("carencia", ""))
            
            c_val1, c_val2 = st.columns(2)
            st.session_state.dados["aluguel"] = c_val1.text_input("Aluguel (R$) *", d.get("aluguel", "0"))
            st.session_state.dados["iptu"] = c_val2.text_input("IPTU (R$)", d.get("iptu", "0"))
            
            st.session_state.dados["garantia"] = st.text_input("Garantia Proposta", d.get("garantia", ""))
            st.session_state.dados["condicoes_gerais"] = st.text_area("Condições Gerais (Reajustes/Multas)", d.get("condicoes_gerais", ""))
            st.session_state.dados["info_gerais_manuais"] = st.text_area("Informações Gerais (Anotações Livres)", d.get("info_gerais_manuais", ""))
            
    # Restaurando a sub-seção condicional do Fiador
    if "fiador" in str(d.get("garantia", "")).lower():
        st.write("")
        st.markdown("""
        <h4 style="font-weight: 600; margin-bottom: 10px;">
            <i class="bi bi-person-bounding-box" style="color: #F47920; margin-right: 8px;"></i> Análise do Fiador
        </h4>
        """, unsafe_allow_html=True)
        
        cf1, cf2 = st.columns([1, 2])
        with cf1:
            with st.container(border=True):
                up_fiador = st.file_uploader("Upload Docs do Fiador (IR, Matrícula)", type="pdf", accept_multiple_files=True, key="up_fiador")
                if up_fiador and st.button("Analisar Capacidade do Fiador"):
                    st.session_state.dados["checklist_docs"]["Passo 1 (Fiador)"] = [f.name for f in up_fiador]
                    with ai_progress("fiador", "Consolidando matriz do fiador..."):
                        res_fiador = ai.analisar_fiador(up_fiador, d.get("aluguel", "0"))
                        if res_fiador:
                            st.session_state.dados.update(res_fiador)
                            show_toast("✅ Fiador analisado!", "success")
                            st.rerun()
                        else:
                            st.error("Não foi possível analisar o fiador. Verifique se os PDFs são válidos e tente novamente.")
        with cf2:
            with st.container(border=True):
                st.session_state.dados["conclusao_fiador"] = st.text_area("Parecer sobre o Fiador", d.get("conclusao_fiador", ""), height=150)

    st.write("") 
    st.write("")                
    c_b1, c_space, c_b2 = st.columns([1.5, 5, 1.5])               
    with c_b1:
        if st.button("Voltar"): 
            st.session_state.step = 0 
            show_toast("↩️ Retornando ao Passo 0", "info")
            st.rerun()         
    with c_b2:
        if st.button("Avançar"):
            erros = []
            if safe_float(st.session_state.dados.get("aluguel", "0")) <= 0:
                erros.append("Aluguel (deve ser maior que zero)")
            if not st.session_state.dados.get("imovel", "").strip():
                erros.append("Endereço do Imóvel")
            if not st.session_state.dados.get("prazo", "").strip():
                erros.append("Prazo")
            if erros:
                st.error(f"Preencha os campos obrigatórios: {', '.join(erros)}")
            else:
                st.session_state.step = 2
                show_toast(":material/contact_page: Ficha cadastral — carregue as referências", "info")
                st.rerun()
