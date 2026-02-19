"""
Application de Gestion de Flotte - Point d'entrée principal.

Architecture modulaire :
- app.py : Point d'entrée + configuration
- database.py : Connexion Google Sheets + CRUD
- pdf.py : Génération PDF
- styles.py : Thèmes CSS
- alertes.py : Système d'alertes
- pages/ : Modules de pages
"""
import streamlit as st
import streamlit.components.v1 as components

from styles import get_css, THEMES
from alertes import verifier_alertes, verifier_alertes_scooters, verifier_alertes_engins
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

components.html(f"""
<script>
(function() {{
    var doc = window.parent.document;
    var isMobile = window.parent.innerWidth <= 768;
    var sidebarOpen = !isMobile;
    var bgColor = '{t["hamburger_bg"]}';
    var hoverColor = '{t["hamburger_hover"]}';
    var textColor = '{t["h1_color"]}';

    function getSidebarWidth() {{
        if (window.parent.innerWidth <= 480) return Math.min(window.parent.innerWidth * 0.85, 280);
        if (window.parent.innerWidth <= 768) return Math.min(window.parent.innerWidth * 0.85, 300);
        return 300;
    }}

    function setSidebarState(open) {{
        var sidebar = doc.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;
        sidebarOpen = open;
        var w = getSidebarWidth();
        if (open) {{
            sidebar.setAttribute('aria-expanded', 'true');
            sidebar.style.setProperty('transform', 'none', 'important');
            sidebar.style.setProperty('width', w + 'px', 'important');
            sidebar.style.setProperty('min-width', w + 'px', 'important');
            sidebar.style.setProperty('visibility', 'visible', 'important');
            if (isMobile) {{
                sidebar.style.setProperty('position', 'fixed', 'important');
                sidebar.style.setProperty('z-index', '99999', 'important');
                sidebar.style.setProperty('top', '0', 'important');
                sidebar.style.setProperty('left', '0', 'important');
                sidebar.style.setProperty('height', '100vh', 'important');
                sidebar.style.setProperty('box-shadow', '4px 0 20px rgba(0,0,0,0.3)', 'important');
            }} else {{
                sidebar.style.setProperty('position', 'relative', 'important');
                sidebar.style.removeProperty('z-index');
                sidebar.style.removeProperty('box-shadow');
            }}
        }} else {{
            sidebar.setAttribute('aria-expanded', 'false');
            sidebar.style.setProperty('transform', 'translateX(-' + w + 'px)', 'important');
            sidebar.style.setProperty('width', '0px', 'important');
            sidebar.style.setProperty('min-width', '0px', 'important');
            sidebar.style.setProperty('visibility', 'hidden', 'important');
            sidebar.style.setProperty('position', 'fixed', 'important');
        }}
        var btn = doc.getElementById('custom-hamburger');
        if (btn) btn.innerHTML = open ? '&#10005;' : '&#9776;';
    }}

    function createHamburger() {{
        var existing = doc.getElementById('custom-hamburger');
        if (existing) existing.remove();
        var btn = doc.createElement('button');
        btn.id = 'custom-hamburger';
        btn.innerHTML = '&#10005;';
        btn.style.cssText = 'position:fixed;top:14px;left:14px;z-index:999999;background:'+bgColor+';color:'+textColor+';border:1px solid rgba(128,128,128,0.2);border-radius:8px;width:40px;height:40px;font-size:22px;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 10px rgba(0,0,0,0.15);transition:all 0.2s;pointer-events:auto;';
        btn.onmouseover = function() {{ btn.style.background = hoverColor; }};
        btn.onmouseout = function() {{ btn.style.background = bgColor; }};
        btn.onclick = function(e) {{
            e.preventDefault();
            e.stopPropagation();
            setSidebarState(!sidebarOpen);
        }};
        doc.body.appendChild(btn);
    }}

    function init() {{
        createHamburger();
        setSidebarState(true);
    }}

    init();
    setTimeout(init, 300);
    setTimeout(init, 1000);
    setTimeout(init, 2500);
}})();
</script>
""", height=0)

# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def check_password():
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
