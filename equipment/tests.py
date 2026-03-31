from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from wagtail.documents import get_document_model

from equipment.models import Equipment, EquipmentLoan, LoanItem

Document = get_document_model()


# ── Modèle Equipment ─────────────────────────────────────────────────


class EquipmentModelTests(TestCase):
    """Tests unitaires pour le modèle Equipment."""

    def test_str(self):
        """
        Given un matériel « Barnum »
        When on appelle str() dessus
        Then le résultat est « Barnum »
        """
        eq = Equipment.objects.create(name="Barnum", quantity=5)
        self.assertEqual(str(eq), "Barnum")

    def test_ordering(self):
        """
        Given 3 matériels créés dans le désordre (Tables, Barnums, Chaises)
        When on récupère la liste
        Then ils sont triés par nom alphabétique
        """
        Equipment.objects.create(name="Tables", quantity=10)
        Equipment.objects.create(name="Barnums", quantity=5)
        Equipment.objects.create(name="Chaises", quantity=30)
        names = list(Equipment.objects.values_list("name", flat=True))
        self.assertEqual(names, ["Barnums", "Chaises", "Tables"])

    def test_loaned_quantity_empty(self):
        """
        Given un matériel sans prêt
        When on accède à loaned_quantity
        Then la valeur est 0
        """
        eq = Equipment.objects.create(name="Barnum", quantity=5)
        self.assertEqual(eq.loaned_quantity, 0)

    def test_loaned_quantity_with_loans(self):
        """
        Given un matériel prêté dans 2 prêts (2 + 1)
        When on accède à loaned_quantity
        Then la valeur est 3
        """
        eq = Equipment.objects.create(name="Barnum", quantity=5)
        loan1 = EquipmentLoan.objects.create(borrower_name="Alice")
        loan2 = EquipmentLoan.objects.create(borrower_name="Bob")
        LoanItem.objects.create(loan=loan1, equipment=eq, quantity=2)
        LoanItem.objects.create(loan=loan2, equipment=eq, quantity=1)
        self.assertEqual(eq.loaned_quantity, 3)

    def test_available_quantity(self):
        """
        Given un matériel (stock=5) avec 2 unités prêtées
        When on accède à available_quantity
        Then la valeur est 3
        """
        eq = Equipment.objects.create(name="Barnum", quantity=5)
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        LoanItem.objects.create(loan=loan, equipment=eq, quantity=2)
        self.assertEqual(eq.available_quantity, 3)

    def test_available_quantity_all_loaned(self):
        """
        Given un matériel (stock=2) avec 2 unités prêtées
        When on accède à available_quantity
        Then la valeur est 0
        """
        eq = Equipment.objects.create(name="Barnum", quantity=2)
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        LoanItem.objects.create(loan=loan, equipment=eq, quantity=2)
        self.assertEqual(eq.available_quantity, 0)


# ── Modèle EquipmentLoan ─────────────────────────────────────────────


class EquipmentLoanModelTests(TestCase):
    """Tests unitaires pour le modèle EquipmentLoan."""

    def test_str(self):
        """
        Given un prêt à « Alice »
        When on appelle str() dessus
        Then le résultat est « Prêt à Alice »
        """
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        self.assertEqual(str(loan), "Prêt à Alice")

    def test_total_items_empty(self):
        """
        Given un prêt sans lignes
        When on accède à total_items
        Then la valeur est 0
        """
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        self.assertEqual(loan.total_items, 0)

    def test_total_items_with_lines(self):
        """
        Given un prêt avec 2 lignes de matériel
        When on accède à total_items
        Then la valeur est 2
        """
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        eq1 = Equipment.objects.create(name="Barnum", quantity=5)
        eq2 = Equipment.objects.create(name="Table", quantity=10)
        LoanItem.objects.create(loan=loan, equipment=eq1, quantity=2)
        LoanItem.objects.create(loan=loan, equipment=eq2, quantity=3)
        self.assertEqual(loan.total_items, 2)

    def test_total_quantity(self):
        """
        Given un prêt avec 2 lignes (quantités 2 et 3)
        When on accède à total_quantity
        Then la valeur est 5
        """
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        eq1 = Equipment.objects.create(name="Barnum", quantity=5)
        eq2 = Equipment.objects.create(name="Table", quantity=10)
        LoanItem.objects.create(loan=loan, equipment=eq1, quantity=2)
        LoanItem.objects.create(loan=loan, equipment=eq2, quantity=3)
        self.assertEqual(loan.total_quantity, 5)

    def test_total_quantity_empty(self):
        """
        Given un prêt sans lignes
        When on accède à total_quantity
        Then la valeur est 0
        """
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        self.assertEqual(loan.total_quantity, 0)

    def test_cascade_delete_loan(self):
        """
        Given un prêt avec 2 lignes de matériel
        When on supprime le prêt
        Then les lignes sont supprimées en cascade
        """
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        eq = Equipment.objects.create(name="Barnum", quantity=5)
        LoanItem.objects.create(loan=loan, equipment=eq, quantity=2)
        LoanItem.objects.create(loan=loan, equipment=eq, quantity=1)
        loan.delete()
        self.assertEqual(LoanItem.objects.count(), 0)


# ── Modèle LoanItem ──────────────────────────────────────────────────


class LoanItemModelTests(TestCase):
    """Tests unitaires pour le modèle LoanItem."""

    def test_str(self):
        """
        Given une ligne de prêt « Barnum ×2 »
        When on appelle str() dessus
        Then le résultat est « Barnum ×2 »
        """
        eq = Equipment.objects.create(name="Barnum", quantity=5)
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        item = LoanItem.objects.create(loan=loan, equipment=eq, quantity=2)
        self.assertEqual(str(item), "Barnum ×2")

    def test_ordering(self):
        """
        Given 2 lignes de prêt (Table, Barnum)
        When on récupère les lignes du prêt
        Then elles sont triées par nom de matériel
        """
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        eq1 = Equipment.objects.create(name="Table", quantity=10)
        eq2 = Equipment.objects.create(name="Barnum", quantity=5)
        LoanItem.objects.create(loan=loan, equipment=eq1, quantity=1)
        LoanItem.objects.create(loan=loan, equipment=eq2, quantity=1)
        names = list(loan.items.values_list("equipment__name", flat=True))
        self.assertEqual(names, ["Barnum", "Table"])

    def test_cascade_delete_equipment(self):
        """
        Given une ligne de prêt liée à un matériel
        When on supprime le matériel
        Then la ligne de prêt est supprimée en cascade
        """
        eq = Equipment.objects.create(name="Barnum", quantity=5)
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        LoanItem.objects.create(loan=loan, equipment=eq, quantity=2)
        eq.delete()
        self.assertEqual(LoanItem.objects.count(), 0)


# ── Helpers pour les vues ─────────────────────────────────────────────


class EquipmentViewMixin:
    """setUp partagé : crée un superuser, un modérateur (groupe) et un user lambda."""

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


# ── Vue equipment_board ──────────────────────────────────────────────


class EquipmentBoardViewTests(EquipmentViewMixin, TestCase):
    """Tests de la vue equipment_board."""

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il accède à l'inventaire du matériel
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse("equipment:equipment_board")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il accède à l'inventaire du matériel
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse("equipment:equipment_board")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_moderator_can_access(self):
        """
        Given un superuser authentifié
        When il accède à l'inventaire du matériel
        Then la réponse est 200 avec le template equipment_board.html
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:equipment_board")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipment/equipment_board.html")

    def test_moderator_group_can_access(self):
        """
        Given un utilisateur du groupe Moderators
        When il accède à l'inventaire du matériel
        Then la réponse est 200
        """
        self.client.force_login(self.group_moderator)
        url = reverse("equipment:equipment_board")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_context_has_equipments(self):
        """
        Given un matériel Barnum dans l'inventaire
        When un modérateur accède à l'inventaire
        Then le contexte contient la liste des matériels
        """
        self.client.force_login(self.moderator)
        Equipment.objects.create(name="Barnum", quantity=5)
        url = reverse("equipment:equipment_board")
        response = self.client.get(url)
        self.assertEqual(len(response.context["equipments"]), 1)

    def test_context_has_loans(self):
        """
        Given un prêt existant
        When un modérateur accède à l'inventaire
        Then le contexte contient la liste des prêts
        """
        self.client.force_login(self.moderator)
        EquipmentLoan.objects.create(borrower_name="Alice")
        url = reverse("equipment:equipment_board")
        response = self.client.get(url)
        self.assertEqual(len(response.context["loans"]), 1)


# ── Vue equipment_create ─────────────────────────────────────────────


class EquipmentCreateViewTests(EquipmentViewMixin, TestCase):
    """Tests de la vue equipment_create."""

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il tente de créer un matériel via POST
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse("equipment:equipment_create")
        response = self.client.post(url, {"name": "Barnum"})
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il tente de créer un matériel via POST
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse("equipment:equipment_create")
        response = self.client.post(url, {"name": "Barnum"})
        self.assertEqual(response.status_code, 302)

    def test_get_not_allowed(self):
        """
        Given un modérateur authentifié
        When il envoie un GET sur equipment_create
        Then la réponse est 405 (Method Not Allowed)
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:equipment_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_create_equipment(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec name='Barnum' et quantity=5
        Then le matériel Barnum est créé avec une quantité de 5
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:equipment_create")
        response = self.client.post(url, {"name": "Barnum", "quantity": "5"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Equipment.objects.filter(name="Barnum").exists())
        eq = Equipment.objects.get(name="Barnum")
        self.assertEqual(eq.quantity, 5)

    def test_create_equipment_empty_name(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec un nom vide
        Then aucun matériel n'est créé
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:equipment_create")
        self.client.post(url, {"name": ""})
        self.assertEqual(Equipment.objects.count(), 0)

    def test_create_equipment_whitespace_name(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec un nom composé d'espaces
        Then aucun matériel n'est créé
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:equipment_create")
        self.client.post(url, {"name": "   "})
        self.assertEqual(Equipment.objects.count(), 0)

    def test_create_equipment_invalid_quantity(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec quantity='abc'
        Then aucun matériel n'est créé (erreur de validation)
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:equipment_create")
        self.client.post(url, {"name": "Barnum", "quantity": "abc"})
        self.assertEqual(Equipment.objects.count(), 0)

    def test_create_equipment_negative_quantity(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec quantity='-5'
        Then aucun matériel n'est créé (erreur de validation)
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:equipment_create")
        self.client.post(url, {"name": "Barnum", "quantity": "-5"})
        self.assertEqual(Equipment.objects.count(), 0)


# ── Vue equipment_delete ─────────────────────────────────────────────


class EquipmentDeleteViewTests(EquipmentViewMixin, TestCase):
    """Tests de la vue equipment_delete."""

    def setUp(self):
        super().setUp()
        self.equipment = Equipment.objects.create(name="Barnum", quantity=5)

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il tente de supprimer un matériel via POST
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse("equipment:equipment_delete", args=[self.equipment.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il tente de supprimer un matériel via POST
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse("equipment:equipment_delete", args=[self.equipment.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_delete_equipment(self):
        """
        Given un modérateur et un matériel Barnum
        When il envoie un POST pour supprimer le matériel
        Then le matériel est supprimé
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:equipment_delete", args=[self.equipment.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Equipment.objects.filter(pk=self.equipment.pk).exists())

    def test_delete_nonexistent_equipment(self):
        """
        Given un modérateur authentifié
        When il tente de supprimer un matériel inexistant (pk=99999)
        Then la réponse est 404
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:equipment_delete", args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ── Vue loan_create ──────────────────────────────────────────────────


class LoanCreateViewTests(EquipmentViewMixin, TestCase):
    """Tests de la vue loan_create."""

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il tente de créer un prêt via POST
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse("equipment:loan_create")
        response = self.client.post(url, {"borrower_name": "Alice"})
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il tente de créer un prêt via POST
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse("equipment:loan_create")
        response = self.client.post(url, {"borrower_name": "Alice"})
        self.assertEqual(response.status_code, 302)

    def test_get_not_allowed(self):
        """
        Given un modérateur authentifié
        When il envoie un GET sur loan_create
        Then la réponse est 405 (Method Not Allowed)
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_create_loan(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec borrower_name='Alice'
        Then le prêt est créé pour Alice
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_create")
        response = self.client.post(url, {"borrower_name": "Alice", "start_date": "2026-03-31", "end_date": "2026-04-15"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(EquipmentLoan.objects.filter(borrower_name="Alice").exists())

    def test_create_loan_with_agreement(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec un fichier de convention
        Then le prêt est créé avec un document Wagtail attaché
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_create")
        agreement = SimpleUploadedFile("convention.pdf", b"pdf-content", content_type="application/pdf")
        response = self.client.post(url, {"borrower_name": "Alice", "start_date": "2026-03-31", "end_date": "2026-04-15", "agreement": agreement})
        self.assertEqual(response.status_code, 200)
        loan = EquipmentLoan.objects.get(borrower_name="Alice")
        self.assertIsNotNone(loan.agreement)
        self.assertIsInstance(loan.agreement, Document)

    def test_create_loan_empty_borrower(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec un emprunteur vide
        Then aucun prêt n'est créé
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_create")
        self.client.post(url, {"borrower_name": ""})
        self.assertEqual(EquipmentLoan.objects.count(), 0)

    def test_create_loan_whitespace_borrower(self):
        """
        Given un modérateur authentifié
        When il envoie un POST avec un emprunteur composé d'espaces
        Then aucun prêt n'est créé
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_create")
        self.client.post(url, {"borrower_name": "   "})
        self.assertEqual(EquipmentLoan.objects.count(), 0)


# ── Vue loan_delete ──────────────────────────────────────────────────


class LoanDeleteViewTests(EquipmentViewMixin, TestCase):
    """Tests de la vue loan_delete."""

    def setUp(self):
        super().setUp()
        self.loan = EquipmentLoan.objects.create(borrower_name="Alice")
        self.equipment = Equipment.objects.create(name="Barnum", quantity=5)
        LoanItem.objects.create(loan=self.loan, equipment=self.equipment, quantity=2)

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il tente de supprimer un prêt via POST
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse("equipment:loan_delete", args=[self.loan.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il tente de supprimer un prêt via POST
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse("equipment:loan_delete", args=[self.loan.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_delete_loan(self):
        """
        Given un modérateur et un prêt à Alice avec 1 ligne
        When il envoie un POST pour supprimer le prêt
        Then le prêt et ses lignes sont supprimés
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_delete", args=[self.loan.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(EquipmentLoan.objects.filter(pk=self.loan.pk).exists())
        self.assertEqual(LoanItem.objects.count(), 0)

    def test_delete_nonexistent_loan(self):
        """
        Given un modérateur authentifié
        When il tente de supprimer un prêt inexistant (pk=99999)
        Then la réponse est 404
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_delete", args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ── Vue loan_item_add ────────────────────────────────────────────────


class LoanItemAddViewTests(EquipmentViewMixin, TestCase):
    """Tests de la vue loan_item_add."""

    def setUp(self):
        super().setUp()
        self.loan = EquipmentLoan.objects.create(borrower_name="Alice")
        self.equipment = Equipment.objects.create(name="Barnum", quantity=5)

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il tente d'ajouter du matériel à un prêt via POST
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse("equipment:loan_item_add", args=[self.loan.pk])
        response = self.client.post(url, {"equipment": self.equipment.pk, "quantity": "1"})
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il tente d'ajouter du matériel à un prêt via POST
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse("equipment:loan_item_add", args=[self.loan.pk])
        response = self.client.post(url, {"equipment": self.equipment.pk, "quantity": "1"})
        self.assertEqual(response.status_code, 302)

    def test_add_item(self):
        """
        Given un modérateur, un prêt et un matériel Barnum
        When il envoie un POST avec equipment=Barnum et quantity=3
        Then la ligne de prêt est créée avec la bonne quantité
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_add", args=[self.loan.pk])
        response = self.client.post(url, {"equipment": self.equipment.pk, "quantity": "3"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            LoanItem.objects.filter(loan=self.loan, equipment=self.equipment, quantity=3).exists()
        )

    def test_add_item_no_equipment(self):
        """
        Given un modérateur et un prêt
        When il envoie un POST sans sélectionner de matériel
        Then aucune ligne de prêt n'est créée
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_add", args=[self.loan.pk])
        response = self.client.post(url, {"equipment": "", "quantity": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LoanItem.objects.count(), 0)

    def test_add_item_invalid_quantity(self):
        """
        Given un modérateur, un prêt et un matériel
        When il envoie un POST avec quantity='abc'
        Then aucune ligne n'est créée (erreur de validation)
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_add", args=[self.loan.pk])
        self.client.post(url, {"equipment": self.equipment.pk, "quantity": "abc"})
        self.assertEqual(LoanItem.objects.count(), 0)

    def test_add_multiple_items(self):
        """
        Given un modérateur et un prêt
        When il ajoute 2 matériels différents
        Then le prêt a 2 lignes
        """
        self.client.force_login(self.moderator)
        eq2 = Equipment.objects.create(name="Table", quantity=10)
        url = reverse("equipment:loan_item_add", args=[self.loan.pk])
        self.client.post(url, {"equipment": self.equipment.pk, "quantity": "2"})
        self.client.post(url, {"equipment": eq2.pk, "quantity": "5"})
        self.assertEqual(self.loan.items.count(), 2)

    def test_returns_loan_card_partial(self):
        """
        Given un modérateur et un prêt
        When il ajoute du matériel
        Then le template loan_card.html est utilisé dans la réponse
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_add", args=[self.loan.pk])
        response = self.client.post(url, {"equipment": self.equipment.pk, "quantity": "1"})
        self.assertTemplateUsed(response, "equipment/partials/loan_card.html")

    def test_nonexistent_loan(self):
        """
        Given un modérateur authentifié
        When il tente d'ajouter du matériel à un prêt inexistant (pk=99999)
        Then la réponse est 404
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_add", args=[99999])
        response = self.client.post(url, {"equipment": self.equipment.pk, "quantity": "1"})
        self.assertEqual(response.status_code, 404)

    def test_add_item_exceeds_stock(self):
        """
        Given un matériel avec 5 en stock et 0 prêté
        When un modérateur tente d'en prêter 6
        Then aucune ligne n'est créée et un message d'erreur est retourné
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_add", args=[self.loan.pk])
        response = self.client.post(url, {"equipment": self.equipment.pk, "quantity": "6"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LoanItem.objects.count(), 0)
        self.assertContains(response, "Stock insuffisant")

    def test_add_item_exceeds_remaining_stock(self):
        """
        Given un matériel avec 5 en stock dont 3 déjà prêtés
        When un modérateur tente d'en prêter 3 de plus (il n'en reste que 2)
        Then aucune ligne n'est créée et un message d'erreur est retourné
        """
        self.client.force_login(self.moderator)
        LoanItem.objects.create(loan=self.loan, equipment=self.equipment, quantity=3)
        loan2 = EquipmentLoan.objects.create(borrower_name="Bob")
        url = reverse("equipment:loan_item_add", args=[loan2.pk])
        response = self.client.post(url, {"equipment": self.equipment.pk, "quantity": "3"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LoanItem.objects.filter(loan=loan2).count(), 0)
        self.assertContains(response, "Stock insuffisant")

    def test_add_item_zero_available(self):
        """
        Given un matériel entièrement prêté (5/5)
        When un modérateur tente d'en prêter 1
        Then aucune ligne n'est créée et un message d'erreur est retourné
        """
        self.client.force_login(self.moderator)
        LoanItem.objects.create(loan=self.loan, equipment=self.equipment, quantity=5)
        loan2 = EquipmentLoan.objects.create(borrower_name="Bob")
        url = reverse("equipment:loan_item_add", args=[loan2.pk])
        response = self.client.post(url, {"equipment": self.equipment.pk, "quantity": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LoanItem.objects.filter(loan=loan2).count(), 0)
        self.assertContains(response, "Stock insuffisant")

    def test_add_item_triggers_equipment_updated(self):
        """
        Given un modérateur qui ajoute du matériel à un prêt
        When la réponse est reçue
        Then le header HX-Trigger contient « equipmentUpdated »
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_add", args=[self.loan.pk])
        response = self.client.post(url, {"equipment": self.equipment.pk, "quantity": "1"})
        self.assertEqual(response["HX-Trigger"], "equipmentUpdated")


# ── Vue loan_item_remove ─────────────────────────────────────────────


class LoanItemRemoveViewTests(EquipmentViewMixin, TestCase):
    """Tests de la vue loan_item_remove."""

    def setUp(self):
        super().setUp()
        self.loan = EquipmentLoan.objects.create(borrower_name="Alice")
        self.equipment = Equipment.objects.create(name="Barnum", quantity=5)
        self.item = LoanItem.objects.create(loan=self.loan, equipment=self.equipment, quantity=2)

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il tente de retirer du matériel d'un prêt via POST
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse("equipment:loan_item_remove", args=[self.item.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il tente de retirer du matériel d'un prêt via POST
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse("equipment:loan_item_remove", args=[self.item.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_remove_item(self):
        """
        Given un modérateur et une ligne de prêt
        When il envoie un POST pour retirer la ligne
        Then la ligne est supprimée
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_remove", args=[self.item.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(LoanItem.objects.filter(pk=self.item.pk).exists())

    def test_remove_nonexistent_item(self):
        """
        Given un modérateur authentifié
        When il tente de retirer une ligne inexistante (pk=99999)
        Then la réponse est 404
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_remove", args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_returns_loan_card_partial(self):
        """
        Given un modérateur et une ligne de prêt
        When il retire la ligne
        Then le template loan_card.html est utilisé dans la réponse
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_remove", args=[self.item.pk])
        response = self.client.post(url)
        self.assertTemplateUsed(response, "equipment/partials/loan_card.html")

    def test_loan_quantity_updates_after_remove(self):
        """
        Given un prêt avec 2 lignes (quantités 2 et 3)
        When on retire la première ligne
        Then total_quantity passe de 5 à 3
        """
        self.client.force_login(self.moderator)
        LoanItem.objects.create(loan=self.loan, equipment=self.equipment, quantity=3)
        self.assertEqual(self.loan.total_quantity, 5)
        url = reverse("equipment:loan_item_remove", args=[self.item.pk])
        self.client.post(url)
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.total_quantity, 3)

    def test_remove_item_triggers_equipment_updated(self):
        """
        Given un modérateur qui retire du matériel d'un prêt
        When la réponse est reçue
        Then le header HX-Trigger contient « equipmentUpdated »
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:loan_item_remove", args=[self.item.pk])
        response = self.client.post(url)
        self.assertEqual(response["HX-Trigger"], "equipmentUpdated")


# ── Vue equipment_list ───────────────────────────────────────────────


class EquipmentListViewTests(EquipmentViewMixin, TestCase):
    """Tests de la vue equipment_list (GET partial HTMX)."""

    def test_anonymous_redirects_to_login(self):
        """
        Given un visiteur anonyme
        When il accède à la liste du matériel
        Then il est redirigé vers la page de connexion (302)
        """
        url = reverse("equipment:equipment_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_lambda_user_redirected(self):
        """
        Given un utilisateur sans le groupe Moderators
        When il accède à la liste du matériel
        Then il est redirigé (302)
        """
        self.client.force_login(self.lambda_user)
        url = reverse("equipment:equipment_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_moderator_can_access(self):
        """
        Given un modérateur authentifié
        When il accède à la liste du matériel
        Then la réponse est 200 et utilise le bon template
        """
        self.client.force_login(self.moderator)
        url = reverse("equipment:equipment_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipment/partials/equipment_list.html")

    def test_context_has_equipments(self):
        """
        Given 2 matériels en base
        When un modérateur accède à la liste
        Then le context contient les 2 matériels
        """
        self.client.force_login(self.moderator)
        Equipment.objects.create(name="Barnum", quantity=5)
        Equipment.objects.create(name="Table", quantity=10)
        url = reverse("equipment:equipment_list")
        response = self.client.get(url)
        self.assertEqual(len(response.context["equipments"]), 2)


# ── HX-Trigger sur loan_delete ───────────────────────────────────────


class LoanDeleteHxTriggerTests(EquipmentViewMixin, TestCase):
    """Vérifie que loan_delete envoie HX-Trigger: equipmentUpdated."""

    def test_delete_loan_triggers_equipment_updated(self):
        """
        Given un modérateur qui supprime un prêt
        When la réponse est reçue
        Then le header HX-Trigger contient « equipmentUpdated »
        """
        self.client.force_login(self.moderator)
        loan = EquipmentLoan.objects.create(borrower_name="Alice")
        url = reverse("equipment:loan_delete", args=[loan.pk])
        response = self.client.post(url)
        self.assertEqual(response["HX-Trigger"], "equipmentUpdated")
