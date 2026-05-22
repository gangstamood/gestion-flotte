import streamlit as st
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build


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

ALL_SHEET_NAMES = [
    'vehicules', 'attributions', 'categories', 'services', 'interventions',
    'carburant', 'engins', 'attributions_engins', 'categories_engins',
    'interventions_engins', 'scooters', 'attributions_scooters',
    'categories_scooters', 'interventions_scooters', 'liens', 'fiches_vehicules',
    'distribution_clefs', 'golfettes', 'attributions_golfettes',
    'categories_golfettes', 'interventions_golfettes', 'parametres'
]

DISTRIB_EXT_ID = "1lHvCjEL-KZ0llBPKiZrWocOcHlcAoQkW5d72KShi1GY"


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
    headers = list(dict.fromkeys(k for row in data for k in row.keys()))
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
        required_sheets = ['vehicules', 'attributions', 'categories', 'services', 'interventions', 'carburant', 'engins', 'attributions_engins', 'categories_engins', 'interventions_engins', 'scooters', 'attributions_scooters', 'categories_scooters', 'interventions_scooters', 'liens', 'fiches_vehicules', 'distribution_clefs', 'golfettes', 'attributions_golfettes', 'categories_golfettes', 'interventions_golfettes', 'parametres']
        for sheet_name in required_sheets:
            if sheet_name not in existing_sheets:
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
                ).execute()
    except Exception:
        pass


# CRUD VÉHICULES
def get_vehicules():
    return read_sheet('vehicules')

AGENCES = ["Morlaix", "Lorient", "Rennes", "Quimper", "Brest"]

def add_vehicule(immat, type_v, marque, agence):
    vehicules = get_vehicules()
    if not any(v.get('immatriculation') == immat for v in vehicules):
        vehicules.append({'immatriculation': immat, 'type': type_v, 'marque': marque, 'agence': agence})
        write_sheet('vehicules', vehicules)

def delete_vehicule(immat):
    vehicules = [v for v in get_vehicules() if v.get('immatriculation') != immat]
    write_sheet('vehicules', vehicules)

def get_fiches_vehicules():
    return read_sheet('fiches_vehicules')

def save_fiche_vehicule(immat, contrat_url, photos_entree, photos_sortie, notes):
    fiches = get_fiches_vehicules()
    existing = next((f for f in fiches if f.get('immatriculation') == immat), None)
    data = {'immatriculation': immat, 'contrat_url': contrat_url, 'photos_entree': photos_entree, 'photos_sortie': photos_sortie, 'notes': notes}
    if existing:
        fiches = [data if f.get('immatriculation') == immat else f for f in fiches]
    else:
        fiches.append(data)
    write_sheet('fiches_vehicules', fiches)

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


# CRUD CATÉGORIES & SERVICES
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


# CRUD INTERVENTIONS VÉHICULES
def get_interventions():
    return read_sheet('interventions')

def add_intervention(immat, type_i, date, heure, comm, statut):
    interventions = get_interventions()
    interventions.append({'immatriculation': immat, 'type': type_i, 'date': date, 'heure': heure, 'commentaire': comm, 'statut': statut})
    write_sheet('interventions', interventions)


# CRUD CARBURANT
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


# CRUD LIENS
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


# CRUD ENGINS
def get_engins():
    return read_sheet('engins')

def add_engin(num_serie, type_e, marque, numero_prestataire=""):
    engins = get_engins()
    if not any(e.get('numero_serie') == num_serie for e in engins):
        engins.append({'numero_serie': num_serie, 'type': type_e, 'marque': marque, 'numero_prestataire': numero_prestataire})
        write_sheet('engins', engins)

def update_engin_prestataire(num_serie, numero_prestataire):
    engins = get_engins()
    for e in engins:
        if e.get('numero_serie') == num_serie:
            e['numero_prestataire'] = numero_prestataire
            break
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

def add_intervention_engin(num_serie, type_i, date, heure, comm, statut, telephone="", horaires=""):
    interventions = get_interventions_engins()
    interventions.append({'numero_serie': num_serie, 'type': type_i, 'date': date, 'heure': heure, 'commentaire': comm, 'statut': statut, 'telephone': telephone, 'horaires': horaires})
    write_sheet('interventions_engins', interventions)


# CRUD SCOOTERS
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


# CRUD DISTRIBUTION CLEFS
def get_distribution_clefs():
    return read_sheet('distribution_clefs')

_RETOUR_COL = {
    'Clef engins':    'G',
    'Clef véhicules': 'E',
    'Clef golfettes': 'E',
}

def add_distribution_clef(categorie, identifiant, nom, commentaire):
    now = datetime.now()
    ext_sheet, ext_row = _write_distrib_externe(categorie, identifiant, nom, commentaire, now)
    entry = {
        'date': now.strftime("%d/%m/%Y"),
        'heure': now.strftime("%H:%M"),
        'categorie': categorie,
        'identifiant': identifiant,
        'nom': nom,
        'commentaire': commentaire,
        'retour_clef': '',
        'ext_sheet': ext_sheet,
        'ext_row': str(ext_row) if ext_row else ''
    }
    clefs = get_distribution_clefs()
    clefs.append(entry)
    write_sheet('distribution_clefs', clefs)

def retour_clef(idx):
    clefs = get_distribution_clefs()
    if 0 <= idx < len(clefs):
        clefs[idx]['retour_clef'] = datetime.now().strftime("%d/%m/%Y %H:%M")
        write_sheet('distribution_clefs', clefs)
        _cocher_retour_externe(clefs[idx])

def delete_distribution_clef(idx):
    clefs = get_distribution_clefs()
    if 0 <= idx < len(clefs):
        clefs.pop(idx)
        write_sheet('distribution_clefs', clefs)

def _write_distrib_externe(categorie, identifiant, nom, commentaire, dt):
    try:
        date_str = dt.strftime("%d/%m/%Y")
        if categorie == 'engin':
            sheet_name = 'Clef engins'
            prefix = identifiant[0].upper() if identifiant else ''
            frontal = identifiant if prefix == 'C' else ''
            telesco = identifiant if prefix == 'T' else ''
            nacelle = identifiant if prefix == 'N' else ''
            if not frontal and not telesco and not nacelle:
                frontal = identifiant
            row = [date_str, frontal, telesco, nacelle, nom, commentaire, False]
        elif categorie == 'vehicule':
            sheet_name = 'Clef véhicules'
            row = [date_str, identifiant, nom, commentaire, False]
        elif categorie == 'golfette':
            sheet_name = 'Clef golfettes'
            row = [date_str, identifiant, nom, commentaire, False]
        else:
            return '', None
        result = sheets_service.spreadsheets().values().append(
            spreadsheetId=DISTRIB_EXT_ID,
            range=f"'{sheet_name}'!A:G",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]}
        ).execute()
        updated = result.get('updates', {}).get('updatedRange', '')
        row_num = None
        if updated:
            import re
            m = re.search(r':.*?(\d+)$', updated)
            if m:
                row_num = int(m.group(1))
        return sheet_name, row_num
    except Exception:
        return '', None

# CRUD GOLFETTES
def get_golfettes():
    return read_sheet('golfettes')

def add_golfette(num_serie, type_g, marque):
    golfettes = get_golfettes()
    if not any(g.get('numero_serie') == num_serie for g in golfettes):
        golfettes.append({'numero_serie': num_serie, 'type': type_g, 'marque': marque})
        write_sheet('golfettes', golfettes)

def delete_golfette(num_serie):
    golfettes = [g for g in get_golfettes() if g.get('numero_serie') != num_serie]
    write_sheet('golfettes', golfettes)

def get_attributions_golfettes():
    return read_sheet('attributions_golfettes')

def add_attribution_golfette(num_serie, service, date_debut, date_fin, periode):
    attributions = get_attributions_golfettes()
    attributions.append({'numero_serie': num_serie, 'service': service, 'date': date_debut, 'date_fin': date_fin, 'periode': periode, 'retourne': ''})
    write_sheet('attributions_golfettes', attributions)

def retourner_golfette(num_serie):
    attributions = get_attributions_golfettes()
    for attr in reversed(attributions):
        if attr.get('numero_serie') == num_serie and not attr.get('retourne'):
            attr['retourne'] = datetime.now().strftime("%d/%m/%Y %H:%M")
            break
    write_sheet('attributions_golfettes', attributions)

def update_attribution_golfette(idx, data):
    attributions = get_attributions_golfettes()
    if 0 <= idx < len(attributions):
        attributions[idx].update(data)
        write_sheet('attributions_golfettes', attributions)

def delete_attribution_golfette(idx):
    attributions = get_attributions_golfettes()
    if 0 <= idx < len(attributions):
        attributions.pop(idx)
        write_sheet('attributions_golfettes', attributions)

def get_categories_golfettes():
    cats = read_sheet('categories_golfettes')
    if not cats:
        defaults = [{'nom': c} for c in ["Électrique", "Thermique", "Autre"]]
        write_sheet('categories_golfettes', defaults)
        return ["Électrique", "Thermique", "Autre"]
    return [c.get('nom', '') for c in cats if c.get('nom')]

def add_category_golfette(nom):
    cats = get_categories_golfettes()
    if nom not in cats:
        write_sheet('categories_golfettes', [{'nom': c} for c in cats + [nom]])

def delete_category_golfette(nom):
    write_sheet('categories_golfettes', [{'nom': c} for c in get_categories_golfettes() if c != nom])

def get_interventions_golfettes():
    return read_sheet('interventions_golfettes')

def add_intervention_golfette(num_serie, type_i, date, heure, comm, statut, telephone="", horaires=""):
    interventions = get_interventions_golfettes()
    interventions.append({'numero_serie': num_serie, 'type': type_i, 'date': date, 'heure': heure, 'commentaire': comm, 'statut': statut, 'telephone': telephone, 'horaires': horaires})
    write_sheet('interventions_golfettes', interventions)


def _cocher_retour_externe(entry):
    try:
        sheet_name = entry.get('ext_sheet', '')
        ext_row = entry.get('ext_row', '')
        if not sheet_name or not ext_row:
            return
        col = _RETOUR_COL.get(sheet_name)
        if not col:
            return
        cell = f"'{sheet_name}'!{col}{ext_row}"
        sheets_service.spreadsheets().values().update(
            spreadsheetId=DISTRIB_EXT_ID,
            range=cell,
            valueInputOption="RAW",
            body={"values": [[True]]}
        ).execute()
    except Exception:
        pass
    except Exception:
        pass


# CRUD PARAMÈTRES
def get_parametres():
    """Retourne un dict {cle: valeur} depuis la feuille parametres."""
    rows = read_sheet('parametres')
    return {r['cle']: r.get('valeur', '') for r in rows if r.get('cle')}

def set_parametre(cle, valeur):
    """Crée ou met à jour une entrée dans la feuille parametres."""
    rows = read_sheet('parametres')
    for r in rows:
        if r.get('cle') == cle:
            r['valeur'] = valeur
            write_sheet('parametres', rows)
            return
    rows.append({'cle': cle, 'valeur': valeur})
    write_sheet('parametres', rows)
