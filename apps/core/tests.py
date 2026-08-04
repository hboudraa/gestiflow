import pytest
from apps.core import email_service

class TestEmailBodyEscaping:
    def test_html_tags_in_corps_are_escaped(self):
        corps_malveillant = '<script>alert("xss")</script>'
        html = email_service.construire_corps_html(corps_malveillant)
        assert '<script>' not in html
        assert '&lt;script&gt;' in html

    def test_newlines_are_still_converted_to_br(self):
        corps_normal = "Bonjour,\nVeuillez trouver ci-joint votre facture.\nCordialement."
        html = email_service.construire_corps_html(corps_normal)
        assert '<br>' in html or '<br/>' in html or '<br />' in html

    def test_html_entities_in_legit_text_are_escaped(self):
        corps = 'Merci pour votre commande chez "Import & Export SARL"'
        html = email_service.construire_corps_html(corps)
        assert '&amp;' in html
        # Ensure quotes are escaped (either &quot; or encoded)
        assert '&quot;' in html or '"' not in html
