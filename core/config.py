import streamlit as st

# --- CORES OFICIAIS ---
COR_PRIMARIA = "#F47920"     # Laranja Paulo Bio
COR_SECUNDARIA = "#2C3E50"   # Azul Marinho / Chumbo
COR_TERCIARIA = "#7F8C8D"    # Cinza

def aplicar_estilo():
    """Injeta o CSS Neo-Brutalista para visual Premium de Auditoria."""
    st.markdown(
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">',
        unsafe_allow_html=True
    )
    st.markdown(f"""
    <style>
        /* ═══════════════════════════════════════════════════
           FONTES — Space Grotesk (Títulos) + Inter (Corpo)
        ═══════════════════════════════════════════════════ */
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Space Grotesk', sans-serif !important;
            font-weight: 700 !important;
            color: #FFFFFF !important;
            letter-spacing: -0.02em;
        }}

        /* OCULTAÇÃO DO CHROME PADRÃO DO STREAMLIT */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        [data-testid="stHeader"] {{ background-color: transparent !important; }}
        [data-testid="stToolbar"] {{ display: none !important; }}

        /* ═══════════════════════════════════════════════════
           FUNDO PRINCIPAL — Chumbo Escuro sólido
        ═══════════════════════════════════════════════════ */
        .stApp, .main {{ background-color: #0F1923 !important; }}
        .block-container {{
            background-color: #0F1923 !important;
            padding-top: 24px !important;
            max-width: 1280px !important;
        }}

        /* ═══════════════════════════════════════════════════
           SIDEBAR — Chumbo com borda laranja nítida
        ═══════════════════════════════════════════════════ */
        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"] {{
            background-color: #141E2B !important;
        }}
        [data-testid="stSidebar"] {{
            border-right: 3px solid {COR_PRIMARIA} !important;
        }}

        /* TEXTOS GERAIS */
        p, span, label, div {{ color: #C8D6E5 !important; font-weight: 400 !important; }}

        /* ═══════════════════════════════════════════════════
           CARDS — Bordas nítidas (0 arredondamento)
           Sem glassmorphism. Sólidos. Afiados.
        ═══════════════════════════════════════════════════ */
        [data-testid="stVerticalBlockBorderWrapper"] > div {{
            border-radius: 2px !important;
            border: 1px solid rgba(244, 121, 32, 0.25) !important;
            background-color: #1A2636 !important;
            padding: 20px !important;
        }}

        /* ═══════════════════════════════════════════════════
           INPUTS — Fundo claro para contraste com tela escura
        ═══════════════════════════════════════════════════ */
        input, textarea, .stTextInput input, .stTextArea textarea {{
            background-color: #1F2E3F !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(244, 121, 32, 0.4) !important;
            border-radius: 2px !important;
            font-family: 'Inter', sans-serif !important;
        }}
        input:focus, textarea:focus {{
            border-color: {COR_PRIMARIA} !important;
            box-shadow: 0 0 0 4px rgba(244, 121, 32, 0.4) !important;
            outline: none !important;
        }}
        input:focus-visible, textarea:focus-visible {{
            outline: 3px solid {COR_PRIMARIA} !important;
            outline-offset: 2px !important;
        }}

        /* ═══════════════════════════════════════════════════
           BOTÕES — Sharp, laranja, micro-animação
        ═══════════════════════════════════════════════════ */
        /* Botões padrão (área principal) */
        .stButton > button {{
            background-color: {COR_PRIMARIA} !important;
            color: #FFFFFF !important;
            border-radius: 2px !important;
            border: none !important;
            height: 44px !important;
            width: 100% !important;
            font-weight: 700 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 13px !important;
            transition: all 0.15s ease-out !important;
        }}
        .stButton > button:hover {{
            background-color: #FF8C30 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(244, 121, 32, 0.4) !important;
        }}
        .stButton > button:active {{
            transform: translateY(0px) !important;
        }}
        /* Foco visível para acessibilidade WCAG 2.4.7 */
        .stButton > button:focus,
        .stButton > button:focus-visible {{
            outline: 3px solid #FFFFFF !important;
            outline-offset: 2px !important;
            background-color: #FF8C30 !important;
        }}

        /* ═══════════════════════════════════════════════════
           SIDEBAR BUTTONS — Sutil, uniforme (sobrescreve via
           data-testid da sidebar nativa do Streamlit)
        ═══════════════════════════════════════════════════ */
        [data-testid="stSidebar"] .stButton > button {{
            background-color: transparent !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            color: #7F8C8D !important;
            height: 30px !important;
            font-size: 11px !important;
            font-weight: 400 !important;
            font-family: 'Inter', sans-serif !important;
            letter-spacing: 0 !important;
            text-transform: none !important;
            box-shadow: none !important;
            transform: none !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            background-color: rgba(244,121,32,0.08) !important;
            border-color: rgba(244,121,32,0.4) !important;
            color: #F47920 !important;
            transform: none !important;
            box-shadow: none !important;
        }}

        /* ═══════════════════════════════════════════════════
           DANGER BUTTON — Exclusão (borda vermelha)
        ═══════════════════════════════════════════════════ */
        .btn-danger .stButton > button {{
            height: 44px !important;
            background-color: transparent !important;
            border: 1px solid rgba(231,76,60,0.5) !important;
            color: #E74C3C !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            box-shadow: none !important;
            transform: none !important;
        }}
        .btn-danger .stButton > button:hover {{
            background-color: rgba(231,76,60,0.12) !important;
            border-color: #E74C3C !important;
            color: #E74C3C !important;
            transform: none !important;
            box-shadow: none !important;
        }}

        /* ═══════════════════════════════════════════════════
           FILE UPLOADER — Visual expressivo com ícone
        ═══════════════════════════════════════════════════ */
        [data-testid="stFileUploadDropzone"] {{
            background-color: rgba(244, 121, 32, 0.04) !important;
            border: 2px dashed rgba(244, 121, 32, 0.35) !important;
            border-radius: 2px !important;
            transition: all 0.25s ease;
            padding: 24px 16px !important;
            min-height: 100px !important;
            position: relative;
        }}
        [data-testid="stFileUploadDropzone"]:hover {{
            border-color: {COR_PRIMARIA} !important;
            background-color: rgba(244, 121, 32, 0.08) !important;
            box-shadow: 0 0 20px rgba(244,121,32,0.08);
        }}
        /* Ícone decorativo no dropzone via pseudo-element */
        [data-testid="stFileUploadDropzone"]::before {{
            font-family: "bootstrap-icons" !important;
            content: "\\F148" !important;  /* bi-cloud-arrow-up */
            display: block;
            text-align: center;
            font-size: 28px;
            color: rgba(244,121,32,0.5);
            margin-bottom: 4px;
            line-height: 1;
        }}
        [data-testid="stFileUploadDropzone"]:hover::before {{
            color: {COR_PRIMARIA};
        }}
        /* Texto interno mais legível */
        [data-testid="stFileUploadDropzone"] div,
        [data-testid="stFileUploadDropzone"] span,
        [data-testid="stFileUploadDropzone"] small {{
            font-family: 'Inter', sans-serif !important;
            font-size: 12px !important;
        }}

        /* ═══════════════════════════════════════════════════
           DIVIDERS
        ═══════════════════════════════════════════════════ */
        hr {{ border-color: rgba(244, 121, 32, 0.3) !important; }}

        /* ═══════════════════════════════════════════════════
           SELECT / RADIO / CHECKBOX
        ═══════════════════════════════════════════════════ */
        [data-testid="stSelectbox"] div {{
            background-color: #1F2E3F !important;
            border-radius: 2px !important;
            color: #FFFFFF !important;
        }}

        /* ═══════════════════════════════════════════════════
           KPI CARDS — Componente de métricas gigantes
        ═══════════════════════════════════════════════════ */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 2px;
            margin-bottom: 16px;
        }}
        .kpi-card {{
            background-color: #1A2636;
            border-left: 3px solid {COR_PRIMARIA};
            padding: 16px 20px;
            border-radius: 0 2px 2px 0;
        }}
        .kpi-card .kpi-label {{
            font-family: 'Inter', sans-serif;
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: {COR_PRIMARIA} !important;
            margin-bottom: 4px;
        }}
        .kpi-card .kpi-value {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 28px;
            font-weight: 700;
            color: #FFFFFF !important;
            line-height: 1;
        }}
        .kpi-card .kpi-sub {{
            font-size: 11px;
            color: #7F8C8D !important;
            margin-top: 4px;
        }}
        /* variantes de cor */
        .kpi-card.verde  {{ border-left-color: #27AE60; }}
        .kpi-card.verde  .kpi-label {{ color: #27AE60 !important; }}
        .kpi-card.vermelho {{ border-left-color: #E74C3C; }}
        .kpi-card.vermelho .kpi-label {{ color: #E74C3C !important; }}
        .kpi-card.amarelo {{ border-left-color: #F1C40F; }}
        .kpi-card.amarelo .kpi-label {{ color: #F1C40F !important; }}

        /* ═══════════════════════════════════════════════════
           CONTEXT HEADER (Dashboard Head)
        ═══════════════════════════════════════════════════ */
        .ctx-bar {{
            display: flex;
            gap: 24px;
            align-items: center;
            background-color: #141E2B;
            border-bottom: 2px solid {COR_PRIMARIA};
            padding: 10px 24px;
            margin-bottom: 20px;
            border-radius: 2px;
        }}
        .ctx-item {{
            display: flex;
            flex-direction: column;
        }}
        .ctx-label {{
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: {COR_PRIMARIA} !important;
        }}
        .ctx-val {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 14px;
            font-weight: 600;
            color: #FFFFFF !important;
        }}

        /* ═══════════════════════════════════════════════════
           STEPPER (Trilha de Progresso)
        ═══════════════════════════════════════════════════ */
        .stepper {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px 0 24px 0;
            overflow-x: auto;
        }}
        .step-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            min-width: 72px;
        }}
        .step-circle {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            font-size: 13px;
            transition: all 0.3s ease;
        }}
        .step-circle.done {{
            background-color: {COR_PRIMARIA};
            color: #0F1923;
            box-shadow: 0 0 12px rgba(244, 121, 32, 0.5);
        }}
        .step-circle.active {{
            background-color: #0F1923;
            color: {COR_PRIMARIA};
            border: 2px solid {COR_PRIMARIA};
            box-shadow: 0 0 0 3px rgba(244, 121, 32, 0.2);
        }}
        .step-circle.pending {{
            background-color: #1A2636;
            color: #3E5771;
            border: 2px solid #2C3E50;
        }}
        .step-label {{
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}
        .step-label.done   {{ color: {COR_PRIMARIA} !important; }}
        .step-label.active {{ color: #FFFFFF !important; }}
        .step-label.pending {{ color: #3E5771 !important; }}
        .step-connector {{
            flex: 1;
            height: 2px;
            min-width: 20px;
            margin-bottom: 22px;
            transition: background-color 0.3s ease;
        }}
        .step-connector.done    {{ background-color: {COR_PRIMARIA}; }}
        .step-connector.pending {{ background-color: #1A2636; }}

        /* ═══════════════════════════════════════════════════
           VEREDITO CARDS
        ═══════════════════════════════════════════════════ */
        .veredito-card {{
            padding: 20px 24px;
            border-radius: 2px;
            border-left: 6px solid;
            margin-top: 16px;
            display: flex;
            align-items: center;
            gap: 18px;
        }}
        .veredito-card.aprovado {{
            background-color: rgba(39, 174, 96, 0.1);
            border-color: #27AE60;
        }}
        .veredito-card.ressalva {{
            background-color: rgba(241, 196, 15, 0.1);
            border-color: #F1C40F;
        }}
        .veredito-card.reprovado {{
            background-color: rgba(231, 76, 60, 0.1);
            border-color: #E74C3C;
        }}
        .veredito-icon {{
            font-size: 38px;
            line-height: 1;
            flex-shrink: 0;
        }}
        .veredito-card.aprovado .veredito-icon {{ color: #27AE60 !important; }}
        .veredito-card.ressalva .veredito-icon {{ color: #F1C40F !important; }}
        .veredito-card.reprovado .veredito-icon {{ color: #E74C3C !important; }}
        .veredito-body {{
            display: flex;
            flex-direction: column;
        }}
        .veredito-label {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: #FFFFFF !important;
        }}
        .veredito-sub {{
            font-size: 13px;
            color: rgba(200,214,229,0.7) !important;
            margin-top: 4px;
        }}

        /* ═══════════════════════════════════════════════════
           SKELETON LOADERS
        ═══════════════════════════════════════════════════ */
        .skeleton {{
            background: linear-gradient(90deg, #1A2636 25%, #2C3E50 50%, #1A2636 75%);
            background-size: 200% 100%;
            animation: skeleton-shimmer 1.5s infinite;
            border-radius: 2px;
        }}
        @keyframes skeleton-shimmer {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
        .skeleton-text {{ height: 16px; margin-bottom: 8px; }}
        .skeleton-title {{ height: 24px; width: 60%; margin-bottom: 12px; }}
        .skeleton-box {{ height: 120px; }}

        /* ── prefers-reduced-motion ─────────────────────────────────────────── */
        @media (prefers-reduced-motion: reduce) {{
            .skeleton {{
                animation: none !important;
                background: #1A2636 !important;
                opacity: 0.6;
            }}
            .toast {{
                animation: none !important;
                opacity: 1 !important;
                transform: translateX(0) !important;
            }}
            .step-circle, .step-connector {{
                transition: none !important;
            }}
            .stButton > button {{
                transition: none !important;
                transform: none !important;
            }}
            [data-testid="stFileUploadDropzone"] {{
                transition: none !important;
            }}
        }}

        /* ═══════════════════════════════════════════════════
           TOAST NOTIFICATIONS
        ═══════════════════════════════════════════════════ */
        .toast-container {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .toast {{
            padding: 14px 20px;
            border-radius: 2px;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: toast-slide-in 0.3s ease-out;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        @keyframes toast-slide-in {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        .toast.success {{ background-color: #27AE60; color: #FFFFFF; border-left: 4px solid #1E8449; }}
        .toast.error {{ background-color: #E74C3C; color: #FFFFFF; border-left: 4px solid #C0392B; }}
        .toast.info {{ background-color: #3498DB; color: #FFFFFF; border-left: 4px solid #2980B9; }}
        .toast.warning {{ background-color: #F1C40F; color: #0F1923; border-left: 4px solid #D4AC0D; }}

        /* ═══════════════════════════════════════════════════
           TOOLTIPS
        ═══════════════════════════════════════════════════ */
        .tooltip-wrapper {{
            position: relative;
            display: inline-flex;
            align-items: center;
        }}
        .tooltip-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background-color: rgba(244, 121, 32, 0.2);
            color: #F47920;
            font-size: 10px;
            font-weight: 700;
            cursor: help;
            margin-left: 6px;
        }}
        .tooltip-content {{
            visibility: hidden;
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background-color: #1A2636;
            border: 1px solid #F47920;
            padding: 10px 14px;
            border-radius: 2px;
            font-size: 12px;
            color: #C8D6E5;
            width: max-content;
            max-width: 280px;
            z-index: 100;
            opacity: 0;
            transition: opacity 0.2s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }}
        .tooltip-wrapper:hover .tooltip-content {{
            visibility: visible;
            opacity: 1;
        }}

        /* ═══════════════════════════════════════════════════
           EXPANDER / PAINEL DE FILTROS — Visual de painel
        ═══════════════════════════════════════════════════ */
        details[data-testid="stExpander"] {{
            background-color: #1A2636 !important;
            border: 1px solid rgba(244,121,32,0.2) !important;
            border-radius: 2px !important;
            overflow: hidden;
        }}
        details[data-testid="stExpander"] > summary {{
            background-color: #141E2B !important;
            padding: 10px 16px !important;
            border-bottom: 1px solid rgba(244,121,32,0.15) !important;
        }}
        details[data-testid="stExpander"] > summary:hover {{
            background-color: rgba(244,121,32,0.06) !important;
        }}
        details[data-testid="stExpander"] > summary span {{
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
            color: #C8D6E5 !important;
        }}
        details[data-testid="stExpander"] > div {{
            padding: 12px 16px !important;
        }}

        /* ═══════════════════════════════════════════════════
           EMPTY STATES
        ═══════════════════════════════════════════════════ */
        .empty-state {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 48px 24px;
            text-align: center;
        }}
        .empty-state-icon {{
            font-size: 48px;
            color: #3E5771;
            margin-bottom: 16px;
        }}
        .empty-state-title {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 18px;
            font-weight: 600;
            color: #FFFFFF;
            margin-bottom: 8px;
        }}
        .empty-state-desc {{
            font-size: 14px;
            color: #7F8C8D;
            max-width: 320px;
        }}

        /* ═══════════════════════════════════════════════════
           TEMA CLARO
        ═══════════════════════════════════════════════════ */
        /* ═══════════════════════════════════════════════════
           TEMA CLARO — Cobertura completa de todos os componentes
        ═══════════════════════════════════════════════════ */

        /* Fundos base */
        [data-theme="light"] .stApp,
        [data-theme="light"] .main {{ background-color: #F5F6FA !important; }}
        [data-theme="light"] .block-container {{ background-color: #F5F6FA !important; }}

        /* Textos */
        [data-theme="light"] h1, [data-theme="light"] h2,
        [data-theme="light"] h3, [data-theme="light"] h4,
        [data-theme="light"] h5, [data-theme="light"] h6 {{ color: #0F1923 !important; }}
        [data-theme="light"] p, [data-theme="light"] span,
        [data-theme="light"] label, [data-theme="light"] div {{ color: #2C3E50 !important; }}

        /* Sidebar */
        [data-theme="light"] [data-testid="stSidebar"],
        [data-theme="light"] [data-testid="stSidebarContent"] {{
            background-color: #FFFFFF !important;
            border-right: 3px solid {COR_PRIMARIA} !important;
        }}
        [data-theme="light"] [data-testid="stSidebar"] .stButton > button {{
            color: #2C3E50 !important;
            border-color: rgba(244, 121, 32, 0.3) !important;
        }}
        [data-theme="light"] [data-testid="stSidebar"] .stButton > button:hover {{
            background-color: rgba(244, 121, 32, 0.1) !important;
            color: #F47920 !important;
        }}

        /* Cards e containers */
        [data-theme="light"] [data-testid="stVerticalBlockBorderWrapper"] > div {{
            background-color: #FFFFFF !important;
            border-color: rgba(244, 121, 32, 0.2) !important;
        }}

        /* Inputs */
        [data-theme="light"] input, [data-theme="light"] textarea {{
            background-color: #F5F6FA !important;
            color: #0F1923 !important;
            border: 2px solid {COR_PRIMARIA} !important;
            caret-color: {COR_PRIMARIA} !important;
        }}
        [data-theme="light"] input::placeholder, [data-theme="light"] textarea::placeholder {{
            color: #555555 !important;
            opacity: 0.85 !important;
        }}

        /* Selectbox */
        [data-theme="light"] [data-testid="stSelectbox"] div {{
            background-color: #FFFFFF !important;
            color: #0F1923 !important;
        }}

        /* KPI Cards */
        [data-theme="light"] .kpi-card {{
            background-color: #FFFFFF !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }}
        [data-theme="light"] .kpi-card .kpi-value {{ color: #0F1923 !important; }}
        [data-theme="light"] .kpi-card .kpi-sub {{ color: #7F8C8D !important; }}

        /* Context Header */
        [data-theme="light"] .ctx-bar {{
            background-color: #FFFFFF !important;
            border-bottom-color: {COR_PRIMARIA} !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }}
        [data-theme="light"] .ctx-val {{ color: #0F1923 !important; }}
        [data-theme="light"] .ctx-label {{ color: {COR_PRIMARIA} !important; }}

        /* Stepper */
        [data-theme="light"] .step-circle.pending {{
            background-color: #E2E8F0 !important;
            color: #555555 !important;
            border-color: #BDC3CA !important;
        }}
        [data-theme="light"] .step-circle.active {{
            background-color: #FFFFFF !important;
            color: {COR_PRIMARIA} !important;
            border-color: {COR_PRIMARIA} !important;
        }}
        [data-theme="light"] .step-circle.done {{
            background-color: {COR_PRIMARIA} !important;
            color: #FFFFFF !important;
        }}
        [data-theme="light"] .step-label.pending {{ color: #555555 !important; }}
        [data-theme="light"] .step-label.active  {{ color: #0F1923 !important; }}
        [data-theme="light"] .step-label.done    {{ color: {COR_PRIMARIA} !important; }}
        [data-theme="light"] .step-connector.pending {{ background-color: #D1D5DB !important; }}

        /* Veredito Cards */
        [data-theme="light"] .veredito-card.aprovado {{
            background-color: rgba(39,174,96,0.08) !important;
        }}
        [data-theme="light"] .veredito-card.ressalva {{
            background-color: rgba(241,196,15,0.08) !important;
        }}
        [data-theme="light"] .veredito-card.reprovado {{
            background-color: rgba(231,76,60,0.08) !important;
        }}
        [data-theme="light"] .veredito-label {{ color: #0F1923 !important; }}
        [data-theme="light"] .veredito-sub   {{ color: #555555 !important; }}

        /* Empty State */
        [data-theme="light"] .empty-state-icon  {{ color: #7F8C8D !important; }}
        [data-theme="light"] .empty-state-title {{ color: #0F1923 !important; }}
        [data-theme="light"] .empty-state-desc  {{ color: #555555 !important; }}

        /* Expanders */
        [data-theme="light"] details[data-testid="stExpander"] {{
            background-color: #FFFFFF !important;
            border-color: rgba(244,121,32,0.15) !important;
        }}
        [data-theme="light"] details[data-testid="stExpander"] > summary {{
            background-color: #F5F6FA !important;
            border-bottom-color: rgba(244,121,32,0.1) !important;
        }}
        [data-theme="light"] details[data-testid="stExpander"] > summary span {{
            color: #2C3E50 !important;
        }}
        [data-theme="light"] details[data-testid="stExpander"] > summary:hover {{
            background-color: rgba(244,121,32,0.05) !important;
        }}

        /* Tooltips */
        [data-theme="light"] .tooltip-content {{
            background-color: #FFFFFF !important;
            color: #2C3E50 !important;
            border-color: {COR_PRIMARIA} !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}

        /* Dividers */
        [data-theme="light"] hr {{ border-color: rgba(244,121,32,0.2) !important; }}

        /* File uploader dropzone */
        [data-theme="light"] [data-testid="stFileUploadDropzone"] {{
            background-color: rgba(244,121,32,0.03) !important;
            border-color: rgba(244,121,32,0.3) !important;
        }}
        [data-theme="light"] [data-testid="stFileUploadDropzone"] div,
        [data-theme="light"] [data-testid="stFileUploadDropzone"] span,
        [data-theme="light"] [data-testid="stFileUploadDropzone"] small {{
            color: #555555 !important;
        }}
    </style>
    """, unsafe_allow_html=True)
