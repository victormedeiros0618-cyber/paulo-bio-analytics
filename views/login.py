import streamlit as st


def show_login():

    st.markdown("""
    <style>
        /* Remove scroll em todos os contêineres do Streamlit */
        html, body { overflow: hidden !important; }
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        section.main,
        .main .block-container {
            overflow: hidden !important;
            height: 100vh !important;
            padding: 0 !important;
            max-width: 100% !important;
        }

        /* Botão Entrar na cor da marca */
        [data-testid="stForm"] button {
            background-color: #F47920 !important;
            border-color: #F47920 !important;
            color: #0F1923 !important;
            font-weight: 700 !important;
        }
        [data-testid="stForm"] button:hover { background-color: #d96810 !important; }
        [data-testid="stForm"] small { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # Padding topo para posicionar verticalmente sem scroll
    st.markdown('<div style="height:6vh"></div>', unsafe_allow_html=True)

    _, col_c, _ = st.columns([1, 1.2, 1])
    with col_c:
        # Logo centralizada
        _, col_logo, _ = st.columns([1, 1, 1])
        with col_logo:
            st.image("logoOPB.png", use_container_width=True)

        st.markdown("""
        <h3 style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                   text-align:center; margin:16px 0 4px; color:#FFFFFF;">
            Acesso ao Sistema
        </h3>
        <p style="text-align:center; color:#7F8C8D; margin-bottom:20px; font-size:13px;">
            Paulo Bio Imóveis — uso interno
        </p>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            with st.form("form_login"):
                usuario = st.text_input("Usuário", placeholder="seu.usuario")
                senha = st.text_input("Senha", type="password", placeholder="••••••••")
                st.write("")
                submitted = st.form_submit_button(
                    "Entrar", type="primary", use_container_width=True
                )
                if submitted:
                    _autenticar(usuario.strip(), senha)

        st.markdown(
            '<p style="text-align:center; color:#7F8C8D; font-size:11px; margin-top:12px;">'
            'Plataforma de uso interno — Paulo Bio Imóveis</p>',
            unsafe_allow_html=True
        )


def _autenticar(usuario: str, senha: str):
    senhas = st.secrets.get("passwords", {})
    nomes = st.secrets.get("usuarios_nomes", {})
    emails = st.secrets.get("usuarios_emails", {})

    if not usuario:
        st.error("Informe o usuário.")
        return

    senha_correta = senhas.get(usuario)
    if senha_correta is None:
        st.error("Usuário não encontrado.")
        return

    if senha != senha_correta:
        st.error("Senha incorreta.")
        return

    st.session_state.logged_in = True
    st.session_state.usuario_logado = nomes.get(usuario, usuario)
    st.session_state.email_usuario = emails.get(usuario, "")
    st.rerun()
