import base64
import streamlit as st
from openai import OpenAI
from utils.formatters import extrair_json_seguro
from core.logger import get_logger

logger = get_logger(__name__)


class AIService:
    def __init__(self):
        self.api_key = st.secrets["OPENROUTER_API_KEY"]
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            timeout=120.0,
        )
        self.model = "google/gemini-2.5-flash"

    def _generate_content(self, prompt, files=None):
        parts = []
        if files:
            for f in files:
                f.seek(0)
                content = f.read()

                if not content:
                    logger.warning("Arquivo %s está vazio — ignorado.", f.name)
                    st.warning(f"Arquivo {f.name} está vazio.")
                    continue

                if len(content) > 20 * 1024 * 1024:
                    logger.warning("Arquivo %s excede 20MB (%d bytes) — ignorado.", f.name, len(content))
                    st.warning(f"Arquivo {f.name} excede 20MB. Ignorando.")
                    continue

                try:
                    b64 = base64.standard_b64encode(content).decode("utf-8")
                    parts.append({
                        "type": "file",
                        "file": {
                            "filename": f.name,
                            "file_data": f"data:application/pdf;base64,{b64}",
                        },
                    })
                    logger.debug("Arquivo %s codificado (%d bytes).", f.name, len(content))
                except Exception as e:
                    logger.error("Falha ao processar arquivo %s: %s", f.name, e)
                    st.warning(f"Não foi possível processar {f.name}: {e}")
                    continue

        if not parts:
            logger.error("Nenhum arquivo válido para análise.")
            st.error("Nenhum arquivo válido para análise.")
            return {}

        parts.append({"type": "text", "text": prompt})

        try:
            logger.info("Enviando requisição para modelo %s (%d partes).", self.model, len(parts))
            res = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": parts}],
            )
            text = res.choices[0].message.content
            if not text:
                logger.warning("IA retornou resposta vazia.")
                st.warning("A IA não retornou conteúdo.")
                return {}
            logger.info("Resposta recebida da IA (%d caracteres).", len(text))
            return extrair_json_seguro(text)
        except Exception as e:
            erro_str = str(e)
            if "clipboard" in erro_str.lower() or "image" in erro_str.lower():
                logger.error("Erro de formato de PDF na IA: %s", erro_str)
                st.error("Erro ao processar PDF: formato incompatível. Verifique se os arquivos são PDFs válidos.")
            else:
                logger.error("Erro na chamada da IA: %s", erro_str)
                st.error(f"Erro na IA: {erro_str}")
            return {}

    def extrair_contrato(self, files):
        prompt = """Analise o Contrato Social e Aditivos: extraia empresa, cnpj, endereco_empresa, data_abertura, capital_social, administrador. 
        Gere 'socios_participacao' como um texto corrido (string) listando o quadro societário e percentuais (NÃO use array/lista).
        Gere 'informacoes_adicionais' como um relato textual contínuo (string) sobre o histórico de aditivos (NÃO use array/lista).
        Retorne um JSON contendo exatamente estas chaves: empresa, cnpj, endereco_empresa, data_abertura, capital_social, administrador, socios_participacao, informacoes_adicionais."""
        return self._generate_content(prompt, files)

    def extrair_proposta(self, file):
        prompt = """Extraia dados detalhados da proposta de locação: pretendente, atividade, imovel, prazo, data_inicio, carencia, aluguel, iptu, garantia. 
        Gere 'condicoes_gerais' como texto (string) relatando reajustes e escalas (NÃO use array/lista).
        Gere 'info_gerais_manuais' como texto (string) relatando anotações extras e contatos (NÃO use array/lista).
        Retorne somente um JSON com as chaves: pretendente, atividade, imovel, prazo, data_inicio, carencia, aluguel, iptu, garantia, condicoes_gerais, info_gerais_manuais."""
        return self._generate_content(prompt, [file])

    def analisar_fiador(self, files, aluguel):
        prompt = f"""AUDITORIA DE FIADOR (Aluguel Pretendido: R$ {aluguel}): 
        Extraia e ANALISE os dados do fiador para compor a matriz financeira. 
        Gere um JSON com as chaves exatas abaixo (use strings, NUNCA arrays):
        {{
            "rend_tributaveis": "Valor anual R$",
            "rend_nao_tributaveis": "Valor anual R$",
            "renda_media_oficial": "Média mensal R$",
            "renda_media_atual": "Média mensal atual R$",
            "patrimonio_declarado": "Valor total R$",
            "aluguel_pretendido": "{aluguel}",
            "dividas": "Valor total de dívidas/ônus R$",
            "onus": "Descrição de ônus se houver",
            "segmentacao_patrimonio": "Descreva o que é Aplicação (liquidez) e o que é Patrimônio Físico (imóveis/veículos)",
            "conclusao_fiador": "Texto fluido avaliando se o patrimônio e renda do fiador sustentam o pretendente (mínimo 3x aluguel)."
        }}
        Retorne SOMENTE o JSON."""
        return self._generate_content(prompt, files)

    def extrair_referencias(self, file):
        prompt = """Extraia de forma textual (strings curtas, NUNCA lista/array) as Referências Locatícias (endereço, contato, valor), Comercias e Bancárias. 
        Retorne JSON estruturado no formato exato: { "ref_locaticias": "...", "ref_comerciais": "...", "ref_bancarias": "..." }. Se ausentar, devolva em branco."""
        return self._generate_content(prompt, [file])

    def mapear_serasa(self, files, empresa, cnpj):
        prompt = f"""ANÁLISE DE RISCO SERASA ({empresa} - {cnpj}): 
        1. Valide o CNPJ e a empresa. 'alerta_divergencia_serasa' deve conter aviso se houver.
        2. 'score_serasa' (string número) e 'risco_serasa' (alto/médio/baixo).
        3. No 'mapeamento_dividas' (TEXTO), descreva detalhadamente pendências (PEFIN, REFIN, etc) da empresa E TAMBÉM analise o contágio societário: verifique se há ou não pendências em OUTRAS empresas que o(s) sócio(s) possuam (quando listadas) e descreva os apontamentos se houver.
        Retorne SOMENTE UM JSON estruturado:
        {{
            "alerta_divergencia_serasa": "",
            "score_serasa": "",
            "risco_serasa": "",
            "mapeamento_dividas": ""
        }}
        """
        return self._generate_content(prompt, files)

    def auditar_certidoes(self, files, empresa, cnpj):
        prompt = f"""AUDITORIA JURÍDICA BRASILEIRA ({empresa} - {cnpj}): 
        Verifique Certidões. Identifique 'alerta_divergencia_certidoes' (string) se CNPJ não corresponder. 
        Gere 'resumo_certidoes' como um UNICO TEXTO descritivo (string, sem arrays/listas) explicando as ações relevantes.
        Retorne JSON com as chaves: alerta_divergencia_certidoes, resumo_certidoes."""
        return self._generate_content(prompt, files)

    def auditar_contabil(self, files, empresa, cnpj, aluguel, iptu):
        prompt = f"""AUDITORIA FINANCEIRA ({empresa} - {cnpj}): 
        Aluguel: {aluguel}, IPTU: {iptu}. 
        Atue como um analista financeiro sênior. Em anexo, estão os Balanços Patrimoniais e as DREs de 2024 e 2025 da empresa.
        Sua tarefa é extrair os dados contábeis e elaborar um resumo financeiro dividido em duas partes. Siga rigorosamente o passo a passo abaixo:
        Parte 1: Tabela Consolidada (Formato Obrigatório)
        Busque os dados cruzando as informações da DRE (para Receitas e Resultados) e do Balanço Patrimonial (para Ativos, Passivos e PL). Crie uma única tabela consolidada comparando 2024 e 2025, contendo EXATAMENTE as seguintes linhas:
        Receita Bruta (DRE), Resultado do Ano (DRE - Especifique se é Lucro ou Prejuízo), Patrimônio Líquido (Balanço), Ativo Circulante, Ativo Não Circulante, Passivo Circulante, Passivo Não Circulante, Imobilizado (Balanço).
        Parte 2: Análise do Resultado Acumulado Histórico (Raciocínio Lógico)
        Escreva dois parágrafos respondendo: qual o resultado acumulado atual (lucro ou prejuízo)?
        - Identifique o 'Prejuízo Acumulado' de 2024 (valor exato) que deixou o PL negativo.
        - Identifique a reversão em 2025 com o Lucro do Exercício (valor exato).
        - Conclua que o lucro de 2025 absorveu o prejuízo histórico, tornando o PL positivo.
        Retorne SOMENTE o JSON:
        {{
            "periodos": ["2024", "2025"],
            "receita_bruta": ["R$ ...", "R$ ..."],
            "resultado": ["R$ ...", "R$ ..."],
            "analise_executiva": "Tabela consolidada e análise técnica do resultado acumulado.",
            "alerta_divergencia_contabil": ""
        }}
        Retorne SOMENTE o JSON."""
        return self._generate_content(prompt, files)

    def analisar_patrimonio_socios(self, files, d):
        # Extrai contexto dos passos anteriores para enriquecer o parecer
        _empresa      = d.get('empresa', 'não informado')
        _abertura     = d.get('data_abertura', 'não informado')
        _capital      = d.get('capital_social', 'não informado')
        _aluguel      = d.get('aluguel', 'não informado')
        _score        = d.get('score_serasa', 'não informado')
        _risco        = d.get('risco_serasa', 'não informado')
        _dividas      = d.get('mapeamento_dividas', 'sem apontamentos')
        _ref_loc      = d.get('ref_locaticias', 'não informado')
        _periodos     = d.get('periodos', [])
        _receitas     = d.get('receita_bruta', [])
        _resultados   = d.get('resultado', [])
        _analise_cont = d.get('analise_executiva', 'não informado')
        _ult_resultado = _resultados[-1] if _resultados else 'não informado'
        _ult_receita   = _receitas[-1] if _receitas else 'não informado'
        _ult_periodo   = _periodos[-1] if _periodos else 'não informado'

        prompt = f"""CONTEXTO DOS PASSOS ANTERIORES (use para preencher o parecer):
        - Empresa: {_empresa} | Fundação: {_abertura} | Capital Social: {_capital}
        - Aluguel Pretendido: R$ {_aluguel}
        - Referência Locatícia: {_ref_loc}
        - Score Serasa: {_score} | Risco: {_risco}
        - Contágio/Dívidas: {_dividas}
        - Períodos Contábeis: {_periodos} | Receita Bruta: {_receitas} | Resultado: {_resultados}
        - Análise Técnica Contábil: {_analise_cont}

        ANÁLISE DE PATRIMÔNIO E PARECER (Aluguel Pretendido: {_aluguel}):
        1. 'conclusao_socio' (TEXTO): Com base no IR dos sócios ANEXADO, avalie o patrimônio segmentando Aplicação/Liquidez e Patrimônio Imobiliário. Identifique dívidas declaradas e conclua sobre a saúde patrimonial.
        2. 'parecer_final' (TEXTO): Gere um parecer formal executivo preenchendo TODOS os campos entre colchetes com dados reais do CONTEXTO e do IR ANEXADO. NÃO deixe colchetes no texto final:

        Trata-se de uma empresa com [calcule: anos desde {_abertura} até hoje] de existência (fundada em {_abertura}). O capital social da empresa é de {_capital}. A empresa apresenta {_risco} no SERASA (Score {_score}). O mesmo cenário se aplica ao sócio, com [status SERASA do sócio extraído de: {_dividas}]. Pretendem alugar conosco imóvel por R$ {_aluguel}. A referência locatícia é positiva, conforme: {_ref_loc}. A série histórica do resultado é {_resultados}. Em relação às informações financeiras, o resultado mais recente é {_ult_resultado} em {_ult_periodo}, com receita bruta de {_ult_receita}, e comprometimento de [calcule: {_aluguel} dividido por {_ult_receita} vezes 100]% da receita bruta. Além disso, a liquidez da CIA é [extraia da análise: {_analise_cont}], com ativo não circulante [valor do balanço] maior que o passivo não circulante, e imobilizado de [valor do balanço]. O sócio possui patrimônio declarado de [valor total do IR ANEXADO], composto por [valor de aplicações financeiras do IR] em aplicações e [imóveis declarados no IR] em imóveis. A relação patrimônio x dívida é [avalie], com dívida declarada de [dívidas do IR]. Dessa forma, [conclua se há ou não objeção para aprovação, justificando tecnicamente].

        Retorne JSON estruturado: {{ "conclusao_socio": "...", "parecer_final": "..." }}."""
        return self._generate_content(prompt, files)


