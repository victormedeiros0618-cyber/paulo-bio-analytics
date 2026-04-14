import streamlit as st
import json
import requests
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from core.logger import get_logger

logger = get_logger(__name__)


class DBService:
    def __init__(self):
        """
        Substituímos o cliente oficial 'supabase' por chamadas Diretas à API REST (PostgREST).
        Isso resolve o erro de 'ModuleNotFoundError' causado pela falha na instalação 
        das dependências complexas no Python 3.14.
        """
        # Supabase Config
        self.supabase_url = st.secrets["supabase"]["url"]
        self.supabase_key = st.secrets["supabase"]["key"]
        self.rest_url = f"{self.supabase_url}/rest/v1/analises"
        
        # GSheets Config (Legacy)
        self.gs_enabled = "gcp_service_account" in st.secrets

    def salvar_analise(self, dados, decisao):
        """Salva a análise tanto no Supabase quanto no Google Sheets."""
        sucesso_supabase = self._salvar_supabase_rest(dados, decisao)
        sucesso_gsheets = self._salvar_gsheets(dados, decisao) if self.gs_enabled else False
        if sucesso_supabase:
            self._registrar_auditoria(
                acao="ANALISE_CRIADA",
                entidade="Análise",
                entidade_id=dados.get("cnpj") or dados.get("pretendente", ""),
                detalhe=f"Análise criada: {dados.get('empresa', dados.get('pretendente', ''))} — {decisao}",
                meta={"status": decisao, "aluguel": str(dados.get("aluguel", ""))},
            )
        return sucesso_supabase or sucesso_gsheets

    def _salvar_supabase_rest(self, dados, decisao):
        """Implementação manual via API REST para evitar a dependência do pacote 'supabase'."""
        try:
            # Limpeza robusta do R$ e formatação brasileira para float (ex: R$ 20.000,00 -> 20000.0)
            al_raw = str(dados.get("aluguel", "0"))
            al_clean = al_raw.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            try:
                al_float = float(''.join(c for c in al_clean if c.isdigit() or c == '.'))
            except:
                al_float = 0.0

            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            
            payload = {
                "usuario_nome": st.session_state.get("usuario_logado"),
                "usuario_email": st.session_state.get("email_usuario"),
                "empresa": dados.get("empresa", dados.get("pretendente")),
                "cnpj": dados.get("cnpj"),
                "pretendente": dados.get("pretendente"),
                "imovel": dados.get("imovel"),
                "aluguel": al_float,
                "status": decisao,
                "dados": dados
            }
            
            logger.info("Salvando análise no Supabase: empresa=%s status=%s", payload.get("empresa"), decisao)
            response = requests.post(self.rest_url, headers=headers, json=payload)

            if response.status_code in [200, 201]:
                logger.info("Análise salva com sucesso no Supabase.")
                return True
            else:
                logger.error("Erro Supabase (%d): %s", response.status_code, response.text)
                st.error(f"Erro na API do Supabase ({response.status_code}): {response.text}")
                return False
        except Exception as e:
            logger.error("Erro de conexão com Supabase: %s", e)
            st.error(f"Erro de conexão com Supabase: {e}")
            return False

    def listar_analises(self, limite=100):
        """Busca análises do Supabase para o Histórico e Dashboard."""
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            # Ordem desc pela data (created_at)
            url = f"{self.rest_url}?select=*&order=created_at.desc&limit={limite}"
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                dados = res.json()
                logger.info("Listagem Supabase: %d análises retornadas.", len(dados))
                return dados
            logger.warning("Listagem Supabase retornou status %d.", res.status_code)
            return []
        except Exception as e:
            logger.error("Erro ao listar análises do Supabase: %s", e)
            return []

    def excluir_analise(self, analise_id: str) -> bool:
        """Exclui uma análise pelo ID no Supabase."""
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
            }
            url = f"{self.rest_url}?id=eq.{analise_id}"
            res = requests.delete(url, headers=headers)
            if res.status_code in [200, 204]:
                logger.info("Análise %s excluída com sucesso.", analise_id)
                self._registrar_auditoria(
                    acao="ANALISE_EXCLUIDA",
                    entidade="Análise",
                    entidade_id=analise_id,
                    detalhe=f"Análise {analise_id} excluída",
                )
                return True
            logger.error("Erro ao excluir análise %s: %d %s", analise_id, res.status_code, res.text)
            return False
        except Exception as e:
            logger.error("Erro de conexão ao excluir análise: %s", e)
            return False

    def _registrar_auditoria(self, acao: str, entidade: str, entidade_id: str,
                              detalhe: str, meta: dict | None = None) -> None:
        """Grava um evento de auditoria na tabela audit_log do Supabase. Fire-and-forget."""
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            }
            payload = {
                "usuario": st.session_state.get("email_usuario") or st.session_state.get("usuario_logado", "sistema"),
                "acao": acao,
                "entidade": entidade,
                "entidade_id": entidade_id,
                "detalhe": detalhe,
                "meta": json.dumps(meta or {}),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            audit_url = f"{self.supabase_url}/rest/v1/audit_log"
            requests.post(audit_url, headers=headers, json=payload, timeout=5)
            logger.info("Auditoria registrada: %s %s %s", acao, entidade, entidade_id)
        except Exception as e:
            logger.warning("Falha ao registrar auditoria (non-fatal): %s", e)

    def _salvar_gsheets(self, dados, decisao):
        """Lógica legada de salvamento em Google Sheets."""
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
            client = gspread.authorize(creds)
            planilha = client.open("banco_locacao_paulo_bio").sheet1 
            
            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            empresa = dados.get("empresa", dados.get("pretendente", "Não informado"))
            dados_json = json.dumps(dados) 
            
            planilha.append_row([data_atual, empresa, decisao, dados_json, ""])
            logger.info("Análise salva no Google Sheets: empresa=%s", empresa)
            return True
        except Exception as e:
            logger.error("Erro no Google Sheets: %s", e)
            st.error(f"Erro no GSheets: {e}")
            return False
