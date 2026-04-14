"""
views/configuracoes.py
Tela de configurações por usuário.

Permite que cada analista personalize:
  - Nome da empresa (usado no cabeçalho do laudo)
  - Cabeçalho do laudo (texto livre inserido antes do parecer)
  - Rodapé do laudo (texto livre inserido ao final do PDF)

As configurações são salvas na tabela `configuracoes_usuario` do Supabase
e carregadas em `st.session_state["config_usuario"]` no início de cada sessão.
"""

import streamlit as st
from services.db_service import DBService
from core.logger import get_logger

logger = get_logger(__name__)

_PLACEHOLDER_CABECALHO = (
    "Ex: Este laudo foi elaborado com base nos documentos apresentados pelo "
    "locatário e reflete a análise técnica da equipe Paulo Bio Imóveis."
)
_PLACEHOLDER_RODAPE = (
    "Ex: Paulo Bio Imóveis — Análise de Crédito Locatício | "
    "Documento de uso interno e confidencial."
)


def show_configuracoes() -> None:
    st.markdown("## :material/settings: Configurações do Analista")
    st.markdown(
        "<p style='color:#7F8C8D;font-size:14px;margin-bottom:24px;'>"
        "Personalize os textos que aparecem no cabeçalho e rodapé dos laudos gerados.</p>",
        unsafe_allow_html=True,
    )

    email = st.session_state.get("email_usuario", "")
    if not email:
        st.warning("Não foi possível identificar o usuário. Faça login novamente.")
        return

    # Carrega configurações atuais (já devem estar em session_state após login,
    # mas faz fallback ao banco se necessário)
    config_atual: dict = st.session_state.get("config_usuario") or {}
    if not config_atual:
        db = DBService()
        config_atual = db.get_config_usuario(email)
        st.session_state["config_usuario"] = config_atual

    st.markdown("### :material/business_center: Identidade da Empresa")
    nome_empresa = st.text_input(
        "Nome da Empresa",
        value=config_atual.get("nome_empresa", "Paulo Bio Imóveis"),
        help="Aparece no cabeçalho do PDF e no parecer final.",
        max_chars=120,
    )

    st.markdown("### :material/article: Textos do Laudo")

    cabecalho = st.text_area(
        "Cabeçalho do Laudo",
        value=config_atual.get("cabecalho_laudo", ""),
        placeholder=_PLACEHOLDER_CABECALHO,
        height=110,
        max_chars=600,
        help="Inserido logo após o título do laudo, antes do parecer.",
    )

    rodape = st.text_area(
        "Rodapé do Laudo",
        value=config_atual.get("rodape_laudo", ""),
        placeholder=_PLACEHOLDER_RODAPE,
        height=90,
        max_chars=400,
        help="Inserido ao final do PDF, abaixo do parecer.",
    )

    # Contador de caracteres
    col_ch, col_rd = st.columns(2)
    col_ch.caption(f"{len(cabecalho)}/600 caracteres")
    col_rd.caption(f"{len(rodape)}/400 caracteres")

    st.markdown("<br>", unsafe_allow_html=True)

    col_salvar, col_reset = st.columns([2, 1])

    with col_salvar:
        if st.button(
            ":material/save: Salvar Configurações",
            type="primary",
            use_container_width=True,
        ):
            nova_config = {
                "nome_empresa": nome_empresa.strip() or "Paulo Bio Imóveis",
                "cabecalho_laudo": cabecalho.strip(),
                "rodape_laudo": rodape.strip(),
            }
            db = DBService()
            if db.salvar_config_usuario(email, nova_config):
                st.session_state["config_usuario"] = nova_config
                st.success("Configurações salvas com sucesso!")
                logger.info("Configurações salvas para %s", email)
            else:
                st.error("Erro ao salvar configurações. Tente novamente.")

    with col_reset:
        if st.button(
            ":material/restart_alt: Restaurar Padrões",
            use_container_width=True,
            help="Restaura os valores padrão da empresa.",
        ):
            defaults = {
                "nome_empresa": "Paulo Bio Imóveis",
                "cabecalho_laudo": "",
                "rodape_laudo": "",
            }
            db = DBService()
            if db.salvar_config_usuario(email, defaults):
                st.session_state["config_usuario"] = defaults
                st.success("Configurações restauradas para o padrão.")
                st.rerun()

    # Preview do laudo
    with st.expander(":material/preview: Prévia do Laudo", expanded=False):
        st.markdown("---")
        nome_preview = nome_empresa.strip() or "Paulo Bio Imóveis"
        st.markdown(f"**{nome_preview}** — Análise de Crédito Locatício")
        if cabecalho.strip():
            st.info(cabecalho.strip())
        st.markdown(
            "_[...conteúdo do parecer gerado pela IA aparecerá aqui...]_",
            help="O parecer é gerado automaticamente com base nos documentos analisados.",
        )
        if rodape.strip():
            st.caption(rodape.strip())
        st.markdown("---")
