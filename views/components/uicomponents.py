import time
from contextlib import contextmanager
from typing import Callable

import streamlit as st

# ── Mensagens padrão por passo ─────────────────────────────────────────────────
_MSGS_PADRAO: dict[str, list[str]] = {
    "contrato": [
        "📄 Lendo Contrato Social e Aditivos...",
        "🏢 Identificando quadro societário...",
        "🔍 Extraindo capital social e administradores...",
        "🧠 Consolidando estrutura da empresa...",
    ],
    "proposta": [
        "📋 Lendo proposta de locação...",
        "🏠 Identificando imóvel e condições...",
        "💰 Extraindo valores e prazos...",
        "🧠 Consolidando dados da proposta...",
    ],
    "fiador": [
        "📑 Lendo declarações do fiador...",
        "💰 Mapeando rendimentos tributáveis...",
        "🏦 Analisando patrimônio declarado...",
        "🧠 Consolidando matriz financeira do fiador...",
    ],
    "referencias": [
        "📇 Lendo referências...",
        "🏠 Identificando referências locatícias...",
        "🏢 Mapeando referências comerciais e bancárias...",
        "🧠 Consolidando referências...",
    ],
    "serasa": [
        "📄 Lendo PDFs do Serasa...",
        "🔍 Identificando pendências e credores...",
        "🔗 Analisando contágio societário...",
        "🧠 Consolidando o mapa de riscos...",
    ],
    "certidoes": [
        "📄 Lendo certidões judiciais...",
        "⚖️ Identificando ações e processos...",
        "🔍 Verificando divergências de CNPJ...",
        "🧠 Consolidando auditoria jurídica...",
    ],
    "contabil": [
        "📊 Lendo DRE e Balanço Patrimonial...",
        "💹 Calculando receita bruta e resultado...",
        "🏦 Analisando patrimônio líquido e passivos...",
        "🧠 Consolidando auditoria financeira...",
    ],
    "patrimonio": [
        "📑 Lendo IR dos sócios/responsáveis...",
        "💰 Mapeando patrimônio declarado...",
        "📝 Redigindo parecer executivo final...",
        "🧠 Consolidando análise patrimonial...",
    ],
}


def show_toast(message: str, type: str = "info") -> None:
    """
    Exibe toast notification inline (Streamlit native).
    types: success, error, info, warning
    """
    if type == "success":
        st.success(message)
    elif type == "error":
        st.error(message)
    elif type == "warning":
        st.warning(message)
    else:
        st.info(message)


def empty_state(icon: str, title: str, description: str) -> None:
    """Renderiza empty state com ícone, título e descrição."""
    st.markdown(f'''
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-desc">{description}</div>
    </div>
    ''', unsafe_allow_html=True)


@contextmanager
def ai_progress(passo: str, mensagem_final: str = "Finalizando análise..."):
    """
    Context manager que exibe progress bar animada durante chamadas à IA.

    Uso:
        with ai_progress("serasa"):
            resultado = ai.mapear_serasa(files, empresa, cnpj)

    Args:
        passo: chave do dicionário _MSGS_PADRAO (ex: "serasa", "contrato").
               Se não existir, usa mensagens genéricas.
        mensagem_final: texto exibido na última etapa.
    """
    msgs = _MSGS_PADRAO.get(passo, [
        "📄 Enviando documentos para análise...",
        "🔍 Processando com IA...",
        "🧠 Consolidando resultados...",
        mensagem_final,
    ])

    placeholder = st.empty()
    barra = st.progress(0, text="Iniciando análise...")

    total = len(msgs) + 1  # +1 para etapa final

    try:
        for i, msg in enumerate(msgs):
            placeholder.info(msg)
            barra.progress(int((i + 1) / total * 85), text=msg)
            time.sleep(0.55)

        placeholder.info(f"⚙️ {mensagem_final}")
        barra.progress(90, text=mensagem_final)

        yield  # ← chamada real à IA acontece aqui

        barra.progress(100, text="✅ Concluído!")
        time.sleep(0.4)

    finally:
        placeholder.empty()
        barra.empty()
