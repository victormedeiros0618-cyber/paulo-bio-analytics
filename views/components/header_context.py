import streamlit as st

# Ícones Bootstrap por campo
_ICONS = {
    "empresa": "bi-building",
    "cnpj": "bi-upc-scan",
    "aluguel": "bi-cash-coin",
    "score_serasa": "bi-shield-check",
    "risco_serasa": "bi-exclamation-triangle",
}

# Cores de risco para o score
def _risco_cor(risco: str) -> str:
    r = risco.lower()
    if "baixo" in r: return "#27AE60"
    if "medio" in r or "médio" in r: return "#F1C40F"
    if "alto" in r: return "#E74C3C"
    return "#F47920"


def render_dashboard_head():
    """
    Renderiza o cabeçalho de contexto persistente acima dos passos.
    Fica visível a partir do Passo 2 em diante, trazendo as infos-âncora
    do processo sem interferir em nenhuma lógica de extração ou estado.
    """
    d = st.session_state.dados

    empresa = d.get("empresa") or "—"
    cnpj = d.get("cnpj") or "—"
    aluguel = d.get("aluguel") or "—"
    score = d.get("score_serasa") or ""
    risco = d.get("risco_serasa") or ""
    risco_cor = _risco_cor(risco) if risco else "#7F8C8D"

    # Bloco score: só exibe quando já extraído
    score_html = ""
    if score:
        score_html = f"""<div class="ctx-item">
<span class="ctx-label">Score Serasa</span>
<span class="ctx-val" style="color:{risco_cor} !important;">{score}</span>
</div>
<div class="ctx-item">
<span class="ctx-label">Risco</span>
<span class="ctx-val" style="color:{risco_cor} !important;">{risco if risco else "N/A"}</span>
</div>"""

    st.markdown(f"""
<div class="ctx-bar">
<div class="ctx-item">
<span class="ctx-label"><i class="bi bi-building"></i> Empresa</span>
<span class="ctx-val">{empresa}</span>
</div>
<div class="ctx-item">
<span class="ctx-label"><i class="bi bi-upc-scan"></i> CNPJ</span>
<span class="ctx-val">{cnpj}</span>
</div>
<div class="ctx-item">
<span class="ctx-label"><i class="bi bi-cash-coin"></i> Aluguel Alvo</span>
<span class="ctx-val">R$ {aluguel}</span>
</div>
{score_html}
</div>
""", unsafe_allow_html=True)
