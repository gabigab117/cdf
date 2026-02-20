from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models, IntegrityError

from core.models import DocumentCategory, CustomDocument


class DocumentCategoryTests(TestCase):
    """Tests pour le snippet DocumentCategory."""

    def test_str(self):
        cat = DocumentCategory.objects.create(name="Factures")
        self.assertEqual(str(cat), "Factures")

    def test_ordering(self):
        DocumentCategory.objects.create(name="Relevés")
        DocumentCategory.objects.create(name="Assurance")
        DocumentCategory.objects.create(name="Factures")
        names = list(DocumentCategory.objects.values_list("name", flat=True))
        self.assertEqual(names, ["Assurance", "Factures", "Relevés"])


class CustomDocumentTests(TestCase):
    """Tests pour le modèle CustomDocument."""

    def setUp(self):
        self.category = DocumentCategory.objects.create(name="Divers")

    def test_str(self):
        doc = CustomDocument.objects.create(
            title="Mon document",
            category=self.category,
            file=SimpleUploadedFile("test.pdf", b"content"),
        )
        self.assertEqual(str(doc), "Mon document")

    def test_category_required(self):
        """La catégorie est obligatoire (PROTECT, non nullable)."""
        with self.assertRaises(IntegrityError):
            CustomDocument.objects.create(
                title="Sans catégorie",
                file=SimpleUploadedFile("test.pdf", b"content"),
            )

    def test_category_protected_on_delete(self):
        """Impossible de supprimer une catégorie utilisée par un document."""
        cat = DocumentCategory.objects.create(name="Temp")
        CustomDocument.objects.create(
            title="Doc",
            category=cat,
            file=SimpleUploadedFile("test.pdf", b"content"),
        )
        with self.assertRaises(models.ProtectedError):
            cat.delete()
