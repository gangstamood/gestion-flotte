import hmac
import streamlit as st
from datetime import datetime

MAX_LOGIN_ATTEMPTS = 5
SESSION_TIMEOUT_MINUTES = 60


def check_password(t):
    def password_entered():
        # Rate limiting
        attempts = st.session_state.get("_login_attempts", 0)
        if attempts >= MAX_LOGIN_ATTEMPTS:
            st.session_state["password_correct"] = False
            if "password" in st.session_state:
                del st.session_state["password"]
            return

        if hmac.compare_digest(st.session_state["password"], st.secrets["app_password"]):
            st.session_state["password_correct"] = True
            st.session_state["_login_time"] = datetime.now().isoformat()
            st.session_state["_login_attempts"] = 0
        else:
            st.session_state["password_correct"] = False
            st.session_state["_login_attempts"] = attempts + 1
        del st.session_state["password"]

    def _is_session_expired():
        login_time = st.session_state.get("_login_time")
        if not login_time:
            return True
        try:
            elapsed = (datetime.now() - datetime.fromisoformat(login_time)).total_seconds()
            return elapsed > SESSION_TIMEOUT_MINUTES * 60
        except Exception:
            return True

    def show_login(error=None):
        st.markdown("<div style='max-width: 400px; margin: 15vh auto; text-align: center;'>", unsafe_allow_html=True)
        st.markdown("## 🚗 Gestion de Flotte")
        st.markdown(f"<p style='color: {t['intro_color']}; margin-bottom: 2rem;'>Connectez-vous pour accéder à l'application</p>", unsafe_allow_html=True)

        attempts = st.session_state.get("_login_attempts", 0)
        if attempts >= MAX_LOGIN_ATTEMPTS:
            st.error("🔒 Trop de tentatives. Rechargez la page.")
        else:
            st.text_input("🔒 Mot de passe", type="password", on_change=password_entered, key="password")
            if error:
                st.error(error)
            if attempts > 0:
                st.warning(f"Tentative {attempts}/{MAX_LOGIN_ATTEMPTS}")

        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    # Session timeout check
    if st.session_state.get("password_correct") and _is_session_expired():
        st.session_state["password_correct"] = False
        st.session_state.pop("_login_time", None)

    if "password_correct" not in st.session_state:
        show_login()
    elif not st.session_state["password_correct"]:
        show_login("❌ Mot de passe incorrect")
