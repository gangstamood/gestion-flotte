"""
Module d'authentification pour l'application Gestion de Flotte.
"""
import streamlit as st
from styles import THEMES, get_css


def check_password():
    """
    Vérifie l'authentification de l'utilisateur.
    Affiche le formulaire de login si nécessaire.
    """
    t = THEMES[st.session_state['theme']]

    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    def show_login(error=None):
        st.markdown("<div style='max-width: 400px; margin: 15vh auto; text-align: center;'>", unsafe_allow_html=True)
        st.markdown("## 🚗 Gestion de Flotte")
        st.markdown(f"<p style='color: {t['intro_color']}; margin-bottom: 2rem;'>Connectez-vous pour accéder à l'application</p>", unsafe_allow_html=True)
        st.text_input("🔒 Mot de passe", type="password", on_change=password_entered, key="password")
        if error:
            st.error(error)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    if "password_correct" not in st.session_state:
        show_login()
    elif not st.session_state["password_correct"]:
        show_login("❌ Mot de passe incorrect")