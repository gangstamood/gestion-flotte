import streamlit as st
from styles import get_css, THEMES
from auth import check_password
from hamburger import inject_hamburger
from database import (
    init_database, _load_all_sheets,
    get_categories, get_services, get_categories_engins, get_categories_scooters,
    get_fiches_vehicules
)
from sidebar import render_sidebar
from pages.dashboard import render_dashboard
from pages.vehicules import render_vehicules
from pages.scooters import render_scooters
from pages.engins import render_engins
from pages.parametres import render_parametres

st.set_page_config(page_title="Gestion de Flotte", page_icon="🚗", layout="wide", initial_sidebar_state="expanded")

if 'theme' not in st.session_state:
    st.session_state['theme'] = 'Sombre Classique'

t = THEMES[st.session_state['theme']]
st.markdown(get_css(t), unsafe_allow_html=True)

inject_hamburger(t)
check_password(t)

init_database()

# CHARGEMENT DONNÉES (1 seul appel API batchGet)
_all = _load_all_sheets()
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
fiches_vehicules = _all.get('fiches_vehicules', [])

# INITIALISATION SESSION STATE
if 'page' not in st.session_state:
    st.session_state.page = "📊 Dashboard"
if 'dashboard_detail' not in st.session_state:
    st.session_state.dashboard_detail = None
if 'eng_sem_offset' not in st.session_state:
    st.session_state.eng_sem_offset = 0

# SIDEBAR
render_sidebar(t, attributions, attributions_scooters, attributions_engins, services)

# ROUTEUR DE PAGES
page = st.session_state.page

VEHICULE_PAGES = ["➕ Saisir un véhicule", "🔧 Attribuer un véhicule", "⛽ Bons de Carburant", "🔨 Pannes & Interventions", "📋 Fiche véhicule"]
SCOOTER_PAGES = ["🛵 Saisir un scooter", "🔧 Attribuer un scooter", "🔨 Interventions Scooters"]
ENGIN_PAGES = ["🚜 Saisir un engin", "🔧 Attribuer un engin", "🔨 Interventions Engins"]

if page == "📊 Dashboard":
    render_dashboard(t, vehicules, attributions, scooters, attributions_scooters,
                     engins, attributions_engins, interventions, interventions_scooters,
                     interventions_engins, services, liens)
elif page in VEHICULE_PAGES:
    render_vehicules(page, t, vehicules, attributions, categories, services, bons_carburant, interventions, fiches_vehicules)
elif page in SCOOTER_PAGES:
    render_scooters(page, t, scooters, attributions_scooters, categories_scooters, services, interventions_scooters)
elif page in ENGIN_PAGES:
    render_engins(page, t, engins, attributions_engins, categories_engins, services, interventions_engins)
elif page == "⚙️ Paramètres":
    render_parametres(t, categories, services, categories_engins, categories_scooters, liens)
