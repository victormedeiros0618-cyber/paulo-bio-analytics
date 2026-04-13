from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from fpdf import FPDF
from utils.formatters import formatar_moeda_br, limpa_pdf, safe_float, limpa_markdown


# ---------------------------------------------------------------------------
# Tipagem do dicionário de dados
# ---------------------------------------------------------------------------

class DadosRelatorio(TypedDict, total=False):
    # Negócio
    pretendente: str
    atividade: str
    imovel: str
    aluguel: float | str
    iptu: float | str
    prazo: str | int
    garantia: str
    condicoes_gerais: str
    info_gerais_manuais: str
    # Societário
    empresa: str
    cnpj: str
    data_abertura: str
    capital_social: str
    socios_participacao: str
    administrador: str
    # Fiadores (opcionais — página só renderiza se presente)
    rend_tributaveis: str
    rend_nao_tributaveis: str
    renda_media_oficial: str
    renda_media_atual: str
    patrimonio_declarado: str
    aluguel_pretendido: str
    dividas: str
    onus: str
    segmentacao_patrimonio: str
    conclusao_fiador: str
    # Crédito
    score_serasa: str
    risco_serasa: str
    mapeamento_dividas: str
    # Financeiro
    periodos: list[str]
    receita_bruta: list[str]
    resultado: list[str]
    analise_executiva: str
    # Veredito
    solucao_complementar: str

# ---------------------------------------------------------------------------
# Constantes visuais centralizadas
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PDFConfig:
    # Paleta corporativa
    PRIMARY_R: int = 244
    PRIMARY_G: int = 121
    PRIMARY_B: int = 32

    DARK_R: int = 44
    DARK_G: int = 62
    DARK_B: int = 80

    GRAY_R: int = 128
    GRAY_G: int = 128
    GRAY_B: int = 128

    LIGHT_BG_R: int = 248
    LIGHT_BG_G: int = 248
    LIGHT_BG_B: int = 248

    # Tipografia
    FONT: str = "Helvetica"
    FONT_SIZE_BODY: int = 10
    FONT_SIZE_SMALL: int = 8
    FONT_SIZE_TITLE_SECTION: int = 14
    FONT_SIZE_TITLE_PAGE: int = 26
    FONT_SIZE_CARD_VALUE: int = 11
    FONT_SIZE_CARD_LABEL: int = 8
    FONT_SIZE_VERDICT: int = 14

    # Margens e espaçamento
    MARGIN_LEFT: float = 20.0
    MARGIN_TOP: float = 20.0
    MARGIN_RIGHT: float = 20.0
    LINE_HEIGHT_BODY: int = 6
    LINE_HEIGHT_SECTION: int = 8

    # Layout de cards
    CARD_X_START: float = 20.0
    CARD_WIDTH: float = 54.0
    CARD_HEIGHT: float = 20.0
    CARD_GAP: float = 3.0     # espaço entre cards (3 cards + gaps = ~170mm)

    # Localização
    MESES_PT: tuple[str, ...] = (
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    )

    def data_hoje_ptbr(self) -> str:
        hoje = datetime.now()
        return f"{hoje.day:02d} de {self.MESES_PT[hoje.month - 1]} de {hoje.year}"

    def data_hoje_numerica(self) -> str:
        return datetime.now().strftime("%d/%m/%Y")


CFG = PDFConfig()


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class PDFExecutivo(FPDF):
    """
    Template do relatório executivo Paulo Bio Imóveis.
    Cada seção do documento é um método isolado, recebendo os dados
    necessários — sem estado mutável além do cursor do FPDF.
    """

    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(
            left=CFG.MARGIN_LEFT,
            top=CFG.MARGIN_TOP,
            right=CFG.MARGIN_RIGHT,
        )
        self.set_auto_page_break(auto=True, margin=25)
        # Usa fontes built-in do FPDF (Helvetica) - mais compatível
        # subtitle_empresa = "Paulo Bio Imóveis"
        # subtitle_contato = "contato@paulobio.com.br"

    # ------------------------------------------------------------------
    # Header / Footer
    # ------------------------------------------------------------------

    def header(self) -> None:
        if self.page_no() > 1:
            self.set_fill_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
            self.rect(0, 0, 210, 4, "F")
            self.ln(5)

    def footer(self) -> None:
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_fill_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
            self.rect(0, 293, 210, 4, "F")
            self.set_font(CFG.FONT, "I", CFG.FONT_SIZE_SMALL)
            self.set_text_color(CFG.GRAY_R, CFG.GRAY_G, CFG.GRAY_B)
            self.cell(
                0, 10,
                limpa_pdf(
                    f"Relatório Confidencial - Paulo Bio Imóveis | Página {self.page_no()}"
                ),
                align="R",
            )

    # ------------------------------------------------------------------
    # Helpers de estilo reutilizáveis
    # ------------------------------------------------------------------

    def _section_title(self, txt: str) -> None:
        """Título de seção com linha laranja abaixo."""
        self.ln(8)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_TITLE_SECTION)
        self.set_text_color(CFG.DARK_R, CFG.DARK_G, CFG.DARK_B)
        self.cell(0, CFG.LINE_HEIGHT_SECTION, limpa_pdf(txt), ln=1)
        self.set_draw_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
        self.line(CFG.MARGIN_LEFT, self.get_y(), 190, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def _row(self, label: str, value: str) -> None:
        """Par label + valor em linha."""
        # Garante que o cursor está na margem esquerda antes de cada linha
        self.set_x(CFG.MARGIN_LEFT)
        self.set_text_color(0, 0, 0)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        label_w = 55.0
        self.cell(label_w, CFG.LINE_HEIGHT_BODY, limpa_pdf(label))
        self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
        # Largura explícita = área útil - label — nunca fica negativa
        value_w = 210.0 - CFG.MARGIN_LEFT - CFG.MARGIN_RIGHT - label_w
        self.multi_cell(value_w, CFG.LINE_HEIGHT_BODY, limpa_pdf(str(value)), align="J")

    def _draw_card(self, x: float, y: float, label: str, value: str) -> None:
        """Card informativo com borda laranja."""
        self.set_fill_color(250, 250, 250)
        self.set_draw_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
        self.rect(x, y, CFG.CARD_WIDTH, CFG.CARD_HEIGHT, "FD")
        self.set_xy(x + 2, y + 3)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_CARD_LABEL)
        self.set_text_color(CFG.GRAY_R, CFG.GRAY_G, CFG.GRAY_B)
        self.cell(50, 4, limpa_pdf(label), ln=1)
        self.set_x(x + 2)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_CARD_VALUE)
        self.set_text_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
        self.cell(50, 8, limpa_pdf(value), ln=1)

    # ------------------------------------------------------------------
    # Seções do relatório
    # ------------------------------------------------------------------

    def render_capa(self, dados: DadosRelatorio) -> None:
        """Página 1 — capa profissional."""
        self.add_page()
        self.ln(60)

        self.set_font(CFG.FONT, "B", 11)
        self.set_text_color(CFG.GRAY_R, CFG.GRAY_G, CFG.GRAY_B)
        self.cell(
            0, 5,
            limpa_pdf(f"RELATÓRIO EXECUTIVO · {datetime.now().year}"),
            ln=1, align="C",
        )

        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_TITLE_PAGE)
        self.set_text_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
        self.cell(
            0, 20,
            limpa_pdf("Análise de Crédito e Risco"),
            ln=1, align="C",
        )
        self.ln(15)

        empresa_nome = str(dados.get("empresa", dados.get("pretendente", ""))).strip() or "Não informado"
        imovel_nome = str(dados.get("imovel", "")).strip() or "Não informado"

        self.set_fill_color(CFG.LIGHT_BG_R, CFG.LIGHT_BG_G, CFG.LIGHT_BG_B)
        self.rect(30, self.get_y(), 150, 30, "F")
        self.set_y(self.get_y() + 5)

        self.set_text_color(0, 0, 0)
        self.set_font(CFG.FONT, "B", 15)
        self.cell(0, 10, limpa_pdf(empresa_nome), ln=1, align="C")

        self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
        self.set_text_color(80, 80, 80)
        # multi_cell centralizado para suportar endereços longos sem quebrar o layout da capa
        self.multi_cell(0, 6, limpa_pdf(f"Imóvel: {imovel_nome}"), align="C")
        self.ln(1)

        self.set_y(220)
        self.set_font(CFG.FONT, "B", 12)
        self.set_text_color(100, 100, 100)
        self.cell(
            0, 10,
            limpa_pdf(f"Santo André - SP, {CFG.data_hoje_numerica()}"),
            ln=1, align="C",
        )

    def render_negocio_e_qualificacao(self, dados: DadosRelatorio) -> None:
        """Página 2 — dados do negócio e qualificação societária."""
        self.add_page()

        self._section_title("1. Dados do Negócio")
        self._row("Pretendente:", str(dados.get("pretendente", "-")))
        self._row("Atividade:", str(dados.get("atividade", "-")))
        self._row("Imóvel:", str(dados.get("imovel", "-")))
        self.ln(5)

        y_cards = self.get_y()
        self._draw_card(
            CFG.CARD_X_START, y_cards,
            "ALUGUEL MENSAL",
            formatar_moeda_br(safe_float(dados.get("aluguel", 0))),
        )
        self._draw_card(
            CFG.CARD_X_START + CFG.CARD_WIDTH + CFG.CARD_GAP, y_cards,
            "IPTU (PARCELA)",
            formatar_moeda_br(safe_float(dados.get("iptu", 0))),
        )
        self._draw_card(
            CFG.CARD_X_START + (CFG.CARD_WIDTH + CFG.CARD_GAP) * 2, y_cards,
            "PRAZO",
            f"{dados.get('prazo', '-')} meses",
        )
        self.set_y(y_cards + CFG.CARD_HEIGHT + 5)

        self._row("Garantia:", str(dados.get("garantia", "-")))
        self.ln(2)
        self._row("Condições Gerais:", str(dados.get("condicoes_gerais", "-")))
        self._row("Informações Adicionais:", str(dados.get("info_gerais_manuais", "-")))

        self._section_title("2. Qualificação Societária")
        self._row("Razão Social:", str(dados.get("empresa", "-")))
        self._row("CNPJ:", str(dados.get("cnpj", "-")))
        self._row("Fundação:", str(dados.get("data_abertura", "-")))
        self._row("Capital Social:", str(dados.get("capital_social", "-")))
        self._row("Quadro Societário:", str(dados.get("socios_participacao", "-")))
        self._row("Administrador:", str(dados.get("administrador", "-")))

    def render_fiadores(self, dados: DadosRelatorio) -> None:
        """Página de Fiadores — só renderizada se dados relevantes existirem."""
        self.add_page()
        self._section_title("3. Auditoria de Fiadores")

        # Cabeçalho da tabela
        self.set_fill_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
        self.set_text_color(255, 255, 255)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        self.cell(90, 8, limpa_pdf(" Indicador"), border=1, align="L", fill=True)
        self.cell(80, 8, limpa_pdf(" Valor / Descrição"), border=1, ln=1, align="L", fill=True)

        # Linhas da tabela
        campos: list[tuple[str, str]] = [
            ("Rendimentos Tributáveis (IRPF)", "rend_tributaveis"),
            ("Rendimentos não Tributáveis (IRPF)", "rend_nao_tributaveis"),
            ("Renda Mensal média Oficial", "renda_media_oficial"),
            ("Renda Mensal atual", "renda_media_atual"),
            ("Patrimônio declarado", "patrimonio_declarado"),
            ("Aluguel Pretendido", "aluguel_pretendido"),
            ("Dívidas", "dividas"),
            ("Ônus", "onus"),
        ]
        self.set_text_color(0, 0, 0)
        self.set_font(CFG.FONT, "", 9)
        for label, key in campos:
            self.cell(90, 7, limpa_pdf(f" {label}"), border=1, align="L")
            self.cell(80, 7, limpa_pdf(f" {dados.get(key, '-')}"), border=1, ln=1, align="L")

        self.ln(5)
        self._row("Segmentação de Patrimônio:", str(dados.get("segmentacao_patrimonio", "-")))
        self.ln(2)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf("Conclusão Crítica (Fiador):"), ln=1)
        self.set_font(CFG.FONT, "I", CFG.FONT_SIZE_BODY)
        # Limpeza de markdown para evitar caracteres como pipe (|) ou arrays no texto corrido
        texto_limpo_fiador = limpa_markdown(str(dados.get("conclusao_fiador", "-")))
        self.multi_cell(0, 5, limpa_pdf(texto_limpo_fiador), align="J")

    def render_credito_e_financeiro(self, dados: DadosRelatorio) -> None:
        """Página de análise de crédito e financeira."""
        self.add_page()

        self._section_title("4. Análise de Risco (Serasa/Crédito)")
        self._row("Score Serasa:", str(dados.get("score_serasa", "-")))
        self._row("Nível de Risco:", str(dados.get("risco_serasa", "-")))
        self.ln(2)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf("Apontamentos e Contágio Societário:"), ln=1)
        self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
        self.multi_cell(
            0, 5,
            limpa_pdf(str(dados.get("mapeamento_dividas", "Sem restrições mapeadas."))),
            align="J",
        )

        self._section_title("5. Análise Contábil/Financeira")

        # Cabeçalho da matriz financeira
        self.set_fill_color(CFG.DARK_R, CFG.DARK_G, CFG.DARK_B)
        self.set_text_color(255, 255, 255)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        self.cell(40, 8, limpa_pdf(" Período"), border=1, align="C", fill=True)
        self.cell(65, 8, limpa_pdf(" Receita Bruta"), border=1, align="C", fill=True)
        self.cell(65, 8, limpa_pdf(" Resultado (L/P)"), border=1, ln=1, align="C", fill=True)

        # Linhas de dados
        self.set_text_color(0, 0, 0)
        self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
        periodos: list[str] = dados.get("periodos", [])
        receitas: list[str] = dados.get("receita_bruta", [])
        resultados: list[str] = dados.get("resultado", [])

        for i, periodo in enumerate(periodos):
            self.cell(40, 7, limpa_pdf(str(periodo)), border=1, align="C")
            self.cell(65, 7, limpa_pdf(str(receitas[i]) if i < len(receitas) else "-"), border=1, align="C")
            self.cell(65, 7, limpa_pdf(str(resultados[i]) if i < len(resultados) else "-"), border=1, ln=1, align="C")

        self.ln(5)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf("Parecer Técnico do Auditor Financeiro:"), ln=1)
        self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
        # Limpeza agressiva de tabelas markdown vindo da IA para PDF
        texto_limpo_financeiro = limpa_markdown(str(dados.get("analise_executiva", "Análise não realizada.")))
        self.multi_cell(
            0, 5,
            limpa_pdf(texto_limpo_financeiro),
            align="J",
        )

    def render_parecer_final(self, dados: DadosRelatorio, decisao: str) -> None:
        """Página de parecer oficial e veredito."""
        self.add_page()

        self._section_title("6. Parecer Oficial Paulo Bio")
        self.set_font(CFG.FONT, "B", 11)
        # Limpeza de markdown para garantir que o parecer oficial saia sem caracteres especiais no PDF
        texto_limpo_parecer = limpa_markdown(str(dados.get("parecer_oficial", "Parecer não incluído.")))
        self.multi_cell(
            0, CFG.LINE_HEIGHT_BODY,
            limpa_pdf(texto_limpo_parecer),
            align="J",
        )

        # Solução Complementar
        solucao = dados.get("solucao_complementar", "")
        if solucao:
            self.ln(8)
            self._section_title("7. Solução Complementar")
            self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
            # Limpeza de markdown para a solução complementar
            texto_limpo_solucao = limpa_markdown(solucao)
            self.multi_cell(
                0, CFG.LINE_HEIGHT_BODY,
                limpa_pdf(texto_limpo_solucao),
                align="J",
            )
        
        # Checklist de Documentos Analisados
        checklist = dados.get("checklist_docs", {})
        if checklist:
            self.ln(8)
            self._section_title("Documentos Consultados (Checklist)")
            self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
            for passo, arquivos in checklist.items():
                if arquivos:
                    # Printa o Passo em bold
                    self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
                    self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf(f"[X] {passo}:"), ln=1)
                    # Printa os arquivos em formato bullet point
                    self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
                    for arq in arquivos:
                        self.set_x(CFG.MARGIN_LEFT + 5)
                        self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf(f"- {arq}"), ln=1)

        self.ln(10)
        self.set_fill_color(CFG.LIGHT_BG_R, CFG.LIGHT_BG_G, CFG.LIGHT_BG_B)
        self.rect(CFG.MARGIN_LEFT, self.get_y(), 170, 15, "F")
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_VERDICT)
        self.set_text_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
        self.cell(0, 15, limpa_pdf(f"VEREDITO: {decisao}"), ln=1, align="C")

        self.ln(15)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, limpa_pdf("____________________________________________________"), ln=1, align="C")
        self.cell(0, 5, limpa_pdf("DEPARTAMENTO JURÍDICO / CRÉDITO - PAULO BIO IMÓVEIS"), ln=1, align="C")


# ---------------------------------------------------------------------------
# Validação de entrada
# ---------------------------------------------------------------------------

def _validar_dados(dados: dict) -> DadosRelatorio:
    """
    Garante tipos mínimos esperados e retorna um DadosRelatorio seguro.
    Não lança mais ValueError se um campo de lista for string, tenta corrigir.
    """
    if not isinstance(dados, dict):
        try:
            dados = dict(dados)
        except:
            dados = {}

    campos_lista = ("periodos", "receita_bruta", "resultado")
    for campo in campos_lista:
        if campo in dados and not isinstance(dados[campo], list):
            # Se a IA retornou string em vez de array, transforma num array seguro
            val = dados[campo]
            if isinstance(val, str):
                dados[campo] = [x.strip() for x in val.split(',')]
            else:
                dados[campo] = [str(val)]

    return dados  # type: ignore[return-value]


def _tem_dados_fiadores(dados: DadosRelatorio) -> bool:
    """Verifica se há dados suficientes para renderizar a seção de fiadores."""
    return bool(dados.get("conclusao_fiador") or dados.get("rend_tributaveis"))


# ---------------------------------------------------------------------------
# Ponto de entrada público
# ---------------------------------------------------------------------------

def gerar_pdf_bytes(dados: dict, decisao: str) -> bytes:
    """
    Gera o PDF executivo e retorna os bytes prontos para salvar ou servir via HTTP.

    Args:
        dados:   Dicionário com os dados do relatório (ver DadosRelatorio).
        decisao: Texto do veredito final (ex: "APROVADO" / "REPROVADO").

    Returns:
        bytes do PDF em UTF-8 (fpdf2 nativo, sem encode manual).

    Raises:
        TypeError:  Se 'dados' não for um dict.
        ValueError: Se campos com tipo incorreto forem detectados.
        RuntimeError: Se a geração do PDF falhar por erro interno do fpdf2.
    """
    dados_validados = _validar_dados(dados)

    try:
        pdf = PDFExecutivo()
        pdf.render_capa(dados_validados)
        pdf.render_negocio_e_qualificacao(dados_validados)

        if _tem_dados_fiadores(dados_validados):
            pdf.render_fiadores(dados_validados)

        pdf.render_credito_e_financeiro(dados_validados)
        pdf.render_parecer_final(dados_validados, decisao)

        # fpdf2 moderno: output() pode retornar bytearray ou bytes dependendo da versão
        # Streamlit requer bytes explícito para st.download_button
        out = pdf.output(dest="S")
        if isinstance(out, str):
            return out.encode("latin1")
        return bytes(out)  # garante bytes mesmo se fpdf2 retornar bytearray

    except Exception as exc:
        raise RuntimeError(f"Falha ao gerar PDF: {exc}") from exc