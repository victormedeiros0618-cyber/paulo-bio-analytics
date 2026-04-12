"""
Inicialização do Sentry para monitoramento de erros em produção.
Chamado uma única vez no topo de app.py antes de qualquer outro import de view.
"""

import streamlit as st
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import logging


def init_sentry() -> None:
    """
    Inicializa o Sentry SDK se o DSN estiver configurado nos secrets.
    Em desenvolvimento (sem DSN), silencia sem lançar exceção.
    """
    dsn = st.secrets.get("SENTRY_DSN", "")
    if not dsn:
        return

    environment = st.secrets.get("ENVIRONMENT", "production")

    # Captura logs de WARNING e acima no Sentry como breadcrumbs,
    # e ERROR/CRITICAL como eventos separados
    logging_integration = LoggingIntegration(
        level=logging.WARNING,        # breadcrumb mínimo
        event_level=logging.ERROR,    # cria Issue a partir de ERROR
    )

    sentry_sdk.init(
        dsn=dsn,
        integrations=[logging_integration],
        environment=environment,
        traces_sample_rate=0.2,   # 20% das transações para performance
        send_default_pii=False,   # LGPD — não envia dados pessoais
    )
