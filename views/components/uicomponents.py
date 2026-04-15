import time
from contextlib import contextmanager

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


def render_upload_status(uploaded_files: list, resultados: dict[str, bool] | None = None) -> None:
    """
    Renderiza feedback visual individual por arquivo após upload múltiplo.

    Args:
        uploaded_files: Lista de UploadedFile do Streamlit.
        resultados:     Dict {nome_arquivo: True/False} indicando sucesso por arquivo.
                        Se None, exibe apenas os arquivos carregados (estado neutro).
    """
    if not uploaded_files:
        return

    itens_html = []
    for f in uploaded_files:
        nome = f.name
        tamanho_kb = round(f.size / 1024, 1) if hasattr(f, "size") else "?"

        if resultados is None:
            # Estado neutro — arquivo carregado mas ainda não processado
            icone = '<span style="color:#7F8C8D;">⏳</span>'
            cor_nome = "#C8D6E5"
        elif resultados.get(nome, False):
            icone = '<span style="color:#27AE60;">✔</span>'
            cor_nome = "#C8D6E5"
        else:
            icone = '<span style="color:#E74C3C;">✗</span>'
            cor_nome = "#E74C3C"

        itens_html.append(
            f'<div style="display:flex; align-items:center; gap:8px; padding:4px 0; '
            f'border-bottom:1px solid rgba(255,255,255,0.05);">'
            f'<span style="font-size:14px; width:20px; text-align:center;">{icone}</span>'
            f'<span style="font-size:12px; color:{cor_nome}; flex:1; overflow:hidden; '
            f'text-overflow:ellipsis; white-space:nowrap;">{nome}</span>'
            f'<span style="font-size:10px; color:#7F8C8D;">{tamanho_kb} KB</span>'
            f'</div>'
        )

    html = (
        '<div style="background:#1A2636; border:1px solid rgba(244,121,32,0.2); '
        'border-radius:2px; padding:8px 12px; margin-top:8px;">'
        '<div style="font-size:10px; color:#F47920; font-weight:700; '
        'text-transform:uppercase; letter-spacing:.08em; margin-bottom:6px;">'
        f'📎 {len(uploaded_files)} arquivo(s)</div>'
        + "".join(itens_html)
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


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
    <div class="empty-state" role="status" aria-live="polite" aria-label="{title}">
        <div class="empty-state-icon" aria-hidden="true">{icon}</div>
        <div class="empty-state-title" role="heading" aria-level="2">{title}</div>
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
