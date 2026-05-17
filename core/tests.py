from datetime import date

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from wagtail.models import Collection

from core.models import CustomDocument


class CustomDocumentTests(TestCase):
    """Tests pour le modèle CustomDocument."""

    def test_str(self):
        """
        Given un document avec le titre « Mon document »
        When on appelle str() dessus
        Then le résultat est « Mon document »
        """
        doc = CustomDocument.objects.create(
            title="Mon document",
            file=SimpleUploadedFile("test.pdf", b"content"),
        )
        self.assertEqual(str(doc), "Mon document")

    def test_document_has_collection(self):
        """
        Given un document créé sans collection explicite
        When on accède à sa collection
        Then il appartient à la collection Root par défaut
        """
        doc = CustomDocument.objects.create(
            title="Doc sans collection explicite",
            file=SimpleUploadedFile("test.pdf", b"content"),
        )
        self.assertIsNotNone(doc.collection)
        self.assertEqual(doc.collection.name, "Root")

    def test_document_in_custom_collection(self):
        """
        Given une collection « Factures » créée sous Root
        When on crée un document assigné à cette collection
        Then le document appartient bien à la collection « Factures »
        """
        root = Collection.objects.get(depth=1)
        factures = root.add_child(name="Factures")
        doc = CustomDocument.objects.create(
            title="Facture 1",
            collection=factures,
            file=SimpleUploadedFile("facture.pdf", b"content"),
        )
        self.assertEqual(doc.collection.name, "Factures")


# ── Helpers vue document_list ───────────────────────────────


class DocumentListViewMixin:
    """setUp partagé : superuser, modérateur (groupe) et user lambda."""

    def setUp(self):
        super().setUp()
        self.moderator = User.objects.create_superuser(
            "modo", "modo@test.com", "pass",
        )
        self.group_moderator = User.objects.create_user(
            "modo_group", "mg@test.com", "pass",
        )
        moderators_group, _ = Group.objects.get_or_create(name="Moderators")
        self.group_moderator.groups.add(moderators_group)
        self.lambda_user = User.objects.create_user(
            "lambda", "lambda@test.com", "pass",
        )
        self.url = reverse("core:document_list")


# ── Vue document_list ─ accès ──────────────────────────────


class DocumentListAccessTests(DocumentListViewMixin, TestCase):
    """Protection d'accès de la vue document_list."""

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il accède à la liste des documents
        Then il est redirigé (302)
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur hors groupe Moderators
        When il accède à la liste des documents
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_superuser_can_access(self):
        """
        Given un superuser authentifié
        When il accède à la liste des documents
        Then la réponse est 200 avec le template document_list.html
        """
        self.client.force_login(self.moderator)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/document_list.html")

    def test_moderator_group_can_access(self):
        """
        Given un utilisateur du groupe Moderators
        When il accède à la liste des documents
        Then la réponse est 200
        """
        self.client.force_login(self.group_moderator)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


# ── Vue document_list ─ tri & filtres ──────────────────────────


class DocumentListContentTests(DocumentListViewMixin, TestCase):
    """Tri et filtres de la vue document_list."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.moderator)
        root = Collection.objects.get(depth=1)
        self.factures = root.add_child(name="Factures")
        self.contrats = root.add_child(name="Contrats")

        self.doc_recent = CustomDocument.objects.create(
            title="Facture mars",
            collection=self.factures,
            document_date=date(2026, 3, 15),
            file=SimpleUploadedFile("a.pdf", b"a"),
        )
        self.doc_old = CustomDocument.objects.create(
            title="Facture janvier",
            collection=self.factures,
            document_date=date(2026, 1, 5),
            file=SimpleUploadedFile("b.pdf", b"b"),
        )
        self.doc_no_date = CustomDocument.objects.create(
            title="Contrat sans date",
            collection=self.contrats,
            document_date=None,
            file=SimpleUploadedFile("c.pdf", b"c"),
        )

    def test_ordering_by_document_date_desc_nulls_last(self):
        """
        Given 3 docs (mars, janvier, sans date)
        When un modérateur charge la liste
        Then l'ordre est mars, janvier, puis le doc sans date en fin
        """
        response = self.client.get(self.url)
        titles = [d.title for d in response.context["documents"]]
        self.assertEqual(
            titles,
            ["Facture mars", "Facture janvier", "Contrat sans date"],
        )

    def test_filter_by_title(self):
        """
        Given 3 documents
        When on filtre avec ?q=janvier
        Then seul le doc « Facture janvier » est retourné
        """
        response = self.client.get(self.url, {"q": "janvier"})
        titles = [d.title for d in response.context["documents"]]
        self.assertEqual(titles, ["Facture janvier"])

    def test_filter_by_collection(self):
        """
        Given des docs dans 2 collections
        When on filtre par la collection « Contrats »
        Then seuls les docs de cette collection sont retournés
        """
        response = self.client.get(
            self.url, {"collection": str(self.contrats.pk)},
        )
        titles = [d.title for d in response.context["documents"]]
        self.assertEqual(titles, ["Contrat sans date"])

    def test_invalid_collection_param_ignored(self):
        """
        Given un paramètre collection non numérique
        When on charge la liste
        Then tous les documents sont retournés (filtre ignoré)
        """
        response = self.client.get(self.url, {"collection": "abc"})
        self.assertEqual(len(response.context["documents"]), 3)


# ── Vue document_list ─ branchement HTMX ────────────────────────


class DocumentListHtmxTests(DocumentListViewMixin, TestCase):
    """Rendu du partial pour les requêtes HTMX."""

    def test_htmx_request_returns_partial(self):
        """
        Given une requête avec l'en-tête HX-Request
        When un modérateur charge la liste
        Then la réponse utilise uniquement le partial document_results.html
        """
        self.client.force_login(self.moderator)
        response = self.client.get(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/partials/document_results.html")
        self.assertTemplateNotUsed(response, "core/document_list.html")

    def test_regular_request_returns_full_page(self):
        """
        Given une requête sans en-tête HX-Request
        When un modérateur charge la liste
        Then la réponse utilise la page complète
        """
        self.client.force_login(self.moderator)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "core/document_list.html")


# ── Vue legal ────────────────────────────────────────────────────────


class LegalViewTests(TestCase):
    """Tests de la vue legal."""

    def test_legal_accessible_anonymously(self):
        """
        Given un visiteur anonyme
        When il accède à /mentions-legales/
        Then la réponse est 200
        """
        url = reverse("legal")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_legal_uses_correct_template(self):
        """
        Given un visiteur quelconque
        When il accède à la page des mentions légales
        Then le template core/legal.html est utilisé
        """
        url = reverse("legal")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "core/legal.html")
