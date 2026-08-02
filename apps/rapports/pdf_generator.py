"""
apps/rapports/pdf_generator.py
ReportLab-based PDF generation for GestiFlow.
Generates: Facture, Devis, Achat, Location, Tarif, Bilan Journalier
"""
from io import BytesIO
from decimal import Decimal
import logging

from django.http import HttpResponse
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Page dimensions ───────────────────────────────────────────
PAGE_W, PAGE_H = A4   # 210mm x 297mm

# ── Color palette ─────────────────────────────────────────────
C_PRIMARY = colors.HexColor('#1E3A5F')
C_SECONDARY = colors.HexColor('#2E75B6')
C_ACCENT  = colors.HexColor('#3B82F6')
C_SUCCESS = colors.HexColor('#10B981')
C_WARNING = colors.HexColor('#F59E0B')
C_DANGER  = colors.HexColor('#EF4444')
C_DARK    = colors.HexColor('#1A1A2E')
C_TEXT    = colors.HexColor('#1A1A2E')
C_MUTED   = colors.HexColor('#6B7280')
C_LIGHT   = colors.HexColor('#F0F4FA')
C_WHITE   = colors.HexColor('#FFFFFF')
C_BORDER  = colors.HexColor('#D9D9D9')

logger = logging.getLogger(__name__)


def cfg():
    """Returns company config from Parametre DB first, then .env fallback."""
    base = getattr(settings, 'GESTIFLOW', {})
    def get_param(cle, env_key, default=''):
        try:
            from apps.core.models import Parametre
            val = Parametre.get(cle, '')
            if val: return val
        except Exception as e:
            logger.exception(f"Erreur dans pdf_generator.cfg (parametre {cle}): {e}")
        return base.get(env_key, default)
    return {
        'nom':    get_param('NOM_ENTREPRISE', 'NOM_ENTREPRISE', 'Mon Entreprise'),
        'adresse':get_param('ADRESSE',        'ADRESSE',        ''),
        'tel':    get_param('TELEPHONE',      'TELEPHONE',      ''),
        'email':  get_param('EMAIL',          'EMAIL',          ''),
        'devise': get_param('DEVISE',         'DEVISE',         'DA'),
        'logo':   get_param('LOGO',           'LOGO',           ''),
    }


class PDFDoc:
    """ReportLab canvas wrapper for GestiFlow documents."""

    def __init__(self, buf, title='GestiFlow Document'):
        self.buf   = buf
        self.c     = canvas.Canvas(buf, pagesize=A4)
        self.c.setTitle(title)
        self.m     = 15 * mm          # margin
        self.y     = PAGE_H - 15 * mm # current Y position
        self.usable_w = PAGE_W - 2 * self.m
        self.ent   = cfg()

    # ── Primitives ────────────────────────────────────────────
    def text(self, x, y, txt, font='Helvetica', size=9, color=None, align='left'):
        if color is None: color = C_TEXT
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        if align == 'right':
            self.c.drawRightString(x, y, str(txt))
        elif align == 'center':
            self.c.drawCentredString(x, y, str(txt))
        else:
            self.c.drawString(x, y, str(txt))

    def rect(self, x, y, w, h, fill_color=None, stroke_color=None, stroke_width=0):
        self.c.saveState()
        if fill_color:
            self.c.setFillColor(fill_color)
        if stroke_color:
            self.c.setStrokeColor(stroke_color)
            self.c.setLineWidth(stroke_width or 0.5)
        self.c.rect(x, y, w, h,
                    fill=1 if fill_color else 0,
                    stroke=1 if stroke_color else 0)
        self.c.restoreState()

    def line(self, x1, y1, x2, y2, color=None, width=0.5):
        self.c.saveState()
        self.c.setStrokeColor(color or C_BORDER)
        self.c.setLineWidth(width)
        self.c.line(x1, y1, x2, y2)
        self.c.restoreState()

    def check_space(self, needed):
        """Start new page if not enough vertical space."""
        if self.y < (self.m + needed):
            self.draw_footer()
            self.c.showPage()
            self.y = PAGE_H - 15 * mm
            self.draw_page_header_stripe()

    def draw_page_header_stripe(self):
        """Thin primary stripe at top of continuation pages."""
        self.rect(0, PAGE_H - 3 * mm, PAGE_W, 3 * mm, fill_color=C_PRIMARY)

    # ── Document header ───────────────────────────────────────
    def draw_header(self, titre_doc, numero, date_str, echeance_str=None):
        top = self.y
        self.rect(0, PAGE_H - 3 * mm, PAGE_W, 3 * mm, fill_color=C_PRIMARY)

        # Left: document info
        self.text(self.m, top - 10 * mm, titre_doc,
                  font='Helvetica-Bold', size=28, color=C_PRIMARY)
        self.text(self.m, top - 17 * mm, f'N\u00b0 {numero}',
                  font='Helvetica-Bold', size=11, color=C_TEXT)
        self.text(self.m, top - 22 * mm, f'Date : {date_str}',
                  font='Helvetica', size=9, color=C_MUTED)
        if echeance_str:
            self.text(self.m, top - 27 * mm, f'\u00c9ch\u00e9ance : {echeance_str}',
                      font='Helvetica', size=9, color=C_MUTED)

        # Right: logo or company name
        rx = PAGE_W - self.m
        logo_path = self.ent.get('logo', '')
        logo_drawn = False

        if logo_path:
            import os as _os
            from django.conf import settings as dj_s
            abs_logo = (_os.path.join(dj_s.MEDIA_ROOT, logo_path[len('/media/'):])
                        if logo_path.startswith('/media/') else logo_path)
            if _os.path.isfile(abs_logo):
                try:
                    from reportlab.lib.utils import ImageReader
                    img   = ImageReader(abs_logo)
                    img_w = 50 * mm
                    img_h = 18 * mm
                    img_x = rx - img_w
                    img_y = top - img_h - 5 * mm
                    self.c.drawImage(img, img_x, img_y,
                                     width=img_w, height=img_h,
                                     preserveAspectRatio=True,
                                     anchor='c', mask='auto')
                    self.text(rx, img_y - 5 * mm, self.ent['nom'],
                              font='Helvetica-Bold', size=10,
                              color=C_TEXT, align='right')
                    logo_drawn = True
                except Exception as e:
                    logger.exception(f"Erreur lors du dessin du logo dans le PDF: {e}")

        if not logo_drawn:
            self.text(rx, top - 10 * mm, self.ent['nom'],
                      font='Helvetica-Bold', size=11,
                      color=C_TEXT, align='right')
            y_ent = top - 15 * mm
            for line_txt in [self.ent.get('adresse',''),
                              self.ent.get('tel',''),
                              self.ent.get('email','')]:
                if line_txt:
                    self.text(rx, y_ent, line_txt,
                              font='Helvetica', size=8,
                              color=C_MUTED, align='right')
                    y_ent -= 4 * mm

        sep_y = top - 32 * mm
        self.line(self.m, sep_y, PAGE_W - self.m, sep_y,
                  color=C_PRIMARY, width=1.5)
        self.y = sep_y - 5 * mm

    # ── Client block ──────────────────────────────────────────
    def draw_client_bloc(self, client, statut_label=None, statut_color=None,
                          vendeur=None):
        y0 = self.y
        # Left box: client info
        box_w = self.usable_w * 0.5 - 3 * mm
        self.rect(self.m, y0 - 35 * mm, box_w, 35 * mm,
                  fill_color=colors.HexColor('#F8FAFC'),
                  stroke_color=C_BORDER, stroke_width=0.3)

        self.text(self.m + 3 * mm, y0 - 5 * mm,
                  'FACTUR\u00c9 \u00c0', font='Helvetica', size=7, color=C_MUTED)
        self.text(self.m + 3 * mm, y0 - 10 * mm,
                  client.nom, font='Helvetica-Bold', size=11, color=C_TEXT)
        y_c = y0 - 15 * mm
        for line_txt in [f'Code : {client.code}',
                          client.telephone or '',
                          client.email or '',
                          client.adresse_complete or '']:
            if line_txt:
                self.text(self.m + 3 * mm, y_c, line_txt,
                          font='Helvetica', size=8, color=C_TEXT)
                y_c -= 5 * mm

        # Right box: status & vendor
        rx = self.m + box_w + 6 * mm
        rw = self.usable_w * 0.5 - 3 * mm
        self.rect(rx, y0 - 35 * mm, rw, 35 * mm,
                  fill_color=colors.HexColor('#F8FAFC'),
                  stroke_color=C_BORDER, stroke_width=0.3)

        if statut_label:
            sc = statut_color or C_SUCCESS
            self.rect(rx + 3 * mm, y0 - 14 * mm,
                      rw - 6 * mm, 10 * mm, fill_color=sc)
            self.text(rx + rw / 2, y0 - 10 * mm,
                      statut_label.upper(),
                      font='Helvetica-Bold', size=10,
                      color=C_WHITE, align='center')

        if vendeur:
            self.text(rx + 3 * mm, y0 - 20 * mm,
                      'VENDEUR', font='Helvetica', size=7, color=C_MUTED)
            self.text(rx + 3 * mm, y0 - 25 * mm,
                      vendeur.get_full_name() or vendeur.username,
                      font='Helvetica', size=9, color=C_TEXT)

        self.y = y0 - 40 * mm

    # ── Fournisseur block ─────────────────────────────────────
    def draw_fournisseur_bloc(self, fournisseur):
        y0    = self.y
        box_w = self.usable_w * 0.5 - 3 * mm
        self.rect(self.m, y0 - 30 * mm, box_w, 30 * mm,
                  fill_color=colors.HexColor('#F8FAFC'),
                  stroke_color=C_BORDER, stroke_width=0.3)
        self.text(self.m + 3 * mm, y0 - 5 * mm,
                  'FOURNISSEUR', font='Helvetica', size=7, color=C_MUTED)
        self.text(self.m + 3 * mm, y0 - 10 * mm,
                  fournisseur.nom, font='Helvetica-Bold', size=11, color=C_TEXT)
        y_f = y0 - 15 * mm
        for t in [fournisseur.telephone or '',
                  fournisseur.email or '',
                  fournisseur.adresse_complete or '']:
            if t:
                self.text(self.m + 3 * mm, y_f, t,
                          font='Helvetica', size=8, color=C_TEXT)
                y_f -= 5 * mm
        self.y = y0 - 35 * mm

    # ── Lines table (with text wrapping) ──────────────────────
    def draw_lignes_table(self, lignes):
        col_desig  = self.usable_w * 0.38
        col_qty    = self.usable_w * 0.09
        col_pu     = self.usable_w * 0.13
        col_remise = self.usable_w * 0.10
        col_tva    = self.usable_w * 0.08
        col_total  = self.usable_w * 0.22
        col_widths = [col_desig, col_qty, col_pu, col_remise, col_tva, col_total]

        # Header
        header_h = 8 * mm
        self.rect(self.m, self.y - header_h, self.usable_w, header_h,
                  fill_color=C_PRIMARY)
        headers = [('D\u00e9signation','left'),('Qt\u00e9','center'),
                   ('PU HT','right'),('Remise','center'),
                   ('TVA','center'),('Total HT','right')]
        lx = self.m
        for (label, align), cw in zip(headers, col_widths):
            y_t = self.y - header_h/2 - 2.5*mm
            if align == 'right':
                self.text(lx+cw-2*mm, y_t, label, font='Helvetica-Bold',
                          size=8.5, color=C_WHITE, align='right')
            elif align == 'center':
                self.text(lx+cw/2, y_t, label, font='Helvetica-Bold',
                          size=8.5, color=C_WHITE, align='center')
            else:
                self.text(lx+2*mm, y_t, label, font='Helvetica-Bold',
                          size=8.5, color=C_WHITE)
            lx += cw
        self.y -= header_h

        # Rows
        st_desig = ParagraphStyle('d', fontName='Helvetica-Bold',
                                  fontSize=8.5, leading=11, wordWrap='LTR')
        st_desc  = ParagraphStyle('dd', fontName='Helvetica', fontSize=7.5,
                                  leading=10, textColor=C_MUTED, wordWrap='LTR')

        for i, ligne in enumerate(lignes):
            desig_txt = str(ligne.designation or '')
            desc_txt  = str(getattr(ligne, 'description', '') or '')

            p_d = Paragraph(desig_txt, st_desig)
            p_d.wrap(col_desig - 4*mm, 200*mm)
            h_d = p_d.height

            h_dd = 0
            p_dd = None
            if desc_txt:
                p_dd = Paragraph(desc_txt, st_desc)
                p_dd.wrap(col_desig - 4*mm, 200*mm)
                h_dd = p_dd.height + 1*mm

            row_h = max(7*mm, h_d + h_dd + 7*mm)
            self.check_space(row_h + 10*mm)

            bg = C_LIGHT if i % 2 == 0 else C_WHITE
            self.rect(self.m, self.y - row_h, self.usable_w, row_h, fill_color=bg)
            self.line(self.m, self.y - row_h, PAGE_W-self.m, self.y - row_h,
                      color=C_BORDER, width=0.3)

            p_d.drawOn(self.c, self.m+2*mm, self.y - 3.5*mm - h_d)
            if p_dd:
                p_dd.drawOn(self.c, self.m+2*mm, self.y - 3.5*mm - h_d - h_dd)

            y_c = self.y - row_h/2 - 2.5*mm
            remise_val = getattr(ligne, 'remise', 0) or 0
            remise_str = f"{float(remise_val):.0f}%" if float(remise_val) > 0 else "\u2014"

            col_start = [sum(col_widths[:k]) for k in range(len(col_widths))]
            other = [
                (f"{float(ligne.quantite):,.2f}", 1, 'center'),
                (f"{float(ligne.prix_unitaire_ht):,.2f}", 2, 'right'),
                (remise_str, 3, 'center'),
                (f"{float(ligne.tva):.0f}%", 4, 'center'),
                (f"{float(ligne.total_ht):,.2f}", 5, 'right'),
            ]
            for val, ci, align in other:
                cx = self.m + col_start[ci]
                cw = col_widths[ci]
                fnt   = 'Helvetica-Bold' if ci == 5 else 'Helvetica'
                color = C_PRIMARY if ci == 5 else C_TEXT
                if align == 'right':
                    self.text(cx+cw-2*mm, y_c, val, font=fnt,
                              size=8.5, color=color, align='right')
                elif align == 'center':
                    self.text(cx+cw/2, y_c, val, font=fnt,
                              size=8.5, color=color, align='center')
                else:
                    self.text(cx+2*mm, y_c, val, font=fnt,
                              size=8.5, color=color)
            self.y -= row_h

    # ── Totals block ──────────────────────────────────────────
    def draw_totaux(self, obj, montant_paye=None):
        self.check_space(55 * mm)
        tx = self.m + self.usable_w * 0.55
        tw = self.usable_w * 0.45
        y0 = self.y - 5 * mm

        def tot_row(label, value, bold=False, color=None, bg=None, h=7*mm):
            nonlocal y0
            if bg:
                self.rect(tx, y0-h, tw, h, fill_color=bg)
            fnt = 'Helvetica-Bold' if bold else 'Helvetica'
            clr = color or C_TEXT
            self.text(tx+3*mm, y0-h/2-2*mm, label, font=fnt, size=9, color=clr)
            self.text(tx+tw-3*mm, y0-h/2-2*mm,
                      f"{float(value):,.2f} {self.ent['devise']}",
                      font=fnt, size=9, color=clr, align='right')
            self.line(tx, y0-h, tx+tw, y0-h, color=C_BORDER, width=0.3)
            y0 -= h

        sous_total = getattr(obj, 'sous_total_ht', obj.total_ht)
        tot_row('Sous-total HT :', sous_total)

        remise = getattr(obj, 'montant_remise', 0) or 0
        if float(remise) > 0:
            tot_row('Remise :', -remise, color=C_DANGER)

        tot_row('Total HT :', obj.total_ht)
        tva = getattr(obj, 'total_tva', 0) or 0
        tot_row(f'TVA :', tva, color=C_MUTED)

        # Total TTC box
        self.rect(tx, y0 - 10*mm, tw, 10*mm, fill_color=C_SECONDARY)
        self.text(tx+3*mm, y0-6*mm, 'TOTAL TTC',
                  font='Helvetica-Bold', size=11, color=C_WHITE)
        self.text(tx+tw-3*mm, y0-6*mm,
                  f"{float(obj.total_ttc):,.2f} {self.ent['devise']}",
                  font='Helvetica-Bold', size=11, color=C_WHITE, align='right')
        y0 -= 10 * mm

        if montant_paye is not None:
            tot_row('Pay\u00e9 :', montant_paye, bold=True, color=C_SUCCESS)
            restant = max(Decimal('0'), obj.total_ttc - Decimal(str(montant_paye)))
            clr = C_DANGER if restant > 0 else C_SUCCESS
            tot_row('Restant d\u00fb :', restant, bold=True, color=clr)

        self.y = y0 - 5 * mm

    # ── Footer ────────────────────────────────────────────────
    def draw_footer(self):
        fy = 12 * mm
        self.line(self.m, fy+5*mm, PAGE_W-self.m, fy+5*mm,
                  color=C_BORDER, width=0.3)
        parts = [p for p in [self.ent['nom'], self.ent['tel'], self.ent['email']] if p]
        from django.utils import timezone
        parts.append(f"G\u00e9n\u00e9r\u00e9 le {timezone.now().strftime('%d/%m/%Y \u00e0 %H:%M')}")
        footer_txt = '  \u00b7  '.join(parts)
        self.text(PAGE_W/2, fy+2*mm, footer_txt,
                  font='Helvetica', size=7.5, color=C_MUTED, align='center')

    def save(self):
        self.c.save()


# ── Public generators ─────────────────────────────────────────

def generer_pdf_facture(facture):
    buf = BytesIO()
    pdf = PDFDoc(buf, title=f"Facture {facture.numero}")

    statut_colors = {
        'payee': C_SUCCESS, 'partielle': C_ACCENT,
        'en_attente': C_WARNING, 'annulee': C_DANGER, 'avoir': C_MUTED,
    }
    pdf.draw_header(
        'FACTURE', facture.numero,
        facture.date_facture.strftime('%d/%m/%Y'),
        facture.date_echeance.strftime('%d/%m/%Y') if facture.date_echeance else None,
    )
    pdf.draw_client_bloc(
        facture.client,
        statut_label=facture.get_statut_display(),
        statut_color=statut_colors.get(facture.statut, C_MUTED),
        vendeur=facture.vendeur,
    )
    pdf.draw_lignes_table(facture.lignes.all())
    pdf.draw_totaux(facture, montant_paye=facture.montant_paye)
    pdf.draw_footer()
    pdf.save()

    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'filename="facture_{facture.numero}.pdf"'
    return response


def generer_pdf_devis(devis):
    buf = BytesIO()
    pdf = PDFDoc(buf, title=f"Devis {devis.numero}")

    pdf.draw_header(
        'DEVIS', devis.numero,
        devis.date_devis.strftime('%d/%m/%Y'),
        devis.date_validite.strftime('%d/%m/%Y') if devis.date_validite else None,
    )
    pdf.draw_client_bloc(
        devis.client,
        statut_label=devis.get_statut_display(),
        statut_color=C_ACCENT,
        vendeur=devis.commercial,
    )
    pdf.draw_lignes_table(devis.lignes.all())

    # Devis has no montant_paye
    devis.sous_total_ht = devis.total_ht
    devis.montant_remise = Decimal('0')
    pdf.draw_totaux(devis)

    # Validity note
    if devis.date_validite:
        pdf.check_space(10 * mm)
        pdf.text(pdf.m, pdf.y - 5*mm,
                 f"Devis valable jusqu'au {devis.date_validite.strftime('%d/%m/%Y')}.",
                 font='Helvetica', size=8, color=C_MUTED)
        pdf.y -= 10 * mm

    pdf.draw_footer()
    pdf.save()

    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'filename="devis_{devis.numero}.pdf"'
    return response


def generer_pdf_achat(achat):
    buf = BytesIO()
    pdf = PDFDoc(buf, title=f"Achat {achat.numero}")

    statut_colors = {
        'paye': C_SUCCESS, 'receptionne': C_ACCENT, 'annule': C_DANGER,
    }
    pdf.draw_header(
        'BON DE COMMANDE', achat.numero,
        achat.date_achat.strftime('%d/%m/%Y'),
    )
    pdf.draw_fournisseur_bloc(achat.fournisseur)

    # Status badge
    sc = statut_colors.get(achat.statut, C_MUTED)
    bx = PAGE_W - pdf.m - 40*mm
    pdf.rect(bx, pdf.y - 12*mm, 40*mm, 10*mm, fill_color=sc)
    pdf.text(bx + 20*mm, pdf.y - 8*mm,
             achat.get_statut_display().upper(),
             font='Helvetica-Bold', size=9, color=C_WHITE, align='center')
    pdf.y -= 15*mm

    # Lines
    col_w = [pdf.usable_w*0.35, pdf.usable_w*0.12, pdf.usable_w*0.18,
              pdf.usable_w*0.08, pdf.usable_w*0.27]
    headers = ['Produit','Qte','PU HT','TVA','Total HT']
    hh = 8*mm
    pdf.rect(pdf.m, pdf.y-hh, pdf.usable_w, hh, fill_color=C_PRIMARY)
    lx = pdf.m
    for h, cw in zip(headers, col_w):
        pdf.text(lx+2*mm, pdf.y-hh/2-2*mm, h,
                 font='Helvetica-Bold', size=8.5, color=C_WHITE)
        lx += cw
    pdf.y -= hh

    for i, ligne in enumerate(achat.lignes.all()):
        rh = 7*mm
        bg = C_LIGHT if i%2==0 else C_WHITE
        pdf.rect(pdf.m, pdf.y-rh, pdf.usable_w, rh, fill_color=bg)
        cells = [
            ligne.designation or ligne.produit.nom,
            f"{float(ligne.quantite):,.2f}",
            f"{float(ligne.prix_unitaire_ht):,.2f}",
            f"{float(ligne.tva):.0f}%",
            f"{float(ligne.total_ht):,.2f}",
        ]
        lx = pdf.m
        for cell, cw in zip(cells, col_w):
            pdf.text(lx+2*mm, pdf.y-rh/2-2*mm, cell,
                     font='Helvetica', size=8.5, color=C_TEXT)
            lx += cw
        pdf.y -= rh

    # Totals
    achat.sous_total_ht  = achat.total_ht
    achat.montant_remise = Decimal('0')
    pdf.draw_totaux(achat)
    pdf.draw_footer()
    pdf.save()

    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'filename="achat_{achat.numero}.pdf"'
    return response


def generer_pdf_location(location):
    buf = BytesIO()
    pdf = PDFDoc(buf, title=f"Location {location.numero}")

    pdf.draw_header(
        'LOCATION', location.numero,
        location.date_debut.strftime('%d/%m/%Y'),
    )
    pdf.draw_client_bloc(
        location.client,
        statut_label=location.get_statut_display(),
        statut_color=C_ACCENT,
    )

    # Info dates
    pdf.text(pdf.m, pdf.y-5*mm,
             f"Debut : {location.date_debut.strftime('%d/%m/%Y %H:%M')}   "
             f"Retour prevu : {location.date_fin_prevue.strftime('%d/%m/%Y %H:%M')}",
             font='Helvetica', size=9, color=C_TEXT)
    if location.date_fin_reelle:
        pdf.text(pdf.m, pdf.y-10*mm,
                 f"Retour reel : {location.date_fin_reelle.strftime('%d/%m/%Y %H:%M')}",
                 font='Helvetica', size=9, color=C_TEXT)
        pdf.y -= 5*mm
    pdf.y -= 15*mm

    # Articles
    col_w = [pdf.usable_w*0.35, pdf.usable_w*0.12, pdf.usable_w*0.15,
              pdf.usable_w*0.15, pdf.usable_w*0.23]
    headers = ['Article','Qte','Prix/Jour','Nb Jours','Sous-total HT']
    hh = 8*mm
    pdf.rect(pdf.m, pdf.y-hh, pdf.usable_w, hh, fill_color=C_PRIMARY)
    lx = pdf.m
    for h, cw in zip(headers, col_w):
        pdf.text(lx+2*mm, pdf.y-hh/2-2*mm, h,
                 font='Helvetica-Bold', size=8.5, color=C_WHITE)
        lx += cw
    pdf.y -= hh

    for i, art in enumerate(location.articles.select_related('produit').all()):
        rh = 7*mm
        bg = C_LIGHT if i%2==0 else C_WHITE
        pdf.rect(pdf.m, pdf.y-rh, pdf.usable_w, rh, fill_color=bg)
        cells = [
            art.produit.nom,
            f"{float(art.quantite):,.2f}",
            f"{float(art.prix_location_jour):,.2f}",
            str(art.nombre_jours),
            f"{float(art.sous_total_ht):,.2f}",
        ]
        lx = pdf.m
        for cell, cw in zip(cells, col_w):
            pdf.text(lx+2*mm, pdf.y-rh/2-2*mm, cell,
                     font='Helvetica', size=8.5, color=C_TEXT)
            lx += cw
        pdf.y -= rh

    # Totals
    location.sous_total_ht  = location.total_ht
    location.montant_remise = Decimal('0')
    location.total_tva      = location.total_ht * Decimal('0.19')
    pdf.draw_totaux(location)

    if location.depot_garantie > 0:
        pdf.check_space(8*mm)
        pdf.text(pdf.m, pdf.y-5*mm,
                 f"Depot de garantie : {float(location.depot_garantie):,.2f} DA",
                 font='Helvetica-Bold', size=9, color=C_TEXT)
        pdf.y -= 10*mm

    if location.penalite_retard > 0:
        pdf.text(pdf.m, pdf.y-5*mm,
                 f"Penalite de retard : {float(location.penalite_retard):,.2f} DA",
                 font='Helvetica-Bold', size=9, color=C_DANGER)
        pdf.y -= 10*mm

    pdf.draw_footer()
    pdf.save()

    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'filename="location_{location.numero}.pdf"'
    return response


def generer_pdf_tarif(produits, entreprise_info=None):
    buf  = BytesIO()
    pdf  = PDFDoc(buf, title="Liste des tarifs")
    ent  = entreprise_info or cfg()

    pdf.rect(0, PAGE_H-4*mm, PAGE_W, 4*mm, fill_color=C_PRIMARY)
    pdf.text(pdf.m, pdf.y-10*mm, "LISTE DES TARIFS",
             font='Helvetica-Bold', size=28, color=C_PRIMARY)
    pdf.text(pdf.m, pdf.y-18*mm, ent['nom'],
             font='Helvetica-Bold', size=13, color=C_TEXT)
    if ent.get('tel'):
        pdf.text(pdf.m, pdf.y-23*mm, f"Tel : {ent['tel']}",
                 font='Helvetica', size=9, color=C_MUTED)
    from django.utils import timezone
    pdf.text(PAGE_W-pdf.m, pdf.y-10*mm,
             f"Edite le {timezone.now().strftime('%d/%m/%Y')}",
             font='Helvetica', size=9, color=C_MUTED, align='right')
    pdf.y -= 30*mm
    pdf.line(pdf.m, pdf.y, PAGE_W-pdf.m, pdf.y, color=C_PRIMARY, width=1.5)
    pdf.y -= 6*mm

    col_w = [pdf.usable_w*0.14, pdf.usable_w*0.42, pdf.usable_w*0.10,
              pdf.usable_w*0.17, pdf.usable_w*0.17]
    headers = ['Reference','Designation','Unite','Prix HT (DA)','Prix TTC (DA)']

    def draw_headers():
        pdf.rect(pdf.m, pdf.y-8*mm, pdf.usable_w, 8*mm, fill_color=C_PRIMARY)
        lx = pdf.m
        for h, cw in zip(headers, col_w):
            pdf.text(lx+2*mm, pdf.y-5.5*mm, h,
                     font='Helvetica-Bold', size=8, color=C_WHITE)
            lx += cw
        pdf.y -= 8*mm

    draw_headers()

    produits_list  = list(produits)
    current_cat    = None
    row_h          = 7.5*mm

    for idx, p in enumerate(produits_list):
        pdf.check_space(row_h + 12*mm)
        cat_name = p.categorie.nom if p.categorie else 'Autres'
        if cat_name != current_cat:
            if current_cat is not None:
                pdf.y -= 2*mm
            current_cat = cat_name
            pdf.rect(pdf.m, pdf.y-6*mm, pdf.usable_w, 6*mm,
                     fill_color=colors.HexColor('#EBF3FB'))
            pdf.text(pdf.m+3*mm, pdf.y-4.5*mm, cat_name.upper(),
                     font='Helvetica-Bold', size=8.5, color=C_DARK)
            pdf.y -= 6*mm

        bg = C_LIGHT if idx%2==0 else C_WHITE
        pdf.rect(pdf.m, pdf.y-row_h, pdf.usable_w, row_h, fill_color=bg)
        pdf.line(pdf.m, pdf.y-row_h, PAGE_W-pdf.m, pdf.y-row_h,
                 color=C_BORDER, width=0.3)

        prix_ttc = float(p.prix_vente) * (1 + float(p.tva)/100)
        cells = [
            (p.reference,              'left',   False),
            (p.nom[:52],               'left',   True),
            (p.get_unite_display(),    'center', False),
            (f"{float(p.prix_vente):,.2f}", 'right', False),
            (f"{prix_ttc:,.2f}",       'right',  True),
        ]
        lx = pdf.m
        for (val, align, bold), cw in zip(cells, col_w):
            fnt   = 'Helvetica-Bold' if bold else 'Helvetica'
            color = C_PRIMARY if (align=='right' and bold) else C_TEXT
            y_pos = pdf.y - row_h/2 - 2*mm
            if align == 'right':
                pdf.text(lx+cw-2*mm, y_pos, val, font=fnt,
                         size=8.5, color=color, align='right')
            elif align == 'center':
                pdf.text(lx+cw/2, y_pos, val, font=fnt,
                         size=8.5, color=color, align='center')
            else:
                pdf.text(lx+2*mm, y_pos, val, font=fnt, size=8.5, color=color)
            lx += cw
        pdf.y -= row_h

    pdf.draw_footer()
    pdf.save()

    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'filename="liste_tarifs.pdf"'
    return response


def generer_pdf_bilan_journalier(date_bilan, data):
    buf = BytesIO()
    pdf = PDFDoc(buf, title=f"Bilan journalier {date_bilan}")
    ent = cfg()

    pdf.rect(0, PAGE_H-4*mm, PAGE_W, 4*mm, fill_color=C_PRIMARY)
    pdf.text(pdf.m, pdf.y-10*mm, "BILAN JOURNALIER",
             font='Helvetica-Bold', size=24, color=C_PRIMARY)
    pdf.text(pdf.m, pdf.y-17*mm, ent['nom'],
             font='Helvetica-Bold', size=11, color=C_TEXT)
    pdf.text(PAGE_W-pdf.m, pdf.y-10*mm,
             date_bilan.strftime('%A %d %B %Y').capitalize(),
             font='Helvetica-Bold', size=11, color=C_MUTED, align='right')
    sep_y = pdf.y-22*mm
    pdf.line(pdf.m, sep_y, PAGE_W-pdf.m, sep_y, color=C_PRIMARY, width=1.5)
    pdf.y = sep_y - 8*mm

    # KPI boxes
    box_w = (pdf.usable_w - 3*5*mm) / 4
    boxes = [
        ("CA du jour",  f"{float(data.get('ca_jour',0)):,.0f} DA", C_PRIMARY),
        ("Encaisse",    f"{float(data.get('encaisse_jour',0)):,.0f} DA", C_SUCCESS),
        ("Factures",    str(data.get('nb_factures',0)), C_DARK),
        ("Alertes stock",str(data.get('alertes_stock',0)), C_WARNING),
    ]
    bx = pdf.m
    for label, val, color in boxes:
        pdf.rect(bx, pdf.y-20*mm, box_w, 20*mm,
                 fill_color=colors.HexColor('#F8FAFC'),
                 stroke_color=C_BORDER, stroke_width=0.3)
        pdf.text(bx+box_w/2, pdf.y-7*mm, label,
                 font='Helvetica', size=8, color=C_MUTED, align='center')
        pdf.text(bx+box_w/2, pdf.y-14*mm, val,
                 font='Helvetica-Bold', size=13, color=color, align='center')
        bx += box_w + 5*mm
    pdf.y -= 24*mm

    # Factures
    factures = list(data.get('factures', []))
    if factures:
        pdf.text(pdf.m, pdf.y-5*mm,
                 f"FACTURES DU JOUR ({len(factures)})",
                 font='Helvetica-Bold', size=9, color=C_DARK)
        pdf.y -= 8*mm
        col_w2 = [pdf.usable_w*0.25, pdf.usable_w*0.37,
                   pdf.usable_w*0.18, pdf.usable_w*0.20]
        hdrs2  = ['N\u00b0 Facture','Client','Statut','Total TTC']
        pdf.rect(pdf.m, pdf.y-7*mm, pdf.usable_w, 7*mm, fill_color=C_PRIMARY)
        lx = pdf.m
        for h, cw in zip(hdrs2, col_w2):
            pdf.text(lx+2*mm, pdf.y-5*mm, h,
                     font='Helvetica-Bold', size=7.5, color=C_WHITE)
            lx += cw
        pdf.y -= 7*mm
        for i, f in enumerate(factures[:10]):
            bg = C_LIGHT if i%2==0 else C_WHITE
            pdf.rect(pdf.m, pdf.y-6*mm, pdf.usable_w, 6*mm, fill_color=bg)
            cells2 = [f.numero, f.client.nom[:30],
                      f.get_statut_display(), f"{float(f.total_ttc):,.2f} DA"]
            lx = pdf.m
            for cell, cw in zip(cells2, col_w2):
                pdf.text(lx+2*mm, pdf.y-4.5*mm, str(cell),
                         font='Helvetica', size=7.5, color=C_TEXT)
                lx += cw
            pdf.y -= 6*mm
        pdf.y -= 4*mm

    # Services terminés
    services = list(data.get('services_termines', []))
    if services:
        pdf.check_space(20*mm)
        pdf.text(pdf.m, pdf.y-5*mm,
                 f"SERVICES TERMINES ({len(services)})",
                 font='Helvetica-Bold', size=9, color=C_DARK)
        pdf.y -= 8*mm
        for s in services[:5]:
            pdf.text(pdf.m+3*mm, pdf.y-4*mm,
                     f"\u2022 OT-{s.numero}  {s.client.nom}  \u2014  {s.objet_service[:40]}",
                     font='Helvetica', size=8, color=C_TEXT)
            pdf.y -= 5.5*mm

    pdf.draw_footer()
    pdf.save()

    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'filename="bilan_{date_bilan.strftime("%Y%m%d")}.pdf"'
    return response
