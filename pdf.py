"""
Module de génération de PDF pour les bons de carburant.
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generer_pdf_bon(bon, conducteur_nom, conducteur_prenom, logo_url=None):
    """
    Génère un PDF pour un bon de carburant.

    Args:
        bon: Dictionnaire contenant les informations du bon
        conducteur_nom: Nom du conducteur
        conducteur_prenom: Prénom du conducteur
        logo_url: URL optionnelle d'un logo à inclure

    Returns:
        BytesIO: Buffer contenant le PDF généré
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Logo optionnel
    if logo_url:
        try:
            c.drawImage(logo_url, 50, height - 100, width=100, height=80, preserveAspectRatio=True)
        except Exception:
            pass

    # Titre
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 120, "BON DE CARBURANT")
    c.line(50, height - 140, width - 50, height - 140)

    # Informations du bon
    c.setFont("Helvetica-Bold", 12)
    y = height - 180
    c.drawString(80, y, f"N° de Bon : {bon['numero_bon']}")
    y -= 30

    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.8, 0.2, 0.2)
    c.drawString(80, y, f"Carte N°{bon['numero_carte']}")
    c.setFillColorRGB(0, 0, 0)
    y -= 40

    c.setFont("Helvetica", 12)
    c.drawString(80, y, f"Vehicule : {bon['immatriculation']}")
    y -= 25
    c.drawString(80, y, f"Service : {bon['service']}")
    y -= 25
    c.drawString(80, y, f"Date : {bon['date']}")
    y -= 25
    c.drawString(80, y, f"Conducteur : {conducteur_prenom} {conducteur_nom}")

    if bon.get('notes'):
        y -= 25
        c.drawString(80, y, f"Notes : {bon['notes']}")

    y -= 30
    c.line(50, y, width - 50, y)
    y -= 40

    c.setFont("Helvetica-Oblique", 11)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawCentredString(width / 2, y, "Volume, type de carburant et montant a saisir au retour")

    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 50, "Document genere automatiquement - Gestion de Flotte")

    c.save()
    buffer.seek(0)
    return buffer
