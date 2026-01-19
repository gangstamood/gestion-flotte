import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# ============================================================================
# CONFIGURATION DE LA PAGE
# ============================================================================
st.set_page_config(
    page_title="Gestion de Flotte",
    page_icon="🚗",
    layout="wide"
)

# ============================================================================
# FICHIERS DE SAUVEGARDE
# ============================================================================
FICHIER_VEHICULES = "vehicules.csv"
FICHIER_ATTRIBUTIONS = "attributions.csv"
FICHIER_CATEGORIES = "categories.csv"
FICHIER_INTERVENTIONS = "interventions.csv"
FICHIER_SERVICES = "services.csv"
FICHIER_CARBURANT = "carburant.csv"

# ============================================================================
# FONCTIONS DE SAUVEGARDE ET CHARGEMENT
# ============================================================================

def charger_vehicules():
    """Charge les véhicules depuis le fichier CSV s'il existe"""
    if os.path.exists(FICHIER_VEHICULES):
        try:
            df = pd.read_csv(FICHIER_VEHICULES)
            return df.to_dict('records')
        except:
            return []
    return []

def sauvegarder_vehicules(vehicules):
    """Sauvegarde automatique des véhicules dans un fichier CSV"""
    df = pd.DataFrame(vehicules)
    df.to_csv(FICHIER_VEHICULES, index=False)

def charger_attributions():
    """Charge les attributions depuis le fichier CSV s'il existe"""
    if os.path.exists(FICHIER_ATTRIBUTIONS):
        try:
            df = pd.read_csv(FICHIER_ATTRIBUTIONS)
            return df.to_dict('records')
        except:
            return []
    return []

def sauvegarder_attributions(attributions):
    """Sauvegarde automatique des attributions dans un fichier CSV"""
    df = pd.DataFrame(attributions)
    df.to_csv(FICHIER_ATTRIBUTIONS, index=False)

def charger_categories():
    """Charge les catégories personnalisées depuis le fichier CSV"""
    if os.path.exists(FICHIER_CATEGORIES):
        try:
            df = pd.read_csv(FICHIER_CATEGORIES)
            return df['categorie'].tolist()
        except:
            return ["Camion", "Fourgon", "Tractopelle", "Tondeuse", "Utilitaire", "Autre"]
    return ["Camion", "Fourgon", "Tractopelle", "Tondeuse", "Utilitaire", "Autre"]

def sauvegarder_categories(categories):
    """Sauvegarde les catégories personnalisées"""
    df = pd.DataFrame({'categorie': categories})
    df.to_csv(FICHIER_CATEGORIES, index=False)

def charger_interventions():
    """Charge les interventions/pannes depuis le fichier CSV"""
    if os.path.exists(FICHIER_INTERVENTIONS):
        try:
            df = pd.read_csv(FICHIER_INTERVENTIONS)
            return df.to_dict('records')
        except:
            return []
    return []

def sauvegarder_interventions(interventions):
    """Sauvegarde automatique des interventions dans un fichier CSV"""
    df = pd.DataFrame(interventions)
    df.to_csv(FICHIER_INTERVENTIONS, index=False)

def charger_services():
    """Charge les services personnalisés depuis le fichier CSV"""
    if os.path.exists(FICHIER_SERVICES):
        try:
            df = pd.read_csv(FICHIER_SERVICES)
            return df['service'].tolist()
        except:
            return ["Voirie", "Bâtiment", "Espaces verts"]
    return ["Voirie", "Bâtiment", "Espaces verts"]

def sauvegarder_services(services):
    """Sauvegarde les services personnalisés"""
    df = pd.DataFrame({'service': services})
    df.to_csv(FICHIER_SERVICES, index=False)

def charger_carburant():
    """Charge l'historique des bons de carburant depuis le fichier CSV"""
    if os.path.exists(FICHIER_CARBURANT):
        try:
            df = pd.read_csv(FICHIER_CARBURANT)
            return df.to_dict('records')
        except:
            return []
    return []

def sauvegarder_carburant(carburant):
    """Sauvegarde automatique des bons de carburant dans un fichier CSV"""
    df = pd.DataFrame(carburant)
    df.to_csv(FICHIER_CARBURANT, index=False)

def importer_depuis_excel(fichier_excel):
    """Importe les véhicules depuis un fichier Excel"""
    try:
        df = pd.read_excel(fichier_excel)
        df.columns = df.columns.str.lower().str.strip()
        
        colonnes_possibles = {
            'immatriculation': ['immatriculation', 'immat', 'plaque'],
            'type': ['type', 'type_vehicule', 'categorie'],
            'marque': ['marque', 'constructeur']
        }
        
        mapping = {}
        for cle, variantes in colonnes_possibles.items():
            for col in df.columns:
                if col in variantes:
                    mapping[col] = cle
                    break
        
        df = df.rename(columns=mapping)
        colonnes_requises = ['immatriculation', 'type', 'marque']
        colonnes_manquantes = [c for c in colonnes_requises if c not in df.columns]
        
        if colonnes_manquantes:
            return None, f"Colonnes manquantes : {', '.join(colonnes_manquantes)}"
        
        df = df[colonnes_requises]
        df = df.dropna(subset=['immatriculation'])
        vehicules = df.to_dict('records')
        
        return vehicules, None
    
    except Exception as e:
        return None, f"Erreur lors de l'importation : {str(e)}"

def verifier_fin_attributions():
    """Vérifie si des attributions arrivent à leur fin"""
    alertes = []
    for attr in st.session_state.attributions:
        try:
            date_str = attr['date']
            heure_str = attr['heure']
            date_attrib = datetime.strptime(f"{date_str} {heure_str}", "%d/%m/%Y %H:%M")
            maintenant = datetime.now()
            duree = maintenant - date_attrib
            
            if duree > timedelta(hours=8) and 'retourne' not in attr:
                alertes.append({
                    'immatriculation': attr['immatriculation'],
                    'service': attr['service'],
                    'date': attr['date'],
                    'heure': attr['heure'],
                    'duree_heures': int(duree.total_seconds() / 3600)
                })
        except:
            continue
    
    return alertes

# ============================================================================
# INITIALISATION DES DONNÉES
# ============================================================================
if 'categories' not in st.session_state:
    st.session_state.categories = charger_categories()

if 'services' not in st.session_state:
    st.session_state.services = charger_services()

if 'interventions' not in st.session_state:
    st.session_state.interventions = charger_interventions()

if 'carburant' not in st.session_state:
    st.session_state.carburant = charger_carburant()

if 'vehicules' not in st.session_state:
    vehicules_sauvegardes = charger_vehicules()
    if vehicules_sauvegardes:
        st.session_state.vehicules = vehicules_sauvegardes
    else:
        st.session_state.vehicules = [
            {"immatriculation": "AB-123-CD", "type": "Camion", "marque": "Renault"},
            {"immatriculation": "EF-456-GH", "type": "Tractopelle", "marque": "Caterpillar"},
            {"immatriculation": "IJ-789-KL", "type": "Fourgon", "marque": "Peugeot"},
        ]
        sauvegarder_vehicules(st.session_state.vehicules)

if 'attributions' not in st.session_state:
    attributions_sauvegardees = charger_attributions()
    if attributions_sauvegardees:
        st.session_state.attributions = attributions_sauvegardees
    else:
        st.session_state.attributions = [
            {"immatriculation": "AB-123-CD", "service": "Voirie", "date": datetime.now().strftime("%d/%m/%Y"), "heure": "08:30"},
            {"immatriculation": "IJ-789-KL", "service": "Espaces verts", "date": datetime.now().strftime("%d/%m/%Y"), "heure": "09:00"},
        ]
        sauvegarder_attributions(st.session_state.attributions)

# ============================================================================
# MENU LATÉRAL
# ============================================================================
st.sidebar.title("🚗 Menu Navigation")
page = st.sidebar.radio(
    "Choisir une page :",
    ["📊 Dashboard", "📥 Importer des véhicules", "➕ Saisir un véhicule", "🔧 Attribuer un véhicule", "⛽ Bons de Carburant", "🔨 Pannes & Interventions", "⚙️ Paramètres"]
)

st.sidebar.markdown("---")

alertes = verifier_fin_attributions()
if len(alertes) > 0:
    st.sidebar.error(f"🚨 {len(alertes)} véhicule(s) à retourner !")
    with st.sidebar.expander("Voir les alertes"):
        for alerte in alertes:
            st.warning(f"**{alerte['immatriculation']}** - {alerte['service']}\nSorti depuis {alerte['duree_heures']}h")

st.sidebar.markdown("---")
st.sidebar.success("💾 Sauvegarde automatique activée")

# ============================================================================
# PAGE 1 : DASHBOARD
# ============================================================================
if page == "📊 Dashboard":
    st.title("📊 Tableau de Bord - Gestion de Flotte")
    
    total_vehicules = len(st.session_state.vehicules)
    vehicules_sortis = len([attr for attr in st.session_state.attributions if 'retourne' not in attr])
    interventions_en_cours = len([i for i in st.session_state.interventions if i.get('statut') == "En cours"])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="🚙 Total Véhicules", value=total_vehicules)
    
    with col2:
        st.metric(label="🔑 Véhicules Sortis", value=vehicules_sortis)
    
    with col3:
        st.metric(label="🔨 Interventions en cours", value=interventions_en_cours)
    
    st.markdown("---")
    
    # --- SAISIR LES DONNÉES D'UN BON RETOURNÉ ---
    st.subheader("📥 Saisir les données d'un bon retourné")
    
    # Filtrer les bons non saisis
    bons_non_saisis = [b for b in st.session_state.carburant if b.get('statut') == "Non saisi"]
    
    if len(bons_non_saisis) > 0:
        with st.form("form_saisie_retour"):
            # Sélection du bon
            bons_list = [f"{b['numero_bon']} - {b['immatriculation']} - Carte N°{b['numero_carte']} - {b['date']}" for b in bons_non_saisis]
            bon_selectionne = st.selectbox("Sélectionner un bon à compléter *", bons_list)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                type_carburant = st.selectbox("Type de carburant *", ["Diesel", "Sans Plomb 95", "Sans Plomb 98", "GPL", "Électrique"])
            with col2:
                volume = st.number_input("Volume (litres) *", min_value=0.0, step=0.1, format="%.2f")
            with col3:
                montant = st.number_input("Montant (€) *", min_value=0.0, step=0.01, format="%.2f")
            
            submitted_saisie = st.form_submit_button("✅ Enregistrer les données")
            
            if submitted_saisie:
                if volume > 0:
                    # Extraire le numéro de bon
                    numero_bon_selectionne = bon_selectionne.split(" - ")[0]
                    
                    # Mettre à jour le bon
                    for bon in st.session_state.carburant:
                        if bon['numero_bon'] == numero_bon_selectionne:
                            bon['type_carburant'] = type_carburant
                            bon['volume'] = volume
                            bon['montant'] = montant
                            bon['statut'] = "Saisi"
                            break
                    
                    sauvegarder_carburant(st.session_state.carburant)
                    st.success(f"✅ Données enregistrées pour le bon {numero_bon_selectionne} !")
                    st.rerun()
                else:
                    st.error("❌ Le volume doit être supérieur à 0")
    else:
        st.info("✅ Tous les bons ont été saisis ou aucun bon en attente.")
    
    st.markdown("---")
    
    st.subheader("🔍 Filtres")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        types_disponibles = ["Tous"] + sorted(list(set([v['type'] for v in st.session_state.vehicules])))
        filtre_type = st.selectbox("Filtrer par type de véhicule", types_disponibles)
    
    with col_f2:
        filtre_service = st.selectbox("Filtrer par service", ["Tous"] + st.session_state.services)
    
    st.markdown("---")
    
    st.subheader("📋 Sorties du Jour")
    
    if len(st.session_state.attributions) > 0:
        df_attributions = pd.DataFrame(st.session_state.attributions)
        
        df_attributions['type'] = df_attributions['immatriculation'].apply(
            lambda x: next((v['type'] for v in st.session_state.vehicules if v['immatriculation'] == x), "")
        )
        df_attributions['marque'] = df_attributions['immatriculation'].apply(
            lambda x: next((v['marque'] for v in st.session_state.vehicules if v['immatriculation'] == x), "")
        )
        
        if filtre_type != "Tous":
            df_attributions = df_attributions[df_attributions['type'] == filtre_type]
        
        if filtre_service != "Tous":
            df_attributions = df_attributions[df_attributions['service'] == filtre_service]
        
        if len(df_attributions) > 0:
            services_a_afficher = st.session_state.services if filtre_service == "Tous" else [filtre_service]
            
            for service in services_a_afficher:
                df_service = df_attributions[df_attributions['service'] == service]
                
                if len(df_service) > 0:
                    st.markdown(f"### 🔹 {service}")
                    st.dataframe(
                        df_service[['immatriculation', 'type', 'marque', 'date', 'heure']],
                        use_container_width=True,
                        hide_index=True
                    )
                elif filtre_service == "Tous":
                    st.markdown(f"### 🔹 {service}")
                    st.info(f"Aucune sortie prévue pour {service}")
        else:
            st.warning("⚠️ Aucune attribution ne correspond aux filtres sélectionnés.")
    else:
        st.warning("⚠️ Aucune attribution enregistrée pour aujourd'hui.")
    
    st.markdown("---")
    
    st.subheader("🔙 Retourner un Véhicule")
    
    vehicules_sortis_list = [attr for attr in st.session_state.attributions if 'retourne' not in attr]
    
    if len(vehicules_sortis_list) > 0:
        col_r1, col_r2 = st.columns([3, 1])
        
        with col_r1:
            immat_a_retourner = st.selectbox(
                "Choisir un véhicule à retourner",
                [f"{v['immatriculation']} - {v['service']}" for v in vehicules_sortis_list]
            )
        
        with col_r2:
            if st.button("✅ Confirmer le retour", type="primary"):
                immat = immat_a_retourner.split(" - ")[0]
                
                for attr in st.session_state.attributions:
                    if attr['immatriculation'] == immat and 'retourne' not in attr:
                        attr['retourne'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        break
                
                sauvegarder_attributions(st.session_state.attributions)
                st.success(f"✅ Véhicule {immat} retourné avec succès !")
                st.rerun()
    else:
        st.info("Aucun véhicule en sortie actuellement.")

# ============================================================================
# PAGE 2 : IMPORTER
# ============================================================================
elif page == "📥 Importer des véhicules":
    st.title("📥 Importer des Véhicules depuis Excel")
    
    st.info("""
    **Format attendu :** Immatriculation, Type, Marque
    """)
    
    fichier_upload = st.file_uploader("Choisir un fichier Excel", type=['xlsx', 'xls'])
    
    if fichier_upload is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            btn_remplacer = st.button("🔄 Remplacer tous", type="primary")
        
        with col2:
            btn_ajouter = st.button("➕ Ajouter")
        
        if btn_remplacer:
            vehicules_importes, erreur = importer_depuis_excel(fichier_upload)
            
            if erreur:
                st.error(f"❌ {erreur}")
            else:
                st.session_state.vehicules = vehicules_importes
                sauvegarder_vehicules(st.session_state.vehicules)
                st.success(f"✅ {len(vehicules_importes)} véhicules importés !")
                st.rerun()
        
        if btn_ajouter:
            vehicules_importes, erreur = importer_depuis_excel(fichier_upload)
            
            if erreur:
                st.error(f"❌ {erreur}")
            else:
                immat_existantes = [v['immatriculation'] for v in st.session_state.vehicules]
                nouveaux = [v for v in vehicules_importes if v['immatriculation'] not in immat_existantes]
                
                st.session_state.vehicules.extend(nouveaux)
                sauvegarder_vehicules(st.session_state.vehicules)
                st.success(f"✅ {len(nouveaux)} véhicules ajoutés !")
                st.rerun()

# ============================================================================
# PAGE 3 : SAISIR UN VÉHICULE
# ============================================================================
elif page == "➕ Saisir un véhicule":
    st.title("➕ Ajouter un Nouveau Véhicule")
    
    with st.form("form_ajout_vehicule"):
        st.subheader("Informations du véhicule")
        
        immat = st.text_input("Immatriculation *", placeholder="Ex: AB-123-CD")
        type_vehicule = st.selectbox("Type de véhicule *", st.session_state.categories)
        marque = st.text_input("Marque *", placeholder="Ex: Renault, Peugeot...")
        
        submitted = st.form_submit_button("✅ Enregistrer le véhicule")
        
        if submitted:
            if immat and marque:
                immat_existantes = [v['immatriculation'] for v in st.session_state.vehicules]
                
                if immat in immat_existantes:
                    st.error("❌ Cette immatriculation existe déjà !")
                else:
                    nouveau_vehicule = {
                        "immatriculation": immat,
                        "type": type_vehicule,
                        "marque": marque
                    }
                    st.session_state.vehicules.append(nouveau_vehicule)
                    sauvegarder_vehicules(st.session_state.vehicules)
                    st.success(f"✅ Véhicule {immat} ajouté !")
            else:
                st.error("❌ Veuillez remplir tous les champs obligatoires")
    
    st.markdown("---")
    
    st.subheader("📋 Liste des véhicules")
    if len(st.session_state.vehicules) > 0:
        df_vehicules = pd.DataFrame(st.session_state.vehicules)
        st.dataframe(df_vehicules, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun véhicule enregistré.")

# ============================================================================
# PAGE 4 : ATTRIBUER
# ============================================================================
elif page == "🔧 Attribuer un véhicule":
    st.title("🔧 Attribuer un Véhicule à un Service")
    
    if len(st.session_state.vehicules) > 0:
        with st.form("form_attribution"):
            st.subheader("Détails de l'attribution")
            
            immat_choices = [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in st.session_state.vehicules]
            immat_selectionnee = st.selectbox("Choisir un véhicule *", immat_choices)
            
            service = st.selectbox("Service *", st.session_state.services)
            
            col1, col2 = st.columns(2)
            with col1:
                date_sortie = st.date_input("Date", value=datetime.now())
            with col2:
                heure_sortie = st.time_input("Heure", value=datetime.now().time())
            
            submitted = st.form_submit_button("✅ Confirmer l'attribution")
            
            if submitted:
                immat = immat_selectionnee.split(" - ")[0]
                
                nouvelle_attribution = {
                    "immatriculation": immat,
                    "service": service,
                    "date": date_sortie.strftime("%d/%m/%Y"),
                    "heure": heure_sortie.strftime("%H:%M")
                }
                st.session_state.attributions.append(nouvelle_attribution)
                sauvegarder_attributions(st.session_state.attributions)
                st.success(f"✅ Véhicule {immat} attribué !")
    else:
        st.warning("⚠️ Aucun véhicule enregistré.")
    
    st.markdown("---")
    
    st.subheader("📜 Historique")
    if len(st.session_state.attributions) > 0:
        df_attributions = pd.DataFrame(st.session_state.attributions)
        st.dataframe(df_attributions, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune attribution enregistrée.")

# ============================================================================
# PAGE 5 : BONS DE CARBURANT
# ============================================================================
elif page == "⛽ Bons de Carburant":
    st.title("⛽ Gestion des Bons de Carburant")
    
    # --- GÉNÉRER UN BON DE CARBURANT ---
    st.subheader("📝 Générer un Bon de Carburant")
    
    with st.form("form_bon_carburant"):
        col1, col2 = st.columns(2)
        
        with col1:
            if len(st.session_state.vehicules) > 0:
                vehicules_list = [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in st.session_state.vehicules]
                vehicule_selectionne = st.selectbox("Véhicule *", vehicules_list)
            else:
                st.warning("Aucun véhicule enregistré")
                vehicule_selectionne = None
        
        with col2:
            service_bon = st.selectbox("Service *", st.session_state.services)
        
        col3, col4 = st.columns(2)
        with col3:
            date_bon = st.date_input("Date *", value=datetime.now())
        with col4:
            numero_carte = st.text_input("N° de Carte *", placeholder="Ex: 1, 2, A, B...")
        
        notes = st.text_area("Notes / Observations", placeholder="Informations complémentaires...", height=80)
        
        submitted = st.form_submit_button("✅ Générer le bon de carburant")
        
        if submitted:
            if vehicule_selectionne and numero_carte:
                immat = vehicule_selectionne.split(" - ")[0]
                
                # Générer un numéro de bon unique
                numero_bon = f"BC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                nouveau_bon = {
                    "numero_bon": numero_bon,
                    "immatriculation": immat,
                    "service": service_bon,
                    "date": date_bon.strftime("%d/%m/%Y"),
                    "numero_carte": numero_carte,
                    "type_carburant": "",
                    "volume": 0.0,
                    "montant": 0.0,
                    "notes": notes,
                    "statut": "Non saisi"
                }
                
                st.session_state.carburant.append(nouveau_bon)
                sauvegarder_carburant(st.session_state.carburant)
                
                st.success(f"✅ Bon de carburant {numero_bon} généré avec succès !")
                
                # Afficher le bon généré
                st.markdown("---")
                st.markdown("### 📄 Bon de Carburant Généré")
                
                bon_html = f"""
                <div style="border: 2px solid #ccc; padding: 20px; border-radius: 10px; background-color: #f9f9f9;">
                    <h3 style="text-align: center;">BON DE CARBURANT</h3>
                    <hr>
                    <p><strong>N° de Bon :</strong> {numero_bon}</p>
                    <p><strong>Carte N°{numero_carte}</strong></p>
                    <p><strong>Véhicule :</strong> {immat}</p>
                    <p><strong>Service :</strong> {service_bon}</p>
                    <p><strong>Date :</strong> {date_bon.strftime("%d/%m/%Y")}</p>
                """
                
                if notes:
                    bon_html += f"<p><strong>Notes :</strong> {notes}</p>"
                
                bon_html += """
                    <hr>
                    <p style="text-align: center; font-style: italic;">Volume, type de carburant et montant à saisir au retour</p>
                </div>
                """
                
                st.markdown(bon_html, unsafe_allow_html=True)
                
            else:
                st.error("❌ Veuillez remplir tous les champs obligatoires")
    
    st.markdown("---")
    
    # --- HISTORIQUE DES BONS DE CARBURANT ---
    st.subheader("📋 Historique des Bons de Carburant")
    
    if len(st.session_state.carburant) > 0:
        # Filtres
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            vehicules_avec_bons = list(set([b['immatriculation'] for b in st.session_state.carburant]))
            filtre_vehicule_carb = st.selectbox("Filtrer par véhicule", ["Tous"] + sorted(vehicules_avec_bons), key="filtre_vh_carb")
        
        with col_f2:
            services_avec_bons = list(set([b['service'] for b in st.session_state.carburant]))
            filtre_service_carb = st.selectbox("Filtrer par service", ["Tous"] + sorted(services_avec_bons), key="filtre_srv_carb")
        
        with col_f3:
            types_carburant = list(set([b['type_carburant'] for b in st.session_state.carburant if b['type_carburant']]))
            filtre_type_carb = st.selectbox("Filtrer par carburant", ["Tous"] + sorted(types_carburant), key="filtre_type_carb")
        
        # Appliquer les filtres
        bons_filtres = st.session_state.carburant.copy()
        
        if filtre_vehicule_carb != "Tous":
            bons_filtres = [b for b in bons_filtres if b['immatriculation'] == filtre_vehicule_carb]
        
        if filtre_service_carb != "Tous":
            bons_filtres = [b for b in bons_filtres if b['service'] == filtre_service_carb]
        
        if filtre_type_carb != "Tous":
            bons_filtres = [b for b in bons_filtres if b['type_carburant'] == filtre_type_carb]
        
        # Afficher les statistiques
        if len(bons_filtres) > 0:
            # Séparer les bons saisis et non saisis
            bons_saisis = [b for b in bons_filtres if b.get('statut') == "Saisi"]
            bons_non_saisis_filtre = [b for b in bons_filtres if b.get('statut') == "Non saisi"]
            
            st.markdown("#### 📊 Statistiques")
            
            if len(bons_saisis) > 0:
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                
                total_volume = sum([b['volume'] for b in bons_saisis])
                total_montant = sum([b['montant'] for b in bons_saisis])
                nb_bons = len(bons_saisis)
                prix_moyen = total_montant / total_volume if total_volume > 0 else 0
                
                with col_stat1:
                    st.metric("Bons saisis", nb_bons)
                with col_stat2:
                    st.metric("Volume total", f"{total_volume:.2f} L")
                with col_stat3:
                    st.metric("Montant total", f"{total_montant:.2f} €")
                with col_stat4:
                    st.metric("Prix moyen/L", f"{prix_moyen:.3f} €")
            
            if len(bons_non_saisis_filtre) > 0:
                st.warning(f"⚠️ {len(bons_non_saisis_filtre)} bon(s) en attente de saisie")
            
            st.markdown("---")
            
            # Tableau des bons
            st.markdown("#### 📄 Liste des bons")
            
            df_bons = pd.DataFrame(bons_filtres)
            
            # Ajouter le prix au litre seulement pour les bons saisis
            df_bons['prix_litre'] = df_bons.apply(
                lambda row: round(row['montant'] / row['volume'], 3) if row['volume'] > 0 else 0, 
                axis=1
            )
            
            # Réorganiser les colonnes pour l'affichage
            colonnes_affichage = ['numero_bon', 'immatriculation', 'numero_carte', 'service', 'date', 'type_carburant', 'volume', 'montant', 'prix_litre', 'statut']
            df_bons_affichage = df_bons[colonnes_affichage]
            
            st.dataframe(df_bons_affichage, use_container_width=True, hide_index=True)
            
            # Option d'export
            st.markdown("---")
            st.markdown("#### 💾 Export des données")
            
            csv = df_bons_affichage.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger en CSV",
                data=csv,
                file_name=f"bons_carburant_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Aucun bon ne correspond aux filtres sélectionnés.")
    else:
        st.info("Aucun bon de carburant enregistré pour le moment.")

# ============================================================================
# PAGE 6 : PANNES & INTERVENTIONS
# ============================================================================
elif page == "🔨 Pannes & Interventions":
    st.title("🔨 Gestion des Pannes et Interventions")
    
    st.subheader("➕ Déclarer une Panne ou Intervention")
    
    with st.form("form_intervention"):
        col1, col2 = st.columns(2)
        
        with col1:
            if len(st.session_state.vehicules) > 0:
                vehicules_list = [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in st.session_state.vehicules]
                vehicule_selectionne = st.selectbox("Véhicule concerné *", vehicules_list)
            else:
                st.warning("Aucun véhicule enregistré")
                vehicule_selectionne = None
        
        with col2:
            type_intervention = st.selectbox("Type *", ["Panne", "Entretien", "Réparation", "Contrôle technique", "Autre"])
        
        col3, col4 = st.columns(2)
        with col3:
            date_intervention = st.date_input("Date *", value=datetime.now())
        with col4:
            heure_intervention = st.time_input("Heure *", value=datetime.now().time())
        
        commentaire = st.text_area("Commentaire / Description *", placeholder="Décrivez la panne ou l'intervention...", height=100)
        
        statut = st.selectbox("Statut", ["En cours", "Terminée", "En attente"])
        
        submitted = st.form_submit_button("✅ Enregistrer l'intervention")
        
        if submitted:
            if vehicule_selectionne and commentaire:
                immat = vehicule_selectionne.split(" - ")[0]
                
                nouvelle_intervention = {
                    "immatriculation": immat,
                    "type": type_intervention,
                    "date": date_intervention.strftime("%d/%m/%Y"),
                    "heure": heure_intervention.strftime("%H:%M"),
                    "commentaire": commentaire,
                    "statut": statut
                }
                
                st.session_state.interventions.append(nouvelle_intervention)
                sauvegarder_interventions(st.session_state.interventions)
                
                st.success(f"✅ Intervention enregistrée pour {immat} !")
                st.rerun()
            else:
                st.error("❌ Veuillez remplir tous les champs obligatoires")
    
    st.markdown("---")
    
    st.subheader("📋 Historique des Interventions")
    
    if len(st.session_state.interventions) > 0:
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            vehicules_avec_interventions = list(set([i['immatriculation'] for i in st.session_state.interventions]))
            filtre_vehicule = st.selectbox("Filtrer par véhicule", ["Tous"] + sorted(vehicules_avec_interventions))
        
        with col_f2:
            filtre_statut = st.selectbox("Filtrer par statut", ["Tous", "En cours", "Terminée", "En attente"])
        
        interventions_filtrees = st.session_state.interventions.copy()
        
        if filtre_vehicule != "Tous":
            interventions_filtrees = [i for i in interventions_filtrees if i['immatriculation'] == filtre_vehicule]
        
        if filtre_statut != "Tous":
            interventions_filtrees = [i for i in interventions_filtrees if i['statut'] == filtre_statut]
        
        if len(interventions_filtrees) > 0:
            for interv in reversed(interventions_filtrees):
                statut_emoji = "🔴" if interv['statut'] == "En cours" else "✅" if interv['statut'] == "Terminée" else "⏸️"
                
                with st.expander(f"{statut_emoji} {interv['immatriculation']} - {interv['type']} - {interv['date']} {interv['heure']}"):
                    st.write(f"**Véhicule :** {interv['immatriculation']}")
                    st.write(f"**Type :** {interv['type']}")
                    st.write(f"**Date :** {interv['date']} à {interv['heure']}")
                    st.write(f"**Statut :** {interv['statut']}")
                    st.write(f"**Commentaire :**")
                    st.info(interv['commentaire'])
        else:
            st.info("Aucune intervention ne correspond aux filtres.")
    else:
        st.info("Aucune intervention enregistrée.")

# ============================================================================
# PAGE 7 : PARAMÈTRES
# ============================================================================
elif page == "⚙️ Paramètres":
    st.title("⚙️ Paramètres de l'Application")
    
    # --- GESTION DES CATÉGORIES ---
    st.subheader("🏷️ Gestion des Catégories de Véhicules")
    
    st.markdown("#### Catégories actuelles :")
    
    for i, cat in enumerate(st.session_state.categories):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"• {cat}")
        with col2:
            if st.button("🗑️", key=f"delete_cat_{i}"):
                st.session_state.categories.pop(i)
                sauvegarder_categories(st.session_state.categories)
                st.rerun()
    
    st.markdown("---")
    
    st.markdown("#### Ajouter une nouvelle catégorie :")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        nouvelle_categorie = st.text_input("Nom de la catégorie", placeholder="Ex: Tracteur, Grue...", key="input_cat")
    
    with col2:
        st.write("")
        st.write("")
        if st.button("➕ Ajouter", type="primary", key="btn_cat"):
            if nouvelle_categorie and nouvelle_categorie not in st.session_state.categories:
                st.session_state.categories.append(nouvelle_categorie)
                sauvegarder_categories(st.session_state.categories)
                st.success(f"✅ Catégorie '{nouvelle_categorie}' ajoutée !")
                st.rerun()
            elif nouvelle_categorie in st.session_state.categories:
                st.error("❌ Cette catégorie existe déjà !")
            else:
                st.error("❌ Veuillez entrer un nom !")
    
    st.markdown("---")
    st.markdown("---")
    
    # --- GESTION DES SERVICES ---
    st.subheader("🏢 Gestion des Services")
    
    st.markdown("#### Services actuels :")
    
    for i, serv in enumerate(st.session_state.services):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"• {serv}")
        with col2:
            if st.button("🗑️", key=f"delete_serv_{i}"):
                st.session_state.services.pop(i)
                sauvegarder_services(st.session_state.services)
                st.rerun()
    
    st.markdown("---")
    
    st.markdown("#### Ajouter un nouveau service :")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        nouveau_service = st.text_input("Nom du service", placeholder="Ex: Assainissement, Propreté...", key="input_serv")
    
    with col2:
        st.write("")
        st.write("")
        if st.button("➕ Ajouter", type="primary", key="btn_serv"):
            if nouveau_service and nouveau_service not in st.session_state.services:
                st.session_state.services.append(nouveau_service)
                sauvegarder_services(st.session_state.services)
                st.success(f"✅ Service '{nouveau_service}' ajouté !")
                st.rerun()
            elif nouveau_service in st.session_state.services:
                st.error("❌ Ce service existe déjà !")
            else:
                st.error("❌ Veuillez entrer un nom !")

st.sidebar.markdown("---")
st.sidebar.caption("Application créée avec Streamlit 🚀")