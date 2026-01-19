import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import json

st.set_page_config(page_title="Gestion de Flotte", page_icon="🚗", layout="wide")

# CONNEXION BASE DE DONNÉES
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=st.secrets["database"]["host"],
        port=st.secrets["database"]["port"],
        database=st.secrets["database"]["database"],
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        cursor_factory=RealDictCursor,
        sslmode='require'
    )

def init_database():
    """Crée les tables si elles n'existent pas"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Table véhicules
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vehicules (
            immatriculation TEXT PRIMARY KEY,
            type TEXT,
            marque TEXT
        )
    """)
    
    # Table attributions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attributions (
            id SERIAL PRIMARY KEY,
            immatriculation TEXT,
            service TEXT,
            date TEXT,
            heure TEXT,
            retourne TEXT
        )
    """)
    
    # Table catégories
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            nom TEXT UNIQUE
        )
    """)
    
    # Table services
    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id SERIAL PRIMARY KEY,
            nom TEXT UNIQUE
        )
    """)
    
    # Table interventions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interventions (
            id SERIAL PRIMARY KEY,
            immatriculation TEXT,
            type TEXT,
            date TEXT,
            heure TEXT,
            commentaire TEXT,
            statut TEXT
        )
    """)
    
    # Table bons carburant
    cur.execute("""
        CREATE TABLE IF NOT EXISTS carburant (
            numero_bon TEXT PRIMARY KEY,
            immatriculation TEXT,
            service TEXT,
            date TEXT,
            numero_carte TEXT,
            type_carburant TEXT,
            volume REAL,
            montant REAL,
            notes TEXT,
            statut TEXT
        )
    """)
    
    conn.commit()
    cur.close()

# Initialiser la base
init_database()

# FONCTIONS CRUD
def get_vehicules():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vehicules ORDER BY immatriculation")
    result = cur.fetchall()
    cur.close()
    return [dict(row) for row in result]

def add_vehicule(immat, type_v, marque):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO vehicules (immatriculation, type, marque) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        (immat, type_v, marque)
    )
    conn.commit()
    cur.close()

def get_attributions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM attributions ORDER BY id DESC")
    result = cur.fetchall()
    cur.close()
    return [dict(row) for row in result]

def add_attribution(immat, service, date, heure):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO attributions (immatriculation, service, date, heure) VALUES (%s, %s, %s, %s)",
        (immat, service, date, heure)
    )
    conn.commit()
    cur.close()

def retourner_vehicule(immat):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE attributions SET retourne = %s WHERE immatriculation = %s AND retourne IS NULL",
        (datetime.now().strftime("%d/%m/%Y %H:%M"), immat)
    )
    conn.commit()
    cur.close()

def get_categories():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT nom FROM categories ORDER BY nom")
    result = cur.fetchall()
    cur.close()
    cats = [row['nom'] for row in result]
    if not cats:
        # Catégories par défaut
        defaults = ["Camion", "Fourgon", "Tractopelle", "Tondeuse", "Utilitaire", "Autre"]
        for cat in defaults:
            add_category(cat)
        return defaults
    return cats

def add_category(nom):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO categories (nom) VALUES (%s) ON CONFLICT DO NOTHING", (nom,))
    conn.commit()
    cur.close()

def delete_category(nom):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM categories WHERE nom = %s", (nom,))
    conn.commit()
    cur.close()

def get_services():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT nom FROM services ORDER BY nom")
    result = cur.fetchall()
    cur.close()
    srvs = [row['nom'] for row in result]
    if not srvs:
        defaults = ["Voirie", "Bâtiment", "Espaces verts"]
        for srv in defaults:
            add_service(srv)
        return defaults
    return srvs

def add_service(nom):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO services (nom) VALUES (%s) ON CONFLICT DO NOTHING", (nom,))
    conn.commit()
    cur.close()

def delete_service(nom):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM services WHERE nom = %s", (nom,))
    conn.commit()
    cur.close()

def get_interventions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interventions ORDER BY id DESC")
    result = cur.fetchall()
    cur.close()
    return [dict(row) for row in result]

def add_intervention(immat, type_i, date, heure, comm, statut):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO interventions (immatriculation, type, date, heure, commentaire, statut) VALUES (%s, %s, %s, %s, %s, %s)",
        (immat, type_i, date, heure, comm, statut)
    )
    conn.commit()
    cur.close()

def get_carburant():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM carburant ORDER BY numero_bon DESC")
    result = cur.fetchall()
    cur.close()
    return [dict(row) for row in result]

def add_bon_carburant(bon):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO carburant (numero_bon, immatriculation, service, date, numero_carte, 
           type_carburant, volume, montant, notes, statut) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (bon['numero_bon'], bon['immatriculation'], bon['service'], bon['date'], 
         bon['numero_carte'], bon['type_carburant'], bon['volume'], bon['montant'], 
         bon['notes'], bon['statut'])
    )
    conn.commit()
    cur.close()

def update_bon_carburant(numero_bon, type_carb, volume, montant):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE carburant SET type_carburant = %s, volume = %s, montant = %s, statut = 'Saisi' WHERE numero_bon = %s",
        (type_carb, volume, montant, numero_bon)
    )
    conn.commit()
    cur.close()

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
