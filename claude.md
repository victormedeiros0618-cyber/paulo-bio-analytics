# Paulo Bio | Analytics

## O que é
Plataforma inteligente de análise de crédito para locação imobiliária. O sistema automatiza a extração de dados de documentos, análise de risco e geração de pareceres técnicos recomendando ou não a locação para a Paulo Bio Imóveis.

## Stack
- Frontend: Streamlit (Python)
- Backend: Python (Streamlit) / Supabase REST API
- Banco de dados: Supabase (PostgreSQL) + Google Sheets (Legacy)
- Autenticação: Streamlit Secrets / Session State
- Deploy: Streamlit Cloud

## Estrutura do projeto
```
/core            → Configurações globais, temas e constantes (config.py)
/services        → Lógica de integração (ai_service.py, db_service.py, pdf_service.py)
/views           → Interface e roteamento de páginas
  /components    → Componentes UI reaproveitáveis (headers, widgets)
  /steps         → Lógica dos 8 passos da análise (0 a 7)
/utils           → Funções utilitárias (formatadores, extratores)
app.py           → Ponto de entrada da aplicação Streamlit
```

## Variáveis de ambiente
- `SUPABASE_URL` — URL do projeto no Supabase
- `SUPABASE_KEY` — Chave de acesso (Anon/Public)
- `GOOGLE_API_KEY` — Chave da API do Google Gemini (IA)
- `GCP_SERVICE_ACCOUNT` — Credenciais para integração com Google Sheets
[Consulte o segredos (.streamlit/secrets.toml) para os valores]

## Convenções de código
- Commits: Conventional Commits (feat:, fix:, docs:, refactor:, chore:)
- Componentes: snake_case para funções de UI (padrão Streamlit)
- Funções/variáveis: snake_case (PEP 8)
- Tratamento: Erros capturados via try/catch com `st.error` para feedback ao usuário
- CSS: Estilos customizados injetados via `st.markdown`, priorizando o design system Paulo Bio (Orange/Dark/Light)

## Fluxo de trabalho
- Branch principal: `main` (produção)
- Branch de desenvolvimento: `develop`
- Features: `feat/nome-da-feature`
- Fixes: `fix/descricao-do-bug`
- Nunca commitar diretamente na `main`

## Regras importantes
- Nunca hardcodar secrets ou API keys (usar `st.secrets`)
- Manter o estado da aplicação no `st.session_state`
- Toda função de processamento de IA deve prever fallback e tratamento de falhas
- Relatórios PDF devem seguir o template oficial da Paulo Bio Imóveis

## Status atual
O projeto está em fase de refinamento da geração de PDFs (Parecer Final - Passo 7) e consolidação da integração com Supabase para o Histórico e Dashboard, garantindo persistência robusta dos dados.

## O que NÃO fazer
- Não usar `any` em tipagens (quando aplicável via annotations)
- Não fazer processamento pesado diretamente na thread principal da UI (usar spinners/cache)
- Não commitar o arquivo `secrets.toml` ou `.env`
