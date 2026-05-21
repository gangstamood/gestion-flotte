import streamlit as st
from styles import get_css, THEMES
from auth import check_password
from hamburger import inject_hamburger
from database import (
    init_database, _load_all_sheets,
    get_categories, get_services, get_categories_engins, get_categories_scooters,
    get_categories_golfettes, get_fiches_vehicules
)
from sidebar import render_sidebar
from pages.dashboard import render_dashboard
from pages.vehicules import render_vehicules
from pages.scooters import render_scooters
from pages.engins import render_engins
from pages.golfettes import render_golfettes
from pages.parametres import render_parametres
from pages.distribution_clefs import render_distribution_clefs
from pages.planning_wlg import render_planning_wlg
from pages.planning_golfettes_wlg import render_planning_golfettes_wlg
from pages.interventions_wlg import render_interventions_wlg

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
golfettes = _all.get('golfettes', [])
attributions_golfettes = _all.get('attributions_golfettes', [])
_cats_g = _all.get('categories_golfettes', [])
categories_golfettes = [c.get('nom', '') for c in _cats_g if c.get('nom')] or get_categories_golfettes()
interventions_golfettes = _all.get('interventions_golfettes', [])

# INITIALISATION SESSION STATE
if 'page' not in st.session_state:
    st.session_state.page = "📊 Dashboard"
if 'dashboard_detail' not in st.session_state:
    st.session_state.dashboard_detail = None
if 'eng_sem_offset' not in st.session_state:
    st.session_state.eng_sem_offset = 0
if 'wlg_sem_offset' not in st.session_state:
    st.session_state.wlg_sem_offset = 0
if 'wlg_golf_sem_offset' not in st.session_state:
    st.session_state.wlg_golf_sem_offset = 0
if 'golf_sem_offset' not in st.session_state:
    st.session_state.golf_sem_offset = 0
if '_fk' not in st.session_state:
    st.session_state['_fk'] = 0

# SIDEBAR
render_sidebar(t, attributions, attributions_scooters, attributions_engins, services, attributions_golfettes)

# ROUTEUR DE PAGES
page = st.session_state.page

VEHICULE_PAGES = ["➕ Saisir un véhicule", "🔧 Attribuer un véhicule", "⛽ Bons de Carburant", "🔨 Pannes & Interventions", "📋 Fiche véhicule"]
SCOOTER_PAGES = ["🛵 Saisir un scooter", "🔧 Attribuer un scooter", "🔨 Interventions Scooters"]
ENGIN_PAGES = ["📊 Vue Engins", "🚜 Saisir un engin", "🔧 Attribuer un engin", "🔨 Interventions Engins"]
GOLFETTE_PAGES = ["📊 Vue Golfettes", "⛳ Saisir une golfette", "🔧 Attribuer une golfette", "🔨 Interventions Golfettes"]

if page == "📊 Dashboard":
    render_dashboard(t, vehicules, attributions, scooters, attributions_scooters,
                     engins, attributions_engins, interventions, interventions_scooters,
                     interventions_engins, services, liens,
                     golfettes, attributions_golfettes, interventions_golfettes)
elif page == "🔑 Distribution Clés":
    render_distribution_clefs(t, engins, vehicules, scooters, golfettes)
elif page in ("🎪 Planning WLG", "🎪 Planning Engins WLG"):
    render_planning_wlg(t, engins, attributions_engins)
elif page == "⛳ Planning Golfettes WLG":
    render_planning_golfettes_wlg(t, golfettes, attributions_golfettes)
elif page == "🔨 Interventions WLG":
    render_interventions_wlg(t, engins, golfettes, interventions_engins, interventions_golfettes)
elif page in VEHICULE_PAGES:
    render_vehicules(page, t, vehicules, attributions, categories, services, bons_carburant, interventions, fiches_vehicules)
elif page in SCOOTER_PAGES:
    render_scooters(page, t, scooters, attributions_scooters, categories_scooters, services, interventions_scooters)
elif page in ENGIN_PAGES:
    render_engins(page, t, engins, attributions_engins, categories_engins, services, interventions_engins)
elif page in GOLFETTE_PAGES:
    render_golfettes(page, t, golfettes, attributions_golfettes, categories_golfettes, services, interventions_golfettes)
elif page == "⚙️ Paramètres":
    render_parametres(t, categories, services, categories_engins, categories_scooters, categories_golfettes, liens)
