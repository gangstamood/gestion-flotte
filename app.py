"""
Application de Gestion de Flotte - Point d'entrée principal.

Architecture modulaire :
- app.py : Point d'entrée + configuration
- auth.py : Authentification
- hamburger.py : Bouton hamburger JS
- sidebar.py : Navigation + alertes
- database.py : Connexion Google Sheets + CRUD
- pdf.py : Génération PDF
- styles.py : Thèmes CSS
- alertes.py : Système d'alertes
- pages/ : Modules de pages
"""
import streamlit as st

from styles import get_css, THEMES
from auth import check_password
from hamburger import inject_hamburger
from sidebar import render_sidebar
from database import (
    init_database, load_data,
    get_categories, get_services,
    get_categories_engins, get_categories_scooters, _is_engin_active_today
)

# Import des pages
from pages import dashboard, vehicules, scooters, engins, parametres

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DE LA PAGE
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Gestion de Flotte",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
# INITIALISATION DU THÈME
# ═══════════════════════════════════════════════════════════════════════════════

if 'theme' not in st.session_state:
    st.session_state['theme'] = 'Sombre Classique'

t = THEMES[st.session_state['theme']]
st.markdown(get_css(t), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# BOUTON HAMBURGER PERSONNALISÉ
# ═══════════════════════════════════════════════════════════════════════════════

inject_hamburger()

# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

check_password()

# ═══════════════════════════════════════════════════════════════════════════════
# INITIALISATION BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

init_database()

# ═══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DES DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

_all = load_data()

# Extraction des données
vehicules = _all.get('vehicules', [])
attributions = _all.get('attributions', [])
_cats = _all.get('categories', [])
categories = [c.get('nom', '') for c in _cats if c.get('nom')] or get_categories()
_srvs = _all.get('services', [])
services = [s.get('nom', '') for s in _srvs if s.get('nom')] or get_services()
interventions = _all.get('interventions', [])
bons_carburant = _all.get('carburant', [])
engins = _all.get('engins', [])
attributions_engins = _all.get('attributions_engins', [])
_cats_e = _all.get('categories_engins', [])
categories_engins = [c.get('nom', '') for c in _cats_e if c.get('nom')] or get_categories_engins()
interventions_engins = _all.get('interventions_engins', [])
scooters = _all.get('scooters', [])
attributions_scooters = _all.get('attributions_scooters', [])
_cats_s = _all.get('categories_scooters', [])
categories_scooters = [c.get('nom', '') for c in _cats_s if c.get('nom')] or get_categories_scooters()
interventions_scooters = _all.get('interventions_scooters', [])
liens = _all.get('liens', [])

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

page = render_sidebar(attributions, attributions_engins, attributions_scooters)

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTEUR DE PAGES
# ═══════════════════════════════════════════════════════════════════════════════

if page == "📊 Dashboard":
    dashboard.render()

elif page == "➕ Saisir un véhicule":
    vehicules.render_saisir()

elif page == "🔧 Attribuer un véhicule":
    vehicules.render_attribuer()

elif page == "⛽ Bons de Carburant":
    vehicules.render_carburant()

elif page == "🔨 Pannes & Interventions":
    vehicules.render_interventions()

elif page == "🛵 Saisir un scooter":
    scooters.render_saisir()

elif page == "🔧 Attribuer un scooter":
    scooters.render_attribuer()

elif page == "🔨 Interventions Scooters":
    scooters.render_interventions()

elif page == "🚜 Saisir un engin":
    engins.render_saisir()

elif page == "🔧 Attribuer un engin":
    engins.render_attribuer()

elif page == "🔨 Interventions Engins":
    engins.render_interventions()

elif page == "⚙️ Paramètres":
    parametres.render()
