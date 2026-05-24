import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

_TZ = ZoneInfo('Europe/Paris')
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
    'categories_golfettes', 'interventions_golfettes', 'parametres', 'contacts_wlg'
]

DISTRIB_EXT_ID = "1lHvCjEL-KZ0llBPKiZrWocOcHlcAoQkW5d72KShi1GY"


@st.cache_data(ttl=60, show_spinner="Chargement des données...")
def _load_all_sheets():
    ranges = [f"{name}!A:Z" for name in ALL_SHEET_NAMES]
    # Ne pas attraper les exceptions ici : si l'API échoue, Streamlit ne mettra
    # pas le résultat vide en cache et réessaiera à la prochaine interaction.
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


def read_sheet(sheet_name):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:Z"
    ).execute()
    values = result.get('values', [])
    if not values or len(values) < 2:
        return []
    headers = values[0]
    return [dict(zip(headers, row + [''] * (len(headers) - len(row)))) for row in values[1:]]


def _cached(sheet_name):
    """Lecture depuis le cache _load_all_sheets (0 appel API si cache valide)."""
    try:
        return _load_all_sheets().get(sheet_name, [])
    except Exception:
        return []


def write_sheet(sheet_name, data, prev_size=None):
    """Réécrit toute la feuille. Si prev_size est connu et <= len(data),
    on évite l'appel clear() résiduel (1 appel API au lieu de 2).
    """
    try:
        if not data:
            sheets_service.spreadsheets().values().clear(
                spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:Z"
            ).execute()
            return
        headers = list(dict.fromkeys(k for row in data for k in row.keys()))
        values = [headers] + [[row.get(h, '') for h in headers] for row in data]
        # 1. Écrire depuis A1 (données valides immédiatement)
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A1",
            valueInputOption="RAW", body={"values": values}
        ).execute()
        # 2. Supprimer les lignes résiduelles seulement si on a rétréci
        if prev_size is None or prev_size > len(data):
            try:
                sheets_service.spreadsheets().values().clear(
                    spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A{len(values) + 1}:Z10000"
                ).execute()
            except Exception:
                pass
    finally:
        _load_all_sheets.clear()


def append_row(sheet_name, row_dict):
    """Ajoute UNE ligne via l'API append (1 seul appel, beaucoup plus rapide
    qu'un read+rewrite complet). On infère les en-têtes depuis la 1re ligne
    existante pour préserver l'ordre des colonnes.
    """
    try:
        existing = _load_all_sheets().get(sheet_name, [])
        if existing:
            headers = list(dict.fromkeys(k for r in existing for k in r.keys()))
            # Ajouter les nouvelles clés à la fin si besoin
            for k in row_dict:
                if k not in headers:
                    headers.append(k)
        else:
            headers = list(row_dict.keys())
        row_values = [row_dict.get(h, '') for h in headers]
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row_values]}
        ).execute()
    finally:
        _load_all_sheets.clear()


DEFAULTS = {
    'categories':          ["Camion", "Fourgon", "Tractopelle", "Tondeuse", "Utilitaire", "Autre"],
    'services':            ["Voirie", "Bâtiment", "Espaces verts"],
    'categories_engins':   ["Tractopelle", "Tondeuse", "Compacteur", "Nacelle", "Mini-pelle", "Autre"],
    'categories_scooters': ["50cc", "125cc", "Électrique", "Autre"],
    'categories_golfettes':["Électrique", "Thermique", "Autre"],
}


@st.cache_resource
def init_database():
    """Crée les feuilles manquantes ET populate les défauts si elles sont vides.
    Tourne 1 fois par session (cache_resource) → pas d'appels API répétés.
    """
    required_sheets = ['vehicules', 'attributions', 'categories', 'services', 'interventions', 'carburant', 'engins', 'attributions_engins', 'categories_engins', 'interventions_engins', 'scooters', 'attributions_scooters', 'categories_scooters', 'interventions_scooters', 'liens', 'fiches_vehicules', 'distribution_clefs', 'golfettes', 'attributions_golfettes', 'categories_golfettes', 'interventions_golfettes', 'parametres', 'contacts_wlg']
    try:
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        existing_sheets = [s['properties']['title'] for s in sheet_metadata['sheets']]
        missing = [s for s in required_sheets if s not in existing_sheets]
        if missing:
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={"requests": [{"addSheet": {"properties": {"title": s}}} for s in missing]}
            ).execute()
        # Populate les défauts pour les feuilles vides (1 fois par session)
        for sheet_name, defaults in DEFAULTS.items():
            try:
                current = read_sheet(sheet_name)
                if not current:
                    write_sheet(sheet_name, [{'nom': v} for v in defaults])
            except Exception:
                pass
    except Exception:
        pass


# CRUD VÉHICULES
def get_vehicules():
    return _cached('vehicules')

AGENCES = ["Morlaix", "Lorient", "Rennes", "Quimper", "Brest"]

def add_vehicule(immat, type_v, marque, agence):
    if not any(v.get('immatriculation') == immat for v in _cached('vehicules')):
        append_row('vehicules', {'immatriculation': immat, 'type': type_v, 'marque': marque, 'agence': agence})

def delete_vehicule(immat):
    vehicules = _cached('vehicules')
    new = [v for v in vehicules if v.get('immatriculation') != immat]
    write_sheet('vehicules', new, prev_size=len(vehicules))

def get_fiches_vehicules():
    return _cached('fiches_vehicules')

def save_fiche_vehicule(immat, contrat_url, photos_entree, photos_sortie, notes):
    fiches = _cached('fiches_vehicules')
    data = {'immatriculation': immat, 'contrat_url': contrat_url, 'photos_entree': photos_entree, 'photos_sortie': photos_sortie, 'notes': notes}
    if any(f.get('immatriculation') == immat for f in fiches):
        new_fiches = [data if f.get('immatriculation') == immat else f for f in fiches]
        write_sheet('fiches_vehicules', new_fiches, prev_size=len(fiches))
    else:
        append_row('fiches_vehicules', data)

def get_attributions():
    return _cached('attributions')

def add_attribution(immat, service, date, heure, date_retour_prevue):
    append_row('attributions', {'immatriculation': immat, 'service': service, 'date': date, 'heure': heure, 'date_retour_prevue': date_retour_prevue, 'retourne': ''})

def retourner_vehicule(immat):
    attributions = _cached('attributions')
    for attr in reversed(attributions):
        if attr.get('immatriculation') == immat and not attr.get('retourne'):
            attr['retourne'] = datetime.now(_TZ).strftime("%d/%m/%Y %H:%M")
            break
    write_sheet('attributions', attributions, prev_size=len(attributions))

def update_attribution(idx, data):
    attributions = _cached('attributions')
    if 0 <= idx < len(attributions):
        attributions[idx].update(data)
        write_sheet('attributions', attributions, prev_size=len(attributions))

def delete_attribution(idx):
    attributions = _cached('attributions')
    if 0 <= idx < len(attributions):
        attributions.pop(idx)
        write_sheet('attributions', attributions, prev_size=len(attributions) + 1)


# CRUD CATÉGORIES & SERVICES
def get_categories():
    return [c.get('nom', '') for c in _cached('categories') if c.get('nom')]

def add_category(nom):
    if nom not in get_categories():
        append_row('categories', {'nom': nom})

def delete_category(nom):
    cats = get_categories()
    write_sheet('categories', [{'nom': c} for c in cats if c != nom], prev_size=len(cats))

def get_services():
    return [s.get('nom', '') for s in _cached('services') if s.get('nom')]

def add_service(nom):
    if nom not in get_services():
        append_row('services', {'nom': nom})

def delete_service(nom):
    srvs = get_services()
    write_sheet('services', [{'nom': s} for s in srvs if s != nom], prev_size=len(srvs))


# CRUD INTERVENTIONS VÉHICULES
def get_interventions():
    return _cached('interventions')

def add_intervention(immat, type_i, date, heure, comm, statut):
    append_row('interventions', {'immatriculation': immat, 'type': type_i, 'date': date, 'heure': heure, 'commentaire': comm, 'statut': statut})


# CRUD CARBURANT
def get_carburant():
    return _cached('carburant')

def add_bon_carburant(bon):
    append_row('carburant', bon)

def update_bon_carburant(numero_bon, type_carb, volume, montant):
    bons = _cached('carburant')
    for bon in bons:
        if bon.get('numero_bon') == numero_bon:
            bon['type_carburant'] = type_carb
            bon['volume'] = str(volume)
            bon['montant'] = str(montant)
            bon['statut'] = 'Saisi'
    write_sheet('carburant', bons, prev_size=len(bons))

def delete_bon_carburant(numero_bon):
    bons = _cached('carburant')
    new = [b for b in bons if b.get('numero_bon') != numero_bon]
    write_sheet('carburant', new, prev_size=len(bons))


# CRUD LIENS
def get_liens():
    return _cached('liens')

def add_lien(nom, url):
    if not any(l.get('nom') == nom for l in _cached('liens')):
        append_row('liens', {'nom': nom, 'url': url})

def delete_lien(nom):
    liens = _cached('liens')
    new = [l for l in liens if l.get('nom') != nom]
    write_sheet('liens', new, prev_size=len(liens))


# CRUD ENGINS
def get_engins():
    return _cached('engins')

def add_engin(num_serie, type_e, marque, numero_prestataire=""):
    if not any(e.get('numero_serie') == num_serie for e in _cached('engins')):
        append_row('engins', {'numero_serie': num_serie, 'type': type_e, 'marque': marque, 'numero_prestataire': numero_prestataire})

def update_engin_prestataire(num_serie, numero_prestataire):
    engins = _cached('engins')
    for e in engins:
        if e.get('numero_serie') == num_serie:
            e['numero_prestataire'] = numero_prestataire
            break
    write_sheet('engins', engins, prev_size=len(engins))

def delete_engin(num_serie):
    engins = _cached('engins')
    new = [e for e in engins if e.get('numero_serie') != num_serie]
    write_sheet('engins', new, prev_size=len(engins))

def get_attributions_engins():
    return _cached('attributions_engins')

def _is_engin_active_today(attr):
    """Retourne True si l'attribution couvre aujourd'hui (date_debut <= today <= date_fin)."""
    if attr.get('retourne'):
        return False
    try:
        today = datetime.now(_TZ).date()
        date_debut = datetime.strptime(attr['date'], "%d/%m/%Y").date()
        date_fin = datetime.strptime(attr.get('date_fin', attr['date']), "%d/%m/%Y").date()
        return date_debut <= today <= date_fin
    except Exception:
        return not attr.get('retourne')

def add_attribution_engin(num_serie, service, date_debut, date_fin, periode):
    append_row('attributions_engins', {'numero_serie': num_serie, 'service': service, 'date': date_debut, 'date_fin': date_fin, 'periode': periode, 'retourne': ''})

def retourner_engin(num_serie):
    attributions = _cached('attributions_engins')
    for attr in reversed(attributions):
        if attr.get('numero_serie') == num_serie and not attr.get('retourne'):
            attr['retourne'] = datetime.now(_TZ).strftime("%d/%m/%Y %H:%M")
            break
    write_sheet('attributions_engins', attributions, prev_size=len(attributions))

def update_attribution_engin(idx, data):
    attributions = _cached('attributions_engins')
    if 0 <= idx < len(attributions):
        attributions[idx].update(data)
        write_sheet('attributions_engins', attributions, prev_size=len(attributions))

def delete_attribution_engin(idx):
    attributions = _cached('attributions_engins')
    if 0 <= idx < len(attributions):
        attributions.pop(idx)
        write_sheet('attributions_engins', attributions, prev_size=len(attributions) + 1)

def get_categories_engins():
    return [c.get('nom', '') for c in _cached('categories_engins') if c.get('nom')]

def add_category_engin(nom):
    if nom not in get_categories_engins():
        append_row('categories_engins', {'nom': nom})

def delete_category_engin(nom):
    cats = get_categories_engins()
    write_sheet('categories_engins', [{'nom': c} for c in cats if c != nom], prev_size=len(cats))

def get_interventions_engins():
    return _cached('interventions_engins')

def add_intervention_engin(num_serie, type_i, date, heure, comm, statut, telephone="", horaires=""):
    append_row('interventions_engins', {'numero_serie': num_serie, 'type': type_i, 'date': date, 'heure': heure, 'commentaire': comm, 'statut': statut, 'telephone': telephone, 'horaires': horaires})


# CRUD SCOOTERS
def get_scooters():
    return _cached('scooters')

def add_scooter(immat, type_s, marque):
    if not any(s.get('immatriculation') == immat for s in _cached('scooters')):
        append_row('scooters', {'immatriculation': immat, 'type': type_s, 'marque': marque})

def delete_scooter(immat):
    scooters = _cached('scooters')
    new = [s for s in scooters if s.get('immatriculation') != immat]
    write_sheet('scooters', new, prev_size=len(scooters))

def get_attributions_scooters():
    return _cached('attributions_scooters')

def add_attribution_scooter(immat, service, date, heure, date_retour_prevue, casque=""):
    append_row('attributions_scooters', {'immatriculation': immat, 'service': service, 'date': date, 'heure': heure, 'date_retour_prevue': date_retour_prevue, 'casque': casque, 'retourne': ''})

def retourner_scooter(immat):
    attributions = _cached('attributions_scooters')
    for attr in reversed(attributions):
        if attr.get('immatriculation') == immat and not attr.get('retourne'):
            attr['retourne'] = datetime.now(_TZ).strftime("%d/%m/%Y %H:%M")
            break
    write_sheet('attributions_scooters', attributions, prev_size=len(attributions))

def update_attribution_scooter(idx, data):
    attributions = _cached('attributions_scooters')
    if 0 <= idx < len(attributions):
        attributions[idx].update(data)
        write_sheet('attributions_scooters', attributions, prev_size=len(attributions))

def delete_attribution_scooter(idx):
    attributions = _cached('attributions_scooters')
    if 0 <= idx < len(attributions):
        attributions.pop(idx)
        write_sheet('attributions_scooters', attributions, prev_size=len(attributions) + 1)

def get_categories_scooters():
    return [c.get('nom', '') for c in _cached('categories_scooters') if c.get('nom')]

def add_category_scooter(nom):
    if nom not in get_categories_scooters():
        append_row('categories_scooters', {'nom': nom})

def delete_category_scooter(nom):
    cats = get_categories_scooters()
    write_sheet('categories_scooters', [{'nom': c} for c in cats if c != nom], prev_size=len(cats))

def get_interventions_scooters():
    return _cached('interventions_scooters')

def add_intervention_scooter(immat, type_i, date, heure, comm, statut):
    append_row('interventions_scooters', {'immatriculation': immat, 'type': type_i, 'date': date, 'heure': heure, 'commentaire': comm, 'statut': statut})


# CRUD DISTRIBUTION CLEFS
def get_distribution_clefs():
    return _cached('distribution_clefs')

_RETOUR_COL = {
    'Clef engins':    'G',
    'Clef véhicules': 'E',
    'Clef golfettes': 'E',
}

def add_distribution_clef(categorie, identifiant, nom, commentaire):
    now = datetime.now(_TZ)
    ext_sheet, ext_row = _write_distrib_externe(categorie, identifiant, nom, commentaire, now)
    append_row('distribution_clefs', {
        'date': now.strftime("%d/%m/%Y"),
        'heure': now.strftime("%H:%M"),
        'categorie': categorie,
        'identifiant': identifiant,
        'nom': nom,
        'commentaire': commentaire,
        'retour_clef': '',
        'ext_sheet': ext_sheet,
        'ext_row': str(ext_row) if ext_row else ''
    })

def retour_clef(idx):
    clefs = _cached('distribution_clefs')
    if 0 <= idx < len(clefs):
        clefs[idx]['retour_clef'] = datetime.now(_TZ).strftime("%d/%m/%Y %H:%M")
        write_sheet('distribution_clefs', clefs, prev_size=len(clefs))
        _cocher_retour_externe(clefs[idx])

def delete_distribution_clef(idx):
    clefs = _cached('distribution_clefs')
    if 0 <= idx < len(clefs):
        clefs.pop(idx)
        write_sheet('distribution_clefs', clefs, prev_size=len(clefs) + 1)

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
    return _cached('golfettes')

def add_golfette(num_serie, type_g, marque):
    if not any(g.get('numero_serie') == num_serie for g in _cached('golfettes')):
        append_row('golfettes', {'numero_serie': num_serie, 'type': type_g, 'marque': marque})

def delete_golfette(num_serie):
    golfettes = _cached('golfettes')
    new = [g for g in golfettes if g.get('numero_serie') != num_serie]
    write_sheet('golfettes', new, prev_size=len(golfettes))

def get_attributions_golfettes():
    return _cached('attributions_golfettes')

def add_attribution_golfette(num_serie, service, date_debut, date_fin, periode):
    append_row('attributions_golfettes', {'numero_serie': num_serie, 'service': service, 'date': date_debut, 'date_fin': date_fin, 'periode': periode, 'retourne': ''})

def retourner_golfette(num_serie):
    attributions = _cached('attributions_golfettes')
    for attr in reversed(attributions):
        if attr.get('numero_serie') == num_serie and not attr.get('retourne'):
            attr['retourne'] = datetime.now(_TZ).strftime("%d/%m/%Y %H:%M")
            break
    write_sheet('attributions_golfettes', attributions, prev_size=len(attributions))

def update_attribution_golfette(idx, data):
    attributions = _cached('attributions_golfettes')
    if 0 <= idx < len(attributions):
        attributions[idx].update(data)
        write_sheet('attributions_golfettes', attributions, prev_size=len(attributions))

def delete_attribution_golfette(idx):
    attributions = _cached('attributions_golfettes')
    if 0 <= idx < len(attributions):
        attributions.pop(idx)
        write_sheet('attributions_golfettes', attributions, prev_size=len(attributions) + 1)

def get_categories_golfettes():
    return [c.get('nom', '') for c in _cached('categories_golfettes') if c.get('nom')]

def add_category_golfette(nom):
    if nom not in get_categories_golfettes():
        append_row('categories_golfettes', {'nom': nom})

def delete_category_golfette(nom):
    cats = get_categories_golfettes()
    write_sheet('categories_golfettes', [{'nom': c} for c in cats if c != nom], prev_size=len(cats))

def get_interventions_golfettes():
    return _cached('interventions_golfettes')

def add_intervention_golfette(num_serie, type_i, date, heure, comm, statut, telephone="", horaires=""):
    append_row('interventions_golfettes', {'numero_serie': num_serie, 'type': type_i, 'date': date, 'heure': heure, 'commentaire': comm, 'statut': statut, 'telephone': telephone, 'horaires': horaires})


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


# CRUD CONTACTS WLG
def get_contacts_wlg():
    return _cached('contacts_wlg')

def add_contact_wlg(categorie, nom, telephone, horaires):
    append_row('contacts_wlg', {'categorie': categorie, 'nom': nom, 'telephone': telephone, 'horaires': horaires})

def delete_contact_wlg(idx):
    contacts = _cached('contacts_wlg')
    if 0 <= idx < len(contacts):
        contacts.pop(idx)
        write_sheet('contacts_wlg', contacts, prev_size=len(contacts) + 1)


# CRUD PARAMÈTRES
def get_parametres():
    """Retourne un dict {cle: valeur} depuis le cache."""
    return {r['cle']: r.get('valeur', '') for r in _cached('parametres') if r.get('cle')}

def set_parametre(cle, valeur):
    """Crée ou met à jour une entrée dans la feuille parametres."""
    rows = _cached('parametres')
    for r in rows:
        if r.get('cle') == cle:
            r['valeur'] = valeur
            write_sheet('parametres', rows, prev_size=len(rows))
            return
    append_row('parametres', {'cle': cle, 'valeur': valeur})
