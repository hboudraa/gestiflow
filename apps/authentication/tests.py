import pytest
from django.urls import reverse
from apps.authentication.models import Utilisateur

@pytest.fixture
def utilisateur(db):
    return Utilisateur.objects.create_user(
        username="testuser", password="TestPass123!", role="vendeur"
    )

@pytest.mark.django_db
class TestLoginRedirectSecurity:
    def test_next_url_safe_relative_path_is_respected(self, client, utilisateur):
        url = reverse('auth:connexion') + '?next=/produits/'
        response = client.post(url, {
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        assert response.status_code == 302
        assert response.url == '/produits/'

    def test_next_url_external_host_is_rejected(self, client, utilisateur):
        url = reverse('auth:connexion') + '?next=https://evil-phishing-site.com/steal'
        response = client.post(url, {
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        assert response.status_code == 302
        assert 'evil-phishing-site.com' not in response.url

    def test_next_url_protocol_relative_is_rejected(self, client, utilisateur):
        url = reverse('auth:connexion') + '?next=//evil-phishing-site.com'
        response = client.post(url, {
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        assert response.status_code == 302
        assert 'evil-phishing-site.com' not in response.url

    def test_next_url_javascript_scheme_is_rejected(self, client, utilisateur):
        url = reverse('auth:connexion') + '?next=javascript:alert(1)'
        response = client.post(url, {
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        assert response.status_code == 302
        assert 'javascript:' not in response.url
