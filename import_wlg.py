"""
Import WLG26 — chariots, télescopiques, nacelles + attributions depuis le planning Excel.
Usage : python import_wlg.py
"""
import re
import os
import pandas as pd
import toml
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

XLSX_PATH = '/Users/alan/Downloads/PLANNING ENGINS WLG26 EN COURS.xlsx'
SECRETS_PATH = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')

TYPE_MAP = {
    'CHARIOT': 'Chariot 4X4 Diesel',
    'TELESCO': 'Télescopique',
    'NACELLE': 'Nacelle Diesel',
}


def fmt_date(val):
    if val is None:
        return ''
    try:
        if hasattr(val, 'strftime'):
            return val.strftime("%d/%m/%Y")
        return pd.to_datetime(val).strftime("%d/%m/%Y")
    except Exception:
        return ''


def connect():
    secrets = toml.load(SECRETS_PATH)
    creds = Credentials.from_service_account_info(
        dict(secrets['gcp_service_account']),
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    sid = secrets['google_sheets']['spreadsheet_id']
    svc = build('sheets', 'v4', credentials=creds)
    return svc, sid


def read_sheet(svc, sid, name):
    result = svc.spreadsheets().values().get(
        spreadsheetId=sid, range=f"{name}!A:Z"
    ).execute()
    rows = result.get('values', [])
    if not rows or len(rows) < 2:
        return []
    headers = rows[0]
    return [dict(zip(headers, row + [''] * max(0, len(headers) - len(row)))) for row in rows[1:]]


def write_sheet(svc, sid, name, data):
    svc.spreadsheets().values().clear(spreadsheetId=sid, range=f"{name}!A:Z").execute()
    if not data:
        return
    headers = list(data[0].keys())
    values = [headers] + [[str(row.get(h, '') or '') for h in headers] for row in data]
    svc.spreadsheets().values().update(
        spreadsheetId=sid, range=f"{name}!A1",
        valueInputOption='RAW', body={'values': values}
    ).execute()
    print(f"  ✅ {name} : {len(data)} lignes écrites")


def main():
    print("📖 Lecture du fichier Excel...")
    xl = pd.ExcelFile(XLSX_PATH)
    df = pd.read_excel(xl, sheet_name='PLANNING ENGINS WLG26', header=None)

    engins_to_add = []
    attributions_to_add = []

    for _, row in df.iloc[3:].iterrows():
        engin_id = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
        # Garder uniquement C1-C24, T1-T8, N1-N9
        if not re.match(r'^[CTN]\d+$', engin_id):
            continue

        type_raw = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ''
        taille = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
        utilisateur = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
        date_debut = fmt_date(row.iloc[6])
        date_fin = fmt_date(row.iloc[7])

        if not type_raw or type_raw == 'nan':
            continue

        type_norm = next((v for k, v in TYPE_MAP.items() if k in type_raw.upper()), type_raw)
        marque = taille if taille and taille != 'nan' else ''

        engins_to_add.append({
            'numero_serie': engin_id,
            'type': type_norm,
            'marque': marque,
        })

        if date_debut and date_fin and utilisateur and utilisateur != 'nan':
            attributions_to_add.append({
                'numero_serie': engin_id,
                'service': utilisateur,
                'date': date_debut,
                'date_fin': date_fin,
                'periode': 'Journée',
                'retourne': '',
            })

    print(f"  {len(engins_to_add)} engins à importer")
    print(f"  {len(attributions_to_add)} attributions à importer")

    print("\n🔌 Connexion Google Sheets...")
    svc, sid = connect()

    existing_engins = read_sheet(svc, sid, 'engins')
    existing_ids = {e.get('numero_serie') for e in existing_engins}
    existing_attrs = read_sheet(svc, sid, 'attributions_engins')
    existing_attr_keys = {(a.get('numero_serie'), a.get('date')) for a in existing_attrs}

    # Catégories
    cats = read_sheet(svc, sid, 'categories_engins')
    cat_noms = {c.get('nom') for c in cats}
    new_types = {e['type'] for e in engins_to_add} - cat_noms
    if new_types:
        cats += [{'nom': t} for t in sorted(new_types)]
        write_sheet(svc, sid, 'categories_engins', cats)
        print(f"  Catégories ajoutées : {sorted(new_types)}")

    # Engins
    new_engins = [e for e in engins_to_add if e['numero_serie'] not in existing_ids]
    if new_engins:
        write_sheet(svc, sid, 'engins', existing_engins + new_engins)
        print(f"  ✅ {len(new_engins)} engins ajoutés")
    else:
        print("  Engins : déjà présents, rien ajouté")

    # Attributions
    new_attrs = [a for a in attributions_to_add if (a['numero_serie'], a['date']) not in existing_attr_keys]
    if new_attrs:
        write_sheet(svc, sid, 'attributions_engins', existing_attrs + new_attrs)
        print(f"  ✅ {len(new_attrs)} attributions ajoutées")
    else:
        print("  Attributions : déjà présentes, rien ajouté")

    print("\n🎉 Import WLG26 terminé !")
    print(f"\n{'ID':5s} {'Type':22s} {'Taille':10s} {'Zone assignée'}")
    print("-" * 60)
    for e in engins_to_add:
        z = next((a['service'] for a in attributions_to_add if a['numero_serie'] == e['numero_serie']), '?')
        print(f"{e['numero_serie']:5s} {e['type']:22s} {e['marque']:10s} {z}")


if __name__ == '__main__':
    main()
