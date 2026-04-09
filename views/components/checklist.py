import streamlit as st

def render_document_checklist():
    """
    Renderiza um checklist visual dos documentos que já foram subidos.
    Ajuda o analista a ter certeza de que não esqueceu nada antes do parecer.
    """
    with st.sidebar:
        # --- Botão Debug/Mock (apenas em ambiente de desenvolvimento) ---
        debug_mode = st.secrets.get("DEBUG_MODE", False)
        if debug_mode and st.button("🛠️ Injetar Dados Mock (Teste PDF)", help="Preenche todo o relatório automaticamente para testar o PDF."):
            if "dados" not in st.session_state:
                st.session_state.dados = {}
            st.session_state.dados.update({
                "empresa": "TechCorp Soluções S.A.",
                "cnpj": "12.345.678/0001-99",
                "data_abertura": "15/03/2010",
                "capital_social": "R$ 500.000,00",
                "administrador": "Victor Padilha",
                "socios_participacao": "Victor Padilha (60%), Maria Silva (40%)",
                "informacoes_adicionais": "Empresa sólida no mercado de tecnologia, aditivos regulares e capital social integralizado.",
                "pretendente": "TechCorp Soluções S.A.",
                "atividade": "Desenvolvimento de Software",
                "imovel": "Galpão Industrial - São Bernardo do Campo",
                "prazo": "36",
                "data_inicio": "01/06/2026",
                "carencia": "0",
                "aluguel": "15000",
                "iptu": "850",
                "garantia": "Fiador com Imóvel",
                "condicoes_gerais": "Reajuste anual pelo IGPM.",
                "info_gerais_manuais": "Cliente solicitou pintura externa.",
                "score_serasa": "850",
                "risco_serasa": "Baixo",
                "mapeamento_dividas": "Nenhuma dívida ativa no Serasa. Sócios sem apontamentos negativos.",
                "alerta_divergencia_serasa": "",
                "alerta_divergencia_certidoes": "",
                "resumo_certidoes": "Certidões Estaduais e Federais negativas de débitos.",
                "periodos": ["2024", "2025"],
                "receita_bruta": ["R$ 1.200.000,00", "R$ 1.800.000,00"],
                "resultado": ["R$ 200.000,00", "R$ 350.000,00"],
                "analise_executiva": "A empresa demonstra excelente solidez financeira e forte capacidade de pagamento. A receita cresceu 50% entre 2024 e 2025, enquanto a lucratividade acompanhou o ritmo garantindo boa liquidez.",
                "rend_tributaveis": "R$ 250.000,00",
                "rend_nao_tributaveis": "R$ 80.000,00",
                "renda_media_oficial": "R$ 20.833,33",
                "renda_media_atual": "R$ 22.000,00",
                "patrimonio_declarado": "R$ 1.500.000,00",
                "aluguel_pretendido": "15000",
                "dividas": "Financiamento Habitacional ativo (Caixa)",
                "onus": "Apartamento em alienação fiduciária.",
                "segmentacao_patrimonio": "R$ 1.200.000 em imóveis físicos. R$ 300.000 em aplicações com liquidez.",
                "conclusao_fiador": "O fiador apresenta excelente garantias físicas, e a renda suporta os requisitos superando a margem mínima de 3x do aluguel atual.",
                "conclusao_socio": "A saúde financeira dos sócios é altamente favorável e sem contágio restritivo.",
                "parecer_final": "Trata-se de uma empresa sólida. O aluguel não compromete nem 10% da receita anual, e os fiadores possuem excelente liquidez. Recomendo explicitamente a continuação da operação.",
                "parecer_oficial": "Após profunda análise técnica sobre a capacidade creditícia da locatária, atestamos que a operação imobiliária goza de absoluta garantia documental e lastro financeiro.\nO risco atrelado é substancialmente mitigado pelos indicadores positivos confirmados.",
                "solucao_complementar": "",
                "checklist_docs": {
                    "Passo 0 (Contrato)": ["contrato_mock.pdf"],
                    "Passo 1 (Proposta)": ["proposta_mock.pdf"],
                    "Passo 2 (Ficha)": ["ficha_mock.pdf"],
                    "Passo 3 (Serasa)": ["serasa_mock.pdf"],
                    "Passo 5 (Contábil)": ["balanco_mock.pdf"],
                    "Passo 6 (IR)": ["ir_mock.pdf"]
                }
            })
            st.session_state.step = 7
            st.rerun()

