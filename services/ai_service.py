import base64
import streamlit as st
from openai import OpenAI
from utils.formatters import extrair_json_seguro
from core.logger import get_logger
from core.prompt_loader import get_prompt
from core.cache import build_cache_key, get_cached, set_cached

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

    def _cached_generate(self, passo: str, files: list, prompt: str, **cache_kwargs) -> dict:
        """Wrapper com cache: verifica hit antes de chamar a IA."""
        key = build_cache_key(passo, files, **cache_kwargs)
        cached = get_cached(key)
        if cached is not None:
            st.info("♻️ Resultado carregado do cache (mesmo PDF já analisado).")
            return cached
        result = self._generate_content(prompt, files)
        if result:
            set_cached(key, result)
        return result

    def extrair_contrato(self, files):
        prompt = get_prompt("passo_0_contrato")
        return self._cached_generate("passo_0_contrato", files, prompt)

    def extrair_proposta(self, file):
        prompt = get_prompt("passo_1_proposta")
        return self._cached_generate("passo_1_proposta", [file], prompt)

    def analisar_fiador(self, files, aluguel):
        prompt = get_prompt("passo_2_fiador", aluguel=str(aluguel))
        return self._cached_generate("passo_2_fiador", files, prompt, aluguel=str(aluguel))

    def extrair_referencias(self, file):
        prompt = get_prompt("passo_2_referencias")
        return self._cached_generate("passo_2_referencias", [file], prompt)

    def mapear_serasa(self, files, empresa, cnpj):
        prompt = get_prompt("passo_3_serasa", empresa=str(empresa), cnpj=str(cnpj))
        return self._cached_generate("passo_3_serasa", files, prompt, empresa=str(empresa), cnpj=str(cnpj))

    def auditar_certidoes(self, files, empresa, cnpj):
        prompt = get_prompt("passo_4_certidoes", empresa=str(empresa), cnpj=str(cnpj))
        return self._cached_generate("passo_4_certidoes", files, prompt, empresa=str(empresa), cnpj=str(cnpj))

    def auditar_contabil(self, files, empresa, cnpj, aluguel, iptu):
        prompt = get_prompt(
            "passo_5_contabil",
            empresa=str(empresa),
            cnpj=str(cnpj),
            aluguel=str(aluguel),
            iptu=str(iptu),
        )
        return self._cached_generate(
            "passo_5_contabil", files, prompt,
            empresa=str(empresa), cnpj=str(cnpj),
            aluguel=str(aluguel), iptu=str(iptu),
        )

    def analisar_patrimonio_socios(self, files, d):
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

        # Configurações personalizadas do analista (carregadas no login)
        _config = st.session_state.get("config_usuario") or {}
        _nome_empresa = _config.get("nome_empresa") or "Paulo Bio Imóveis"
        _cabecalho = _config.get("cabecalho_laudo", "").strip()
        _cabecalho_instrucao = (
            f"- Cabeçalho personalizado para incluir no início do parecer: {_cabecalho}"
            if _cabecalho else ""
        )

        prompt = get_prompt(
            "passo_6_patrimonio",
            empresa=str(_empresa),
            data_abertura=str(_abertura),
            capital_social=str(_capital),
            aluguel=str(_aluguel),
            ref_locaticias=str(_ref_loc),
            score_serasa=str(_score),
            risco_serasa=str(_risco),
            mapeamento_dividas=str(_dividas),
            periodos=str(_periodos),
            receita_bruta=str(_receitas),
            resultado=str(_resultados),
            analise_executiva=str(_analise_cont),
            ult_resultado=str(_ult_resultado),
            ult_receita=str(_ult_receita),
            ult_periodo=str(_ult_periodo),
            nome_empresa=_nome_empresa,
            cabecalho_instrucao=_cabecalho_instrucao,
        )
        return self._cached_generate(
            "passo_6_patrimonio", files, prompt,
            empresa=str(_empresa), aluguel=str(_aluguel),
            score_serasa=str(_score), ult_periodo=str(_ult_periodo),
        )
