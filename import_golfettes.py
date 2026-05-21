"""
Import du planning golfettes WLG 2026 dans l'app Gestion de Flotte.
Source : WLG - Golfette 2026 - REPARTITION GOLFETTES 2026.pdf
Usage  : python3 import_golfettes.py
"""
import os
import toml
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SECRETS_PATH = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')

# ---------------------------------------------------------------------------
# Données extraites du PDF
# ---------------------------------------------------------------------------

GOLFETTES = [
    # (numero_serie, type, marque)
    ("G1",  "Cargo L",   ""),
    ("G2",  "Cargo L",   ""),
    ("G3",  "Cargo L",   ""),
    ("G4",  "Cargo L",   ""),
    ("G5",  "Cargo L",   ""),
    ("G6",  "Cargo L",   ""),
    ("G7",  "Cargo L",   ""),
    ("G8",  "4 places",  ""),
    ("G9",  "Cargo S",   ""),
    ("G10", "Cargo S",   ""),
    ("G11", "Cargo S",   ""),
    ("G12", "Cargo S",   ""),
    ("G13", "Cargo S",   ""),
    ("G14", "Cargo S",   ""),
    ("G15", "Cargo S",   ""),
    ("G16", "Cargo S",   ""),
    ("G17", "4 places",  ""),
    ("G18", "4 places",  ""),
    ("G19", "6 places",  ""),
    ("G20", "6 places",  ""),
    ("G21", "6 places",  ""),
    ("G22", "6 places",  ""),
    ("G23", "4 places",  ""),
]

# Attributions : (numero_serie, service, date_debut, date_fin)
# Pour les golfettes à affectation changeante, on crée plusieurs lignes.
ATTRIBUTIONS = [
    # G1 — Cargo L — 18/05 → 13/06
    ("G1",  "BARRIERES - LEA",          "18/05/2026", "13/06/2026"),

    # G2 — Cargo L — 13/05 → 12/06
    ("G2",  "ELECTRICITE - LENI",       "13/05/2026", "12/06/2026"),

    # G3 — Cargo L — 13/05 → 12/06
    ("G3",  "ELECTRICITE - LENI",       "13/05/2026", "12/06/2026"),

    # G4 — Cargo L — 25/05 → 13/06
    ("G4",  "AREMACS",                  "25/05/2026", "13/06/2026"),

    # G5 — Cargo L — 25/05 → 13/06 (3 phases : SCÉNO → AREMACS → SCÉNO)
    ("G5",  "SCÉNO - BEN",              "25/05/2026", "29/05/2026"),
    ("G5",  "AREMACS",                  "30/05/2026", "04/06/2026"),
    ("G5",  "SCÉNO - BEN",              "05/06/2026", "13/06/2026"),

    # G6 — Cargo L — 25/05 → 13/06 (SIGNA SCÉNO avec 3 jours bloqués 1-3 juin)
    ("G6",  "SIGNA SCÉNO - BEN",        "25/05/2026", "31/05/2026"),
    ("G6",  "SIGNA SCÉNO - BEN",        "04/06/2026", "13/06/2026"),

    # G7 — Cargo L — 01/06 → 09/06 (AA-CÉLINE puis MOBILIER-DAMIEN)
    ("G7",  "AA - CÉLINE",              "01/06/2026", "04/06/2026"),
    ("G7",  "MOBILIER - DAMIEN",        "05/06/2026", "09/06/2026"),

    # G8 — 4 places — 13/05 → 12/06 (DT multi-rôles, même équipe)
    ("G8",  "DT",                       "13/05/2026", "12/06/2026"),

    # G9 — Cargo S — 25/05 → 10/06 (SCÉNO PARTENAIRE → HAPPY → SCÉNO PARTENAIRES)
    ("G9",  "SCÉNO PARTENAIRE - BEN",   "25/05/2026", "31/05/2026"),
    ("G9",  "HAPPY",                    "01/06/2026", "04/06/2026"),
    ("G9",  "SCÉNO PARTENAIRES",        "05/06/2026", "10/06/2026"),

    # G10 — Cargo S — 18/05 → 13/06
    ("G10", "REGIE SITE - LEA",         "18/05/2026", "13/06/2026"),

    # G11 — Cargo S — 29/05 → 10/06
    ("G11", "ESPACE CONCEPT",           "29/05/2026", "10/06/2026"),

    # G12 — Cargo S — 25/05 → 13/06
    ("G12", "SCÈNES - EMILIE / THEO",   "25/05/2026", "13/06/2026"),

    # G13 — Cargo S — 30/05 → 11/06
    ("G13", "EQUIPE VOLANTE",           "30/05/2026", "11/06/2026"),

    # G14 — Cargo S — 30/05 → 11/06
    ("G14", "EQUIPE VOLANTE",           "30/05/2026", "11/06/2026"),

    # G15 — Cargo S — 22/05 → 09/06 (FOOD puis MOBILIER-DAMIEN)
    ("G15", "FOOD",                     "22/05/2026", "31/05/2026"),
    ("G15", "MOBILIER - DAMIEN",        "01/06/2026", "09/06/2026"),

    # G16 — Cargo S — 25/05 → 13/06
    ("G16", "PROD / REGIE",             "25/05/2026", "13/06/2026"),

    # G17 — 4 places — 03/06 → 09/06
    ("G17", "SECU",                     "03/06/2026", "09/06/2026"),

    # G18 — 4 places — 27/05 → 09/06
    ("G18", "PARTENAIRES - SIMON",      "27/05/2026", "09/06/2026"),

    # G19 — 6 places — 04/05 → 08/06
    ("G19", "ARTISTIQUE - JB",          "04/05/2026", "08/06/2026"),

    # G20 — 6 places — 04/05 → 08/06
    ("G20", "ARTISTIQUE - CLOTHILDE",   "04/05/2026", "08/06/2026"),

    # G21 — 6 places — 04/05 → 08/06
    ("G21", "ARTISTIQUE - SVEN",        "04/05/2026", "08/06/2026"),

    # G22 — 6 places — 30/05 → 09/06
    ("G22", "BAR - FLO",                "30/05/2026", "09/06/2026"),

    # G23 — 4 places — 03/06 → 09/06
    ("G23", "SPARE",                    "03/06/2026", "09/06/2026"),
]

CATEGORIES_GOLFETTES = ["Cargo L", "Cargo S", "4 places", "6 places"]


# ---------------------------------------------------------------------------
# Connexion / helpers
# ---------------------------------------------------------------------------

def connect():
    secrets = toml.load(SECRETS_PATH)
    creds_info = dict(secrets['gcp_service_account'])
    spreadsheet_id = secrets['google_sheets']['spreadsheet_id']
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    return service, spreadsheet_id


def ensure_sheets(svc, sid, sheet_names):
    meta = svc.spreadsheets().get(spreadsheetId=sid).execute()
    existing = {s['properties']['title'] for s in meta['sheets']}
    to_create = [n for n in sheet_names if n not in existing]
    if to_create:
        requests = [{"addSheet": {"properties": {"title": n}}} for n in to_create]
        svc.spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": requests}
        ).execute()
        print(f"  Feuilles créées : {to_create}")
    return existing | set(to_create)


def read_sheet(svc, sid, name):
    result = svc.spreadsheets().values().get(
        spreadsheetId=sid, range=f"{name}!A:Z"
    ).execute()
    rows = result.get('values', [])
    if not rows or len(rows) < 1:
        return []
    headers = rows[0]
    return [
        dict(zip(headers, row + [''] * max(0, len(headers) - len(row))))
        for row in rows[1:]
    ]


def write_sheet(svc, sid, name, data):
    if not data:
        return
    headers = list(data[0].keys())
    values = [headers] + [[str(row.get(h, '') or '') for h in headers] for row in data]
    svc.spreadsheets().values().update(
        spreadsheetId=sid,
        range=f'{name}!A1',
        valueInputOption='RAW',
        body={'values': values}
    ).execute()
    print(f"  ✅ {name} : {len(data)} lignes écrites")


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

def main():
    print("🔌 Connexion Google Sheets...")
    svc, sid = connect()
    print("  Connecté !\n")

    # --- Création des feuilles si absentes ---
    ensure_sheets(svc, sid, ['golfettes', 'attributions_golfettes', 'categories_golfettes', 'interventions_golfettes'])

    # --- Catégories golfettes ---
    existing_cats_g = read_sheet(svc, sid, 'categories_golfettes')
    existing_cat_g_noms = {c.get('nom', '') for c in existing_cats_g}
    new_cats_g = [{'nom': c} for c in CATEGORIES_GOLFETTES if c not in existing_cat_g_noms]
    if new_cats_g or not existing_cats_g:
        all_cats_g = [{'nom': c} for c in CATEGORIES_GOLFETTES]
        write_sheet(svc, sid, 'categories_golfettes', all_cats_g)
        print(f"  Catégories golfettes : {CATEGORIES_GOLFETTES}")
    else:
        print("  Catégories golfettes : déjà à jour")

    # --- Golfettes ---
    existing_golf = read_sheet(svc, sid, 'golfettes')
    existing_ids = {g.get('numero_serie', '') for g in existing_golf}
    new_golf = [
        {'numero_serie': g[0], 'type': g[1], 'marque': g[2]}
        for g in GOLFETTES
        if g[0] not in existing_ids
    ]
    if new_golf:
        all_golf = existing_golf + new_golf
        write_sheet(svc, sid, 'golfettes', all_golf)
        print(f"  {len(new_golf)} golfettes importées")
    else:
        print("  Golfettes : déjà présentes")

    # --- Attributions golfettes ---
    existing_attr = read_sheet(svc, sid, 'attributions_golfettes')
    existing_attr_keys = {
        (a.get('numero_serie', ''), a.get('date', ''), a.get('service', ''))
        for a in existing_attr
    }
    new_attr = []
    for (num, service, date_debut, date_fin) in ATTRIBUTIONS:
        key = (num, date_debut, service)
        if key not in existing_attr_keys:
            new_attr.append({
                'numero_serie': num,
                'service': service,
                'date': date_debut,
                'date_fin': date_fin,
                'periode': 'Journée',
                'retourne': '',
            })
    if new_attr:
        all_attr = existing_attr + new_attr
        write_sheet(svc, sid, 'attributions_golfettes', all_attr)
        print(f"  {len(new_attr)} attributions importées")
    else:
        print("  Attributions : déjà présentes")

    print("\n🎉 Import terminé !")
    print(f"   {len(GOLFETTES)} golfettes (G1-G23)")
    print(f"   {len(ATTRIBUTIONS)} lignes d'attribution")
    print("\n   Types : Cargo L, Cargo S, 4 places, 6 places")
    print("   Période : 04/05/2026 → 13/06/2026")


if __name__ == '__main__':
    main()
