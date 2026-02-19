"""
Module de connexion et CRUD Google Sheets.
Gère toutes les opérations de base de données.
"""
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# CONNEXION GOOGLE SHEETS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_sheets_service():
    """Initialise et retourne le service Google Sheets."""
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build('sheets', 'v4', credentials=credentials)


def get_spreadsheet_id():
    """Retourne l'ID du spreadsheet depuis les secrets."""
    return st.secrets["google_sheets"]["spreadsheet_id"]


# Instance globale
sheets_service = get_sheets_service()
SPREADSHEET_ID = get_spreadsheet_id()


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE BASE (READ/WRITE)
# ═══════════════════════════════════════════════════════════════════════════════

def read_sheet(sheet_name):
    """Lit une feuille Google Sheets et retourne une liste de dictionnaires."""
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
    """Écrit des données dans une feuille Google Sheets."""
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
    """Initialise les feuilles Google Sheets requises si elles n'existent pas."""
    try:
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        existing_sheets = [s['properties']['title'] for s in sheet_metadata['sheets']]
        required_sheets = [
            'vehicules', 'attributions', 'categories', 'services', 'interventions',
            'carburant', 'engins', 'attributions_engins', 'categories_engins',
            'interventions_engins', 'scooters', 'attributions_scooters',
            'categories_scooters', 'interventions_scooters', 'liens'
        ]
        for sheet_name in required_sheets:
            if sheet_name not in existing_sheets:
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
                ).execute()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT BATCH AVEC CACHE
# ═══════════════════════════════════════════════════════════════════════════════

ALL_SHEET_NAMES = [
    'vehicules', 'attributions', 'categories', 'services', 'interventions',
    'carburant', 'engins', 'attributions_engins', 'categories_engins',
    'interventions_engins', 'scooters', 'attributions_scooters',
    'categories_scooters', 'interventions_scooters', 'liens'
]


@st.cache_data(ttl=60, show_spinner="Chargement des données...")
def _load_all_sheets():
    """Charge toutes les feuilles en un seul appel API."""
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
                data[ALL_SHEET_NAMES[i]] = [
                    dict(zip(headers, row + [''] * (len(headers) - len(row))))
                    for row in values[1:]
                ]
        return data
    except Exception:
        return {name: [] for name in ALL_SHEET_NAMES}


def load_data():
    """Retourne toutes les données chargées."""
    return _load_all_sheets()


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD VÉHICULES
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD ATTRIBUTIONS VÉHICULES
# ═══════════════════════════════════════════════════════════════════════════════

def get_attributions():
    return read_sheet('attributions')


def add_attribution(immat, service, date, heure, date_retour_prevue):
    attributions = get_attributions()
    attributions.append({
        'immatriculation': immat, 'service': service, 'date': date,
        'heure': heure, 'date_retour_prevue': date_retour_prevue, 'retourne': ''
    })
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


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD CATÉGORIES
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD SERVICES
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD INTERVENTIONS VÉHICULES
# ═══════════════════════════════════════════════════════════════════════════════

def get_interventions():
    return read_sheet('interventions')


def add_intervention(immat, type_i, date, heure, comm, statut):
    interventions = get_interventions()
    interventions.append({
        'immatriculation': immat, 'type': type_i, 'date': date,
        'heure': heure, 'commentaire': comm, 'statut': statut
    })
    write_sheet('interventions', interventions)


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD CARBURANT
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD LIENS
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD ENGINS
# ═══════════════════════════════════════════════════════════════════════════════

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
    """Retourne True si l'attribution couvre aujourd'hui."""
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
    attributions.append({
        'numero_serie': num_serie, 'service': service, 'date': date_debut,
        'date_fin': date_fin, 'periode': periode, 'retourne': ''
    })
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
    interventions.append({
        'numero_serie': num_serie, 'type': type_i, 'date': date,
        'heure': heure, 'commentaire': comm, 'statut': statut
    })
    write_sheet('interventions_engins', interventions)


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD SCOOTERS
# ═══════════════════════════════════════════════════════════════════════════════

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
    attributions.append({
        'immatriculation': immat, 'service': service, 'date': date,
        'heure': heure, 'date_retour_prevue': date_retour_prevue,
        'casque': casque, 'retourne': ''
    })
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
    interventions.append({
        'immatriculation': immat, 'type': type_i, 'date': date,
        'heure': heure, 'commentaire': comm, 'statut': statut
    })
    write_sheet('interventions_scooters', interventions)
