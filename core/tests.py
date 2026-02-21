from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from wagtail.models import Collection

from core.models import CustomDocument


class CustomDocumentTests(TestCase):
    """Tests pour le modèle CustomDocument."""

    def test_str(self):
        doc = CustomDocument.objects.create(
            title="Mon document",
            file=SimpleUploadedFile("test.pdf", b"content"),
        )
        self.assertEqual(str(doc), "Mon document")

    def test_document_has_collection(self):
        """Un document appartient toujours à une collection (Root par défaut)."""
        doc = CustomDocument.objects.create(
            title="Doc sans collection explicite",
            file=SimpleUploadedFile("test.pdf", b"content"),
        )
        self.assertIsNotNone(doc.collection)
        self.assertEqual(doc.collection.name, "Root")

    def test_document_in_custom_collection(self):
        """Un document peut être assigné à une collection personnalisée."""
        root = Collection.objects.get(depth=1)
        factures = root.add_child(name="Factures")
        doc = CustomDocument.objects.create(
            title="Facture 1",
            collection=factures,
            file=SimpleUploadedFile("facture.pdf", b"content"),
        )
        self.assertEqual(doc.collection.name, "Factures")
