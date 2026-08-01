from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

def get_entreprise_email():
    try:
        from apps.core.models import Parametre
        email = Parametre.get('EMAIL', '')
        nom   = Parametre.get('NOM_ENTREPRISE', 'GestiFlow')
        if email: return f'{nom} <{email}>'
    except Exception: pass
    return settings.DEFAULT_FROM_EMAIL

def _send_with_pdf(destinataire, sujet, corps, pdf_bytes, filename, cc=None):
    expediteur = get_entreprise_email()
    corps_html = corps.replace('\n', '<br>')
    html_body  = f'<div style="font-family:Arial,sans-serif;font-size:14px;max-width:600px;margin:0 auto;"><div style="background:#1e3a5f;padding:20px 30px;border-radius:8px 8px 0 0;"><span style="color:white;font-size:20px;font-weight:bold;">GestiFlow</span></div><div style="background:#fff;padding:30px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;"><p>{corps_html}</p><hr><p style="font-size:12px;color:#94a3b8;">Ce message a ete envoye automatiquement par GestiFlow.</p></div></div>'
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
