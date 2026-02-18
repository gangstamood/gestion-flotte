from datetime import datetime, timedelta


def verifier_alertes(attributions):
    """Véhicules avec date de retour prévue dans <= 2 jours."""
    alertes = []
    for attr in attributions:
        if attr.get('retourne'):
            continue
        try:
            date_retour_prevue = attr.get('date_retour_prevue', '')
            if date_retour_prevue:
                date_retour = datetime.strptime(date_retour_prevue, "%d/%m/%Y")
                jours_restants = (date_retour.date() - datetime.now().date()).days
                if jours_restants <= 2:
                    alertes.append({
                        'immatriculation': attr['immatriculation'],
                        'service': attr['service'],
                        'jours_restants': jours_restants,
                        'date_retour': date_retour_prevue,
                    })
        except Exception:
            continue
    return alertes


def verifier_alertes_scooters(attributions):
    """Scooters avec date de retour prévue dans <= 2 jours."""
    alertes = []
    for attr in attributions:
        if attr.get('retourne'):
            continue
        try:
            date_retour_prevue = attr.get('date_retour_prevue', '')
            if date_retour_prevue:
                date_retour = datetime.strptime(date_retour_prevue, "%d/%m/%Y")
                jours_restants = (date_retour.date() - datetime.now().date()).days
                if jours_restants <= 2:
                    alertes.append({
                        'immatriculation': attr['immatriculation'],
                        'service': attr['service'],
                        'jours_restants': jours_restants,
                        'date_retour': date_retour_prevue,
                    })
        except Exception:
            continue
    return alertes


def verifier_alertes_engins(attributions):
    """Engins en location depuis plus de 8 heures."""
    alertes = []
    for attr in attributions:
        if attr.get('retourne'):
            continue
        try:
            date_attrib = datetime.strptime(
                f"{attr['date']} {attr['heure']}", "%d/%m/%Y %H:%M"
            )
            duree = datetime.now() - date_attrib
            if duree > timedelta(hours=8):
                alertes.append({
                    'numero_serie': attr['numero_serie'],
                    'service': attr['service'],
                    'duree_heures': int(duree.total_seconds() / 3600),
                })
        except Exception:
            continue
    return alertes
