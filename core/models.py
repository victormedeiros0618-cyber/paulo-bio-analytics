"""
Pydantic models para validação e tipagem dos outputs da IA.
Substitui dicts soltos retornados por extrair_json_seguro().

Uso:
    from core.models import ContratoModel
    resultado = ContratoModel.from_dict(dados_brutos)
    empresa = resultado.empresa  # tipado, com fallback seguro
"""

from typing import Any
from pydantic import BaseModel, Field, field_validator


class BaseAnaliseModel(BaseModel):
    """Base com configuração comum e método from_dict tolerante a falhas."""

    model_config = {"extra": "allow"}  # aceita campos extras da IA sem quebrar

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> "BaseAnaliseModel":
        """
        Constrói o model a partir de um dict bruto da IA.
        Campos ausentes recebem seus valores default (string vazia ou None).
        Nunca lança exceção — garante que o workflow continua mesmo com IA parcial.
        """
        try:
            return cls(**dados)
        except Exception:
            # Fallback: usa apenas os campos que existem, ignora inválidos
            campos_validos = {}
            for field_name in cls.model_fields:
                if field_name in dados:
                    campos_validos[field_name] = dados[field_name]
            return cls(**campos_validos)


# ─── Passo 0 — Contrato Social ────────────────────────────────────────────────

class ContratoModel(BaseAnaliseModel):
    empresa: str = ""
    cnpj: str = ""
    endereco_empresa: str = ""
    data_abertura: str = ""
    capital_social: str = ""
    administrador: str = ""
    socios_participacao: str = ""
    informacoes_adicionais: str = ""


# ─── Passo 1 — Proposta de Locação ───────────────────────────────────────────

class PropostaModel(BaseAnaliseModel):
    pretendente: str = ""
    atividade: str = ""
    imovel: str = ""
    prazo: str = ""
    data_inicio: str = ""
    carencia: str = ""
    aluguel: str = ""
    iptu: str = ""
    garantia: str = ""
    condicoes_gerais: str = ""
    info_gerais_manuais: str = ""


# ─── Passo 2 — Fiadores (IRPF) ───────────────────────────────────────────────

class FiadorModel(BaseAnaliseModel):
    rend_tributaveis: str = ""
    rend_nao_tributaveis: str = ""
    renda_media_oficial: str = ""
    renda_media_atual: str = ""
    patrimonio_declarado: str = ""
    aluguel_pretendido: str = ""
    dividas: str = ""
    onus: str = ""
    segmentacao_patrimonio: str = ""
    conclusao_fiador: str = ""


# ─── Passo 3 — Serasa ────────────────────────────────────────────────────────

class SerasaModel(BaseAnaliseModel):
    alerta_divergencia_serasa: str = ""
    score_serasa: str = ""
    risco_serasa: str = ""
    mapeamento_dividas: str = ""

    @field_validator("risco_serasa")
    @classmethod
    def normalizar_risco(cls, v: str) -> str:
        """Normaliza risco para minúsculas: alto/médio/baixo."""
        return v.lower().strip() if v else ""


# ─── Passo 4 — Certidões ─────────────────────────────────────────────────────

class CertidoesModel(BaseAnaliseModel):
    alerta_divergencia_certidoes: str = ""
    resumo_certidoes: str = ""


# ─── Passo 5 — Auditoria Contábil ────────────────────────────────────────────

class ContabilModel(BaseAnaliseModel):
    periodos: list[str] = Field(default_factory=list)
    receita_bruta: list[str] = Field(default_factory=list)
    resultado: list[str] = Field(default_factory=list)
    analise_executiva: str = ""
    alerta_divergencia_contabil: str = ""


# ─── Passo 6 — IR dos Sócios + Parecer Final ─────────────────────────────────

class PatrimonioSociosModel(BaseAnaliseModel):
    conclusao_socio: str = ""
    parecer_final: str = ""


# ─── Model consolidado de toda a análise ─────────────────────────────────────

class AnaliseCompleta(BaseAnaliseModel):
    """
    Representa o payload completo gravado no Supabase (campo 'dados').
    Agrega todos os passos em um único model validado.
    """
    # Passo 0
    empresa: str = ""
    cnpj: str = ""
    endereco_empresa: str = ""
    data_abertura: str = ""
    capital_social: str = ""
    administrador: str = ""
    socios_participacao: str = ""
    # Passo 1
    pretendente: str = ""
    imovel: str = ""
    aluguel: str = ""
    iptu: str = ""
    garantia: str = ""
    # Passo 3
    score_serasa: str = ""
    risco_serasa: str = ""
    mapeamento_dividas: str = ""
    # Passo 4
    resumo_certidoes: str = ""
    # Passo 5
    periodos: list[str] = Field(default_factory=list)
    receita_bruta: list[str] = Field(default_factory=list)
    resultado: list[str] = Field(default_factory=list)
    analise_executiva: str = ""
    # Passo 6
    conclusao_socio: str = ""
    parecer_final: str = ""
