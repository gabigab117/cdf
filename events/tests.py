from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from wagtail.models import Collection, Page, PageViewRestriction, Site
from wagtail.test.utils import WagtailPageTestCase

from core.models import CustomDocument
from events.models import (
    EventDocument,
    EventIndexPage,
    EventPage,
    EventStation,
    StationAssignment,
)


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
        """
        Given la page racine du site
        When on tente de créer une EventIndexPage dessous
        Then la création est autorisée
        """
        self.assertCanCreateAt(Page, EventIndexPage)

    def test_can_create_event_page_under_index(self):
        """
        Given une EventIndexPage existante
        When on tente de créer une EventPage dessous
        Then la création est autorisée
        """
        self.assertCanCreateAt(EventIndexPage, EventPage)

    def test_cannot_create_event_page_under_root(self):
        """
        Given la page racine du site
        When on tente de créer une EventPage directement dessous
        Then la création est refusée
        """
        self.assertCanNotCreateAt(Page, EventPage)

    def test_event_page_has_no_subpages(self):
        """
        Given une EventPage
        When on vérifie les sous-pages autorisées
        Then aucun type de sous-page n'est permis
        """
        self.assertAllowedSubpageTypes(EventPage, {})

    def test_event_index_only_allows_event_pages(self):
        """
        Given une EventIndexPage
        When on vérifie les sous-pages autorisées
        Then seul EventPage est permis
        """
        self.assertAllowedSubpageTypes(EventIndexPage, {EventPage})


# ── Rendu des pages ──────────────────────────────────────────────────

class EventIndexPageTests(EventPageTreeMixin, WagtailPageTestCase):
    """Tests de la page d'index des événements."""

    def test_index_is_renderable(self):
        """
        Given une EventIndexPage publiée
        When on la rend
        Then aucune erreur n'est levée
        """
        self.assertPageIsRenderable(self.index_page)

    def test_index_template(self):
        """
        Given une EventIndexPage publiée
        When on accède à son URL
        Then le template event_index_page.html est utilisé
        """
        response = self.client.get(self.index_page.url)
        self.assertTemplateUsed(response, "events/event_index_page.html")

    def test_context_contains_events(self):
        """
        Given une EventIndexPage avec des événements enfants
        When on accède à son URL
        Then le contexte contient la clé 'events'
        """
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
        """
        Given 7 événements et une pagination à 3 par page
        When on accède à la première page
        Then 3 événements sont affichés
        """
        response = self.client.get(self.index_page.url)
        self.assertEqual(len(response.context["events"]), 3)

    def test_second_page_count(self):
        """
        Given 7 événements et une pagination à 3 par page
        When on accède à la deuxième page
        Then 3 événements sont affichés
        """
        response = self.client.get(self.index_page.url + "?page=2")
        self.assertEqual(len(response.context["events"]), 3)

    def test_invalid_page_number_falls_back(self):
        """
        Given une EventIndexPage paginée
        When on passe un numéro de page invalide ('abc')
        Then la réponse est 200 (fallback sur la première page)
        """
        response = self.client.get(self.index_page.url + "?page=abc")
        self.assertEqual(response.status_code, 200)


# ── Accès via PageViewRestriction (Wagtail Privacy) ──────────────────

class EventPageAccessTests(EventPageTreeMixin, WagtailPageTestCase):
    """Vérifie que EventPage respecte les restrictions Wagtail (PageViewRestriction)."""

    def test_public_by_default(self):
        """
        Given une EventPage sans restriction d'accès
        When un visiteur anonyme accède à la page
        Then la réponse est 200
        """
        response = self.client.get(self.event.url)
        self.assertEqual(response.status_code, 200)

    def test_login_restriction_redirects_anonymous(self):
        """
        Given une restriction 'login' sur l'index parent
        When un visiteur anonyme accède à l'EventPage
        Then il est redirigé (302)
        """
        PageViewRestriction.objects.create(
            page=self.index_page,
            restriction_type=PageViewRestriction.LOGIN,
        )
        response = self.client.get(self.event.url)
        self.assertEqual(response.status_code, 302)

    def test_login_restriction_allows_authenticated(self):
        """
        Given une restriction 'login' sur l'index parent
        When un utilisateur authentifié accède à l'EventPage
        Then la réponse est 200
        """
        PageViewRestriction.objects.create(
            page=self.index_page,
            restriction_type=PageViewRestriction.LOGIN,
        )
        user = User.objects.create_user("member", "m@test.com", "pass")
        self.client.force_login(user)
        response = self.client.get(self.event.url)
        self.assertEqual(response.status_code, 200)

    def test_group_restriction_redirects_non_member(self):
        """
        Given une restriction par groupe sur l'index parent
        When un utilisateur hors du groupe accède à l'EventPage
        Then il est redirigé (302)
        """
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
        """
        Given une restriction par groupe sur l'index parent
        When un membre du groupe accède à l'EventPage
        Then la réponse est 200
        """
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
        """
        Given une EventPage publiée
        When on accède à son URL
        Then le template event_page.html est utilisé
        """
        response = self.client.get(self.event.url)
        self.assertTemplateUsed(response, "events/event_page.html")


# ── Visibilité des détails sur l'index (can_view_details) ────────────

class EventIndexDetailsVisibilityTests(EventPageTreeMixin, WagtailPageTestCase):
    """Vérifie la visibilité des détails sur la page d'index selon les permissions."""

    def test_anonymous_cannot_view_details(self):
        """
        Given un visiteur anonyme
        When il accède à la page d'index
        Then can_view_details est False et 'Voir détails' est absent
        """
        response = self.client.get(self.index_page.url)
        self.assertFalse(response.context['can_view_details'])
        self.assertNotContains(response, 'Voir détails')

    def test_simple_user_cannot_view_details(self):
        """
        Given un utilisateur sans permissions Wagtail
        When il accède à la page d'index
        Then can_view_details est False et 'Voir détails' est absent
        """
        user = User.objects.create_user("lambda", "l@test.com", "pass")
        self.client.force_login(user)
        response = self.client.get(self.index_page.url)
        self.assertFalse(response.context['can_view_details'])
        self.assertNotContains(response, 'Voir détails')

    def test_superuser_can_view_details(self):
        """
        Given un superuser authentifié
        When il accède à la page d'index
        Then can_view_details est True et 'Voir détails' est présent
        """
        admin = User.objects.create_superuser("admin", "a@test.com", "pass")
        self.client.force_login(admin)
        response = self.client.get(self.index_page.url)
        self.assertTrue(response.context['can_view_details'])
        self.assertContains(response, 'Voir détails')


# ── Documents dans le contexte ────────────────────────────────────────

class EventDocumentsContextTests(EventPageTreeMixin, WagtailPageTestCase):
    """Teste le contexte des documents associés à un événement."""

    def setUp(self):
        super().setUp()

        root_collection = Collection.objects.get(depth=1)
        self.col_factures = root_collection.add_child(name="Factures")
        self.col_releves = root_collection.add_child(name="Relevés")

        doc1 = CustomDocument.objects.create(
            title="Facture 1",
            collection=self.col_factures,
            file=SimpleUploadedFile("f1.pdf", b"data"),
        )
        doc2 = CustomDocument.objects.create(
            title="Relevé 1",
            collection=self.col_releves,
            file=SimpleUploadedFile("r1.pdf", b"data"),
        )
        EventDocument.objects.create(page=self.event, document=doc1, sort_order=0)
        EventDocument.objects.create(page=self.event, document=doc2, sort_order=1)

    def test_context_contains_event_documents(self):
        """
        Given un événement avec des documents associés
        When on accède à la page de l'événement
        Then le contexte contient la clé 'event_documents'
        """
        response = self.client.get(self.event.url)
        self.assertIn("event_documents", response.context)

    def test_documents_ordered_by_collection_name(self):
        """
        Given un événement avec des documents dans différentes collections
        When on accède à la page de l'événement
        Then les documents sont triés par nom de collection
        """
        response = self.client.get(self.event.url)
        docs = list(response.context["event_documents"])
        collection_names = [d.document.collection.name for d in docs]
        self.assertEqual(collection_names, sorted(collection_names))

    def test_all_documents_present(self):
        """
        Given un événement avec 2 documents associés
        When on accède à la page de l'événement
        Then tous les documents sont présents dans le contexte
        """
        response = self.client.get(self.event.url)
        docs = list(response.context["event_documents"])
        self.assertEqual(len(docs), self.event.event_documents.count())


# ── Modèles EventStation / StationAssignment ─────────────────────────

class EventPageStationPropertiesTests(EventPageTreeMixin, WagtailPageTestCase):
    """Tests des propriétés stations sur EventPage."""

    def test_total_required_empty(self):
        """
        Given un événement sans postes
        When on accède à total_required
        Then la valeur est 0
        """
        self.assertEqual(self.event.total_required, 0)

    def test_total_assigned_empty(self):
        """
        Given un événement sans postes
        When on accède à total_assigned
        Then la valeur est 0
        """
        self.assertEqual(self.event.total_assigned, 0)

    def test_total_required_with_stations(self):
        """
        Given un événement avec un poste Frites (2) et un poste BBQ (3)
        When on accède à total_required
        Then la valeur est 5
        """
        EventStation.objects.create(event=self.event, name="Frites", required_count=2)
        EventStation.objects.create(event=self.event, name="BBQ", required_count=3)
        self.assertEqual(self.event.total_required, 5)

    def test_total_assigned_with_assignments(self):
        """
        Given un événement avec 3 affectations réparties sur 2 postes
        When on accède à total_assigned
        Then la valeur est 3
        """
        s1 = EventStation.objects.create(event=self.event, name="Frites", required_count=2)
        s2 = EventStation.objects.create(event=self.event, name="BBQ", required_count=3)
        StationAssignment.objects.create(station=s1, name="Alice")
        StationAssignment.objects.create(station=s2, name="Bob")
        StationAssignment.objects.create(station=s2, name="Charlie")
        self.assertEqual(self.event.total_assigned, 3)

    def test_stations_with_counts_returns_all(self):
        """
        Given un événement avec 2 postes (order 0 et 1)
        When on accède à stations_with_counts
        Then les 2 postes sont retournés triés par order
        """
        EventStation.objects.create(event=self.event, name="Frites", order=1)
        EventStation.objects.create(event=self.event, name="BBQ", order=0)
        stations = list(self.event.stations_with_counts)
        self.assertEqual(len(stations), 2)
        self.assertEqual(stations[0].name, "BBQ")


class EventStationModelTests(EventPageTreeMixin, WagtailPageTestCase):
    """Tests unitaires pour EventStation et StationAssignment."""

    def test_station_str(self):
        """
        Given un poste BBQ lié à l'événement "Fête du 13 Juillet"
        When on appelle str() sur le poste
        Then le résultat est "BBQ — Fête du 13 Juillet"
        """
        station = EventStation.objects.create(
            event=self.event, name="BBQ", required_count=2,
        )
        self.assertEqual(str(station), "BBQ — Fête du 13 Juillet")

    def test_assigned_count_empty(self):
        """
        Given un poste Caisse sans affectation
        When on accède à assigned_count
        Then la valeur est 0
        """
        station = EventStation.objects.create(
            event=self.event, name="Caisse", required_count=2,
        )
        self.assertEqual(station.assigned_count, 0)

    def test_assigned_count_with_people(self):
        """
        Given un poste Caisse avec 2 personnes affectées
        When on accède à assigned_count
        Then la valeur est 2
        """
        station = EventStation.objects.create(
            event=self.event, name="Caisse", required_count=2,
        )
        StationAssignment.objects.create(station=station, name="Alice")
        StationAssignment.objects.create(station=station, name="Bob")
        self.assertEqual(station.assigned_count, 2)

    def test_is_complete_false(self):
        """
        Given un poste Frites (required=2) avec 1 seule affectation
        When on accède à is_complete
        Then la valeur est False
        """
        station = EventStation.objects.create(
            event=self.event, name="Frites", required_count=2,
        )
        StationAssignment.objects.create(station=station, name="Alice")
        self.assertFalse(station.is_complete)

    def test_is_complete_true(self):
        """
        Given un poste Frites (required=2) avec 2 affectations
        When on accède à is_complete
        Then la valeur est True
        """
        station = EventStation.objects.create(
            event=self.event, name="Frites", required_count=2,
        )
        StationAssignment.objects.create(station=station, name="Alice")
        StationAssignment.objects.create(station=station, name="Bob")
        self.assertTrue(station.is_complete)

    def test_is_complete_over_required(self):
        """
        Given un poste Frites (required=1) avec 2 affectations
        When on accède à is_complete
        Then la valeur est True (sureffectif accepté)
        """
        station = EventStation.objects.create(
            event=self.event, name="Frites", required_count=1,
        )
        StationAssignment.objects.create(station=station, name="Alice")
        StationAssignment.objects.create(station=station, name="Bob")
        self.assertTrue(station.is_complete)

    def test_station_ordering(self):
        """
        Given 3 postes avec order 2, 1, 0
        When on récupère les stations de l'événement
        Then elles sont triées par order croissant
        """
        s2 = EventStation.objects.create(event=self.event, name="BBQ", order=2)
        s1 = EventStation.objects.create(event=self.event, name="Caisse", order=1)
        s0 = EventStation.objects.create(event=self.event, name="Frites", order=0)
        stations = list(self.event.stations.all())
        self.assertEqual(stations, [s0, s1, s2])

    def test_cascade_delete_event(self):
        """
        Given un événement avec un poste et une affectation
        When on supprime l'événement
        Then les postes et affectations sont supprimés en cascade
        """
        station = EventStation.objects.create(
            event=self.event, name="Buvette", required_count=3,
        )
        StationAssignment.objects.create(station=station, name="Alice")
        self.event.delete()
        self.assertEqual(EventStation.objects.count(), 0)
        self.assertEqual(StationAssignment.objects.count(), 0)

    def test_cascade_delete_station(self):
        """
        Given un poste Buvette avec 2 affectations
        When on supprime le poste
        Then les affectations sont supprimées en cascade
        """
        station = EventStation.objects.create(
            event=self.event, name="Buvette", required_count=3,
        )
        StationAssignment.objects.create(station=station, name="Alice")
        StationAssignment.objects.create(station=station, name="Bob")
        station.delete()
        self.assertEqual(StationAssignment.objects.count(), 0)

    def test_assignment_str_without_role(self):
        """
        Given une affectation "Alice" sans rôle
        When on appelle str() sur l'affectation
        Then le résultat est "Alice"
        """
        station = EventStation.objects.create(event=self.event, name="Caisse")
        a = StationAssignment.objects.create(station=station, name="Alice")
        self.assertEqual(str(a), "Alice")

    def test_assignment_str_with_role(self):
        """
        Given une affectation "Bob" avec le rôle "bière uniquement"
        When on appelle str() sur l'affectation
        Then le résultat est "Bob (bière uniquement)"
        """
        station = EventStation.objects.create(event=self.event, name="Buvette")
        a = StationAssignment.objects.create(
            station=station, name="Bob", role="bière uniquement",
        )
        self.assertEqual(str(a), "Bob (bière uniquement)")

    def test_assignment_ordering(self):
        """
        Given 3 affectations créées dans le désordre (Charlie, Alice, Bob)
        When on récupère les affectations du poste
        Then elles sont triées par nom alphabétique
        """
        station = EventStation.objects.create(event=self.event, name="Buvette")
        StationAssignment.objects.create(station=station, name="Charlie")
        StationAssignment.objects.create(station=station, name="Alice")
        StationAssignment.objects.create(station=station, name="Bob")
        names = list(station.assignments.values_list('name', flat=True))
        self.assertEqual(names, ["Alice", "Bob", "Charlie"])


# ── Helpers pour les vues stations ───────────────────────────────────

class StationViewMixin(EventPageTreeMixin):
    """setUp partagé : crée un superuser, un modérateur (groupe) et un user lambda."""

    def setUp(self):
        super().setUp()
        self.moderator = User.objects.create_superuser(
            "modo", "modo@test.com", "pass",
        )
        self.group_moderator = User.objects.create_user(
            "modo_group", "mg@test.com", "pass",
        )
        moderators_group, _ = Group.objects.get_or_create(name='Moderators')
        self.group_moderator.groups.add(moderators_group)
        self.lambda_user = User.objects.create_user(
            "lambda", "lambda@test.com", "pass",
        )


# ── Vue station_board ────────────────────────────────────────────────

class StationBoardViewTests(StationViewMixin, WagtailPageTestCase):
    """Tests de la vue station_board."""

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il accède au tableau des postes
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse('events:station_board', args=[self.event.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il accède au tableau des postes
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse('events:station_board', args=[self.event.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_moderator_can_access(self):
        """
        Given un superuser authentifié
        When il accède au tableau des postes
        Then la réponse est 200 avec le template station_board.html
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_board', args=[self.event.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/station_board.html')

    def test_moderator_group_can_access(self):
        """
        Given un utilisateur du groupe Moderators
        When il accède au tableau des postes
        Then la réponse est 200
        """
        self.client.force_login(self.group_moderator)
        url = reverse('events:station_board', args=[self.event.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_context_has_forms(self):
        """
        Given un modérateur authentifié
        When il accède au tableau des postes
        Then le contexte contient station_form et assignment_form
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_board', args=[self.event.pk])
        response = self.client.get(url)
        self.assertIn('station_form', response.context)
        self.assertIn('assignment_form', response.context)

    def test_context_has_stations(self):
        """
        Given un événement avec un poste Frites
        When un modérateur accède au tableau des postes
        Then le contexte contient 1 station via event.stations_with_counts
        """
        self.client.force_login(self.moderator)
        EventStation.objects.create(event=self.event, name="Frites", required_count=2)
        url = reverse('events:station_board', args=[self.event.pk])
        response = self.client.get(url)
        event = response.context['event']
        self.assertEqual(len(event.stations_with_counts), 1)

    def test_context_totals(self):
        """
        Given un événement avec un poste (required=2) et 1 affectation
        When un modérateur accède au tableau des postes
        Then total_required vaut 2 et total_assigned vaut 1
        """
        self.client.force_login(self.moderator)
        s = EventStation.objects.create(event=self.event, name="Frites", required_count=2)
        StationAssignment.objects.create(station=s, name="Alice")
        url = reverse('events:station_board', args=[self.event.pk])
        response = self.client.get(url)
        event = response.context['event']
        self.assertEqual(event.total_required, 2)
        self.assertEqual(event.total_assigned, 1)

    def test_nonexistent_event_404(self):
        """
        Given un modérateur authentifié
        When il accède au tableau d'un événement inexistant (pk=99999)
        Then la réponse est 404
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_board', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ── Vue station_create ───────────────────────────────────────────────

class StationCreateViewTests(StationViewMixin, WagtailPageTestCase):
    """Tests de la vue station_create."""

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il tente de créer un poste via POST
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse('events:station_create', args=[self.event.pk])
        response = self.client.post(url, {'name': 'BBQ'})
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il tente de créer un poste via POST
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse('events:station_create', args=[self.event.pk])
        response = self.client.post(url, {'name': 'BBQ'})
        self.assertEqual(response.status_code, 302)

    def test_get_not_allowed(self):
        """
        Given un modérateur authentifié
        When il envoie un GET sur station_create
        Then la réponse est 405 (Method Not Allowed)
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_create', args=[self.event.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_create_station(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec name='BBQ', description='Grillades', required_count=3
        Then le poste BBQ est créé avec les bonnes valeurs
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_create', args=[self.event.pk])
        response = self.client.post(url, {
            'name': 'BBQ',
            'description': 'Grillades',
            'required_count': '3',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(EventStation.objects.filter(name='BBQ', event=self.event).exists())
        station = EventStation.objects.get(name='BBQ')
        self.assertEqual(station.required_count, 3)
        self.assertEqual(station.description, 'Grillades')

    def test_create_station_empty_name(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec un nom vide
        Then aucun poste n'est créé
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_create', args=[self.event.pk])
        response = self.client.post(url, {'name': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EventStation.objects.count(), 0)

    def test_create_station_whitespace_name(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec un nom composé d'espaces
        Then aucun poste n'est créé
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_create', args=[self.event.pk])
        self.client.post(url, {'name': '   '})
        self.assertEqual(EventStation.objects.count(), 0)

    def test_create_station_invalid_required_count(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec required_count='abc'
        Then aucun poste n'est créé (erreur de validation)
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_create', args=[self.event.pk])
        response = self.client.post(url, {'name': 'Test', 'required_count': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EventStation.objects.count(), 0)

    def test_create_station_negative_required_count(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec required_count='-5'
        Then aucun poste n'est créé (erreur de validation min_value=1)
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_create', args=[self.event.pk])
        self.client.post(url, {'name': 'Test', 'required_count': '-5'})
        self.assertEqual(EventStation.objects.count(), 0)


# ── Vue station_delete ───────────────────────────────────────────────

class StationDeleteViewTests(StationViewMixin, WagtailPageTestCase):
    """Tests de la vue station_delete."""

    def setUp(self):
        super().setUp()
        self.station = EventStation.objects.create(
            event=self.event, name="Buvette", required_count=3,
        )
        StationAssignment.objects.create(station=self.station, name="Alice")

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il tente de supprimer un poste via POST
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse('events:station_delete', args=[self.station.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il tente de supprimer un poste via POST
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse('events:station_delete', args=[self.station.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_delete_station(self):
        """
        Given un modérateur et un poste Buvette avec 1 affectation
        When il envoie un POST pour supprimer le poste
        Then le poste et ses affectations sont supprimés
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_delete', args=[self.station.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(EventStation.objects.filter(pk=self.station.pk).exists())
        self.assertEqual(StationAssignment.objects.count(), 0)

    def test_delete_nonexistent_station(self):
        """
        Given un modérateur authentifié
        When il tente de supprimer un poste inexistant (pk=99999)
        Then la réponse est 404
        """
        self.client.force_login(self.moderator)
        url = reverse('events:station_delete', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ── Vue assignment_add ───────────────────────────────────────────────

class AssignmentAddViewTests(StationViewMixin, WagtailPageTestCase):
    """Tests de la vue assignment_add."""

    def setUp(self):
        super().setUp()
        self.station = EventStation.objects.create(
            event=self.event, name="Caisse", required_count=2,
        )

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il tente d'ajouter une affectation via POST
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse('events:assignment_add', args=[self.station.pk])
        response = self.client.post(url, {'name': 'Alice'})
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il tente d'ajouter une affectation via POST
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse('events:assignment_add', args=[self.station.pk])
        response = self.client.post(url, {'name': 'Alice'})
        self.assertEqual(response.status_code, 302)

    def test_add_assignment(self):
        """
        Given un modérateur et un poste Caisse
        When il envoie un POST avec name='Alice' et role='tickets'
        Then l'affectation est créée avec le bon nom et rôle
        """
        self.client.force_login(self.moderator)
        url = reverse('events:assignment_add', args=[self.station.pk])
        response = self.client.post(url, {'name': 'Alice', 'role': 'tickets'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            StationAssignment.objects.filter(
                station=self.station, name='Alice', role='tickets',
            ).exists()
        )

    def test_add_assignment_without_role(self):
        """
        Given un modérateur et un poste Caisse
        When il envoie un POST avec name='Bob' sans rôle
        Then l'affectation est créée avec un rôle vide
        """
        self.client.force_login(self.moderator)
        url = reverse('events:assignment_add', args=[self.station.pk])
        response = self.client.post(url, {'name': 'Bob'})
        self.assertEqual(response.status_code, 200)
        a = StationAssignment.objects.get(station=self.station, name='Bob')
        self.assertEqual(a.role, '')

    def test_add_assignment_empty_name(self):
        """
        Given un modérateur et un poste Caisse
        When il envoie un POST avec un nom vide
        Then aucune affectation n'est créée
        """
        self.client.force_login(self.moderator)
        url = reverse('events:assignment_add', args=[self.station.pk])
        response = self.client.post(url, {'name': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StationAssignment.objects.count(), 0)

    def test_add_multiple_assignments(self):
        """
        Given un modérateur et un poste Caisse
        When il ajoute successivement Alice puis Bob
        Then le poste a 2 affectations
        """
        self.client.force_login(self.moderator)
        url = reverse('events:assignment_add', args=[self.station.pk])
        self.client.post(url, {'name': 'Alice'})
        self.client.post(url, {'name': 'Bob'})
        self.assertEqual(self.station.assignments.count(), 2)

    def test_returns_station_card_partial(self):
        """
        Given un modérateur et un poste Caisse
        When il ajoute une affectation
        Then le template station_card.html est utilisé dans la réponse
        """
        self.client.force_login(self.moderator)
        url = reverse('events:assignment_add', args=[self.station.pk])
        response = self.client.post(url, {'name': 'Alice'})
        self.assertTemplateUsed(response, 'events/partials/station_card.html')


# ── Vue assignment_remove ────────────────────────────────────────────

class AssignmentRemoveViewTests(StationViewMixin, WagtailPageTestCase):
    """Tests de la vue assignment_remove."""

    def setUp(self):
        super().setUp()
        self.station = EventStation.objects.create(
            event=self.event, name="Service", required_count=2,
        )
        self.assignment = StationAssignment.objects.create(
            station=self.station, name="Alice",
        )

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il tente de retirer une affectation via POST
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse('events:assignment_remove', args=[self.assignment.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il tente de retirer une affectation via POST
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse('events:assignment_remove', args=[self.assignment.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_remove_assignment(self):
        """
        Given un modérateur et une affectation Alice sur le poste Service
        When il envoie un POST pour retirer l'affectation
        Then l'affectation est supprimée
        """
        self.client.force_login(self.moderator)
        url = reverse('events:assignment_remove', args=[self.assignment.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(StationAssignment.objects.filter(pk=self.assignment.pk).exists())

    def test_remove_nonexistent_assignment(self):
        """
        Given un modérateur authentifié
        When il tente de retirer une affectation inexistante (pk=99999)
        Then la réponse est 404
        """
        self.client.force_login(self.moderator)
        url = reverse('events:assignment_remove', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_remove_returns_station_card_partial(self):
        """
        Given un modérateur et une affectation existante
        When il retire l'affectation
        Then le template station_card.html est utilisé dans la réponse
        """
        self.client.force_login(self.moderator)
        url = reverse('events:assignment_remove', args=[self.assignment.pk])
        response = self.client.post(url)
        self.assertTemplateUsed(response, 'events/partials/station_card.html')

    def test_station_count_updates_after_remove(self):
        """
        Given un poste Service avec 2 affectations (Alice et Bob)
        When on retire l'affectation d'Alice
        Then assigned_count passe de 2 à 1
        """
        self.client.force_login(self.moderator)
        StationAssignment.objects.create(station=self.station, name="Bob")
        self.assertEqual(self.station.assigned_count, 2)
        url = reverse('events:assignment_remove', args=[self.assignment.pk])
        self.client.post(url)
        self.station.refresh_from_db()
        self.assertEqual(self.station.assigned_count, 1)
