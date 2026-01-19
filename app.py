import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

st.set_page_config(page_title="Gestion de Flotte", page_icon="🚗", layout="wide")

# ============================================
# STYLES CSS - DARK MODE DASHBOARD
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    h1 {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2, h3 {
        color: #e0e0e0 !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e1e32 0%, #252542 100%);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.15);
    }
    
    [data-testid="stMetric"] label {
        color: #a0a0a0 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
    }
    
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        background-color: #1e1e32 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }
    
    .stTextInput > label,
    .stSelectbox > label,
    .stTextArea > label,
    .stNumberInput > label,
    .stDateInput > label,
    .stTimeInput > label {
        color: #c0c0c0 !important;
        font-weight: 500 !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }
    
    [data-testid="stForm"] {
        background: linear-gradient(145deg, #1e1e32 0%, #252542 100%);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 1.5rem;
    }
    
    .stDataFrame {
        background: #1e1e32;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    .streamlit-expanderHeader {
        background: #1e1e32 !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 10px !important;
        color: #e0e0e0 !important;
    }
    
    hr {
        border-color: rgba(255,255,255,0.05) !important;
        margin: 2rem 0 !important;
    }
    
    p, .stText, .stMarkdown { color: #c0c0c0; }
    strong { color: #e0e0e0; }
    
    .page-intro {
        color: #808080;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    
    .sidebar-title {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #1a1a2e; }
    ::-webkit-scrollbar-thumb { background: #3a3a5e; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# AUTHENTIFICATION PAR MOT DE PASSE
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<div style='max-width: 400px; margin: 15vh auto; text-align: center;'>", unsafe_allow_html=True)
        st.markdown("## 🚗 Gestion de Flotte")
        st.markdown("<p style='color: #808080; margin-bottom: 2rem;'>Connectez-vous pour accéder à l'application</p>", unsafe_allow_html=True)
        st.text_input("🔒 Mot de passe", type="password", on_change=password_entered, key="password")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()
    elif not st.session_state["password_correct"]:
        st.markdown("<div style='max-width: 400px; margin: 15vh auto; text-align: center;'>", unsafe_allow_html=True)
        st.markdown("## 🚗 Gestion de Flotte")
        st.markdown("<p style='color: #808080; margin-bottom: 2rem;'>Connectez-vous pour accéder à l'application</p>", unsafe_allow_html=True)
        st.text_input("🔒 Mot de passe", type="password", on_change=password_entered, key="password")
        st.error("❌ Mot de passe incorrect")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

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
    except:
        return []

def write_sheet(sheet_name, data):
    if not data:
        return
    headers = list(data[0].keys())
    values = [headers] + [[row.get(h, '') for h in headers] for row in data]
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A1",
        valueInputOption="RAW", body={"values": values}
    ).execute()

def init_database():
    try:
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        existing_sheets = [s['properties']['title'] for s in sheet_metadata['sheets']]
        required_sheets = ['vehicules', 'attributions', 'categories', 'services', 'interventions', 'carburant']
        for sheet_name in required_sheets:
            if sheet_name not in existing_sheets:
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
                ).execute()
    except:
        pass

init_database()

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

def add_attribution(immat, service, date, heure):
    attributions = get_attributions()
    attributions.append({'immatriculation': immat, 'service': service, 'date': date, 'heure': heure, 'retourne': ''})
    write_sheet('attributions', attributions)

def retourner_vehicule(immat):
    attributions = get_attributions()
    for attr in attributions:
        if attr.get('immatriculation') == immat and not attr.get('retourne'):
            attr['retourne'] = datetime.now().strftime("%d/%m/%Y %H:%M")
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

def generer_pdf_bon(bon, conducteur_nom, conducteur_prenom, logo_url=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    if logo_url:
        try:
            c.drawImage(logo_url, 50, height - 100, width=100, height=80, preserveAspectRatio=True)
        except:
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

def verifier_alertes(attributions):
    alertes = []
    for attr in attributions:
        if attr.get('retourne'):
            continue
        try:
            date_attrib = datetime.strptime(f"{attr['date']} {attr['heure']}", "%d/%m/%Y %H:%M")
            duree = datetime.now() - date_attrib
            if duree > timedelta(hours=8):
                alertes.append({'immatriculation': attr['immatriculation'], 'service': attr['service'], 'duree_heures': int(duree.total_seconds() / 3600)})
        except:
            continue
    return alertes

# CHARGEMENT DONNÉES
vehicules = get_vehicules()
attributions = get_attributions()
categories = get_categories()
services = get_services()
interventions = get_interventions()
bons_carburant = get_carburant()

# SIDEBAR
with st.sidebar:
    st.markdown("<div class='sidebar-title'>🚗 Flotte</div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #606060; font-size: 0.85rem; margin-bottom: 2rem;'>Gestion de véhicules</p>", unsafe_allow_html=True)
    
    page = st.radio("Navigation", [
        "📊 Dashboard", "📥 Importer des véhicules", "➕ Saisir un véhicule",
        "🔧 Attribuer un véhicule", "⛽ Bons de Carburant",
        "🔨 Pannes & Interventions", "⚙️ Paramètres"
    ], label_visibility="collapsed")
    
    st.markdown("---")
    alertes = verifier_alertes(attributions)
    if alertes:
        st.markdown(f"<div style='background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 1rem;'><p style='color: #ef4444; font-weight: 600; margin: 0;'>🚨 {len(alertes)} véhicule(s) à retourner</p></div>", unsafe_allow_html=True)
        with st.expander("Voir les alertes"):
            for a in alertes:
                st.warning(f"{a['immatriculation']} - {a['service']} ({a['duree_heures']}h)")
    
    st.markdown("---")
    st.markdown("<div style='background: rgba(16, 185, 129, 0.1); border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem;'><p style='color: #10b981; font-size: 0.8rem; margin: 0;'>🗄️ Base connectée</p></div>", unsafe_allow_html=True)

# PAGES
if page == "📊 Dashboard":
    st.markdown("# 📊 Tableau de Bord")
    st.markdown("<p class='page-intro'>Vue d'ensemble de votre flotte</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🚙 Véhicules", len(vehicules))
    col2.metric("🔑 En sortie", len([a for a in attributions if not a.get('retourne')]))
    col3.metric("🔨 Interventions", len([i for i in interventions if i['statut'] == "En cours"]))
    col4.metric("⛽ Bons non saisis", len([b for b in bons_carburant if b.get('statut') == "Non saisi"]))
    
    st.markdown("---")
    st.markdown("### 🔍 Filtres")
    col_f1, col_f2 = st.columns(2)
    types_dispo = ["Tous"] + sorted(list(set([v['type'] for v in vehicules]))) if vehicules else ["Tous"]
    filtre_type = col_f1.selectbox("Type", types_dispo)
    filtre_service = col_f2.selectbox("Service", ["Tous"] + services)
    
    st.markdown("---")
    st.markdown("### 📋 Sorties du Jour")
    if attributions:
        df = pd.DataFrame(attributions)
        df['type'] = df['immatriculation'].apply(lambda x: next((v['type'] for v in vehicules if v['immatriculation'] == x), ""))
        df['marque'] = df['immatriculation'].apply(lambda x: next((v['marque'] for v in vehicules if v['immatriculation'] == x), ""))
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
    
    st.markdown("---")
    st.markdown("### 🔙 Retourner un Véhicule")
    sortis = [a for a in attributions if not a.get('retourne')]
    if sortis:
        col_r1, col_r2 = st.columns([3, 1])
        immat_ret = col_r1.selectbox("Véhicule", [f"{v['immatriculation']} - {v['service']}" for v in sortis])
        if col_r2.button("✅ Retourner", type="primary"):
            retourner_vehicule(immat_ret.split(" - ")[0])
            st.success(f"✅ Retourné !")
            st.rerun()
    else:
        st.info("Aucun véhicule en sortie")

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
            col1.markdown(f"<div style='background: #1e1e32; border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;'><span style='color: #fff; font-weight: 600;'>{vh['immatriculation']}</span> <span style='color: #808080;'>— {vh['type']} {vh['marque']}</span></div>", unsafe_allow_html=True)
            if col2.button("🗑️", key=f"del_{vh['immatriculation']}"):
                delete_vehicule(vh['immatriculation'])
                st.rerun()

elif page == "📥 Importer des véhicules":
    st.markdown("# 📥 Importer des véhicules")
    st.markdown("<p class='page-intro'>Importez depuis un fichier CSV ou Excel</p>", unsafe_allow_html=True)
    st.info("💡 Colonnes requises : immatriculation, type, marque")
    uploaded_file = st.file_uploader("Choisir un fichier", type=['csv', 'xlsx'])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            st.dataframe(df, use_container_width=True, hide_index=True)
            if st.button("✅ Importer", type="primary"):
                count = 0
                for _, row in df.iterrows():
                    if 'immatriculation' in row and 'type' in row and 'marque' in row:
                        add_vehicule(str(row['immatriculation']), str(row['type']), str(row['marque']))
                        count += 1
                st.success(f"✅ {count} véhicule(s) importé(s) !")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

elif page == "🔧 Attribuer un véhicule":
    st.markdown("# 🔧 Attribution")
    st.markdown("<p class='page-intro'>Attribuer un véhicule à un service</p>", unsafe_allow_html=True)
    if vehicules:
        with st.form("form_attr"):
            col1, col2 = st.columns(2)
            immat_sel = col1.selectbox("Véhicule *", [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in vehicules])
            service = col2.selectbox("Service *", services)
            col3, col4 = st.columns(2)
            date_s = col3.date_input("Date", value=datetime.now())
            heure_s = col4.time_input("Heure", value=datetime.now().time())
            if st.form_submit_button("✅ Confirmer", type="primary"):
                add_attribution(immat_sel.split(" - ")[0], service, date_s.strftime("%d/%m/%Y"), heure_s.strftime("%H:%M"))
                st.success(f"✅ Attribué !")
                st.rerun()
    else:
        st.warning("⚠️ Aucun véhicule")
    st.markdown("---")
    st.markdown("### 📜 Historique")
    if attributions:
        st.dataframe(pd.DataFrame(attributions), use_container_width=True, hide_index=True)

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
                    bon = {"numero_bon": num_bon, "immatriculation": vh_sel.split(" - ")[0], "service": service_bon, "date": date_bon.strftime("%d/%m/%Y"), "numero_carte": num_carte, "conducteur_nom": conducteur_nom, "conducteur_prenom": conducteur_prenom, "type_carburant": "", "volume": 0.0, "montant": 0.0, "notes": notes, "statut": "Non saisi"}
                    add_bon_carburant(bon)
                    st.session_state.dernier_bon = {'bon': bon, 'conducteur_nom': conducteur_nom, 'conducteur_prenom': conducteur_prenom, 'logo_url': logo_url}
                    st.success(f"✅ Bon {num_bon} généré !")
                    st.rerun()
                else:
                    st.error("❌ Champs requis")
        if 'dernier_bon' in st.session_state:
            bon = st.session_state.dernier_bon['bon']
            st.markdown(f"<div style='background: #1e1e32; border-radius: 16px; padding: 2rem; margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);'><h3 style='color: #fff; text-align: center;'>📄 BON DE CARBURANT</h3><p style='color: #808080;'><strong style='color: #c0c0c0;'>N°:</strong> {bon['numero_bon']} | <strong style='color: #c0c0c0;'>Véhicule:</strong> {bon['immatriculation']} | <strong style='color: #ef4444;'>Carte N°{bon['numero_carte']}</strong></p></div>", unsafe_allow_html=True)
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
    non_saisis = [b for b in bons_carburant if b['statut'] == "Non saisi"]
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
        bons_df = pd.DataFrame(bons_carburant)
        bons_df['volume'] = pd.to_numeric(bons_df['volume'], errors='coerce').fillna(0)
        bons_df['montant'] = pd.to_numeric(bons_df['montant'], errors='coerce').fillna(0)
        st.dataframe(bons_df, use_container_width=True, hide_index=True)

elif page == "🔨 Pannes & Interventions":
    st.markdown("# 🔨 Interventions")
    st.markdown("<p class='page-intro'>Déclarer et suivre les interventions</p>", unsafe_allow_html=True)
    st.markdown("### ➕ Déclarer")
    with st.form("form_interv"):
        col1, col2 = st.columns(2)
        vh_sel = col1.selectbox("Véhicule *", [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in vehicules]) if vehicules else None
        type_i = col2.selectbox("Type *", ["Panne", "Entretien", "Réparation", "Contrôle", "Autre"])
        col3, col4 = st.columns(2)
        date_i = col3.date_input("Date *", value=datetime.now())
        heure_i = col4.time_input("Heure *", value=datetime.now().time())
        comm = st.text_area("Commentaire *", height=100)
        statut = st.selectbox("Statut", ["En cours", "Terminée", "En attente"])
        if st.form_submit_button("✅ Enregistrer", type="primary"):
            if vh_sel and comm:
                add_intervention(vh_sel.split(" - ")[0], type_i, date_i.strftime("%d/%m/%Y"), heure_i.strftime("%H:%M"), comm, statut)
                st.success("✅ Enregistré !")
                st.rerun()
    st.markdown("---")
    st.markdown("### 📋 Historique")
    if interventions:
        for interv in interventions[:20]:
            emoji = "🔴" if interv['statut'] == "En cours" else "✅" if interv['statut'] == "Terminée" else "⏸️"
            with st.expander(f"{emoji} {interv['immatriculation']} - {interv['type']} - {interv['date']}"):
                st.write(f"**Type:** {interv['type']} | **Statut:** {interv['statut']}")
                st.info(interv['commentaire'])

elif page == "⚙️ Paramètres":
    st.markdown("# ⚙️ Paramètres")
    st.markdown("<p class='page-intro'>Configurer catégories et services</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏷️ Catégories")
        for cat in categories:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: #1e1e32; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: #e0e0e0;'>{cat}</div>", unsafe_allow_html=True)
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
        st.markdown("### 🏢 Services")
        for srv in services:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: #1e1e32; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: #e0e0e0;'>{srv}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"ds_{srv}"):
                delete_service(srv)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_srv = c1.text_input("Nouveau service", label_visibility="collapsed", placeholder="Nouveau service...")
        if c2.button("➕", key="as", type="primary"):
            if nv_srv:
                add_service(nv_srv)
                st.rerun()
