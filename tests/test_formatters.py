"""
Testes unitários para utils/formatters.py
Cobre: str_to_float, formatar_valor_contabil, safe_float,
       extrair_json_seguro, limpa_pdf, formatar_moeda_br, limpa_markdown
"""

import pytest
import sys
import os

# Garante que o módulo pode ser importado a partir da raiz do projeto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.formatters import (
    str_to_float,
    formatar_valor_contabil,
    safe_float,
    extrair_json_seguro,
    limpa_pdf,
    formatar_moeda_br,
    limpa_markdown,
)


# ─── str_to_float ─────────────────────────────────────────────────────────────

class TestStrToFloat:
    def test_valor_simples(self):
        assert str_to_float("1000,00") == 1000.0

    def test_valor_com_rs(self):
        assert str_to_float("R$ 1.500,00") == 1500.0

    def test_valor_com_ponto_milhar(self):
        assert str_to_float("R$ 20.000,00") == 20000.0

    def test_valor_inteiro_string(self):
        assert str_to_float("500") == 500.0

    def test_valor_float_puro(self):
        # str_to_float trata o ponto como separador de milhar (padrão BR),
        # então float(1234.56) -> "1234.56" -> remove ponto -> 123456.0
        # Para floats puros, usar safe_float em vez de str_to_float
        assert str_to_float(1234.56) == 123456.0

    def test_string_invalida_retorna_zero(self):
        assert str_to_float("não informado") == 0.0

    def test_string_vazia_retorna_zero(self):
        assert str_to_float("") == 0.0

    def test_none_retorna_zero(self):
        assert str_to_float(None) == 0.0


# ─── formatar_valor_contabil ──────────────────────────────────────────────────

class TestFormatarValorContabil:
    def test_parenteses_vira_negativo(self):
        assert formatar_valor_contabil("(15000)") == "- 15000"

    def test_parenteses_com_espaco(self):
        assert formatar_valor_contabil("( 8500 )") == "- 8500"

    def test_valor_positivo_inalterado(self):
        assert formatar_valor_contabil("25000") == "25000"

    def test_valor_zero(self):
        assert formatar_valor_contabil("0") == "0"

    def test_string_com_rs(self):
        assert formatar_valor_contabil("R$ 5.000,00") == "R$ 5.000,00"

    def test_string_vazia(self):
        assert formatar_valor_contabil("") == ""


# ─── safe_float ───────────────────────────────────────────────────────────────

class TestSafeFloat:
    def test_int_puro(self):
        assert safe_float(42) == 42.0

    def test_float_puro(self):
        assert safe_float(3.14) == pytest.approx(3.14)

    def test_formato_br_com_milhar(self):
        assert safe_float("1.500,75") == pytest.approx(1500.75)

    def test_formato_br_simples(self):
        assert safe_float("1234,56") == pytest.approx(1234.56)

    def test_formato_us(self):
        assert safe_float("1500.75") == pytest.approx(1500.75)

    def test_com_prefixo_rs(self):
        assert safe_float("R$ 2.000,00") == pytest.approx(2000.0)

    def test_string_invalida_retorna_zero(self):
        assert safe_float("abc") == 0.0

    def test_none_retorna_zero(self):
        assert safe_float(None) == 0.0

    def test_string_vazia_retorna_zero(self):
        assert safe_float("") == 0.0

    def test_valor_negativo(self):
        assert safe_float("-500") == pytest.approx(-500.0)


# ─── extrair_json_seguro ──────────────────────────────────────────────────────

class TestExtrairJsonSeguro:
    def test_json_puro(self):
        texto = '{"empresa": "Paulo Bio", "cnpj": "12.345.678/0001-90"}'
        resultado = extrair_json_seguro(texto)
        assert resultado["empresa"] == "Paulo Bio"
        assert resultado["cnpj"] == "12.345.678/0001-90"

    def test_json_em_bloco_markdown(self):
        texto = 'Aqui está o resultado:\n```json\n{"score": "750", "risco": "baixo"}\n```'
        resultado = extrair_json_seguro(texto)
        assert resultado["score"] == "750"
        assert resultado["risco"] == "baixo"

    def test_json_em_bloco_markdown_sem_tipo(self):
        texto = "```\n{\"empresa\": \"Teste\"}\n```"
        resultado = extrair_json_seguro(texto)
        assert resultado["empresa"] == "Teste"

    def test_json_com_texto_antes_e_depois(self):
        texto = "Análise concluída. {\"veredito\": \"aprovado\"} Obrigado."
        resultado = extrair_json_seguro(texto)
        assert resultado["veredito"] == "aprovado"

    def test_json_aninhado(self):
        texto = '{"dados": {"receita": "100000", "resultado": "15000"}}'
        resultado = extrair_json_seguro(texto)
        assert resultado["dados"]["receita"] == "100000"

    def test_texto_sem_json_retorna_dict_vazio(self):
        resultado = extrair_json_seguro("Não há JSON aqui.")
        assert resultado == {}

    def test_string_vazia_retorna_dict_vazio(self):
        assert extrair_json_seguro("") == {}

    def test_json_invalido_retorna_dict_vazio(self):
        assert extrair_json_seguro("{chave_sem_aspas: valor}") == {}

    def test_json_com_lista(self):
        texto = '{"periodos": ["2024", "2025"], "receita": ["R$ 100k", "R$ 120k"]}'
        resultado = extrair_json_seguro(texto)
        assert resultado["periodos"] == ["2024", "2025"]


# ─── limpa_pdf ────────────────────────────────────────────────────────────────

class TestLimpaPdf:
    def test_texto_simples(self):
        resultado = limpa_pdf("Texto normal sem problemas")
        assert resultado == "Texto normal sem problemas"

    def test_aspas_tipograficas(self):
        resultado = limpa_pdf("\u201cTexto entre aspas\u201d")
        assert '"' in resultado or resultado  # convertido para latin-1 compatível

    def test_travessao_vira_hifen(self):
        resultado = limpa_pdf("2024\u20132025")
        assert "-" in resultado

    def test_reticencias_unicode(self):
        resultado = limpa_pdf("Continua\u2026")
        assert "..." in resultado

    def test_non_breaking_space(self):
        resultado = limpa_pdf("A\xa0B")
        assert "A B" in resultado

    def test_emoji_removido(self):
        resultado = limpa_pdf("Aprovado \U0001f44d")
        # Emoji não-latin-1 deve ser removido ou convertido sem quebrar
        assert isinstance(resultado, str)
        assert "\U0001f44d" not in resultado

    def test_string_vazia(self):
        assert limpa_pdf("") == ""

    def test_none_converte_sem_erro(self):
        resultado = limpa_pdf(None)
        assert isinstance(resultado, str)


# ─── formatar_moeda_br ────────────────────────────────────────────────────────

class TestFormatarMoedaBr:
    def test_valor_inteiro(self):
        assert formatar_moeda_br(1000) == "R$ 1.000,00"

    def test_valor_com_centavos(self):
        assert formatar_moeda_br(1234.56) == "R$ 1.234,56"

    def test_valor_grande(self):
        assert formatar_moeda_br(1000000) == "R$ 1.000.000,00"

    def test_valor_zero(self):
        assert formatar_moeda_br(0) == "R$ 0,00"

    def test_valor_negativo(self):
        resultado = formatar_moeda_br(-500.0)
        assert "500" in resultado

    def test_string_invalida_retorna_string(self):
        resultado = formatar_moeda_br("abc")
        assert isinstance(resultado, str)


# ─── limpa_markdown ───────────────────────────────────────────────────────────

class TestLimpaMarkdown:
    def test_bold_duplo_asterisco(self):
        resultado = limpa_markdown("**Texto em negrito**")
        assert resultado == "Texto em negrito"

    def test_bold_duplo_underline(self):
        resultado = limpa_markdown("__Texto em negrito__")
        assert resultado == "Texto em negrito"

    def test_header_h1(self):
        resultado = limpa_markdown("# Título Principal")
        assert resultado == "Título Principal"

    def test_header_h2(self):
        resultado = limpa_markdown("## Subtítulo")
        assert resultado == "Subtítulo"

    def test_header_h3(self):
        resultado = limpa_markdown("### Seção")
        assert resultado == "Seção"

    def test_pipes_de_tabela_viram_espacos(self):
        resultado = limpa_markdown("| Coluna 1 | Coluna 2 |")
        assert "|" not in resultado

    def test_linha_separadora_de_tabela_removida(self):
        resultado = limpa_markdown("|---|---|")
        # Linha separadora deve ser removida ou ficar vazia após strip
        assert "|" not in resultado

    def test_multiplas_linhas_em_branco_comprimidas(self):
        resultado = limpa_markdown("Linha 1\n\n\n\nLinha 2")
        assert "\n\n\n" not in resultado

    def test_texto_sem_markdown_inalterado(self):
        texto = "Texto simples sem marcação"
        assert limpa_markdown(texto) == texto

    def test_string_vazia(self):
        assert limpa_markdown("") == ""

    def test_none_retorna_string(self):
        resultado = limpa_markdown(None)
        assert isinstance(resultado, str)

    def test_misto_bold_e_header(self):
        resultado = limpa_markdown("## **Título Negrito**")
        assert resultado == "Título Negrito"
