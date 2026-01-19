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
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z"
        ).execute()
        values = result.get('values', [])
        if not values or len(values) < 2:
            return []
        headers = values[0]
        return [dict(zip(headers, row + [''] * (len(headers) - len(row)))) for row in values[1:]]
    except Exception as e:
        st.error(f"Erreur lors de la lecture de {sheet_name}: {e}")
        return []

def write_sheet(sheet_name, data):
    """Écrit des données dans une feuille Google Sheets"""
    if not data:
        return
    headers = list(data[0].keys())
    values = [headers] + [[row.get(h, '') for h in headers] for row in data]
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()

def init_database():
    """Crée les feuilles si elles n'existent pas"""
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
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation de la base : {e}")

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

def delete_vehicule(immat):
    vehicules = get_vehicules()
    vehicules = [v for v in vehicules if v.get('immatriculation') != immat]
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

def generer_pdf_bon(bon, conducteur_nom, conducteur_prenom, logo_url=None):
    """Génère un PDF du bon de carburant"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Logo (si fourni)
    if logo_url:
        try:
            c.drawImage(logo_url, 50, height - 100, width=100, height=80, preserveAspectRatio=True)
        except Exception as e:
            st.warning(f"Impossible de charger le logo: {e}")
    
    # Titre
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 120, "BON DE CARBURANT")
    
    # Ligne de séparation
    c.line(50, height - 140, width - 50, height - 140)
    
    # Informations
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
        y -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(80, y, "Notes :")
        y -= 20
        c.setFont("Helvetica", 10)
        # Découper les notes longues
        notes_lines = bon['notes'].split('\n')
        for line in notes_lines:
            c.drawString(90, y, line[:80])
            y -= 15
    
    # Ligne de séparation
    y -= 20
    c.line(50, y, width - 50, y)
    
    # Section à remplir
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(80, y, "À REMPLIR AU RETOUR :")
    
    y -= 40
    c.setFont("Helvetica", 12)
    c.drawString(80, y, "Type de carburant : ___________________")
    y -= 30
    c.drawString(80, y, "Volume (L) : ___________________")
    y -= 30
    c.drawString(80, y, "Montant (€) : ___________________")
    
    # Pied de page
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width/2, 50, "Document généré automatiquement - Gestion de Flotte")
    
    c.save()
    buffer.seek(0)
    return buffer

# INTERFACE
st.sidebar.title("📋 Navigation")
page = st.sidebar.radio("Menu", [
    "🏠 Accueil",
    "🚗 Véhicules",
    "📍 Attribuer un véhicule",
    "⛽ Bons de carburant",
    "🔨 Pannes & Interventions",
    "⚙️ Paramètres"
])

vehicules = get_vehicules()
attributions = get_attributions()
categories = get_categories()
services = get_services()
interventions = get_interventions()
bons_carburant = get_carburant()

if page == "🏠 Accueil":
    st.title("🚗 Gestion de Flotte")
    st.markdown("### Tableau de bord")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Véhicules", len(vehicules))
    
    with col2:
        attrib_actives = [a for a in attributions if not a.get('retourne')]
        st.metric("Véhicules en service", len(attrib_actives))
    
    with col3:
        pannes_actives = [i for i in interventions if i.get('statut') == "En cours"]
        st.metric("Interventions en cours", len(pannes_actives))
    
    st.markdown("---")
    
    if attrib_actives:
        st.subheader("🚦 Véhicules actuellement attribués")
        for attr in attrib_actives[:10]:
            with st.expander(f"🚗 {attr['immatriculation']} - {attr['service']}"):
                st.write(f"**Date :** {attr['date']} {attr['heure']}")
    
    if pannes_actives:
        st.markdown("---")
        st.subheader("⚠️ Interventions en cours")
        for interv in pannes_actives[:5]:
            st.warning(f"🔧 {interv['immatriculation']} - {interv['type']} - {interv['commentaire'][:50]}...")

elif page == "🚗 Véhicules":
    st.title("🚗 Gestion des Véhicules")
    
    st.subheader("➕ Ajouter un véhicule")
    
    with st.form("form_vehicule"):
        col1, col2, col3 = st.columns(3)
        
        immat = col1.text_input("Immatriculation *", placeholder="AB-123-CD")
        type_v = col2.selectbox("Type *", categories)
        marque = col3.text_input("Marque *", placeholder="Renault")
        
        if st.form_submit_button("✅ Ajouter"):
            if immat and type_v and marque:
                add_vehicule(immat, type_v, marque)
                st.success(f"✅ {immat} ajouté !")
                st.rerun()
            else:
                st.error("❌ Tous les champs sont requis")
    
    st.markdown("---")
    st.subheader("📋 Liste des véhicules")
    
    if vehicules:
        for vh in vehicules:
            col1, col2 = st.columns([5, 1])
            col1.text(f"🚗 {vh['immatriculation']} - {vh['type']} {vh['marque']}")
            if col2.button("🗑️", key=f"dv_{vh['immatriculation']}"):
                delete_vehicule(vh['immatriculation'])
                st.rerun()
    else:
        st.info("Aucun véhicule enregistré")

elif page == "📍 Attribuer un véhicule":
    st.title("📍 Attribution des Véhicules")
    
    st.subheader("➕ Nouvelle attribution")
    
    if vehicules:
        with st.form("form_attribution"):
            col1, col2 = st.columns(2)
            
            vh_list = [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in vehicules]
            vh_sel = col1.selectbox("Véhicule *", vh_list)
            service = col2.selectbox("Service *", services)
            
            col3, col4 = st.columns(2)
            date_attr = col3.date_input("Date *", value=datetime.now())
            heure_attr = col4.time_input("Heure *", value=datetime.now().time())
            
            if st.form_submit_button("✅ Attribuer"):
                immat = vh_sel.split(" - ")[0]
                add_attribution(immat, service, date_attr.strftime("%d/%m/%Y"), heure_attr.strftime("%H:%M"))
                st.success(f"✅ {immat} attribué à {service} !")
                st.rerun()
    else:
        st.warning("⚠️ Aucun véhicule disponible")
    
    st.markdown("---")
    st.subheader("🔄 Retourner un véhicule")
    
    attrib_actives = [a for a in attributions if not a.get('retourne')]
    
    if attrib_actives:
        for attr in attrib_actives:
            col1, col2 = st.columns([5, 1])
            col1.text(f"🚗 {attr['immatriculation']} chez {attr['service']} depuis {attr['date']} {attr['heure']}")
            if col2.button("↩️", key=f"ret_{attr['immatriculation']}"):
                retourner_vehicule(attr['immatriculation'])
                st.success(f"✅ {attr['immatriculation']} retourné !")
                st.rerun()
    else:
        st.info("✅ Aucun véhicule en service")

elif page == "⛽ Bons de carburant":
    st.title("⛽ Gestion des Bons de Carburant")
    
    st.subheader("📝 Générer un nouveau bon")
    
    attrib_actives = [a for a in attributions if not a.get('retourne')]
    
    col1, col2 = st.columns(2)
    service_bon = col1.selectbox("Service *", services)
    
    vh_service = [a['immatriculation'] for a in attrib_actives if a['service'] == service_bon]
    
    if vh_service:
        with st.form("form_bon"):
            col1, col2 = st.columns(2)
            with col1:
                vh_sel = st.selectbox("Véhicule *", [f"{v['immatriculation']} - {v['type']} {v['marque']}" 
                                                      for v in vehicules if v['immatriculation'] in vh_service])
            with col2:
                st.text("")
            
            col3, col4 = st.columns(2)
            with col3:
                date_bon = st.date_input("Date *", value=datetime.now())
            with col4:
                num_carte = st.text_input("N° Carte *", placeholder="1, 2, A...")
            
            col5, col6 = st.columns(2)
            with col5:
                conducteur_prenom = st.text_input("Prénom conducteur *", placeholder="Jean")
            with col6:
                conducteur_nom = st.text_input("Nom conducteur *", placeholder="Dupont")
            
            logo_url = st.text_input("URL du logo (optionnel)", placeholder="https://exemple.com/logo.png")
            notes = st.text_area("Notes", height=80)
            
            if st.form_submit_button("✅ Générer le bon"):
                if conducteur_nom and conducteur_prenom and num_carte:
                    immat = vh_sel.split(" - ")[0]
                    num_bon = f"BC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    bon = {
                        "numero_bon": num_bon,
                        "immatriculation": immat,
                        "service": service_bon,
                        "date": date_bon.strftime("%d/%m/%Y"),
                        "numero_carte": num_carte,
                        "conducteur_nom": conducteur_nom,
                        "conducteur_prenom": conducteur_prenom,
                        "type_carburant": "",
                        "volume": "0",
                        "montant": "0",
                        "notes": notes,
                        "statut": "Non saisi"
                    }
                    add_bon_carburant(bon)
                    
                    st.session_state.dernier_bon = {
                        'bon': bon,
                        'conducteur_nom': conducteur_nom,
                        'conducteur_prenom': conducteur_prenom,
                        'logo_url': logo_url
                    }
                    
                    st.success(f"✅ Bon {num_bon} généré !")
                    st.rerun()
                else:
                    st.error("❌ Veuillez remplir tous les champs obligatoires")
        
        if 'dernier_bon' in st.session_state:
            st.markdown("---")
            bon = st.session_state.dernier_bon['bon']
            conducteur_nom = st.session_state.dernier_bon['conducteur_nom']
            conducteur_prenom = st.session_state.dernier_bon['conducteur_prenom']
            logo_url = st.session_state.dernier_bon['logo_url']
            
            bon_html = f"""
            <div style="border: 2px solid #333; padding: 30px; border-radius: 10px; background: #fff; max-width: 600px; margin: auto;">
                <h2 style="text-align: center;">BON DE CARBURANT</h2>
                <hr>
                <p><strong>N° :</strong> {bon['numero_bon']}</p>
                <p style="font-size: 18px; color: #d9534f;"><strong>Carte N°{bon['numero_carte']}</strong></p>
                <p><strong>Véhicule :</strong> {bon['immatriculation']}</p>
                <p><strong>Service :</strong> {bon['service']}</p>
                <p><strong>Date :</strong> {bon['date']}</p>
                <p><strong>Conducteur :</strong> {conducteur_prenom} {conducteur_nom}</p>
                {f'<p><strong>Notes :</strong> {bon["notes"]}</p>' if bon.get('notes') else ''}
                <hr>
                <p style="text-align: center; font-style: italic; color: #666;">Volume, type et montant à saisir au retour</p>
            </div>
            """
            st.markdown(bon_html, unsafe_allow_html=True)
            
            pdf_buffer = generer_pdf_bon(bon, conducteur_nom, conducteur_prenom, logo_url if logo_url else None)
            st.download_button(
                label="📥 Télécharger le bon en PDF",
                data=pdf_buffer,
                file_name=f"bon_carburant_{bon['numero_bon']}.pdf",
                mime="application/pdf",
                type="primary"
            )
            
            st.info("💡 Vous pouvez aussi imprimer avec Ctrl+P (Cmd+P)")
            
            if st.button("🔄 Générer un nouveau bon"):
                del st.session_state.dernier_bon
                st.rerun()
    else:
        st.warning(f"⚠️ Aucun véhicule actuellement attribué au service {service_bon}")
        st.info("💡 Attribuez d'abord un véhicule à ce service dans la page 'Attribuer un véhicule'")
    
    st.markdown("---")
    st.subheader("📥 Saisir données bon retourné")
    
    non_saisis = [b for b in bons_carburant if b.get('statut') == "Non saisi"]
    
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
        # CORRECTION : Utilisation correcte de pd.to_numeric sur les colonnes
        bons_df['volume'] = pd.to_numeric(bons_df['volume'], errors='coerce').fillna(0)
        bons_df['montant'] = pd.to_numeric(bons_df['montant'], errors='coerce').fillna(0)
        bons_df['prix_litre'] = bons_df.apply(lambda r: round(r['montant'] / r['volume'], 3) if r['volume'] > 0 else 0, axis=1)
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
            emoji = "🔴" if interv.get('statut') == "En cours" else "✅" if interv.get('statut') == "Terminée" else "⏸️"
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

st.sidebar.caption("🚀 App avec Google Sheets")
