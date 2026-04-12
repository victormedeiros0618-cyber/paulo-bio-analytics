"""
core/prompt_loader.py
Carrega prompts de IA do arquivo YAML e interpola variáveis.

Uso:
    from core.prompt_loader import get_prompt
    prompt = get_prompt("passo_0_contrato")
    prompt = get_prompt("passo_2_fiador", aluguel="5.000,00")
"""

import functools
from pathlib import Path

import yaml

from core.logger import get_logger

logger = get_logger(__name__)

_PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / "analise.yaml"


@functools.lru_cache(maxsize=1)
def _load_yaml() -> dict[str, str]:
    """Carrega o YAML uma única vez e mantém em cache."""
    try:
        with open(_PROMPTS_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        logger.debug("Prompts carregados de %s (%d chaves).", _PROMPTS_PATH, len(data))
        return data
    except FileNotFoundError:
        logger.error("Arquivo de prompts não encontrado: %s", _PROMPTS_PATH)
        return {}
    except yaml.YAMLError as e:
        logger.error("Erro ao parsear YAML de prompts: %s", e)
        return {}


def get_prompt(key: str, **kwargs: str) -> str:
    """
    Retorna o prompt identificado por `key`, com variáveis interpoladas.

    Args:
        key: chave do prompt no YAML (ex: "passo_0_contrato").
        **kwargs: variáveis para substituir via str.format_map.

    Returns:
        String do prompt com variáveis substituídas.
        Em caso de chave inexistente, retorna string vazia e loga erro.
    """
    prompts = _load_yaml()
    template = prompts.get(key)

    if template is None:
        logger.error("Prompt '%s' não encontrado no YAML.", key)
        return ""

    if not kwargs:
        return template.strip()

    try:
        return template.format_map(kwargs).strip()
    except KeyError as e:
        logger.error("Variável %s ausente ao interpolar prompt '%s'.", e, key)
        return template.strip()
