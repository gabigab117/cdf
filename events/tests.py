from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from events.models import EventIndexPage, EventPage, EventDocument
from core.models import DocumentCategory, CustomDocument


class EventPageTreeMixin:
    """setUp partagé : root → index → event."""

    def setUp(self):
        super().setUp()
        root_page = Page.get_first_root_node()
        Site.objects.create(
            hostname="testsite", root_page=root_page, is_default_site=True,
        )

        self.index_page = EventIndexPage(
            title="Événements", intro="<p>Bienvenue</p>", events_per_page=3,
        )
        root_page.add_child(instance=self.index_page)

        self.event = EventPage(
            title="Fête du 13 Juillet",
            date_event=timezone.now(),
        )
        self.index_page.add_child(instance=self.event)


# ── Hiérarchie des pages ─────────────────────────────────────────────

class EventPageHierarchyTests(WagtailPageTestCase):
    """Vérifie les règles parent_page_types / subpage_types."""

    def test_can_create_event_index_under_root(self):
        self.assertCanCreateAt(Page, EventIndexPage)

    def test_can_create_event_page_under_index(self):
        self.assertCanCreateAt(EventIndexPage, EventPage)

    def test_cannot_create_event_page_under_root(self):
        self.assertCanNotCreateAt(Page, EventPage)

    def test_event_page_has_no_subpages(self):
        self.assertAllowedSubpageTypes(EventPage, {})

    def test_event_index_only_allows_event_pages(self):
        self.assertAllowedSubpageTypes(EventIndexPage, {EventPage})


# ── Rendu des pages ──────────────────────────────────────────────────

class EventIndexPageTests(EventPageTreeMixin, WagtailPageTestCase):
    """Tests de la page d'index des événements."""

    def test_index_is_renderable(self):
        self.assertPageIsRenderable(self.index_page)

    def test_index_template(self):
        response = self.client.get(self.index_page.url)
        self.assertTemplateUsed(response, "events/event_index_page.html")

    def test_context_contains_events(self):
        response = self.client.get(self.index_page.url)
        self.assertIn("events", response.context)


class EventIndexPaginationTests(EventPageTreeMixin, WagtailPageTestCase):
    """Test de la pagination (events_per_page = 3)."""

    def setUp(self):
        super().setUp()
        # On a déjà 1 event dans le mixin, en ajouter 6 → total = 7
        for i in range(6):
            self.index_page.add_child(
                instance=EventPage(
                    title=f"Événement {i}",
                    date_event=timezone.now(),
                )
            )

    def test_first_page_count(self):
        response = self.client.get(self.index_page.url)
        self.assertEqual(len(response.context["events"]), 3)

    def test_second_page_count(self):
        response = self.client.get(self.index_page.url + "?page=2")
        self.assertEqual(len(response.context["events"]), 3)

    def test_invalid_page_number_falls_back(self):
        response = self.client.get(self.index_page.url + "?page=abc")
        self.assertEqual(response.status_code, 200)


# ── Accès via PageViewRestriction (Wagtail Privacy) ──────────────────

class EventPageAccessTests(EventPageTreeMixin, WagtailPageTestCase):
    """Vérifie que EventPage respecte les restrictions Wagtail (PageViewRestriction)."""

    def test_public_by_default(self):
        """Sans restriction, la page est accessible à tous."""
        response = self.client.get(self.event.url)
        self.assertEqual(response.status_code, 200)

    def test_login_restriction_redirects_anonymous(self):
        """Avec restriction 'login', un anonyme est redirigé."""
        from wagtail.models import PageViewRestriction
        PageViewRestriction.objects.create(
            page=self.index_page,
            restriction_type=PageViewRestriction.LOGIN,
        )
        response = self.client.get(self.event.url)
        self.assertEqual(response.status_code, 302)

    def test_login_restriction_allows_authenticated(self):
        """Avec restriction 'login', un utilisateur connecté accède à la page."""
        from wagtail.models import PageViewRestriction
        PageViewRestriction.objects.create(
            page=self.index_page,
            restriction_type=PageViewRestriction.LOGIN,
        )
        user = User.objects.create_user("member", "m@test.com", "pass")
        self.client.force_login(user)
        response = self.client.get(self.event.url)
        self.assertEqual(response.status_code, 200)

    def test_group_restriction_redirects_non_member(self):
        """Avec restriction par groupe, un user hors groupe est redirigé."""
        from django.contrib.auth.models import Group
        from wagtail.models import PageViewRestriction
        group = Group.objects.create(name="Membres CDF")
        restriction = PageViewRestriction.objects.create(
            page=self.index_page,
            restriction_type=PageViewRestriction.GROUPS,
        )
        restriction.groups.add(group)
        user = User.objects.create_user("outsider", "o@test.com", "pass")
        self.client.force_login(user)
        response = self.client.get(self.event.url)
        self.assertEqual(response.status_code, 302)

    def test_group_restriction_allows_member(self):
        """Avec restriction par groupe, un membre du groupe accède à la page."""
        from django.contrib.auth.models import Group
        from wagtail.models import PageViewRestriction
        group = Group.objects.create(name="Membres CDF")
        restriction = PageViewRestriction.objects.create(
            page=self.index_page,
            restriction_type=PageViewRestriction.GROUPS,
        )
        restriction.groups.add(group)
        user = User.objects.create_user("member", "m@test.com", "pass")
        user.groups.add(group)
        self.client.force_login(user)
        response = self.client.get(self.event.url)
        self.assertEqual(response.status_code, 200)

    def test_event_page_uses_correct_template(self):
        response = self.client.get(self.event.url)
        self.assertTemplateUsed(response, "events/event_page.html")


# ── Visibilité des détails sur l'index (can_view_details) ────────────

class EventIndexDetailsVisibilityTests(EventPageTreeMixin, WagtailPageTestCase):
    """Vérifie que seuls les utilisateurs avec des permissions Wagtail
    (éditeurs/modérateurs) voient les détails sur la page d'index."""

    def test_anonymous_cannot_view_details(self):
        response = self.client.get(self.index_page.url)
        self.assertFalse(response.context['can_view_details'])
        self.assertNotContains(response, 'Voir détails')

    def test_simple_user_cannot_view_details(self):
        user = User.objects.create_user("lambda", "l@test.com", "pass")
        self.client.force_login(user)
        response = self.client.get(self.index_page.url)
        self.assertFalse(response.context['can_view_details'])
        self.assertNotContains(response, 'Voir détails')

    def test_superuser_can_view_details(self):
        admin = User.objects.create_superuser("admin", "a@test.com", "pass")
        self.client.force_login(admin)
        response = self.client.get(self.index_page.url)
        self.assertTrue(response.context['can_view_details'])
        self.assertContains(response, 'Voir détails')


# ── Documents groupés par catégorie ──────────────────────────────────

class EventDocumentsByCategoryTests(EventPageTreeMixin, WagtailPageTestCase):
    """Teste get_documents_by_category() sur EventPage."""

    def setUp(self):
        super().setUp()

        self.cat_factures = DocumentCategory.objects.create(name="Factures")
        self.cat_releves = DocumentCategory.objects.create(name="Relevés")

        doc1 = CustomDocument.objects.create(
            title="Facture 1",
            category=self.cat_factures,
            file=SimpleUploadedFile("f1.pdf", b"data"),
        )
        doc2 = CustomDocument.objects.create(
            title="Relevé 1",
            category=self.cat_releves,
            file=SimpleUploadedFile("r1.pdf", b"data"),
        )
        EventDocument.objects.create(page=self.event, document=doc1, sort_order=0)
        EventDocument.objects.create(page=self.event, document=doc2, sort_order=1)

    def test_documents_grouped_correctly(self):
        grouped = self.event.get_documents_by_category()
        self.assertIn("Factures", grouped)
        self.assertIn("Relevés", grouped)
        self.assertEqual(len(grouped["Factures"]), 1)
        self.assertEqual(len(grouped["Relevés"]), 1)

    def test_all_documents_have_category(self):
        grouped = self.event.get_documents_by_category()
        total_docs = sum(len(docs) for docs in grouped.values())
        self.assertEqual(total_docs, self.event.event_documents.count())
