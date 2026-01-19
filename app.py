import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="Gestion de Flotte", page_icon="🚗", layout="wide")

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
    """Lit une feuille Google Sheets et retourne une liste de dictionnaires"""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z"
        ).execute()
        values = result.get('values', [])
        if not values or len(values) < 2:
            return []
        headers = values[0]
        return [dict(zip(headers, row + [''] * (len(headers) - len(row)))) for row in values[1:]]
    except:
        return []

def write_sheet(sheet_name, data):
    """Écrit des données dans une feuille Google Sheets"""
    if not data:
        return
    headers = list(data[0].keys())
    values = [headers] + [[row.get(h, '') for h in headers] for row in data]
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()

def init_database():
    """Crée les feuilles si elles n'existent pas"""
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        existing_sheets = [s['properties']['title'] for s in sheet_metadata['sheets']]
        
        required_sheets = ['vehicules', 'attributions', 'categories', 'services', 'interventions', 'carburant']
        
        for sheet_name in required_sheets:
            if sheet_name not in existing_sheets:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
                ).execute()
    except:
        pass

# Initialiser la base
init_database()

# FONCTIONS CRUD
def get_vehicules():
    return read_sheet('vehicules')

def add_vehicule(immat, type_v, marque):
    vehicules = get_vehicules()
    if not any(v.get('immatriculation') == immat for v in vehicules):
        vehicules.append({'immatriculation': immat, 'type': type_v, 'marque': marque})
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
    cats = [c for c in get_categories() if c != nom]
    write_sheet('categories', [{'nom': c} for c in cats])

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
    srvs = [s for s in get_services() if s != nom]
    write_sheet('services', [{'nom': s} for s in srvs])

def get_interventions():
    return read_sheet('interventions')

def add_intervention(immat, type_i, date, heure, comm, statut):
    interventions = get_interventions()
    interventions.append({
        'immatriculation': immat,
        'type': type_i,
        'date': date,
        'heure': heure,
        'commentaire': comm,
        'statut': statut
    })
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

def verifier_alertes(attributions):
    alertes = []
    for attr in attributions:
        if attr.get('retourne'):
            continue
        try:
            date_attrib = datetime.strptime(f"{attr['date']} {attr['heure']}", "%d/%m/%Y %H:%M")
            duree = datetime.now() - date_attrib
            if duree > timedelta(hours=8):
                alertes.append({
                    'immatriculation': attr['immatriculation'],
                    'service': attr['service'],
                    'duree_heures': int(duree.total_seconds() / 3600)
                })
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

# MENU
st.sidebar.title("🚗 Menu Navigation")
page = st.sidebar.radio("Choisir une page :", [
    "📊 Dashboard", "📥 Importer des véhicules", "➕ Saisir un véhicule",
    "🔧 Attribuer un véhicule", "⛽ Bons de Carburant",
    "🔨 Pannes & Interventions", "⚙️ Paramètres"
])

st.sidebar.markdown("---")
alertes = verifier_alertes(attributions)
if alertes:
    st.sidebar.error(f"🚨 {len(alertes)} véhicule(s) à retourner !")
    with st.sidebar.expander("Voir"):
        for a in alertes:
            st.warning(f"{a['immatriculation']} - {a['service']}\n{a['duree_heures']}h")

st.sidebar.markdown("---")
st.sidebar.success("🗄️ Base de données PostgreSQL")
st.sidebar.info("👥 Données partagées en temps réel")

# PAGES
if page == "📊 Dashboard":
    st.title("📊 Tableau de Bord")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🚙 Total Véhicules", len(vehicules))
    col2.metric("🔑 Sortis", len([a for a in attributions if not a.get('retourne')]))
    col3.metric("🔨 Interventions", len([i for i in interventions if i['statut'] == "En cours"]))
    
    st.markdown("---")
    st.subheader("🔍 Filtres")
    col_f1, col_f2 = st.columns(2)
    types_dispo = ["Tous"] + sorted(list(set([v['type'] for v in vehicules]))) if vehicules else ["Tous"]
    filtre_type = col_f1.selectbox("Type", types_dispo)
    filtre_service = col_f2.selectbox("Service", ["Tous"] + services)
    
    st.markdown("---")
    st.subheader("📋 Sorties du Jour")
    
    if attributions:
        df = pd.DataFrame(attributions)
        df['type'] = df['immatriculation'].apply(lambda x: next((v['type'] for v in vehicules if v['immatriculation'] == x), ""))
        df['marque'] = df['immatriculation'].apply(lambda x: next((v['marque'] for v in vehicules if v['immatriculation'] == x), ""))
        
        if filtre_type != "Tous":
            df = df[df['type'] == filtre_type]
        if filtre_service != "Tous":
            df = df[df['service'] == filtre_service]
        
        if len(df) > 0:
            services_aff = services if filtre_service == "Tous" else [filtre_service]
            for srv in services_aff:
                df_srv = df[df['service'] == srv]
                if len(df_srv) > 0:
                    st.markdown(f"### 🔹 {srv}")
                    st.dataframe(df_srv[['immatriculation', 'type', 'marque', 'date', 'heure']], use_container_width=True, hide_index=True)
                elif filtre_service == "Tous":
                    st.markdown(f"### 🔹 {srv}")
                    st.info(f"Aucune sortie pour {srv}")
        else:
            st.warning("⚠️ Aucune attribution")
    else:
        st.warning("⚠️ Aucune attribution")
    
    st.markdown("---")
    st.subheader("🔙 Retourner un Véhicule")
    sortis = [a for a in attributions if not a.get('retourne')]
    
    if sortis:
        col_r1, col_r2 = st.columns([3, 1])
        immat_ret = col_r1.selectbox("Véhicule", [f"{v['immatriculation']} - {v['service']}" for v in sortis])
        if col_r2.button("✅ Retourner", type="primary"):
            immat = immat_ret.split(" - ")[0]
            retourner_vehicule(immat)
            st.success(f"✅ {immat} retourné !")
            st.rerun()
    else:
        st.info("Aucun véhicule en sortie")

elif page == "➕ Saisir un véhicule":
    st.title("➕ Nouveau Véhicule")
    
    with st.form("form_vh"):
        immat = st.text_input("Immatriculation *", placeholder="AB-123-CD")
        type_v = st.selectbox("Type *", categories)
        marque = st.text_input("Marque *", placeholder="Renault")
        
        if st.form_submit_button("✅ Enregistrer"):
            if immat and marque:
                add_vehicule(immat, type_v, marque)
                st.success(f"✅ {immat} ajouté !")
                st.rerun()
            else:
                st.error("❌ Champs requis")
    
    st.markdown("---")
    st.subheader("📋 Liste")
    if vehicules:
        st.dataframe(pd.DataFrame(vehicules), use_container_width=True, hide_index=True)

elif page == "🔧 Attribuer un véhicule":
    st.title("🔧 Attribution")
    
    if vehicules:
        with st.form("form_attr"):
            choices = [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in vehicules]
            immat_sel = st.selectbox("Véhicule *", choices)
            service = st.selectbox("Service *", services)
            
            col1, col2 = st.columns(2)
            date_s = col1.date_input("Date", value=datetime.now())
            heure_s = col2.time_input("Heure", value=datetime.now().time())
            
            if st.form_submit_button("✅ Confirmer"):
                immat = immat_sel.split(" - ")[0]
                add_attribution(immat, service, date_s.strftime("%d/%m/%Y"), heure_s.strftime("%H:%M"))
                st.success(f"✅ {immat} attribué !")
                st.rerun()
    else:
        st.warning("⚠️ Aucun véhicule")
    
    st.markdown("---")
    st.subheader("📜 Historique")
    if attributions:
        st.dataframe(pd.DataFrame(attributions), use_container_width=True, hide_index=True)

elif page == "⛽ Bons de Carburant":
    st.title("⛽ Bons de Carburant")
    st.subheader("📝 Générer un Bon")
    
    with st.form("form_bon"):
        col1, col2 = st.columns(2)
        service_bon = col1.selectbox("Service *", services)
        
        vh_srv = []
        for attr in attributions:
            if attr.get('service') == service_bon and not attr.get('retourne'):
                for v in vehicules:
                    if v['immatriculation'] == attr['immatriculation']:
                        vh_srv.append(f"{v['immatriculation']} - {v['type']} {v['marque']}")
                        break
        
        if vh_srv:
            vh_sel = col2.selectbox("Véhicule *", vh_srv)
        else:
            col2.warning(f"Aucun véhicule affecté à {service_bon}")
            vh_sel = None
        
        col3, col4 = st.columns(2)
        date_bon = col3.date_input("Date *", value=datetime.now())
        num_carte = col4.text_input("N° Carte *", placeholder="1, 2, A...")
        notes = st.text_area("Notes", height=80)
        
        if st.form_submit_button("✅ Générer"):
            if vh_sel and num_carte:
                immat = vh_sel.split(" - ")[0]
                num_bon = f"BC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                bon = {
                    "numero_bon": num_bon,
                    "immatriculation": immat,
                    "service": service_bon,
                    "date": date_bon.strftime("%d/%m/%Y"),
                    "numero_carte": num_carte,
                    "type_carburant": "",
                    "volume": 0.0,
                    "montant": 0.0,
                    "notes": notes,
                    "statut": "Non saisi"
                }
                add_bon_carburant(bon)
                
                st.success(f"✅ Bon {num_bon} généré !")
                st.markdown("---")
                
                bon_html = f"""
                <div style="border: 2px solid #333; padding: 30px; border-radius: 10px; background: #fff; max-width: 600px; margin: auto;">
                    <h2 style="text-align: center;">BON DE CARBURANT</h2>
                    <hr>
                    <p><strong>N° :</strong> {num_bon}</p>
                    <p style="font-size: 18px; color: #d9534f;"><strong>Carte N°{num_carte}</strong></p>
                    <p><strong>Véhicule :</strong> {immat}</p>
                    <p><strong>Service :</strong> {service_bon}</p>
                    <p><strong>Date :</strong> {date_bon.strftime("%d/%m/%Y")}</p>
                    {f'<p><strong>Notes :</strong> {notes}</p>' if notes else ''}
                    <hr>
                    <p style="text-align: center; font-style: italic; color: #666;">Volume, type et montant à saisir au retour</p>
                </div>
                """
                st.markdown(bon_html, unsafe_allow_html=True)
                st.info("💡 Ctrl+P pour imprimer")
            else:
                st.error("❌ Champs requis")
    
    st.markdown("---")
    st.subheader("📥 Saisir données bon retourné")
    
    non_saisis = [b for b in bons_carburant if b['statut'] == "Non saisi"]
    
    if non_saisis:
        with st.form("form_saisie"):
            bons_list = [f"{b['numero_bon']} - {b['immatriculation']} - Carte N°{b['numero_carte']}" for b in non_saisis]
            bon_sel = st.selectbox("Bon *", bons_list)
            
            col1, col2, col3 = st.columns(3)
            type_carb = col1.selectbox("Carburant *", ["Diesel", "SP95", "SP98", "GPL", "Électrique"])
            volume = col2.number_input("Volume (L) *", min_value=0.0, step=0.1)
            montant = col3.number_input("Montant (€) *", min_value=0.0, step=0.01)
            
            if st.form_submit_button("✅ Enregistrer"):
                if volume > 0:
                    num_bon_sel = bon_sel.split(" - ")[0]
                    update_bon_carburant(num_bon_sel, type_carb, volume, montant)
                    st.success(f"✅ Données enregistrées !")
                    st.rerun()
                else:
                    st.error("❌ Volume > 0")
    else:
        st.info("✅ Tous saisis")
    
    st.markdown("---")
    st.subheader("📋 Historique")
    
    if bons_carburant:
        bons_df = pd.DataFrame(bons_carburant)
        bons_df['prix_litre'] = bons_df.apply(
            lambda r: round(r['montant'] / r['volume'], 3) if r['volume'] > 0 else 0, axis=1
        )
        bons_df['type_carburant'] = bons_df['type_carburant'].replace('', '-')
        st.dataframe(bons_df, use_container_width=True, hide_index=True)

elif page == "🔨 Pannes & Interventions":
    st.title("🔨 Interventions")
    st.subheader("➕ Déclarer")
    
    with st.form("form_interv"):
        col1, col2 = st.columns(2)
        
        if vehicules:
            vh_list = [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in vehicules]
            vh_sel = col1.selectbox("Véhicule *", vh_list)
        else:
            col1.warning("Aucun véhicule")
            vh_sel = None
        
        type_i = col2.selectbox("Type *", ["Panne", "Entretien", "Réparation", "Contrôle", "Autre"])
        
        col3, col4 = st.columns(2)
        date_i = col3.date_input("Date *", value=datetime.now())
        heure_i = col4.time_input("Heure *", value=datetime.now().time())
        
        comm = st.text_area("Commentaire *", height=100)
        statut = st.selectbox("Statut", ["En cours", "Terminée", "En attente"])
        
        if st.form_submit_button("✅ Enregistrer"):
            if vh_sel and comm:
                immat = vh_sel.split(" - ")[0]
                add_intervention(immat, type_i, date_i.strftime("%d/%m/%Y"), heure_i.strftime("%H:%M"), comm, statut)
                st.success(f"✅ Intervention enregistrée !")
                st.rerun()
            else:
                st.error("❌ Champs requis")
    
    st.markdown("---")
    st.subheader("📋 Historique")
    
    if interventions:
        for interv in interventions[:20]:
            emoji = "🔴" if interv['statut'] == "En cours" else "✅" if interv['statut'] == "Terminée" else "⏸️"
            with st.expander(f"{emoji} {interv['immatriculation']} - {interv['type']} - {interv['date']}"):
                st.write(f"**Type :** {interv['type']}")
                st.write(f"**Statut :** {interv['statut']}")
                st.info(interv['commentaire'])

elif page == "⚙️ Paramètres":
    st.title("⚙️ Paramètres")
    
    st.subheader("🏷️ Catégories")
    for cat in categories:
        col1, col2 = st.columns([4, 1])
        col1.text(f"• {cat}")
        if col2.button("🗑️", key=f"dc_{cat}"):
            delete_category(cat)
            st.rerun()
    
    col1, col2 = st.columns([3, 1])
    nv_cat = col1.text_input("Nouvelle catégorie")
    if col2.button("➕", type="primary", key="ac"):
        if nv_cat:
            add_category(nv_cat)
            st.rerun()
    
    st.markdown("---")
    st.subheader("🏢 Services")
    for srv in services:
        col1, col2 = st.columns([4, 1])
        col1.text(f"• {srv}")
        if col2.button("🗑️", key=f"ds_{srv}"):
            delete_service(srv)
            st.rerun()
    
    col1, col2 = st.columns([3, 1])
    nv_srv = col1.text_input("Nouveau service")
    if col2.button("➕", type="primary", key="as"):
        if nv_srv:
            add_service(nv_srv)
            st.rerun()

st.sidebar.caption("🚀 App avec PostgreSQL")
