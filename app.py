import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import streamlit.components.v1 as components
from styles import get_css, THEMES
from alertes import verifier_alertes, verifier_alertes_scooters, verifier_alertes_engins

st.set_page_config(page_title="Gestion de Flotte", page_icon="🚗", layout="wide", initial_sidebar_state="expanded")

if 'theme' not in st.session_state:
    st.session_state['theme'] = 'Sombre Classique'

t = THEMES[st.session_state['theme']]

st.markdown(get_css(t), unsafe_allow_html=True)

# Bouton hamburger personnalisé + toggle sidebar via manipulation CSS directe
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

# AUTHENTIFICATION PAR MOT DE PASSE
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

# CONNEXION GOOGLE SHEETS
@st.cache_resource
def get_sheets_service():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build('sheets', 'v4', credentials=credentials)

SPREADSHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
sheets_service = get_sheets_service()

def read_sheet(sheet_name):
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:Z"
        ).execute()
        values = result.get('values', [])
        if not values or len(values) < 2:
            return []
        headers = values[0]
        return [dict(zip(headers, row + [''] * (len(headers) - len(row)))) for row in values[1:]]
    except Exception:
        return []

def write_sheet(sheet_name, data):
    sheets_service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:Z"
    ).execute()
    if not data:
        _load_all_sheets.clear()
        return
    headers = list(data[0].keys())
    values = [headers] + [[row.get(h, '') for h in headers] for row in data]
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A1",
        valueInputOption="RAW", body={"values": values}
    ).execute()
    _load_all_sheets.clear()

@st.cache_resource
def init_database():
    try:
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        existing_sheets = [s['properties']['title'] for s in sheet_metadata['sheets']]
        required_sheets = ['vehicules', 'attributions', 'categories', 'services', 'interventions', 'carburant', 'engins', 'attributions_engins', 'categories_engins', 'interventions_engins', 'scooters', 'attributions_scooters', 'categories_scooters', 'interventions_scooters', 'liens']
        for sheet_name in required_sheets:
            if sheet_name not in existing_sheets:
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
                ).execute()
    except Exception:
        pass

init_database()

# CHARGEMENT BATCH AVEC CACHE
ALL_SHEET_NAMES = [
    'vehicules', 'attributions', 'categories', 'services', 'interventions',
    'carburant', 'engins', 'attributions_engins', 'categories_engins',
    'interventions_engins', 'scooters', 'attributions_scooters',
    'categories_scooters', 'interventions_scooters', 'liens'
]

@st.cache_data(ttl=60, show_spinner="Chargement des données...")
def _load_all_sheets():
    ranges = [f"{name}!A:Z" for name in ALL_SHEET_NAMES]
    try:
        result = sheets_service.spreadsheets().values().batchGet(
            spreadsheetId=SPREADSHEET_ID, ranges=ranges
        ).execute()
        data = {}
        for i, vr in enumerate(result.get('valueRanges', [])):
            values = vr.get('values', [])
            if not values or len(values) < 2:
                data[ALL_SHEET_NAMES[i]] = []
            else:
                headers = values[0]
                data[ALL_SHEET_NAMES[i]] = [dict(zip(headers, row + [''] * (len(headers) - len(row)))) for row in values[1:]]
        return data
    except Exception:
        return {name: [] for name in ALL_SHEET_NAMES}

# FONCTIONS CRUD
def get_vehicules():
    return read_sheet('vehicules')

def add_vehicule(immat, type_v, marque):
    vehicules = get_vehicules()
    if not any(v.get('immatriculation') == immat for v in vehicules):
        vehicules.append({'immatriculation': immat, 'type': type_v, 'marque': marque})
        write_sheet('vehicules', vehicules)

def delete_vehicule(immat):
    vehicules = [v for v in get_vehicules() if v.get('immatriculation') != immat]
    write_sheet('vehicules', vehicules)

def get_attributions():
    return read_sheet('attributions')

def add_attribution(immat, service, date, heure, date_retour_prevue):
    attributions = get_attributions()
    attributions.append({'immatriculation': immat, 'service': service, 'date': date, 'heure': heure, 'date_retour_prevue': date_retour_prevue, 'retourne': ''})
    write_sheet('attributions', attributions)

def retourner_vehicule(immat):
    attributions = get_attributions()
    for attr in reversed(attributions):
        if attr.get('immatriculation') == immat and not attr.get('retourne'):
            attr['retourne'] = datetime.now().strftime("%d/%m/%Y %H:%M")
            break
    write_sheet('attributions', attributions)

def update_attribution(idx, data):
    attributions = get_attributions()
    if 0 <= idx < len(attributions):
        attributions[idx].update(data)
        write_sheet('attributions', attributions)

def delete_attribution(idx):
    attributions = get_attributions()
    if 0 <= idx < len(attributions):
        attributions.pop(idx)
        write_sheet('attributions', attributions)

def get_categories():
    cats = read_sheet('categories')
    if not cats:
        defaults = [{'nom': c} for c in ["Camion", "Fourgon", "Tractopelle", "Tondeuse", "Utilitaire", "Autre"]]
        write_sheet('categories', defaults)
        return ["Camion", "Fourgon", "Tractopelle", "Tondeuse", "Utilitaire", "Autre"]
    return [c.get('nom', '') for c in cats if c.get('nom')]

def add_category(nom):
    cats = get_categories()
    if nom not in cats:
        write_sheet('categories', [{'nom': c} for c in cats + [nom]])

def delete_category(nom):
    write_sheet('categories', [{'nom': c} for c in get_categories() if c != nom])

def get_services():
    srvs = read_sheet('services')
    if not srvs:
        defaults = [{'nom': s} for s in ["Voirie", "Bâtiment", "Espaces verts"]]
        write_sheet('services', defaults)
        return ["Voirie", "Bâtiment", "Espaces verts"]
    return [s.get('nom', '') for s in srvs if s.get('nom')]

def add_service(nom):
    srvs = get_services()
    if nom not in srvs:
        write_sheet('services', [{'nom': s} for s in srvs + [nom]])

def delete_service(nom):
    write_sheet('services', [{'nom': s} for s in get_services() if s != nom])

def get_interventions():
    return read_sheet('interventions')

def add_intervention(immat, type_i, date, heure, comm, statut):
    interventions = get_interventions()
    interventions.append({'immatriculation': immat, 'type': type_i, 'date': date, 'heure': heure, 'commentaire': comm, 'statut': statut})
    write_sheet('interventions', interventions)

def get_carburant():
    return read_sheet('carburant')

def add_bon_carburant(bon):
    bons = get_carburant()
    bons.append(bon)
    write_sheet('carburant', bons)

def update_bon_carburant(numero_bon, type_carb, volume, montant):
    bons = get_carburant()
    for bon in bons:
        if bon.get('numero_bon') == numero_bon:
            bon['type_carburant'] = type_carb
            bon['volume'] = str(volume)
            bon['montant'] = str(montant)
            bon['statut'] = 'Saisi'
    write_sheet('carburant', bons)

def delete_bon_carburant(numero_bon):
    bons = [b for b in get_carburant() if b.get('numero_bon') != numero_bon]
    write_sheet('carburant', bons)

# FONCTIONS CRUD LIENS
def get_liens():
    return read_sheet('liens')

def add_lien(nom, url):
    liens = get_liens()
    if not any(l.get('nom') == nom for l in liens):
        liens.append({'nom': nom, 'url': url})
        write_sheet('liens', liens)

def delete_lien(nom):
    liens = [l for l in get_liens() if l.get('nom') != nom]
    write_sheet('liens', liens)

# FONCTIONS CRUD ENGINS
def get_engins():
    return read_sheet('engins')

def add_engin(num_serie, type_e, marque):
    engins = get_engins()
    if not any(e.get('numero_serie') == num_serie for e in engins):
        engins.append({'numero_serie': num_serie, 'type': type_e, 'marque': marque})
        write_sheet('engins', engins)

def delete_engin(num_serie):
    engins = [e for e in get_engins() if e.get('numero_serie') != num_serie]
    write_sheet('engins', engins)

def get_attributions_engins():
    return read_sheet('attributions_engins')

def _is_engin_active_today(attr):
    """Retourne True si l'attribution couvre aujourd'hui (date_debut <= today <= date_fin)."""
    if attr.get('retourne'):
        return False
    try:
        today = datetime.now().date()
        date_debut = datetime.strptime(attr['date'], "%d/%m/%Y").date()
        date_fin = datetime.strptime(attr.get('date_fin', attr['date']), "%d/%m/%Y").date()
        return date_debut <= today <= date_fin
    except Exception:
        return not attr.get('retourne')

def add_attribution_engin(num_serie, service, date_debut, date_fin, periode):
    attributions = get_attributions_engins()
    attributions.append({'numero_serie': num_serie, 'service': service, 'date': date_debut, 'date_fin': date_fin, 'periode': periode, 'retourne': ''})
    write_sheet('attributions_engins', attributions)

def retourner_engin(num_serie):
    attributions = get_attributions_engins()
    for attr in reversed(attributions):
        if attr.get('numero_serie') == num_serie and not attr.get('retourne'):
            attr['retourne'] = datetime.now().strftime("%d/%m/%Y %H:%M")
            break
    write_sheet('attributions_engins', attributions)

def update_attribution_engin(idx, data):
    attributions = get_attributions_engins()
    if 0 <= idx < len(attributions):
        attributions[idx].update(data)
        write_sheet('attributions_engins', attributions)

def delete_attribution_engin(idx):
    attributions = get_attributions_engins()
    if 0 <= idx < len(attributions):
        attributions.pop(idx)
        write_sheet('attributions_engins', attributions)

def get_categories_engins():
    cats = read_sheet('categories_engins')
    if not cats:
        defaults = [{'nom': c} for c in ["Tractopelle", "Tondeuse", "Compacteur", "Nacelle", "Mini-pelle", "Autre"]]
        write_sheet('categories_engins', defaults)
        return ["Tractopelle", "Tondeuse", "Compacteur", "Nacelle", "Mini-pelle", "Autre"]
    return [c.get('nom', '') for c in cats if c.get('nom')]

def add_category_engin(nom):
    cats = get_categories_engins()
    if nom not in cats:
        write_sheet('categories_engins', [{'nom': c} for c in cats + [nom]])

def delete_category_engin(nom):
    write_sheet('categories_engins', [{'nom': c} for c in get_categories_engins() if c != nom])

def get_interventions_engins():
    return read_sheet('interventions_engins')

def add_intervention_engin(num_serie, type_i, date, heure, comm, statut):
    interventions = get_interventions_engins()
    interventions.append({'numero_serie': num_serie, 'type': type_i, 'date': date, 'heure': heure, 'commentaire': comm, 'statut': statut})
    write_sheet('interventions_engins', interventions)

# FONCTIONS CRUD SCOOTERS
def get_scooters():
    return read_sheet('scooters')

def add_scooter(immat, type_s, marque):
    scooters = get_scooters()
    if not any(s.get('immatriculation') == immat for s in scooters):
        scooters.append({'immatriculation': immat, 'type': type_s, 'marque': marque})
        write_sheet('scooters', scooters)

def delete_scooter(immat):
    scooters = [s for s in get_scooters() if s.get('immatriculation') != immat]
    write_sheet('scooters', scooters)

def get_attributions_scooters():
    return read_sheet('attributions_scooters')

def add_attribution_scooter(immat, service, date, heure, date_retour_prevue, casque=""):
    attributions = get_attributions_scooters()
    attributions.append({'immatriculation': immat, 'service': service, 'date': date, 'heure': heure, 'date_retour_prevue': date_retour_prevue, 'casque': casque, 'retourne': ''})
    write_sheet('attributions_scooters', attributions)

def retourner_scooter(immat):
    attributions = get_attributions_scooters()
    for attr in reversed(attributions):
        if attr.get('immatriculation') == immat and not attr.get('retourne'):
            attr['retourne'] = datetime.now().strftime("%d/%m/%Y %H:%M")
            break
    write_sheet('attributions_scooters', attributions)

def update_attribution_scooter(idx, data):
    attributions = get_attributions_scooters()
    if 0 <= idx < len(attributions):
        attributions[idx].update(data)
        write_sheet('attributions_scooters', attributions)

def delete_attribution_scooter(idx):
    attributions = get_attributions_scooters()
    if 0 <= idx < len(attributions):
        attributions.pop(idx)
        write_sheet('attributions_scooters', attributions)

def get_categories_scooters():
    cats = read_sheet('categories_scooters')
    if not cats:
        defaults = [{'nom': c} for c in ["50cc", "125cc", "Électrique", "Autre"]]
        write_sheet('categories_scooters', defaults)
        return ["50cc", "125cc", "Électrique", "Autre"]
    return [c.get('nom', '') for c in cats if c.get('nom')]

def add_category_scooter(nom):
    cats = get_categories_scooters()
    if nom not in cats:
        write_sheet('categories_scooters', [{'nom': c} for c in cats + [nom]])

def delete_category_scooter(nom):
    write_sheet('categories_scooters', [{'nom': c} for c in get_categories_scooters() if c != nom])

def get_interventions_scooters():
    return read_sheet('interventions_scooters')

def add_intervention_scooter(immat, type_i, date, heure, comm, statut):
    interventions = get_interventions_scooters()
    interventions.append({'immatriculation': immat, 'type': type_i, 'date': date, 'heure': heure, 'commentaire': comm, 'statut': statut})
    write_sheet('interventions_scooters', interventions)

def generer_pdf_bon(bon, conducteur_nom, conducteur_prenom, logo_url=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    if logo_url:
        try:
            c.drawImage(logo_url, 50, height - 100, width=100, height=80, preserveAspectRatio=True)
        except Exception:
            pass
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 120, "BON DE CARBURANT")
    c.line(50, height - 140, width - 50, height - 140)
    c.setFont("Helvetica-Bold", 12)
    y = height - 180
    c.drawString(80, y, f"N° de Bon : {bon['numero_bon']}")
    y -= 30
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.8, 0.2, 0.2)
    c.drawString(80, y, f"Carte N°{bon['numero_carte']}")
    c.setFillColorRGB(0, 0, 0)
    y -= 40
    c.setFont("Helvetica", 12)
    c.drawString(80, y, f"Vehicule : {bon['immatriculation']}")
    y -= 25
    c.drawString(80, y, f"Service : {bon['service']}")
    y -= 25
    c.drawString(80, y, f"Date : {bon['date']}")
    y -= 25
    c.drawString(80, y, f"Conducteur : {conducteur_prenom} {conducteur_nom}")
    if bon.get('notes'):
        y -= 25
        c.drawString(80, y, f"Notes : {bon['notes']}")
    y -= 30
    c.line(50, y, width - 50, y)
    y -= 40
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawCentredString(width/2, y, "Volume, type de carburant et montant a saisir au retour")
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 50, "Document genere automatiquement - Gestion de Flotte")
    c.save()
    buffer.seek(0)
    return buffer

# CHARGEMENT DONNÉES (1 seul appel API au lieu de 14)
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

# SIDEBAR
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
        "🔧 Attribuer un véhicule", "⛽ Bons de Carburant",
        "🔨 Pannes & Interventions"
    ]
    scooter_pages = [
        "🛵 Saisir un scooter", "🔧 Attribuer un scooter",
        "🔨 Interventions Scooters"
    ]
    engin_pages = [
        "🚜 Saisir un engin", "🔧 Attribuer un engin",
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

# PAGES
if page == "📊 Dashboard":
    st.markdown("# 📊 Tableau de Bord")
    st.markdown("<p class='page-intro'>Vue d'ensemble de votre flotte</p>", unsafe_allow_html=True)

    if liens:
        st.markdown("### 📎 Tableaux de bord")
        cols = st.columns(min(len(liens), 4))
        for i, lien in enumerate(liens):
            with cols[i % 4]:
                st.link_button(f"📄 {lien.get('nom', '')}", lien.get('url', ''), use_container_width=True)
        st.markdown("---")

    # Calculs pour les métriques
    nb_vehicules = len(vehicules)
    sorties_en_cours = [a for a in attributions if not a.get('retourne')]
    nb_en_sortie = len(sorties_en_cours)
    nb_scooters = len(scooters)
    nb_engins = len(engins)
    interventions_en_cours_v = [i for i in interventions if i.get('statut') == "En cours"]
    interventions_en_cours_e = [i for i in interventions_engins if i.get('statut') == "En cours"]
    interventions_en_cours_s = [i for i in interventions_scooters if i.get('statut') == "En cours"]
    nb_interventions = len(interventions_en_cours_v) + len(interventions_en_cours_e) + len(interventions_en_cours_s)

    # Lookups O(1) pour éviter les recherches linéaires répétées
    vh_map = {v['immatriculation']: v for v in vehicules}
    sco_map = {s['immatriculation']: s for s in scooters}
    eng_map = {e['numero_serie']: e for e in engins}
    sorties_set_vh = {a['immatriculation'] for a in attributions if not a.get('retourne')}
    sorties_set_sco = {a['immatriculation'] for a in attributions_scooters if not a.get('retourne')}
    sorties_set_eng = {a['numero_serie'] for a in attributions_engins if _is_engin_active_today(a)}
    interv_set_vh = {i['immatriculation'] for i in interventions if i.get('statut') == "En cours"}
    interv_set_sco = {i['immatriculation'] for i in interventions_scooters if i.get('statut') == "En cours"}
    interv_set_eng = {i['numero_serie'] for i in interventions_engins if i.get('statut') == "En cours"}

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🚙 Véhicules", nb_vehicules)
        if st.button("📋 Détails", key="btn_vehicules", use_container_width=True):
            st.session_state['dashboard_detail'] = 'vehicules' if st.session_state.get('dashboard_detail') != 'vehicules' else None
    with col2:
        st.metric("🔑 Distribué", nb_en_sortie)
        if st.button("📋 Détails", key="btn_en_sortie", use_container_width=True):
            st.session_state['dashboard_detail'] = 'en_sortie' if st.session_state.get('dashboard_detail') != 'en_sortie' else None
    with col3:
        st.metric("🛵 Scooters", nb_scooters)
        if st.button("📋 Détails", key="btn_scooters", use_container_width=True):
            st.session_state['dashboard_detail'] = 'scooters' if st.session_state.get('dashboard_detail') != 'scooters' else None
    with col4:
        st.metric("🚜 Engins", nb_engins)
        if st.button("📋 Détails", key="btn_engins", use_container_width=True):
            st.session_state['dashboard_detail'] = 'engins' if st.session_state.get('dashboard_detail') != 'engins' else None
    with col5:
        st.metric("🔨 Interventions", nb_interventions)
        if st.button("📋 Détails", key="btn_interventions", use_container_width=True):
            st.session_state['dashboard_detail'] = 'interventions' if st.session_state.get('dashboard_detail') != 'interventions' else None

    # Affichage des détails selon le bouton cliqué
    detail = st.session_state.get('dashboard_detail')

    if detail == 'vehicules':
        st.markdown("---")
        st.markdown("### 🚙 Détail des Véhicules")
        if vehicules:
            for v in vehicules:
                immat = v.get('immatriculation', '')
                # Statut : distribué ou disponible
                en_sortie = immat in sorties_set_vh
                en_interv = immat in interv_set_vh
                if en_interv:
                    statut = "🔧 En intervention"
                    couleur = "#f59e0b"
                elif en_sortie:
                    statut = "🔑 Distribué"
                    couleur = "#ef4444"
                else:
                    statut = "✅ Disponible"
                    couleur = "#10b981"
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid {couleur};border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;font-size:1rem;'>{immat}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{v.get('marque','')} — {v.get('type','')}</span>
                    <br/><span style='color:{couleur};font-weight:500;font-size:0.9rem;'>{statut}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aucun véhicule enregistré")

    elif detail == 'en_sortie':
        st.markdown("---")
        st.markdown("### 🔑 Véhicules distribués")
        if sorties_en_cours:
            for a in sorties_en_cours:
                immat = a.get('immatriculation', '')
                info_v = vh_map.get(immat, {})
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid #ef4444;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;'>{immat}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{info_v.get('marque','')} — {info_v.get('type','')}</span><br/>
                    <span style='color:{t['text_color']};font-size:0.85rem;'>📅 Sorti le {a.get('date','')} à {a.get('heure','')}</span>
                    <span style='color:{t['text_color']};font-size:0.85rem;margin-left:1rem;'>🏢 Service : {a.get('service','')}</span>
                    <span style='color:{t['text_color']};font-size:0.85rem;margin-left:1rem;'>📆 Retour prévu : {a.get('date_retour_prevue','N/A')}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aucun véhicule distribué actuellement")

    elif detail == 'engins':
        st.markdown("---")
        st.markdown("### 🚜 Détail des Engins")
        if engins:
            for e in engins:
                num = e.get('numero_serie', '')
                en_sortie = num in sorties_set_eng
                en_interv = num in interv_set_eng
                if en_interv:
                    statut = "🔧 En intervention"
                    couleur = "#f59e0b"
                elif en_sortie:
                    statut = "🔑 Distribué"
                    couleur = "#ef4444"
                else:
                    statut = "✅ Disponible"
                    couleur = "#10b981"
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid {couleur};border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;font-size:1rem;'>{num}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{e.get('marque','')} — {e.get('type','')}</span>
                    <br/><span style='color:{couleur};font-weight:500;font-size:0.9rem;'>{statut}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aucun engin enregistré")

    elif detail == 'scooters':
        st.markdown("---")
        st.markdown("### 🛵 Détail des Scooters")
        if scooters:
            for s in scooters:
                immat = s.get('immatriculation', '')
                en_sortie = immat in sorties_set_sco
                en_interv = immat in interv_set_sco
                if en_interv:
                    statut = "🔧 En intervention"
                    couleur = "#f59e0b"
                elif en_sortie:
                    statut = "🔑 Distribué"
                    couleur = "#ef4444"
                else:
                    statut = "✅ Disponible"
                    couleur = "#10b981"
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid {couleur};border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;font-size:1rem;'>{immat}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{s.get('marque','')} — {s.get('type','')}</span>
                    <br/><span style='color:{couleur};font-weight:500;font-size:0.9rem;'>{statut}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aucun scooter enregistré")

    elif detail == 'interventions':
        st.markdown("---")
        st.markdown("### 🔨 Interventions en cours")
        if interventions_en_cours_v:
            st.markdown("#### 🚗 Véhicules")
            for i in interventions_en_cours_v:
                immat = i.get('immatriculation', '')
                info_v = vh_map.get(immat, {})
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid #f59e0b;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;'>{immat}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{info_v.get('marque','')} — {info_v.get('type','')}</span><br/>
                    <span style='color:{t['text_color']};font-size:0.85rem;'>🔧 {i.get('type','')} — 📅 {i.get('date','')} à {i.get('heure','')}</span>
                    <span style='color:{t['text_color']};font-size:0.85rem;margin-left:1rem;'>💬 {i.get('commentaire','')}</span>
                </div>""", unsafe_allow_html=True)
        if interventions_en_cours_s:
            st.markdown("#### 🛵 Scooters")
            for i in interventions_en_cours_s:
                immat = i.get('immatriculation', '')
                info_s = sco_map.get(immat, {})
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid #f59e0b;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;'>{immat}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{info_s.get('marque','')} — {info_s.get('type','')}</span><br/>
                    <span style='color:{t['text_color']};font-size:0.85rem;'>🔧 {i.get('type','')} — 📅 {i.get('date','')} à {i.get('heure','')}</span>
                    <span style='color:{t['text_color']};font-size:0.85rem;margin-left:1rem;'>💬 {i.get('commentaire','')}</span>
                </div>""", unsafe_allow_html=True)
        if interventions_en_cours_e:
            st.markdown("#### 🚜 Engins")
            for i in interventions_en_cours_e:
                num = i.get('numero_serie', '')
                info_e = eng_map.get(num, {})
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid #f59e0b;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;'>{num}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{info_e.get('marque','')} — {info_e.get('type','')}</span><br/>
                    <span style='color:{t['text_color']};font-size:0.85rem;'>🔧 {i.get('type','')} — 📅 {i.get('date','')} à {i.get('heure','')}</span>
                    <span style='color:{t['text_color']};font-size:0.85rem;margin-left:1rem;'>💬 {i.get('commentaire','')}</span>
                </div>""", unsafe_allow_html=True)
        if not interventions_en_cours_v and not interventions_en_cours_e and not interventions_en_cours_s:
            st.info("Aucune intervention en cours")

    st.markdown("---")
    st.markdown("### 🔍 Filtres")
    col_f1, col_f2 = st.columns(2)
    types_dispo = (["Tous"] + sorted(set(v['type'] for v in vehicules))) if vehicules else ["Tous"]
    filtre_type = col_f1.selectbox("Type", types_dispo)
    filtre_service = col_f2.selectbox("Service", ["Tous"] + services)
    
    st.markdown("---")
    st.markdown("### 📋 Sorties du Jour")
    
    with st.expander("🚗 Véhicules", expanded=False):
        aujourd_hui = datetime.now().strftime("%d/%m/%Y")
        sorties_jour = [a for a in attributions if a.get('date') == aujourd_hui and not a.get('retourne')]
        if sorties_jour:
            df = pd.DataFrame(sorties_jour)
            df['type'] = df['immatriculation'].map(lambda x: vh_map.get(x, {}).get('type', ''))
            df['marque'] = df['immatriculation'].map(lambda x: vh_map.get(x, {}).get('marque', ''))
            if filtre_type != "Tous":
                df = df[df['type'] == filtre_type]
            if filtre_service != "Tous":
                df = df[df['service'] == filtre_service]
            if len(df) > 0:
                for srv in (services if filtre_service == "Tous" else [filtre_service]):
                    df_srv = df[df['service'] == srv]
                    if len(df_srv) > 0:
                        st.markdown(f"#### 🔹 {srv}")
                        st.dataframe(df_srv[['immatriculation', 'type', 'marque', 'date', 'heure']], use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Aucune attribution")
        else:
            st.warning("⚠️ Aucune attribution")
    
    with st.expander("🛵 Scooters", expanded=False):
        sorties_jour_sco = [a for a in attributions_scooters if a.get('date') == aujourd_hui and not a.get('retourne')]
        if sorties_jour_sco:
            df_sco = pd.DataFrame(sorties_jour_sco)
            df_sco['type'] = df_sco['immatriculation'].map(lambda x: sco_map.get(x, {}).get('type', ''))
            df_sco['marque'] = df_sco['immatriculation'].map(lambda x: sco_map.get(x, {}).get('marque', ''))
            if filtre_service != "Tous":
                df_sco = df_sco[df_sco['service'] == filtre_service]
            if len(df_sco) > 0:
                for srv in (services if filtre_service == "Tous" else [filtre_service]):
                    df_srv = df_sco[df_sco['service'] == srv]
                    if len(df_srv) > 0:
                        st.markdown(f"#### 🔹 {srv}")
                        cols_sco = ['immatriculation', 'type', 'marque', 'date', 'heure']
                        if 'casque' in df_srv.columns:
                            cols_sco.append('casque')
                        st.dataframe(df_srv[cols_sco], use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Aucune attribution")
        else:
            st.warning("⚠️ Aucune attribution")

    with st.expander("🚜 Engins", expanded=False):
        sorties_jour_eng = [a for a in attributions_engins if _is_engin_active_today(a)]
        if sorties_jour_eng:
            df_eng = pd.DataFrame(sorties_jour_eng)
            df_eng['type'] = df_eng['numero_serie'].map(lambda x: eng_map.get(x, {}).get('type', ''))
            df_eng['marque'] = df_eng['numero_serie'].map(lambda x: eng_map.get(x, {}).get('marque', ''))
            if filtre_service != "Tous":
                df_eng = df_eng[df_eng['service'] == filtre_service]
            if len(df_eng) > 0:
                for srv in (services if filtre_service == "Tous" else [filtre_service]):
                    df_srv = df_eng[df_eng['service'] == srv]
                    if len(df_srv) > 0:
                        st.markdown(f"#### 🔹 {srv}")
                        cols_show = [c for c in ['numero_serie', 'type', 'marque', 'date', 'date_fin', 'periode'] if c in df_srv.columns]
                        st.dataframe(df_srv[cols_show], use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Aucune attribution")
        else:
            st.warning("⚠️ Aucune attribution")
    
    st.markdown("---")
    st.markdown("### 🔙 Retours du Jour")

    with st.expander("🚗 Véhicules retournés aujourd'hui", expanded=False):
        retours_jour = [a for a in attributions if a.get('retourne', '').startswith(aujourd_hui)]
        if retours_jour:
            df_ret = pd.DataFrame(retours_jour)
            df_ret['type'] = df_ret['immatriculation'].map(lambda x: vh_map.get(x, {}).get('type', ''))
            df_ret['marque'] = df_ret['immatriculation'].map(lambda x: vh_map.get(x, {}).get('marque', ''))
            if filtre_type != "Tous":
                df_ret = df_ret[df_ret['type'] == filtre_type]
            if filtre_service != "Tous":
                df_ret = df_ret[df_ret['service'] == filtre_service]
            if len(df_ret) > 0:
                for srv in (services if filtre_service == "Tous" else [filtre_service]):
                    df_srv = df_ret[df_ret['service'] == srv]
                    if len(df_srv) > 0:
                        st.markdown(f"#### 🔹 {srv}")
                        st.dataframe(df_srv[['immatriculation', 'type', 'marque', 'date', 'retourne']], use_container_width=True, hide_index=True)
            else:
                st.info("✅ Aucun retour aujourd'hui")
        else:
            st.info("✅ Aucun retour aujourd'hui")

    with st.expander("🛵 Scooters retournés aujourd'hui", expanded=False):
        retours_jour_sco = [a for a in attributions_scooters if a.get('retourne', '').startswith(aujourd_hui)]
        if retours_jour_sco:
            df_ret_sco = pd.DataFrame(retours_jour_sco)
            df_ret_sco['type'] = df_ret_sco['immatriculation'].map(lambda x: sco_map.get(x, {}).get('type', ''))
            df_ret_sco['marque'] = df_ret_sco['immatriculation'].map(lambda x: sco_map.get(x, {}).get('marque', ''))
            if filtre_service != "Tous":
                df_ret_sco = df_ret_sco[df_ret_sco['service'] == filtre_service]
            if len(df_ret_sco) > 0:
                for srv in (services if filtre_service == "Tous" else [filtre_service]):
                    df_srv = df_ret_sco[df_ret_sco['service'] == srv]
                    if len(df_srv) > 0:
                        st.markdown(f"#### 🔹 {srv}")
                        cols_ret_sco = ['immatriculation', 'type', 'marque', 'date', 'retourne']
                        if 'casque' in df_srv.columns:
                            cols_ret_sco.append('casque')
                        st.dataframe(df_srv[cols_ret_sco], use_container_width=True, hide_index=True)
            else:
                st.info("✅ Aucun retour aujourd'hui")
        else:
            st.info("✅ Aucun retour aujourd'hui")

    st.markdown("---")
    st.markdown("### 🔙 Retourner un Véhicule")
    sortis = [a for a in attributions if not a.get('retourne')]
    if sortis:
        col_r1, col_r2 = st.columns([3, 1])
        immat_ret = col_r1.selectbox("Véhicule", [f"{v['immatriculation']} - {v['service']}" for v in sortis])
        if col_r2.button("✅ Retourner", type="primary", key="ret_vh"):
            retourner_vehicule(immat_ret.split(" - ")[0])
            st.success("✅ Retourné !")
            st.rerun()
    else:
        st.info("Aucun véhicule distribué")

    st.markdown("---")
    st.markdown("### 🔙 Retourner un Scooter")
    sortis_sco = [a for a in attributions_scooters if not a.get('retourne')]
    if sortis_sco:
        col_r1, col_r2 = st.columns([3, 1])
        options_sco = []
        for v in sortis_sco:
            casque_info = f" | Casque: {v['casque']}" if v.get('casque') else ""
            options_sco.append(f"{v['immatriculation']} - {v['service']}{casque_info}")
        immat_ret_sco = col_r1.selectbox("Scooter", options_sco)
        if col_r2.button("✅ Retourner", type="primary", key="ret_sco"):
            retourner_scooter(immat_ret_sco.split(" - ")[0])
            st.success("✅ Retourné !")
            st.rerun()
    else:
        st.info("Aucun scooter distribué")

    st.markdown("---")
    st.markdown("### 🔙 Retourner un Engin")
    sortis_engins_dash = [a for a in attributions_engins if _is_engin_active_today(a)]
    if sortis_engins_dash:
        col_r1, col_r2 = st.columns([3, 1])
        engin_ret_dash = col_r1.selectbox("Engin", [f"{e['numero_serie']} - {e['service']}" for e in sortis_engins_dash])
        if col_r2.button("✅ Retourner", type="primary", key="ret_eng_dash"):
            retourner_engin(engin_ret_dash.split(" - ")[0])
            st.success("✅ Retourné !")
            st.rerun()
    else:
        st.info("Aucun engin distribué")

elif page == "➕ Saisir un véhicule":
    st.markdown("# ➕ Nouveau Véhicule")
    st.markdown("<p class='page-intro'>Ajouter un véhicule à votre flotte</p>", unsafe_allow_html=True)
    with st.form("form_vh"):
        col1, col2 = st.columns(2)
        immat = col1.text_input("Immatriculation *", placeholder="AB-123-CD")
        marque = col2.text_input("Marque *", placeholder="Renault")
        type_v = st.selectbox("Type *", categories)
        if st.form_submit_button("✅ Enregistrer", type="primary"):
            if immat and marque:
                add_vehicule(immat, type_v, marque)
                st.success(f"✅ {immat} ajouté !")
                st.rerun()
            else:
                st.error("❌ Champs requis")
    st.markdown("---")
    st.markdown("### 📋 Liste des véhicules")
    if vehicules:
        for vh in vehicules:
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;'><span style='color: {t['h1_color']}; font-weight: 600;'>{vh['immatriculation']}</span> <span style='color: {t['label_color']};'>— {vh['type']} {vh['marque']}</span></div>", unsafe_allow_html=True)
            if col2.button("🗑️", key=f"del_{vh['immatriculation']}"):
                delete_vehicule(vh['immatriculation'])
                st.rerun()

elif page == "🔧 Attribuer un véhicule":
    st.markdown("# 🔧 Attribution")
    st.markdown("<p class='page-intro'>Attribuer un véhicule à un service</p>", unsafe_allow_html=True)
    if vehicules:
        with st.form("form_attr"):
            col1, col2 = st.columns(2)
            immat_sel = col1.selectbox("Véhicule *", [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in vehicules])
            service = col2.selectbox("Service *", services)
            col3, col4 = st.columns(2)
            date_s = col3.date_input("Date sortie", value=datetime.now())
            heure_s = col4.time_input("Heure sortie", value=datetime.now().time())
            date_retour = st.date_input("Date de retour prévue *", value=datetime.now() + timedelta(days=1))
            if st.form_submit_button("✅ Confirmer", type="primary"):
                if date_retour < date_s:
                    st.error("❌ La date de retour doit être après la date de sortie")
                else:
                    add_attribution(immat_sel.split(" - ")[0], service, date_s.strftime("%d/%m/%Y"), heure_s.strftime("%H:%M"), date_retour.strftime("%d/%m/%Y"))
                    st.success(f"✅ Attribué !")
                    st.rerun()
    else:
        st.warning("⚠️ Aucun véhicule")
    st.markdown("---")
    st.markdown("### 📜 Historique")
    if attributions:
        for i, attr in enumerate(reversed(attributions)):
            idx = len(attributions) - 1 - i
            retourne_badge = "✅" if attr.get('retourne') else "🔑"
            with st.expander(f"{retourne_badge} {attr.get('immatriculation', '')} → {attr.get('service', '')} ({attr.get('date', '')})"):
                with st.form(f"edit_attr_vh_{idx}"):
                    col1, col2 = st.columns(2)
                    srv_val = attr.get('service', '')
                    srv_idx = services.index(srv_val) if srv_val in services else 0
                    new_srv = col1.selectbox("Service", services, index=srv_idx, key=f"srv_vh_{idx}")
                    new_dr = col2.text_input("Date retour prévue", value=attr.get('date_retour_prevue', ''), key=f"dr_vh_{idx}")
                    col3, col4 = st.columns(2)
                    new_date = col3.text_input("Date sortie", value=attr.get('date', ''), key=f"ds_vh_{idx}")
                    new_heure = col4.text_input("Heure", value=attr.get('heure', ''), key=f"hs_vh_{idx}")
                    col_s, col_d = st.columns(2)
                    saved = col_s.form_submit_button("💾 Enregistrer")
                    deleted = col_d.form_submit_button("🗑️ Supprimer")
                if saved:
                    update_attribution(idx, {'service': new_srv, 'date_retour_prevue': new_dr, 'date': new_date, 'heure': new_heure})
                    st.success("✅ Modifié !")
                    st.rerun()
                if deleted:
                    delete_attribution(idx)
                    st.success("✅ Supprimé !")
                    st.rerun()
    else:
        st.info("Aucune attribution")

elif page == "⛽ Bons de Carburant":
    st.markdown("# ⛽ Bons de Carburant")
    st.markdown("<p class='page-intro'>Générer et suivre les bons</p>", unsafe_allow_html=True)
    st.markdown("### 📝 Générer un Bon")
    service_bon = st.selectbox("Service *", services, key="service_bon")
    vh_srv = [f"{v['immatriculation']} - {v['type']} {v['marque']}" for attr in attributions if attr.get('service') == service_bon and not attr.get('retourne') for v in vehicules if v['immatriculation'] == attr['immatriculation']]
    if vh_srv:
        with st.form("form_bon"):
            vh_sel = st.selectbox("Véhicule *", vh_srv)
            col1, col2 = st.columns(2)
            date_bon = col1.date_input("Date *", value=datetime.now())
            num_carte = col2.text_input("N° Carte *")
            col3, col4 = st.columns(2)
            conducteur_prenom = col3.text_input("Prénom *")
            conducteur_nom = col4.text_input("Nom *")
            logo_url = st.text_input("URL logo (optionnel)")
            notes = st.text_area("Notes", height=80)
            if st.form_submit_button("✅ Générer", type="primary"):
                if conducteur_nom and conducteur_prenom and num_carte:
                    num_bon = f"BC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    bon = {"numero_bon": num_bon, "immatriculation": vh_sel.split(" - ")[0], "service": service_bon, "date": date_bon.strftime("%d/%m/%Y"), "numero_carte": num_carte, "conducteur_nom": conducteur_nom, "conducteur_prenom": conducteur_prenom, "type_carburant": "", "volume": "", "montant": "", "notes": notes, "statut": "Non saisi"}
                    add_bon_carburant(bon)
                    st.session_state.dernier_bon = {'bon': bon, 'conducteur_nom': conducteur_nom, 'conducteur_prenom': conducteur_prenom, 'logo_url': logo_url}
                    st.success(f"✅ Bon {num_bon} généré !")
                    st.rerun()
                else:
                    st.error("❌ Champs requis")
        if 'dernier_bon' in st.session_state:
            bon = st.session_state.dernier_bon['bon']
            st.markdown(f"<div style='background: {t['input_bg']}; border-radius: 16px; padding: 2rem; margin: 1rem 0; border: 1px solid {t['card_border']};'><h3 style='color: {t['h1_color']}; text-align: center;'>📄 BON DE CARBURANT</h3><p style='color: {t['label_color']};'><strong style='color: {t['strong_color']};'>N°:</strong> {bon['numero_bon']} | <strong style='color: {t['strong_color']};'>Véhicule:</strong> {bon['immatriculation']} | <strong style='color: #ef4444;'>Carte N°{bon['numero_carte']}</strong></p></div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                pdf = generer_pdf_bon(bon, st.session_state.dernier_bon['conducteur_nom'], st.session_state.dernier_bon['conducteur_prenom'], st.session_state.dernier_bon.get('logo_url'))
                st.download_button("📥 Télécharger PDF", pdf, f"bon_{bon['numero_bon']}.pdf", "application/pdf", type="primary")
            with col2:
                if st.button("🔄 Nouveau bon"):
                    del st.session_state.dernier_bon
                    st.rerun()
    else:
        st.warning(f"⚠️ Aucun véhicule attribué au service {service_bon}")
    
    st.markdown("---")
    st.markdown("### 📥 Saisir données retour")
    non_saisis = [b for b in bons_carburant if b.get('statut') == "Non saisi"]
    if non_saisis:
        with st.form("form_saisie"):
            bon_sel = st.selectbox("Bon *", [f"{b['numero_bon']} - {b['immatriculation']}" for b in non_saisis])
            col1, col2, col3 = st.columns(3)
            type_carb = col1.selectbox("Carburant *", ["Diesel", "SP95", "SP98", "GPL", "Électrique"])
            volume = col2.number_input("Volume (L) *", min_value=0.0, step=0.1)
            montant = col3.number_input("Montant (€) *", min_value=0.0, step=0.01)
            if st.form_submit_button("✅ Enregistrer", type="primary"):
                if volume > 0:
                    update_bon_carburant(bon_sel.split(" - ")[0], type_carb, volume, montant)
                    st.success("✅ Enregistré !")
                    st.rerun()
    else:
        st.info("✅ Tous les bons sont saisis")
    
    st.markdown("---")
    st.markdown("### 📋 Historique")
    if bons_carburant:
        h = st.columns([2, 1.5, 1, 1.2, 0.8, 0.9, 1, 0.5])
        for col, label in zip(h, ["N° Bon", "Véhicule", "Date", "Carburant", "Vol. (L)", "Montant (€)", "Statut", ""]):
            col.markdown(f"<small><b>{label}</b></small>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0.25rem 0 0.5rem 0'>", unsafe_allow_html=True)
        for bon in reversed(bons_carburant):
            num = bon.get('numero_bon', '')
            statut = bon.get('statut', '')
            statut_color = '#ef4444' if statut == 'Non saisi' else '#10b981'
            c = st.columns([2, 1.5, 1, 1.2, 0.8, 0.9, 1, 0.5])
            c[0].markdown(f"<small>{num}</small>", unsafe_allow_html=True)
            c[1].markdown(f"<small>{bon.get('immatriculation', '')}</small>", unsafe_allow_html=True)
            c[2].markdown(f"<small>{bon.get('date', '')}</small>", unsafe_allow_html=True)
            c[3].markdown(f"<small>{bon.get('type_carburant', '-')}</small>", unsafe_allow_html=True)
            c[4].markdown(f"<small>{bon.get('volume', '-')}</small>", unsafe_allow_html=True)
            c[5].markdown(f"<small>{bon.get('montant', '-')}</small>", unsafe_allow_html=True)
            c[6].markdown(f"<small style='color:{statut_color}'>{statut}</small>", unsafe_allow_html=True)
            if c[7].button("🗑️", key=f"del_bon_{num}"):
                delete_bon_carburant(num)
                st.rerun()
    else:
        st.info("Aucun bon enregistré")

elif page == "🔨 Pannes & Interventions":
    st.markdown("# 🔨 Interventions Véhicules")
    st.markdown("<p class='page-intro'>Déclarer et suivre les interventions</p>", unsafe_allow_html=True)
    st.markdown("### ➕ Déclarer")
    if vehicules:
        with st.form("form_interv"):
            col1, col2 = st.columns(2)
            vh_sel = col1.selectbox("Véhicule *", [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in vehicules])
            type_i = col2.selectbox("Type *", ["Panne", "Entretien", "Réparation", "Contrôle", "Autre"])
            col3, col4 = st.columns(2)
            date_i = col3.date_input("Date *", value=datetime.now())
            heure_i = col4.time_input("Heure *", value=datetime.now().time())
            comm = st.text_area("Commentaire *", height=100)
            statut = st.selectbox("Statut", ["En cours", "Terminée", "En attente"])
            if st.form_submit_button("✅ Enregistrer", type="primary"):
                if comm:
                    add_intervention(vh_sel.split(" - ")[0], type_i, date_i.strftime("%d/%m/%Y"), heure_i.strftime("%H:%M"), comm, statut)
                    st.success("✅ Enregistré !")
                    st.rerun()
    else:
        st.warning("⚠️ Aucun véhicule enregistré")
    st.markdown("---")
    st.markdown("### 📋 Historique")
    if interventions:
        for interv in interventions[:20]:
            statut = interv.get('statut', '')
            emoji = "🔴" if statut == "En cours" else "✅" if statut == "Terminée" else "⏸️"
            with st.expander(f"{emoji} {interv.get('immatriculation', '')} - {interv.get('type', '')} - {interv.get('date', '')}"):
                st.write(f"**Type:** {interv.get('type', '')} | **Statut:** {statut}")
                st.info(interv.get('commentaire', ''))

elif page == "🛵 Saisir un scooter":
    st.markdown("# 🛵 Nouveau Scooter")
    st.markdown("<p class='page-intro'>Ajouter un scooter à votre flotte</p>", unsafe_allow_html=True)
    with st.form("form_sco"):
        col1, col2 = st.columns(2)
        immat_sco = col1.text_input("Immatriculation *", placeholder="AB-123-CD")
        marque_sco = col2.text_input("Marque *", placeholder="Piaggio")
        type_sco = st.selectbox("Type *", categories_scooters)
        if st.form_submit_button("✅ Enregistrer", type="primary"):
            if immat_sco and marque_sco:
                add_scooter(immat_sco, type_sco, marque_sco)
                st.success(f"✅ {immat_sco} ajouté !")
                st.rerun()
            else:
                st.error("❌ Champs requis")
    st.markdown("---")
    st.markdown("### 📋 Liste des scooters")
    if scooters:
        for sco in scooters:
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;'><span style='color: {t['h1_color']}; font-weight: 600;'>{sco['immatriculation']}</span> <span style='color: {t['label_color']};'>— {sco['type']} {sco['marque']}</span></div>", unsafe_allow_html=True)
            if col2.button("🗑️", key=f"del_sco_{sco['immatriculation']}"):
                delete_scooter(sco['immatriculation'])
                st.rerun()

elif page == "🔧 Attribuer un scooter":
    st.markdown("# 🔧 Attribution Scooter")
    st.markdown("<p class='page-intro'>Attribuer un scooter à un service</p>", unsafe_allow_html=True)
    if scooters:
        with st.form("form_attr_sco"):
            col1, col2 = st.columns(2)
            sco_sel = col1.selectbox("Scooter *", [f"{s['immatriculation']} - {s['type']} {s['marque']}" for s in scooters])
            service_sco = col2.selectbox("Service *", services)
            col3, col4 = st.columns(2)
            date_s_sco = col3.date_input("Date sortie", value=datetime.now())
            heure_s_sco = col4.time_input("Heure sortie", value=datetime.now().time())
            col5, col6 = st.columns(2)
            date_retour_sco = col5.date_input("Date de retour prévue *", value=datetime.now() + timedelta(days=1))
            casque_sco = col6.text_input("🪖 Casque attribué", placeholder="N° ou réf. du casque")
            if st.form_submit_button("✅ Confirmer", type="primary"):
                if date_retour_sco < date_s_sco:
                    st.error("❌ La date de retour doit être après la date de sortie")
                else:
                    add_attribution_scooter(sco_sel.split(" - ")[0], service_sco, date_s_sco.strftime("%d/%m/%Y"), heure_s_sco.strftime("%H:%M"), date_retour_sco.strftime("%d/%m/%Y"), casque_sco)
                    st.success("✅ Attribué !")
                    st.rerun()
    else:
        st.warning("⚠️ Aucun scooter")
    st.markdown("---")
    st.markdown("### 📜 Historique")
    if attributions_scooters:
        for i, attr in enumerate(reversed(attributions_scooters)):
            idx = len(attributions_scooters) - 1 - i
            retourne_badge = "✅" if attr.get('retourne') else "🔑"
            casque_txt = f" | 🪖 {attr.get('casque')}" if attr.get('casque') else ""
            with st.expander(f"{retourne_badge} {attr.get('immatriculation', '')} → {attr.get('service', '')} ({attr.get('date', '')}){casque_txt}"):
                with st.form(f"edit_attr_sco_{idx}"):
                    col1, col2 = st.columns(2)
                    srv_val = attr.get('service', '')
                    srv_idx = services.index(srv_val) if srv_val in services else 0
                    new_srv = col1.selectbox("Service", services, index=srv_idx, key=f"srv_sco_{idx}")
                    new_dr = col2.text_input("Date retour prévue", value=attr.get('date_retour_prevue', ''), key=f"dr_sco_{idx}")
                    col3, col4 = st.columns(2)
                    new_date = col3.text_input("Date sortie", value=attr.get('date', ''), key=f"ds_sco_{idx}")
                    new_heure = col4.text_input("Heure", value=attr.get('heure', ''), key=f"hs_sco_{idx}")
                    new_casque = st.text_input("🪖 Casque", value=attr.get('casque', ''), key=f"cq_sco_{idx}")
                    col_s, col_d = st.columns(2)
                    saved = col_s.form_submit_button("💾 Enregistrer")
                    deleted = col_d.form_submit_button("🗑️ Supprimer")
                if saved:
                    update_attribution_scooter(idx, {'service': new_srv, 'date_retour_prevue': new_dr, 'date': new_date, 'heure': new_heure, 'casque': new_casque})
                    st.success("✅ Modifié !")
                    st.rerun()
                if deleted:
                    delete_attribution_scooter(idx)
                    st.success("✅ Supprimé !")
                    st.rerun()
    else:
        st.info("Aucune attribution")

elif page == "🔨 Interventions Scooters":
    st.markdown("# 🔨 Interventions Scooters")
    st.markdown("<p class='page-intro'>Déclarer et suivre les interventions</p>", unsafe_allow_html=True)
    st.markdown("### ➕ Déclarer")
    if scooters:
        with st.form("form_interv_sco"):
            col1, col2 = st.columns(2)
            sco_sel_i = col1.selectbox("Scooter *", [f"{s['immatriculation']} - {s['type']} {s['marque']}" for s in scooters])
            type_i_sco = col2.selectbox("Type *", ["Panne", "Entretien", "Réparation", "Contrôle", "Autre"])
            col3, col4 = st.columns(2)
            date_i_sco = col3.date_input("Date *", value=datetime.now())
            heure_i_sco = col4.time_input("Heure *", value=datetime.now().time())
            comm_sco = st.text_area("Commentaire *", height=100)
            statut_sco = st.selectbox("Statut", ["En cours", "Terminée", "En attente"])
            if st.form_submit_button("✅ Enregistrer", type="primary"):
                if comm_sco:
                    add_intervention_scooter(sco_sel_i.split(" - ")[0], type_i_sco, date_i_sco.strftime("%d/%m/%Y"), heure_i_sco.strftime("%H:%M"), comm_sco, statut_sco)
                    st.success("✅ Enregistré !")
                    st.rerun()
    else:
        st.warning("⚠️ Aucun scooter enregistré")
    st.markdown("---")
    st.markdown("### 📋 Historique")
    if interventions_scooters:
        for interv in interventions_scooters[:20]:
            statut = interv.get('statut', '')
            emoji = "🔴" if statut == "En cours" else "✅" if statut == "Terminée" else "⏸️"
            with st.expander(f"{emoji} {interv.get('immatriculation', '')} - {interv.get('type', '')} - {interv.get('date', '')}"):
                st.write(f"**Type:** {interv.get('type', '')} | **Statut:** {statut}")
                st.info(interv.get('commentaire', ''))
    else:
        st.info("Aucune intervention enregistrée")

elif page == "🚜 Saisir un engin":
    st.markdown("# 🚜 Nouvel Engin")
    st.markdown("<p class='page-intro'>Ajouter un engin à votre parc</p>", unsafe_allow_html=True)
    with st.form("form_engin"):
        col1, col2 = st.columns(2)
        num_serie = col1.text_input("N° Série / Identifiant *", placeholder="ENG-001")
        marque = col2.text_input("Marque *", placeholder="Caterpillar")
        type_e = st.selectbox("Type *", categories_engins)
        if st.form_submit_button("✅ Enregistrer", type="primary"):
            if num_serie and marque:
                add_engin(num_serie, type_e, marque)
                st.success(f"✅ {num_serie} ajouté !")
                st.rerun()
            else:
                st.error("❌ Champs requis")
    st.markdown("---")
    st.markdown("### 📋 Liste des engins")
    if engins:
        for eng in engins:
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;'><span style='color: {t['h1_color']}; font-weight: 600;'>{eng['numero_serie']}</span> <span style='color: {t['label_color']};'>— {eng['type']} {eng['marque']}</span></div>", unsafe_allow_html=True)
            if col2.button("🗑️", key=f"del_eng_{eng['numero_serie']}"):
                delete_engin(eng['numero_serie'])
                st.rerun()
    else:
        st.info("Aucun engin enregistré")

elif page == "🔧 Attribuer un engin":
    st.markdown("# 🔧 Planning Engins")
    st.markdown("<p class='page-intro'>Planification et suivi des attributions sur période</p>", unsafe_allow_html=True)

    # ── PLANNING SEMAINE ──────────────────────────────────────────────
    st.markdown("### 📅 Planning Semaine")
    if 'eng_sem_offset' not in st.session_state:
        st.session_state['eng_sem_offset'] = 0

    today_date = datetime.now().date()
    lundi = today_date - timedelta(days=today_date.weekday())
    semaine_debut = lundi + timedelta(weeks=st.session_state['eng_sem_offset'])
    semaine_fin_nav = semaine_debut + timedelta(days=6)

    col_nav1, col_nav2, col_nav3 = st.columns([1, 3, 1])
    if col_nav1.button("← Préc.", key="eng_prev"):
        st.session_state['eng_sem_offset'] -= 1
        st.rerun()
    nav_color = t['h23_color']
    col_nav2.markdown(
        f"<h4 style='text-align:center; color:{nav_color}'>Semaine du {semaine_debut.strftime('%d/%m/%Y')} au {semaine_fin_nav.strftime('%d/%m/%Y')}</h4>",
        unsafe_allow_html=True
    )
    if col_nav3.button("Suiv. →", key="eng_next"):
        st.session_state['eng_sem_offset'] += 1
        st.rerun()

    if engins:
        JOURS_FR = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        jours_sem = [semaine_debut + timedelta(days=i) for i in range(7)]
        _PALETTE = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316']
        svc_color = {s: _PALETTE[i % len(_PALETTE)] for i, s in enumerate(services)}

        def _get_slot(num_serie, day, periode):
            for a in attributions_engins:
                if a.get('numero_serie') != num_serie or a.get('retourne'):
                    continue
                try:
                    dd = datetime.strptime(a['date'], "%d/%m/%Y").date()
                    df_d = datetime.strptime(a.get('date_fin', a['date']), "%d/%m/%Y").date()
                    if dd <= day <= df_d:
                        p = a.get('periode', 'Journée')
                        if p == 'Journée' or p == periode:
                            return a['service']
                except Exception:
                    pass
            return None

        cb = t['card_border']
        ib = t['input_bg']
        hc = t['h23_color']
        ic = t['intro_color']
        th_s = f"padding:0.45rem 0.4rem; border:1px solid {cb}; text-align:center; background:{ib}; color:{hc}; font-weight:600; font-size:0.8rem;"
        td_s = f"border:1px solid {cb}; text-align:center; padding:0.3rem 0.25rem; font-size:0.75rem;"
        td_eng_s = f"{td_s} background:{ib}; color:{hc}; text-align:left; padding:0.4rem 0.5rem; min-width:110px;"
        td_slot_s = f"{td_s} background:{ib}; color:{ic}; min-width:52px;"

        html = f"<div style='overflow-x:auto'><table style='width:100%; border-collapse:collapse;'><thead><tr>"
        html += f"<th style='{th_s} text-align:left; min-width:110px;'>Engin</th>"
        html += f"<th style='{th_s} min-width:52px;'>Slot</th>"
        for i, jour in enumerate(jours_sem):
            jour_color = '#f59e0b' if jour == today_date else hc
            html += f"<th style='{th_s} color:{jour_color}; min-width:88px;'>{JOURS_FR[i]}<br>{jour.strftime('%d/%m')}</th>"
        html += "</tr></thead><tbody>"

        for eng in engins:
            num = eng.get('numero_serie', '')
            eng_label = f"<b>{num}</b><br><small style='color:{ic}'>{eng.get('type','')} {eng.get('marque','')}</small>"
            for pi, (periode, icon) in enumerate([('Matin', '🌅'), ('Après-midi', '🌇')]):
                html += "<tr>"
                if pi == 0:
                    html += f"<td rowspan='2' style='{td_eng_s}'>{eng_label}</td>"
                html += f"<td style='{td_slot_s}'>{icon} {periode}</td>"
                for jour in jours_sem:
                    svc = _get_slot(num, jour, periode)
                    if svc:
                        bg = svc_color.get(svc, '#6b7280')
                        html += f"<td style='{td_s} background:{bg}; color:white; font-weight:500;'>{svc}</td>"
                    else:
                        html += f"<td style='{td_s} color:{ic};'>—</td>"
                html += "</tr>"

        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)

        legende = " ".join(
            f"<span style='background:{svc_color.get(s,'#6b7280')}; color:white; padding:0.2rem 0.6rem; border-radius:12px; font-size:0.75rem; margin-right:0.3rem;'>{s}</span>"
            for s in services
        )
        st.markdown(f"<div style='margin-top:0.6rem'>{legende}</div>", unsafe_allow_html=True)
    else:
        st.info("Aucun engin enregistré — ajoutez-en depuis 🚜 Saisir un engin")

    # ── NOUVELLE ATTRIBUTION ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ➕ Nouvelle Attribution")
    if engins:
        with st.form("form_attr_engin"):
            col1, col2 = st.columns(2)
            engin_sel = col1.selectbox("Engin *", [f"{e['numero_serie']} - {e['type']} {e['marque']}" for e in engins])
            service_sel = col2.selectbox("Service *", services)
            col3, col4, col5 = st.columns(3)
            date_deb = col3.date_input("Date début *", value=datetime.now())
            date_fin_inp = col4.date_input("Date fin *", value=datetime.now())
            periode_sel = col5.selectbox("Période *", ["Journée", "Matin", "Après-midi"])
            if st.form_submit_button("✅ Confirmer", type="primary"):
                if date_fin_inp >= date_deb:
                    add_attribution_engin(
                        engin_sel.split(" - ")[0], service_sel,
                        date_deb.strftime("%d/%m/%Y"),
                        date_fin_inp.strftime("%d/%m/%Y"),
                        periode_sel
                    )
                    st.success("✅ Attribution enregistrée !")
                    st.rerun()
                else:
                    st.error("❌ La date de fin doit être ≥ à la date de début")

    # ── HISTORIQUE ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📜 Historique")
    if attributions_engins:
        for i, attr in enumerate(reversed(attributions_engins)):
            idx = len(attributions_engins) - 1 - i
            retourne_badge = "✅" if attr.get('retourne') else "🔑"
            date_fin_lbl = attr.get('date_fin', '')
            periode_lbl = attr.get('periode', '')
            periode_str = f" [{periode_lbl}]" if periode_lbl else ""
            date_str = attr.get('date', '')
            plage_str = f"{date_str} → {date_fin_lbl}" if date_fin_lbl and date_fin_lbl != date_str else date_str
            label_exp = f"{retourne_badge} {attr.get('numero_serie','')} — {attr.get('service','')} | {plage_str}{periode_str}"
            with st.expander(label_exp):
                with st.form(f"edit_attr_eng_{idx}"):
                    col1, col2 = st.columns(2)
                    srv_val = attr.get('service', '')
                    srv_idx = services.index(srv_val) if srv_val in services else 0
                    new_srv = col1.selectbox("Service", services, index=srv_idx, key=f"srv_eng_{idx}")
                    per_opts = ["Journée", "Matin", "Après-midi"]
                    per_val = attr.get('periode', 'Journée')
                    per_idx = per_opts.index(per_val) if per_val in per_opts else 0
                    new_per = col2.selectbox("Période", per_opts, index=per_idx, key=f"per_eng_{idx}")
                    col3, col4 = st.columns(2)
                    new_date = col3.text_input("Date début (JJ/MM/AAAA)", value=attr.get('date', ''), key=f"ds_eng_{idx}")
                    new_datefin = col4.text_input("Date fin (JJ/MM/AAAA)", value=attr.get('date_fin', ''), key=f"df_eng_{idx}")
                    col_s, col_d = st.columns(2)
                    saved = col_s.form_submit_button("💾 Enregistrer")
                    deleted = col_d.form_submit_button("🗑️ Supprimer")
                if saved:
                    update_attribution_engin(idx, {'service': new_srv, 'date': new_date, 'date_fin': new_datefin, 'periode': new_per})
                    st.success("✅ Modifié !")
                    st.rerun()
                if deleted:
                    delete_attribution_engin(idx)
                    st.success("✅ Supprimé !")
                    st.rerun()
    else:
        st.info("Aucune attribution enregistrée")

elif page == "🔨 Interventions Engins":
    st.markdown("# 🔨 Interventions Engins")
    st.markdown("<p class='page-intro'>Déclarer et suivre les interventions sur engins</p>", unsafe_allow_html=True)
    st.markdown("### ➕ Déclarer")
    if engins:
        with st.form("form_interv_engin"):
            col1, col2 = st.columns(2)
            eng_sel = col1.selectbox("Engin *", [f"{e['numero_serie']} - {e['type']} {e['marque']}" for e in engins])
            type_i = col2.selectbox("Type *", ["Panne", "Entretien", "Réparation", "Contrôle", "Autre"])
            col3, col4 = st.columns(2)
            date_i = col3.date_input("Date *", value=datetime.now())
            heure_i = col4.time_input("Heure *", value=datetime.now().time())
            comm = st.text_area("Commentaire *", height=100)
            statut = st.selectbox("Statut", ["En cours", "Terminée", "En attente"])
            if st.form_submit_button("✅ Enregistrer", type="primary"):
                if comm:
                    add_intervention_engin(eng_sel.split(" - ")[0], type_i, date_i.strftime("%d/%m/%Y"), heure_i.strftime("%H:%M"), comm, statut)
                    st.success("✅ Enregistré !")
                    st.rerun()
    else:
        st.warning("⚠️ Aucun engin enregistré")
    st.markdown("---")
    st.markdown("### 📋 Historique")
    if interventions_engins:
        for interv in interventions_engins[:20]:
            statut = interv.get('statut', '')
            emoji = "🔴" if statut == "En cours" else "✅" if statut == "Terminée" else "⏸️"
            with st.expander(f"{emoji} {interv.get('numero_serie', '')} - {interv.get('type', '')} - {interv.get('date', '')}"):
                st.write(f"**Type:** {interv.get('type', '')} | **Statut:** {statut}")
                st.info(interv.get('commentaire', ''))
    else:
        st.info("Aucune intervention enregistrée")

elif page == "⚙️ Paramètres":
    st.markdown("# ⚙️ Paramètres")
    st.markdown("<p class='page-intro'>Configurer l'application</p>", unsafe_allow_html=True)

    st.markdown("### 🎨 Apparence")
    theme_names = list(THEMES.keys())
    current_idx = theme_names.index(st.session_state['theme']) if st.session_state['theme'] in theme_names else 0
    selected_theme = st.selectbox("Thème", theme_names, index=current_idx)
    if selected_theme != st.session_state['theme']:
        st.session_state['theme'] = selected_theme
        st.rerun()

    st.markdown("---")
    st.markdown("### 🚗 Véhicules")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🏷️ Catégories Véhicules")
        for cat in categories:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{cat}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"dc_{cat}"):
                delete_category(cat)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_cat = c1.text_input("Nouvelle catégorie", label_visibility="collapsed", placeholder="Nouvelle catégorie...")
        if c2.button("➕", key="ac", type="primary"):
            if nv_cat:
                add_category(nv_cat)
                st.rerun()
    with col2:
        st.markdown("#### 🏢 Services")
        for srv in services:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{srv}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"ds_{srv}"):
                delete_service(srv)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_srv = c1.text_input("Nouveau service", label_visibility="collapsed", placeholder="Nouveau service...")
        if c2.button("➕", key="as", type="primary"):
            if nv_srv:
                add_service(nv_srv)
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 🚜 Engins")
    st.markdown("#### 🏷️ Catégories Engins")
    col_eng = st.columns(2)[0]
    with col_eng:
        for cat in categories_engins:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{cat}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"dce_{cat}"):
                delete_category_engin(cat)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_cat_eng = c1.text_input("Nouvelle catégorie engin", label_visibility="collapsed", placeholder="Nouvelle catégorie engin...")
        if c2.button("➕", key="ace", type="primary"):
            if nv_cat_eng:
                add_category_engin(nv_cat_eng)
                st.rerun()

    st.markdown("---")
    st.markdown("### 🛵 Scooters")
    st.markdown("#### 🏷️ Catégories Scooters")
    col_sco = st.columns(2)[0]
    with col_sco:
        for cat in categories_scooters:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{cat}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"dcs_{cat}"):
                delete_category_scooter(cat)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_cat_sco = c1.text_input("Nouvelle catégorie scooter", label_visibility="collapsed", placeholder="Nouvelle catégorie scooter...")
        if c2.button("➕", key="acs", type="primary"):
            if nv_cat_sco:
                add_category_scooter(nv_cat_sco)
                st.rerun()

    st.markdown("---")
    st.markdown("### 📎 Liens Tableaux Excel")
    st.markdown(f"<p class='page-intro'>Ces liens apparaissent comme boutons cliquables sur le Dashboard.</p>", unsafe_allow_html=True)
    col_liens = st.columns(2)[0]
    with col_liens:
        for lien in liens:
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{lien.get('nom', '')}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['intro_color']}; font-size: 0.8rem; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;'>{lien.get('url', '')}</div>", unsafe_allow_html=True)
            if c3.button("🗑️", key=f"dl_{lien.get('nom', '')}"):
                delete_lien(lien.get('nom', ''))
                st.rerun()
        with st.form("form_add_lien"):
            c1, c2, c3 = st.columns([2, 3, 1])
            nv_nom = c1.text_input("Nom *", label_visibility="collapsed", placeholder="Ex : Véhicules 2024")
            nv_url = c2.text_input("URL *", label_visibility="collapsed", placeholder="https://...")
            if c3.form_submit_button("➕", type="primary"):
                if nv_nom and nv_url:
                    add_lien(nv_nom, nv_url)
                    st.rerun()
                else:
                    st.error("❌ Nom et URL requis")
