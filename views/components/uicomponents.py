import streamlit as st

def show_toast(message: str, type: str = "info"):
    """
    Exibe toast notification inline (Streamlit native).
    types: success, error, info, warning
    """
    if type == "success":
        st.success(message)
    elif type == "error":
        st.error(message)
    elif type == "warning":
        st.warning(message)
    else:
        st.info(message)

def empty_state(icon: str, title: str, description: str):
    """Renderiza empty state com ícone, título e descrição."""
    st.markdown(f'''
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-desc">{description}</div>
    </div>
    ''', unsafe_allow_html=True)