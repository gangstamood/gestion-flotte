from datetime import datetime, timedelta


def _verifier_alertes_date_retour(attributions, id_key='immatriculation'):
    """Générique: véhicules/scooters avec date de retour prévue dans <= 2 jours."""
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
                        'immatriculation': attr[id_key],
                        'service': attr['service'],
                        'jours_restants': jours_restants,
                        'date_retour': date_retour_prevue,
                    })
        except Exception:
            continue
    return alertes


def verifier_alertes(attributions):
    """Véhicules avec date de retour prévue dans <= 2 jours."""
    return _verifier_alertes_date_retour(attributions)


def verifier_alertes_scooters(attributions):
    """Scooters avec date de retour prévue dans <= 2 jours."""
    return _verifier_alertes_date_retour(attributions)


def verifier_alertes_engins(attributions):
    """Engins dont la date de fin de période est dépassée et non retournés."""
    alertes = []
    today = datetime.now().date()
    for attr in attributions:
        if attr.get('retourne'):
            continue
        try:
            date_fin_str = attr.get('date_fin', '')
            if date_fin_str:
                date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y").date()
                if date_fin < today:
                    jours_retard = (today - date_fin).days
                    alertes.append({
                        'numero_serie': attr['numero_serie'],
                        'service': attr['service'],
                        'date_fin': date_fin_str,
                        'jours_retard': jours_retard,
                    })
            else:
                # Rétrocompat : anciennes attributions sans date_fin
                date_attrib = datetime.strptime(
                    f"{attr['date']} {attr.get('heure', '00:00')}", "%d/%m/%Y %H:%M"
                )
                duree = datetime.now() - date_attrib
                if duree > timedelta(hours=8):
                    alertes.append({
                        'numero_serie': attr['numero_serie'],
                        'service': attr['service'],
                        'date_fin': attr['date'],
                        'jours_retard': 0,
                    })
        except Exception:
            continue
    return alertes
