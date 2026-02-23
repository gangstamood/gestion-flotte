"""
Module pour la sidebar et la navigation de l'application Gestion de Flotte.
"""
import streamlit as st
from styles import THEMES, get_css
from alertes import verifier_alertes, verifier_alertes_scooters, verifier_alertes_engins


def render_sidebar(attributions, attributions_engins, attributions_scooters):
    """
    Affiche la sidebar avec la navigation et les alertes.

    Args:
        attributions: Liste des attributions de véhicules
        attributions_engins: Liste des attributions d'engins
        attributions_scooters: Liste des attributions de scooters

    Returns:
        str: La page actuelle sélectionnée
    """
    t = THEMES[st.session_state['theme']]

    with st.sidebar:
        st.markdown("<div class='sidebar-title'>🚗 Flotte</div>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: {t['intro_color']}; font-size: 0.85rem; margin-bottom: 2rem;'>Gestion de véhicules</p>", unsafe_allow_html=True)

        # Navigation par catégories
        if 'page' not in st.session_state:
            st.session_state.page = "📊 Dashboard"

        def nav_to(p):
            st.session_state.page = p

        vehicule_pages = [
            "➕ Saisir un véhicule",
            "🔧 Attribuer un véhicule",
            "⛽ Bons de Carburant",
            "🔨 Pannes & Interventions"
        ]
        scooter_pages = [
            "🛵 Saisir un scooter",
            "🔧 Attribuer un scooter",
            "🔨 Interventions Scooters"
        ]
        engin_pages = [
            "🚜 Saisir un engin",
            "🔧 Attribuer un engin",
            "🔨 Interventions Engins"
        ]

        # Dashboard
        st.button("📊 Dashboard", key="nav_dashboard", use_container_width=True,
                  type="primary" if st.session_state.page == "📊 Dashboard" else "secondary",
                  on_click=nav_to, args=("📊 Dashboard",))

        # Véhicules
        with st.expander("🚗 Véhicules", expanded=st.session_state.page in vehicule_pages):
            for p in vehicule_pages:
                label = p.split(" ", 1)[1] if " " in p else p
                st.button(label, key=f"nav_{p}", use_container_width=True,
                          type="primary" if st.session_state.page == p else "secondary",
                          on_click=nav_to, args=(p,))

        # Scooters
        with st.expander("🛵 Scooters", expanded=st.session_state.page in scooter_pages):
            for p in scooter_pages:
                label = p.split(" ", 1)[1] if " " in p else p
                st.button(label, key=f"nav_{p}", use_container_width=True,
                          type="primary" if st.session_state.page == p else "secondary",
                          on_click=nav_to, args=(p,))

        # Engins
        with st.expander("🚜 Engins", expanded=st.session_state.page in engin_pages):
            for p in engin_pages:
                label = p.split(" ", 1)[1] if " " in p else p
                st.button(label, key=f"nav_{p}", use_container_width=True,
                          type="primary" if st.session_state.page == p else "secondary",
                          on_click=nav_to, args=(p,))

        # Paramètres
        st.button("⚙️ Paramètres", key="nav_params", use_container_width=True,
                  type="primary" if st.session_state.page == "⚙️ Paramètres" else "secondary",
                  on_click=nav_to, args=("⚙️ Paramètres",))

        page = st.session_state.page

        # ── ALERTES ────────────────────────────────────────────────────────────────
        st.markdown("---")
        alertes = verifier_alertes(attributions)
        if alertes:
            st.markdown(f"<div style='background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 1rem;'><p style='color: #ef4444; font-weight: 600; margin: 0;'>🚨 {len(alertes)} véhicule(s) à retourner bientôt</p></div>", unsafe_allow_html=True)
            with st.expander("Voir les alertes"):
                for a in alertes:
                    if a['jours_restants'] < 0:
                        st.error(f"🔴 {a['immatriculation']} - {a['service']} (en retard de {-a['jours_restants']}j)")
                    elif a['jours_restants'] == 0:
                        st.warning(f"🟠 {a['immatriculation']} - {a['service']} (retour aujourd'hui)")
                    else:
                        st.warning(f"🟡 {a['immatriculation']} - {a['service']} (J-{a['jours_restants']})")

        alertes_engins = verifier_alertes_engins(attributions_engins)
        if alertes_engins:
            st.markdown(f"<div style='background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 10px; padding: 1rem; margin-top: 0.5rem;'><p style='color: #f59e0b; font-weight: 600; margin: 0;'>🚜 {len(alertes_engins)} engin(s) à retourner</p></div>", unsafe_allow_html=True)
            with st.expander("Voir les alertes engins"):
                for a in alertes_engins:
                    if a['jours_retard'] > 0:
                        st.error(f"🔴 {a['numero_serie']} - {a['service']} (retard {a['jours_retard']}j, fin prévue {a['date_fin']})")
                    else:
                        st.warning(f"🟠 {a['numero_serie']} - {a['service']} (fin prévue {a['date_fin']})")

        alertes_scooters = verifier_alertes_scooters(attributions_scooters)
        if alertes_scooters:
            st.markdown(f"<div style='background: rgba(168, 85, 247, 0.1); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 10px; padding: 1rem; margin-top: 0.5rem;'><p style='color: #a855f7; font-weight: 600; margin: 0;'>🛵 {len(alertes_scooters)} scooter(s) à retourner bientôt</p></div>", unsafe_allow_html=True)
            with st.expander("Voir les alertes scooters"):
                for a in alertes_scooters:
                    if a['jours_restants'] < 0:
                        st.error(f"🔴 {a['immatriculation']} - {a['service']} (en retard de {-a['jours_restants']}j)")
                    elif a['jours_restants'] == 0:
                        st.warning(f"🟠 {a['immatriculation']} - {a['service']} (retour aujourd'hui)")
                    else:
                        st.warning(f"🟡 {a['immatriculation']} - {a['service']} (J-{a['jours_restants']})")

        st.markdown("---")
        st.markdown("<div style='background: rgba(16, 185, 129, 0.08); border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem;'><p style='color: #10b981; font-size: 0.8rem; margin: 0;'>🗄️ Base connectée</p></div>", unsafe_allow_html=True)

        return page