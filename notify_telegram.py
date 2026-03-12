#!/usr/bin/env python3
"""Résumé matinal de la flotte — envoi Telegram.

Lecture des secrets (par ordre de priorité) :
  1. Variables d'environnement (GitHub Actions)
  2. .streamlit/secrets.toml (usage local)
"""

import os
import sys
import json
import requests
from datetime import datetime


def load_secrets():
    """Charge les secrets depuis les env vars ou secrets.toml."""
    # Debug: affiche les clés d'env vars disponibles (sans les valeurs)
    print("ENV VARS disponibles (clés):", [k for k in os.environ if k in (
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'SPREADSHEET_ID', 'GCP_SERVICE_ACCOUNT_JSON'
    )])

    # 1. Variables d'environnement (GitHub Actions)
    if 'TELEGRAM_BOT_TOKEN' in os.environ:
        gcp_json = os.environ.get('GCP_SERVICE_ACCOUNT_JSON', '{}')
        return {
            'telegram': {
                'bot_token': os.environ['TELEGRAM_BOT_TOKEN'],
                'chat_id': os.environ['TELEGRAM_CHAT_ID'],
            },
            'google_sheets': {
                'spreadsheet_id': os.environ['SPREADSHEET_ID'],
            },
            'gcp_service_account': json.loads(gcp_json),
        }

    # 2. Fichier local .streamlit/secrets.toml
    secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.streamlit', 'secrets.toml')
    try:
        import tomllib
        with open(secrets_path, 'rb') as f:
            return tomllib.load(f)
    except ImportError:
        import toml
        return toml.load(secrets_path)


secrets = load_secrets()

from google.oauth2 import service_account
from googleapiclient.discovery import build


def get_service():
    creds = service_account.Credentials.from_service_account_info(
        secrets['gcp_service_account'],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return build('sheets', 'v4', credentials=creds)


def read_sheet(service, sheet_name):
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=secrets['google_sheets']['spreadsheet_id'],
            range=f"{sheet_name}!A:Z"
        ).execute()
        values = result.get('values', [])
        if not values or len(values) < 2:
            return []
        headers = values[0]
        return [dict(zip(headers, row + [''] * (len(headers) - len(row)))) for row in values[1:]]
    except Exception as e:
        print(f"Erreur lecture {sheet_name}: {e}")
        return []


def send_telegram(message):
    url = f"https://api.telegram.org/bot{secrets['telegram']['bot_token']}/sendMessage"
    resp = requests.post(url, json={
        'chat_id': secrets['telegram']['chat_id'],
        'text': message,
        'parse_mode': 'HTML'
    })
    return resp.ok


def is_engin_active(attr, today):
    if attr.get('retourne'):
        return False
    try:
        date_debut = datetime.strptime(attr['date'], "%d/%m/%Y").date()
        date_fin = datetime.strptime(attr.get('date_fin', attr['date']), "%d/%m/%Y").date()
        return date_debut <= today <= date_fin
    except Exception:
        return not attr.get('retourne')


def alerte_retour(attr, today):
    if attr.get('retourne'):
        return None
    date_str = attr.get('date_retour_prevue', '')
    if not date_str:
        return None
    try:
        jours = (datetime.strptime(date_str, "%d/%m/%Y").date() - today).days
        return jours if jours <= 2 else None
    except Exception:
        return None


def alerte_engin(attr, today):
    if attr.get('retourne'):
        return None
    date_str = attr.get('date_fin', '')
    if not date_str:
        return None
    try:
        date_fin = datetime.strptime(date_str, "%d/%m/%Y").date()
        return (today - date_fin).days if date_fin < today else None
    except Exception:
        return None


def main():
    today = datetime.now().date()

    service = get_service()
    attr_vh = read_sheet(service, 'attributions')
    attr_sco = read_sheet(service, 'attributions_scooters')
    attr_eng = read_sheet(service, 'attributions_engins')

    vh_actifs = [a for a in attr_vh if not a.get('retourne')]
    sco_actifs = [a for a in attr_sco if not a.get('retourne')]
    eng_actifs = [a for a in attr_eng if is_engin_active(a, today)]

    jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    mois_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
               "août", "septembre", "octobre", "novembre", "décembre"]
    date_label = f"{jours_fr[today.weekday()]} {today.day} {mois_fr[today.month - 1]} {today.year}"

    lines = [f"🚗 <b>Résumé flotte — {date_label}</b>\n"]

    lines.append(f"🚗 <b>Véhicules sortis ({len(vh_actifs)})</b>")
    if vh_actifs:
        for a in vh_actifs:
            lines.append(f"  • {a['immatriculation']} — {a.get('service', '?')} (retour: {a.get('date_retour_prevue', '?')})")
    else:
        lines.append("  Aucun véhicule sorti")

    lines.append(f"\n🛵 <b>Scooters sortis ({len(sco_actifs)})</b>")
    if sco_actifs:
        for a in sco_actifs:
            lines.append(f"  • {a['immatriculation']} — {a.get('service', '?')} (retour: {a.get('date_retour_prevue', '?')})")
    else:
        lines.append("  Aucun scooter sorti")

    lines.append(f"\n🚜 <b>Engins actifs ({len(eng_actifs)})</b>")
    if eng_actifs:
        for a in eng_actifs:
            periode = a.get('periode', '')
            suffix = f", {periode}" if periode else ""
            lines.append(f"  • {a['numero_serie']} — {a.get('service', '?')} (fin: {a.get('date_fin', '?')}{suffix})")
    else:
        lines.append("  Aucun engin actif")

    alertes = []
    for a in vh_actifs:
        j = alerte_retour(a, today)
        if j is not None:
            emoji = "🔴" if j <= 0 else "🟡"
            label = "en retard" if j < 0 else ("aujourd'hui" if j == 0 else f"dans {j} j")
            alertes.append(f"{emoji} VH {a['immatriculation']} — retour {label}")
    for a in sco_actifs:
        j = alerte_retour(a, today)
        if j is not None:
            emoji = "🔴" if j <= 0 else "🟡"
            label = "en retard" if j < 0 else ("aujourd'hui" if j == 0 else f"dans {j} j")
            alertes.append(f"{emoji} SCO {a['immatriculation']} — retour {label}")
    for a in attr_eng:
        j = alerte_engin(a, today)
        if j is not None:
            alertes.append(f"🔴 ENG {a['numero_serie']} — dépassé de {j} jour(s)")

    if alertes:
        lines.append(f"\n⚠️ <b>Alertes ({len(alertes)})</b>")
        for alerte in alertes:
            lines.append(f"  {alerte}")

    message = "\n".join(lines)

    if send_telegram(message):
        print("✅ Notification envoyée avec succès")
    else:
        print("❌ Erreur lors de l'envoi")
        sys.exit(1)


if __name__ == "__main__":
    main()
