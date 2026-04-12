"""
core/cache.py
Cache de análises baseado em hash SHA-256 do conteúdo dos PDFs.

O cache vive em st.session_state['_analise_cache'] durante a sessão do usuário.
Chave: "<nome_do_passo>:<hash1>:<hash2>:..." (hash de cada arquivo + kwargs extras)
Valor: dict resultado da IA

Uso:
    from core.cache import build_cache_key, get_cached, set_cached

    key = build_cache_key("passo_3_serasa", files, empresa=empresa, cnpj=cnpj)
    cached = get_cached(key)
    if cached is not None:
        return cached
    result = ... # chamada real à IA
    set_cached(key, result)
    return result
"""

import hashlib
from typing import IO

import streamlit as st

from core.logger import get_logger

logger = get_logger(__name__)

_SESSION_KEY = "_analise_cache"


def _file_hash(f: IO[bytes]) -> str:
    """Lê o arquivo do início e retorna o SHA-256 hex digest."""
    pos = f.tell()
    f.seek(0)
    digest = hashlib.sha256(f.read()).hexdigest()
    f.seek(pos)
    return digest


def build_cache_key(passo: str, files: list[IO[bytes]], **kwargs: str) -> str:
    """
    Constrói chave de cache combinando nome do passo, hashes dos arquivos
    e quaisquer kwargs adicionais (empresa, cnpj, aluguel, etc).

    Args:
        passo: identificador do passo (ex: "passo_3_serasa").
        files: lista de file-like objects (PDFs).
        **kwargs: parâmetros extras que diferenciam a análise.

    Returns:
        String única para identificar esta combinação de inputs.
    """
    parts = [passo]
    for f in files:
        parts.append(_file_hash(f))
    for k, v in sorted(kwargs.items()):
        parts.append(f"{k}={v}")
    return ":".join(parts)


def get_cached(key: str) -> dict | None:
    """
    Retorna resultado cached para a chave, ou None se não existir.
    """
    cache: dict = st.session_state.get(_SESSION_KEY, {})
    result = cache.get(key)
    if result is not None:
        logger.info("Cache hit: %s", key[:60])
    return result


def set_cached(key: str, value: dict) -> None:
    """
    Persiste resultado no cache da sessão.
    """
    if _SESSION_KEY not in st.session_state:
        st.session_state[_SESSION_KEY] = {}
    st.session_state[_SESSION_KEY][key] = value
    logger.debug("Cache set: %s", key[:60])


def clear_cache() -> None:
    """Limpa todo o cache da sessão atual."""
    st.session_state[_SESSION_KEY] = {}
    logger.info("Cache de análises limpo.")
