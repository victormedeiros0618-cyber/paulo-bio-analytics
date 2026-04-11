"""
Logger estruturado para o analise-locacao.
Substitui print() e st.error() para diagnóstico em produção.

Uso:
    from core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Análise iniciada para %s", empresa)
    logger.warning("Campo ausente: %s", campo)
    logger.error("Falha na IA: %s", erro)
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado com formato padronizado Paulo Bio.
    Cada módulo chama get_logger(__name__) para ter contexto no log.
    """
    logger = logging.getLogger(name)

    # Evita adicionar handlers duplicados em reruns do Streamlit
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Não propagar para o root logger (evita duplicação)
    logger.propagate = False

    return logger
