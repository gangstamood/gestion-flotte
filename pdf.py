import io
import ipaddress
import socket
from urllib.parse import urlparse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _validate_logo_url(url):
    """Valide l'URL du logo pour prévenir les attaques SSRF."""
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return None
    hostname = parsed.hostname or ''
    # Bloquer localhost et variantes
    if hostname in ('localhost', '0.0.0.0', '::1', ''):
        return None
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            return None
    except ValueError:
        # C'est un hostname (pas une IP), résoudre pour vérifier
        try:
            resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
            for _, _, _, _, sockaddr in resolved:
                addr = ipaddress.ip_address(sockaddr[0])
                if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                    return None
        except socket.gaierror:
            return None
    return url


def generer_pdf_bon(bon, conducteur_nom, conducteur_prenom, logo_url=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    safe_logo_url = _validate_logo_url(logo_url)
    if safe_logo_url:
        try:
            c.drawImage(safe_logo_url, 50, height - 100, width=100, height=80, preserveAspectRatio=True)
        except Exception:
            pass
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 120, "BON DE CARBURANT")
    c.line(50, height - 140, width - 50, height - 140)
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
    c.drawCentredString(width/2, y, "Volume, type de carburant et montant a saisir au retour")
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 50, "Document genere automatiquement - Gestion de Flotte")
    c.save()
    buffer.seek(0)
    return buffer
