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
    # Ficha Cadastral (Passo 2 — referências)
    ref_locaticias: str
    ref_comerciais: str
    ref_bancarias: str
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
    # Patrimonial (extraído da analise_executiva ou campos dedicados)
    patrimonio_liquido: list[str]
    ativo_circulante: list[str]
    ativo_nao_circulante: list[str]
    passivo_circulante: list[str]
    passivo_nao_circulante: list[str]
    imobilizado: list[str]
    alerta_divergencia_contabil: str
    # Veredito
    parecer_oficial: str
    solucao_complementar: str
    # Checklist
    checklist_docs: dict[str, list[str]]

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

    # Cores de status
    GREEN_R: int = 39
    GREEN_G: int = 174
    GREEN_B: int = 96

    RED_R: int = 231
    RED_G: int = 76
    RED_B: int = 60

    YELLOW_R: int = 241
    YELLOW_G: int = 196
    YELLOW_B: int = 15

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

    # Largura útil da área de conteúdo
    CONTENT_WIDTH: float = 170.0  # 210 - 20 - 20

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

# Lista completa dos passos do workflow para o checklist
PASSOS_WORKFLOW: list[tuple[str, str]] = [
    ("Passo 0 (Contrato Social)", "Contrato Social e Aditivos"),
    ("Passo 1 (Proposta)", "Proposta de Locação"),
    ("Passo 1 (Fiador)", "IRPF do Fiador"),
    ("Passo 2 (Ficha Cadastral)", "Ficha Cadastral"),
    ("Passo 3 (Serasa)", "Consulta Serasa/Crédito"),
    ("Passo 4 (Certidões)", "Certidões Judiciais"),
    ("Passo 5 (Contábil)", "Balanço e DRE"),
    ("Passo 6 (IR Sócios)", "IR dos Sócios"),
]


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
        self._section_counter: int = 0  # numeração contínua de seções

    # ------------------------------------------------------------------
    # Header / Footer (ABNT — rodapé padronizado)
    # ------------------------------------------------------------------

    def header(self) -> None:
        if self.page_no() > 1:
            self.set_fill_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
            self.rect(0, 0, 210, 3, "F")
            self.ln(5)

    def footer(self) -> None:
        self.set_y(-18)
        # Linha separadora sutil
        self.set_draw_color(200, 200, 200)
        self.line(CFG.MARGIN_LEFT, self.get_y(), 190, self.get_y())
        self.ln(2)
        # Texto à esquerda: confidencial
        self.set_font(CFG.FONT, "I", CFG.FONT_SIZE_SMALL)
        self.set_text_color(CFG.GRAY_R, CFG.GRAY_G, CFG.GRAY_B)
        self.cell(
            CFG.CONTENT_WIDTH / 2, 5,
            limpa_pdf("Paulo Bio Imóveis - Confidencial"),
            align="L",
        )
        # Texto à direita: página X de Y
        self.cell(
            CFG.CONTENT_WIDTH / 2, 5,
            limpa_pdf(f"Página {self.page_no()} de {{nb}}"),
            align="R",
        )

    # ------------------------------------------------------------------
    # Helpers de estilo reutilizáveis
    # ------------------------------------------------------------------

    def _next_section(self, txt: str) -> None:
        """Título de seção numerado automaticamente com linha laranja abaixo."""
        self._section_counter += 1
        full_title = f"{self._section_counter}. {txt}"
        self.ln(8)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_TITLE_SECTION)
        self.set_text_color(CFG.DARK_R, CFG.DARK_G, CFG.DARK_B)
        self.cell(0, CFG.LINE_HEIGHT_SECTION, limpa_pdf(full_title), ln=1)
        self.set_draw_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
        self.line(CFG.MARGIN_LEFT, self.get_y(), 190, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def _section_title(self, txt: str) -> None:
        """Título de seção sem numeração (para sub-seções como checklist)."""
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
        self.set_x(CFG.MARGIN_LEFT)
        self.set_text_color(0, 0, 0)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        label_w = 55.0
        self.cell(label_w, CFG.LINE_HEIGHT_BODY, limpa_pdf(label))
        self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
        value_w = 210.0 - CFG.MARGIN_LEFT - CFG.MARGIN_RIGHT - label_w
        self.multi_cell(value_w, CFG.LINE_HEIGHT_BODY, limpa_pdf(str(value)), align="J")

    def _table_row_wrapped(self, label: str, value: str, label_w: float = 90.0, value_w: float = 80.0, zebra: bool = False) -> None:
        """Linha de tabela com word-wrap no valor — resolve overflow de texto."""
        x_start = self.get_x()
        y_start = self.get_y()

        # Background zebra
        if zebra:
            self.set_fill_color(CFG.LIGHT_BG_R, CFG.LIGHT_BG_G, CFG.LIGHT_BG_B)
        else:
            self.set_fill_color(255, 255, 255)

        # Calcular altura necessária para o valor (multi_cell)
        # Usamos um truque: medir quantas linhas o texto vai ocupar
        text_clean = limpa_pdf(f" {value}")
        # Largura efetiva do texto dentro da célula (margem interna de 1mm)
        effective_w = value_w - 2
        if effective_w <= 0:
            effective_w = value_w
        n_lines = max(1, len(self.multi_cell(effective_w, 5, text_clean, dry_run=True, output="LINES")))
        row_h = max(7, n_lines * 5)

        # Desenhar label (altura fixa = row_h)
        self.set_xy(x_start, y_start)
        self.set_font(CFG.FONT, "", 9)
        self.cell(label_w, row_h, limpa_pdf(f" {label}"), border=1, align="L", fill=True)

        # Desenhar valor com multi_cell
        self.set_xy(x_start + label_w, y_start)
        # Desenhar fundo + borda manualmente
        self.rect(x_start + label_w, y_start, value_w, row_h, "FD")
        self.set_xy(x_start + label_w + 1, y_start + 1)
        self.multi_cell(effective_w, 5, text_clean, align="L")

        # Posicionar cursor na próxima linha
        self.set_xy(x_start, y_start + row_h)

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

    def _draw_commitment_card(self, pct: float) -> None:
        """Card visual de comprometimento de renda com cor semafórica."""
        if pct <= 30:
            r, g, b = CFG.GREEN_R, CFG.GREEN_G, CFG.GREEN_B
            status = "SAUDÁVEL"
        elif pct <= 50:
            r, g, b = CFG.YELLOW_R, CFG.YELLOW_G, CFG.YELLOW_B
            status = "ATENÇÃO"
        else:
            r, g, b = CFG.RED_R, CFG.RED_G, CFG.RED_B
            status = "CRÍTICO"

        y = self.get_y()
        # Fundo do card
        self.set_fill_color(CFG.LIGHT_BG_R, CFG.LIGHT_BG_G, CFG.LIGHT_BG_B)
        self.rect(CFG.MARGIN_LEFT, y, CFG.CONTENT_WIDTH, 18, "F")
        # Barra lateral colorida
        self.set_fill_color(r, g, b)
        self.rect(CFG.MARGIN_LEFT, y, 4, 18, "F")
        # Texto
        self.set_xy(CFG.MARGIN_LEFT + 8, y + 2)
        self.set_font(CFG.FONT, "B", 11)
        self.set_text_color(r, g, b)
        self.cell(40, 7, limpa_pdf(f"{pct:.1f}%"), align="L")
        self.set_font(CFG.FONT, "B", 9)
        self.set_text_color(CFG.DARK_R, CFG.DARK_G, CFG.DARK_B)
        self.cell(30, 7, limpa_pdf(f"({status})"), align="L")
        self.set_font(CFG.FONT, "", 9)
        self.set_text_color(80, 80, 80)
        self.cell(0, 7, limpa_pdf("Comprometimento do aluguel sobre a receita/renda mensal"), align="L")
        self.set_y(y + 22)

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

    def render_sumario_executivo(self, dados: DadosRelatorio, decisao: str) -> None:
        """Página 2 — Sumário Executivo com os dados-chave da análise."""
        self.add_page()
        self._section_title("Sumário Executivo")

        self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
        self.set_text_color(80, 80, 80)
        self.multi_cell(
            0, 5,
            limpa_pdf(
                "Este relatório apresenta a análise de crédito e risco elaborada pela "
                "Paulo Bio Imóveis, contemplando qualificação societária, auditoria de "
                "fiadores, análise de crédito (Serasa), auditoria contábil/financeira e "
                "parecer técnico final."
            ),
            align="J",
        )
        self.ln(5)

        # Mini-tabela de resumo
        campos_resumo: list[tuple[str, str]] = [
            ("Pretendente", str(dados.get("pretendente", dados.get("empresa", "-")))),
            ("CNPJ", str(dados.get("cnpj", "-"))),
            ("Imóvel", str(dados.get("imovel", "-"))),
            ("Aluguel Mensal", formatar_moeda_br(safe_float(dados.get("aluguel", 0)))),
            ("Score Serasa", str(dados.get("score_serasa", "-"))),
            ("Nível de Risco", str(dados.get("risco_serasa", "-"))),
            ("Veredito", decisao),
        ]

        self.set_fill_color(CFG.DARK_R, CFG.DARK_G, CFG.DARK_B)
        self.set_text_color(255, 255, 255)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        self.cell(60, 8, limpa_pdf(" Indicador"), border=1, align="L", fill=True)
        self.cell(110, 8, limpa_pdf(" Valor"), border=1, ln=1, align="L", fill=True)

        self.set_text_color(0, 0, 0)
        for i, (label, valor) in enumerate(campos_resumo):
            zebra = i % 2 == 0
            if zebra:
                self.set_fill_color(CFG.LIGHT_BG_R, CFG.LIGHT_BG_G, CFG.LIGHT_BG_B)
            else:
                self.set_fill_color(255, 255, 255)
            self.set_font(CFG.FONT, "B", 9)
            self.cell(60, 7, limpa_pdf(f" {label}"), border=1, align="L", fill=True)
            # Veredito em cor primária
            if label == "Veredito":
                self.set_font(CFG.FONT, "B", 9)
                self.set_text_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
            else:
                self.set_font(CFG.FONT, "", 9)
                self.set_text_color(0, 0, 0)
            self.cell(110, 7, limpa_pdf(f" {valor}"), border=1, ln=1, align="L", fill=True)
            self.set_text_color(0, 0, 0)

        self.ln(5)
        self.set_font(CFG.FONT, "I", CFG.FONT_SIZE_SMALL)
        self.set_text_color(CFG.GRAY_R, CFG.GRAY_G, CFG.GRAY_B)
        self.cell(
            0, 5,
            limpa_pdf(f"Data de emissão: {CFG.data_hoje_ptbr()}"),
            ln=1,
        )

    def render_negocio_e_qualificacao(self, dados: DadosRelatorio) -> None:
        """Dados do negócio, qualificação societária e ficha cadastral."""
        self.add_page()

        self._next_section("Dados do Negócio")
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

        # --- Seção 2: Qualificação Societária ---
        self._next_section("Qualificação Societária")
        self._row("Razão Social:", str(dados.get("empresa", "-")))
        self._row("CNPJ:", str(dados.get("cnpj", "-")))
        self._row("Fundação:", str(dados.get("data_abertura", "-")))
        self._row("Capital Social:", str(dados.get("capital_social", "-")))
        self._row("Quadro Societário:", str(dados.get("socios_participacao", "-")))
        self._row("Administrador:", str(dados.get("administrador", "-")))

        # --- Melhoria 1: Ficha Cadastral (referências do Passo 2) ---
        ref_loc = str(dados.get("ref_locaticias", "")).strip()
        ref_com = str(dados.get("ref_comerciais", "")).strip()
        ref_ban = str(dados.get("ref_bancarias", "")).strip()

        if ref_loc or ref_com or ref_ban:
            self.ln(4)
            self.set_font(CFG.FONT, "B", 11)
            self.set_text_color(CFG.DARK_R, CFG.DARK_G, CFG.DARK_B)
            self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf("Referências Cadastrais"), ln=1)
            self.ln(2)
            self.set_text_color(0, 0, 0)

            ref_items: list[tuple[str, str]] = [
                ("Ref. Locatícias:", ref_loc or "Não informado"),
                ("Ref. Comerciais:", ref_com or "Não informado"),
                ("Ref. Bancárias:", ref_ban or "Não informado"),
            ]
            for label, valor in ref_items:
                self._row(label, valor)

    def render_fiadores(self, dados: DadosRelatorio) -> None:
        """Página de Fiadores — só renderizada se dados relevantes existirem."""
        self.add_page()
        self._next_section("Auditoria de Fiadores")

        # Cabeçalho da tabela
        self.set_fill_color(CFG.PRIMARY_R, CFG.PRIMARY_G, CFG.PRIMARY_B)
        self.set_text_color(255, 255, 255)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        label_w = 90.0
        value_w = 80.0
        self.cell(label_w, 8, limpa_pdf(" Indicador"), border=1, align="L", fill=True)
        self.cell(value_w, 8, limpa_pdf(" Valor / Descrição"), border=1, ln=1, align="L", fill=True)

        # --- Melhoria 2: Tabela com word-wrap (resolve overflow) ---
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
        for i, (label, key) in enumerate(campos):
            self._table_row_wrapped(
                label,
                str(dados.get(key, "-")),
                label_w=label_w,
                value_w=value_w,
                zebra=(i % 2 == 0),
            )

        self.ln(5)
        self._row("Segmentação de Patrimônio:", str(dados.get("segmentacao_patrimonio", "-")))
        self.ln(2)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf("Conclusão Crítica (Fiador):"), ln=1)
        self.set_font(CFG.FONT, "I", CFG.FONT_SIZE_BODY)
        texto_limpo_fiador = limpa_markdown(str(dados.get("conclusao_fiador", "-")))
        self.multi_cell(0, 5, limpa_pdf(texto_limpo_fiador), align="J")

    def render_credito_e_financeiro(self, dados: DadosRelatorio) -> None:
        """Página de análise de crédito e financeira."""
        self.add_page()

        self._next_section("Análise de Risco (Serasa/Crédito)")
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

        self._next_section("Análise Contábil/Financeira")

        # --- Tabela DRE: Período × Receita × Resultado ---
        self.set_font(CFG.FONT, "B", 11)
        self.set_text_color(CFG.DARK_R, CFG.DARK_G, CFG.DARK_B)
        self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf("Demonstrativo de Resultados"), ln=1)
        self.ln(2)

        self.set_fill_color(CFG.DARK_R, CFG.DARK_G, CFG.DARK_B)
        self.set_text_color(255, 255, 255)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        self.cell(40, 8, limpa_pdf(" Período"), border=1, align="C", fill=True)
        self.cell(65, 8, limpa_pdf(" Receita Bruta"), border=1, align="C", fill=True)
        self.cell(65, 8, limpa_pdf(" Resultado (L/P)"), border=1, ln=1, align="C", fill=True)

        self.set_text_color(0, 0, 0)
        self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
        periodos: list[str] = dados.get("periodos", [])
        receitas: list[str] = dados.get("receita_bruta", [])
        resultados: list[str] = dados.get("resultado", [])

        for i, periodo in enumerate(periodos):
            zebra = i % 2 == 0
            if zebra:
                self.set_fill_color(CFG.LIGHT_BG_R, CFG.LIGHT_BG_G, CFG.LIGHT_BG_B)
            else:
                self.set_fill_color(255, 255, 255)
            self.cell(40, 7, limpa_pdf(str(periodo)), border=1, align="C", fill=True)
            self.cell(65, 7, limpa_pdf(str(receitas[i]) if i < len(receitas) else "-"), border=1, align="C", fill=True)
            self.cell(65, 7, limpa_pdf(str(resultados[i]) if i < len(resultados) else "-"), border=1, ln=1, align="C", fill=True)

        # --- Melhoria 3: Matriz Patrimonial (Balanço) ---
        patrimonio_liq = dados.get("patrimonio_liquido", [])
        ativo_circ = dados.get("ativo_circulante", [])
        ativo_ncirc = dados.get("ativo_nao_circulante", [])
        passivo_circ = dados.get("passivo_circulante", [])
        passivo_ncirc = dados.get("passivo_nao_circulante", [])
        imobilizado = dados.get("imobilizado", [])

        # Verifica se há dados patrimoniais (qualquer lista não-vazia)
        tem_patrimonial = any([patrimonio_liq, ativo_circ, ativo_ncirc, passivo_circ, passivo_ncirc, imobilizado])

        if tem_patrimonial and periodos:
            self.ln(8)
            self.set_font(CFG.FONT, "B", 11)
            self.set_text_color(CFG.DARK_R, CFG.DARK_G, CFG.DARK_B)
            self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf("Balanço Patrimonial Consolidado"), ln=1)
            self.ln(2)

            # Header: Indicador | Período 1 | Período 2 | ...
            n_periodos = len(periodos)
            col_label_w = 60.0
            col_val_w = (CFG.CONTENT_WIDTH - col_label_w) / max(n_periodos, 1)

            self.set_fill_color(CFG.DARK_R, CFG.DARK_G, CFG.DARK_B)
            self.set_text_color(255, 255, 255)
            self.set_font(CFG.FONT, "B", 9)
            self.cell(col_label_w, 8, limpa_pdf(" Indicador"), border=1, align="L", fill=True)
            for p in periodos:
                self.cell(col_val_w, 8, limpa_pdf(str(p)), border=1, align="C", fill=True)
            self.ln()

            # Linhas da matriz
            indicadores: list[tuple[str, list[str]]] = [
                ("Patrimônio Líquido", patrimonio_liq),
                ("Ativo Circulante", ativo_circ),
                ("Ativo Não Circulante", ativo_ncirc),
                ("Passivo Circulante", passivo_circ),
                ("Passivo Não Circulante", passivo_ncirc),
                ("Imobilizado", imobilizado),
            ]

            self.set_text_color(0, 0, 0)
            for idx, (nome_ind, valores) in enumerate(indicadores):
                zebra = idx % 2 == 0
                if zebra:
                    self.set_fill_color(CFG.LIGHT_BG_R, CFG.LIGHT_BG_G, CFG.LIGHT_BG_B)
                else:
                    self.set_fill_color(255, 255, 255)
                self.set_font(CFG.FONT, "B", 9)
                self.cell(col_label_w, 7, limpa_pdf(f" {nome_ind}"), border=1, align="L", fill=True)
                self.set_font(CFG.FONT, "", 9)
                for j in range(n_periodos):
                    val = str(valores[j]) if j < len(valores) else "-"
                    self.cell(col_val_w, 7, limpa_pdf(val), border=1, align="C", fill=True)
                self.ln()

        # --- Comprometimento de Renda ---
        self.ln(5)
        aluguel_val = safe_float(dados.get("aluguel", 0))
        # Tentar renda do fiador primeiro, senão receita bruta mensal
        renda_ref = safe_float(dados.get("renda_media_oficial", 0))

        if renda_ref <= 0 and receitas:
            # Usar última receita bruta anual / 12
            ultima_receita_str = str(receitas[-1]).replace("R$", "").replace(".", "").replace(",", ".").strip()
            try:
                renda_ref = float(ultima_receita_str) / 12
            except (ValueError, ZeroDivisionError):
                renda_ref = 0

        if aluguel_val > 0 and renda_ref > 0:
            pct = (aluguel_val / renda_ref) * 100
            self._draw_commitment_card(pct)

        # --- Parecer Técnico do Auditor ---
        self.ln(3)
        self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
        self.set_text_color(0, 0, 0)
        self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf("Parecer Técnico do Auditor Financeiro:"), ln=1)
        self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
        texto_limpo_financeiro = limpa_markdown(str(dados.get("analise_executiva", "Análise não realizada.")))
        self.multi_cell(
            0, 5,
            limpa_pdf(texto_limpo_financeiro),
            align="J",
        )

    def render_parecer_final(self, dados: DadosRelatorio, decisao: str) -> None:
        """Página de parecer oficial e veredito."""
        self.add_page()

        self._next_section("Parecer Oficial Paulo Bio")
        # --- Melhoria 4: Texto em fonte regular (não bold) ---
        self.set_font(CFG.FONT, "", 11)
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
            self._next_section("Solução Complementar")
            self.set_font(CFG.FONT, "", CFG.FONT_SIZE_BODY)
            texto_limpo_solucao = limpa_markdown(solucao)
            self.multi_cell(
                0, CFG.LINE_HEIGHT_BODY,
                limpa_pdf(texto_limpo_solucao),
                align="J",
            )

        # --- Melhoria 5: Checklist Completo (todos os passos) ---
        checklist = dados.get("checklist_docs", {})
        self.ln(8)
        self._section_title("Documentos Consultados (Checklist)")

        for passo_key, passo_desc in PASSOS_WORKFLOW:
            arquivos = checklist.get(passo_key, [])

            if arquivos:
                # ✓ Verde — documentos presentes
                self.set_text_color(CFG.GREEN_R, CFG.GREEN_G, CFG.GREEN_B)
                self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
                self.set_x(CFG.MARGIN_LEFT)
                # Usar "V" como check visual (Helvetica não tem ✓)
                self.cell(8, CFG.LINE_HEIGHT_BODY, limpa_pdf("[V]"), align="L")
                self.set_text_color(0, 0, 0)
                self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
                self.cell(55, CFG.LINE_HEIGHT_BODY, limpa_pdf(passo_desc))
                self.set_font(CFG.FONT, "", 9)
                self.set_text_color(80, 80, 80)
                nomes = ", ".join(arquivos)
                remaining_w = CFG.CONTENT_WIDTH - 8 - 55
                self.multi_cell(remaining_w, CFG.LINE_HEIGHT_BODY - 1, limpa_pdf(nomes), align="L")
            else:
                # ✗ Vermelho — não anexado
                self.set_text_color(CFG.RED_R, CFG.RED_G, CFG.RED_B)
                self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
                self.set_x(CFG.MARGIN_LEFT)
                self.cell(8, CFG.LINE_HEIGHT_BODY, limpa_pdf("[X]"), align="L")
                self.set_text_color(0, 0, 0)
                self.set_font(CFG.FONT, "B", CFG.FONT_SIZE_BODY)
                self.cell(55, CFG.LINE_HEIGHT_BODY, limpa_pdf(passo_desc))
                self.set_font(CFG.FONT, "I", 9)
                self.set_text_color(CFG.RED_R, CFG.RED_G, CFG.RED_B)
                self.cell(0, CFG.LINE_HEIGHT_BODY, limpa_pdf("Não anexado"), ln=1, align="L")

            self.set_text_color(0, 0, 0)

        # --- Veredito Final ---
        self.ln(10)
        self.set_fill_color(CFG.LIGHT_BG_R, CFG.LIGHT_BG_G, CFG.LIGHT_BG_B)
        self.rect(CFG.MARGIN_LEFT, self.get_y(), CFG.CONTENT_WIDTH, 15, "F")
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
        except Exception:
            dados = {}

    campos_lista = (
        "periodos", "receita_bruta", "resultado",
        "patrimonio_liquido", "ativo_circulante", "ativo_nao_circulante",
        "passivo_circulante", "passivo_nao_circulante", "imobilizado",
    )
    for campo in campos_lista:
        if campo in dados and not isinstance(dados[campo], list):
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
        pdf.alias_nb_pages()  # habilita {nb} para total de páginas no rodapé

        pdf.render_capa(dados_validados)
        pdf.render_sumario_executivo(dados_validados, decisao)
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
