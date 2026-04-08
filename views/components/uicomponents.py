import streamlit as st
import time

def render_skeleton():
    """Renderiza skeleton loader CSS/HTML para estados de loading."""
    st.markdown("""
    <div class="skeleton-wrapper">
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-text" style="width: 80%;"></div>
        <div class="skeleton skeleton-text" style="width: 60%;"></div>
        <div class="skeleton skeleton-box" style="margin-top: 16px;"></div>
    </div>
    """, unsafe_allow_html=True)

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

def tooltip(label: str, help_text: str) -> str:
    """Retorna HTML com tooltip para labels."""
    return f'''
    <span class="tooltip-wrapper">
        {label}
        <span class="tooltip-icon">?</span>
        <span class="tooltip-content">{help_text}</span>
    </span>
    '''

def empty_state(icon: str, title: str, description: str):
    """Renderiza empty state com ícone, título e descrição."""
    st.markdown(f'''
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-desc">{description}</div>
    </div>
    ''', unsafe_allow_html=True)