from django.core.mail import EmailMultiAlternatives
from django.conf import settings
<<<<<<< HEAD
=======
from django.utils.html import escape
>>>>>>> 1e7c075 (Security: prevent open-redirect, escape email body, validate Excel uploads, X-Forwarded-For opt-in, add CSP whitelist)
import logging
logger = logging.getLogger(__name__)

def get_entreprise_email():
    try:
        from apps.core.models import Parametre
        email = Parametre.get('EMAIL', '')
        nom   = Parametre.get('NOM_ENTREPRISE', 'GestiFlow')
        if email: return f'{nom} <{email}>'
    except Exception as e:
        logger.exception(f"Erreur dans get_entreprise_email: {e}")
    return settings.DEFAULT_FROM_EMAIL

<<<<<<< HEAD
def _send_with_pdf(destinataire, sujet, corps, pdf_bytes, filename, cc=None):
    expediteur = get_entreprise_email()
    corps_html = corps.replace('\n', '<br>')
    html_body  = f'<div style="font-family:Arial,sans-serif;font-size:14px;max-width:600px;margin:0 auto;"><div style="background:#1e3a5f;padding:20px 30px;border-radius:8px 8px 0 0;"><span style="color:white;font-size:20px;font-weight:bold;">GestiFlow</span></div><div style="background:#fff;padding:30px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;"><p>{corps_html}</p><hr><p style="font-size:12px;color:#94a3b8;">Ce message a ete envoye automatiquement par GestiFlow.</p></div></div>'
=======
def construire_corps_html(corps):
    """Return the escaped HTML body for an email based on plain `corps` text.
    This helper centralizes escaping (preventing HTML injection) and newline
    -> <br> conversion so it can be unit-tested.
    """
    corps_html = escape(corps).replace('\n', '<br>')
    html_body = (
        '<div style="font-family:Arial,sans-serif;font-size:14px;max-width:600px;margin:0 auto;"'
        '<div style="background:#1e3a5f;padding:20px 30px;border-radius:8px 8px 0 0;">'
        '<span style="color:white;font-size:20px;font-weight:bold;">GestiFlow</span></div>'
        '<div style="background:#fff;padding:30px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;">'
        f'<p>{corps_html}</p><hr><p style="font-size:12px;color:#94a3b8;">Ce message a ete envoye automatiquement par GestiFlow.</p></div></div>'
    )
    return html_body


def _send_with_pdf(destinataire, sujet, corps, pdf_bytes, filename, cc=None):
    expediteur = get_entreprise_email()
    html_body = construire_corps_html(corps)
>>>>>>> 1e7c075 (Security: prevent open-redirect, escape email body, validate Excel uploads, X-Forwarded-For opt-in, add CSP whitelist)
    msg = EmailMultiAlternatives(subject=sujet, body=corps, from_email=expediteur, to=[destinataire], cc=[cc] if cc else [])
    msg.attach_alternative(html_body, 'text/html')
    msg.attach(filename, pdf_bytes, 'application/pdf')
    msg.send(fail_silently=False)
    return True, f'Email envoye avec succes a {destinataire}'

def envoyer_facture_email(facture, destinataire, sujet, corps, cc=None):
    try:
        from apps.rapports.pdf_generator import generer_pdf_facture
        r = generer_pdf_facture(facture)
        return _send_with_pdf(destinataire, sujet, corps, r.content, f'facture_{facture.numero}.pdf', cc)
    except Exception as e:
        return False, f'Erreur : {str(e)[:100]}'

def envoyer_devis_email(devis, destinataire, sujet, corps, cc=None):
    try:
        from apps.rapports.pdf_generator import generer_pdf_devis
        r = generer_pdf_devis(devis)
        return _send_with_pdf(destinataire, sujet, corps, r.content, f'devis_{devis.numero}.pdf', cc)
    except Exception as e:
        return False, f'Erreur : {str(e)[:100]}'
