import streamlit as st
import json
import requests
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
            
            response = requests.post(self.rest_url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                return True
            else:
                st.error(f"Erro na API do Supabase ({response.status_code}): {response.text}")
                return False
        except Exception as e:
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
                return res.json()
            return []
        except:
            return []

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
            return True
        except Exception as e:
            st.error(f"Erro no GSheets: {e}")
            return False
