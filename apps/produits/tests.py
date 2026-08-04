import io
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from apps.authentication.models import Utilisateur

@pytest.fixture
def admin_client(client, db):
    admin = Utilisateur.objects.create_user(
        username="admintest", password="AdminPass123!", role="admin", is_staff=True
    )
    client.force_login(admin)
    return client

@pytest.mark.django_db
class TestImportExcelExtensionValidation:
    @pytest.mark.parametrize("filename", [
        "produits.exe",
        "produits.php",
        "produits.html",
        "produits.csv.exe",
        "produits",
    ])
    def test_disallowed_extensions_are_rejected(self, admin_client, filename):
        fake_file = SimpleUploadedFile(
            filename, b"contenu quelconque", content_type="application/octet-stream"
        )
        response = admin_client.post(
            reverse('produits:import_preview'), {'fichier': fake_file}
        )
        assert response.status_code in (200, 302)
        assert response.status_code != 500

    @pytest.mark.parametrize("filename", [
        "produits.xlsx",
        "produits.xlsm",
        "produits.xltx",
        "produits.xls",
    ])
    def test_allowed_extensions_pass_extension_check(self, admin_client, filename):
        fake_file = SimpleUploadedFile(
            filename, b"contenu quelconque", content_type="application/octet-stream"
        )
        response = admin_client.post(
            reverse('produits:import_preview'), {'fichier': fake_file}
        )
        assert response.status_code != 500
