import io
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ia.models import Summary
from ia.utils import UNREADABLE_MSG


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_moderator(username="mod"):
    return User.objects.create_user(
        username=username, password="pass", is_superuser=True
    )


def _make_fake_document(title="Facture test", date=None, file_path="/tmp/test.pdf"):
    """Retourne un objet document factice (pas en BDD) pour les tests utils."""
    doc = MagicMock()
    doc.title = title
    doc.document_date = date
    doc.file.path = file_path
    return doc


# ---------------------------------------------------------------------------
# Tests : ia.utils.summarize_document
# ---------------------------------------------------------------------------

class SummarizeDocumentUtilsTests(TestCase):

    def _call(self, ocr_text, chat_response="Résumé factice"):
        doc = _make_fake_document()
        with (
            patch("ia.utils.Path.read_bytes", return_value=b"%PDF fake"),
            patch("ia.utils._call_ocr", return_value=ocr_text) as mock_ocr,
            patch("ia.utils._call_chat", return_value=chat_response) as mock_chat,
        ):
            from ia.utils import summarize_document
            result = summarize_document(doc)
        return result, mock_ocr, mock_chat

    def test_unreadable_when_ocr_too_short(self):
        """
        Given un document dont le texte OCR est trop court (< seuil)
        When on appelle summarize_document
        Then le message UNREADABLE_MSG est retourné et le chat n'est pas appelé
        """
        result, _, mock_chat = self._call(ocr_text="trop court")
        self.assertEqual(result, UNREADABLE_MSG)
        mock_chat.assert_not_called()

    def test_empty_ocr_returns_unreadable(self):
        """
        Given un document dont le texte OCR est vide
        When on appelle summarize_document
        Then le message UNREADABLE_MSG est retourné et le chat n'est pas appelé
        """
        result, _, mock_chat = self._call(ocr_text="")
        self.assertEqual(result, UNREADABLE_MSG)
        mock_chat.assert_not_called()

    def test_readable_document_calls_chat(self):
        """
        Given un document dont le texte OCR est suffisamment long
        When on appelle summarize_document
        Then le chat est appelé et son résultat est retourné
        """
        long_text = "Facture EDF — 01/05/2026 — montant : 120,00 € TTC pour l'association"
        result, mock_ocr, mock_chat = self._call(ocr_text=long_text, chat_response="Super résumé")
        self.assertEqual(result, "Super résumé")
        mock_ocr.assert_called_once()
        mock_chat.assert_called_once()

    def test_chat_receives_ocr_text_in_prompt(self):
        """
        Given un document avec un texte OCR lisible
        When on appelle summarize_document
        Then le texte OCR est inclus dans le message utilisateur envoyé au chat
        """
        long_text = "Facture SAUR — eau — 01/05/2026 — 45,00 € TTC pour l'association CDF"
        self._call(ocr_text=long_text)
        # On vérifie que le texte OCR est inclus dans le message envoyé au chat
        with (
            patch("ia.utils.Path.read_bytes", return_value=b"%PDF fake"),
            patch("ia.utils._call_ocr", return_value=long_text),
            patch("ia.utils._call_chat", return_value="ok") as mock_chat,
        ):
            from ia.utils import summarize_document
            summarize_document(_make_fake_document())

        call_messages = mock_chat.call_args[0][0]
        user_msg = next(m for m in call_messages if m["role"] == "user")
        self.assertIn(long_text, user_msg["content"])


# ---------------------------------------------------------------------------
# Tests : ia.utils.analyze_all_documents
# ---------------------------------------------------------------------------

class AnalyzeAllDocumentsUtilsTests(TestCase):

    def test_missing_file_does_not_raise(self):
        """
        Given un document dont le fichier physique est introuvable
        When on appelle analyze_all_documents
        Then aucune exception n'est levée et le chat reçoit un contexte mentionnant « introuvable »
        """
        doc = _make_fake_document()
        with (
            patch("ia.utils.Path.read_bytes", side_effect=FileNotFoundError),
            patch("ia.utils._call_chat", return_value="réponse") as mock_chat,
        ):
            from ia.utils import analyze_all_documents
            result = analyze_all_documents([doc], query="Quelles factures ?")

        self.assertEqual(result, "réponse")
        # Le contexte envoyé au chat doit mentionner le fichier introuvable
        call_messages = mock_chat.call_args[0][0]
        user_msg = next(m for m in call_messages if m["role"] == "user")
        self.assertIn("introuvable", user_msg["content"])

    def test_short_ocr_marks_as_unreadable(self):
        """
        Given un document dont le texte OCR est trop court
        When on appelle analyze_all_documents
        Then le contexte envoyé au chat contient « [contenu illisible] »
        """
        doc = _make_fake_document()
        with (
            patch("ia.utils.Path.read_bytes", return_value=b"%PDF fake"),
            patch("ia.utils._call_ocr", return_value="court"),
            patch("ia.utils._call_chat", return_value="réponse") as mock_chat,
        ):
            from ia.utils import analyze_all_documents
            analyze_all_documents([doc], query="Quelles factures ?")

        call_messages = mock_chat.call_args[0][0]
        user_msg = next(m for m in call_messages if m["role"] == "user")
        self.assertIn("[contenu illisible]", user_msg["content"])

    def test_context_includes_document_title(self):
        """
        Given un document avec un titre et un texte OCR lisible
        When on appelle analyze_all_documents avec une question
        Then le contexte envoyé au chat contient le titre du document et la question
        """
        doc = _make_fake_document(title="Facture EDF mai 2026")
        ocr_text = "Facture EDF — 01/05/2026 — 120,00 € TTC pour l'association CDF"
        with (
            patch("ia.utils.Path.read_bytes", return_value=b"%PDF fake"),
            patch("ia.utils._call_ocr", return_value=ocr_text),
            patch("ia.utils._call_chat", return_value="ok") as mock_chat,
        ):
            from ia.utils import analyze_all_documents
            analyze_all_documents([doc], query="Quelles factures ?")

        call_messages = mock_chat.call_args[0][0]
        user_msg = next(m for m in call_messages if m["role"] == "user")
        self.assertIn("Facture EDF mai 2026", user_msg["content"])
        self.assertIn("Quelles factures ?", user_msg["content"])


# ---------------------------------------------------------------------------
# Tests : vue summarize_document
# ---------------------------------------------------------------------------

class SummarizeDocumentViewTests(TestCase):

    def setUp(self):
        self.user = _make_moderator()
        self.client.force_login(self.user)

    def _post(self, doc_id=1):
        return self.client.post(reverse("ia:summarize_document", args=[doc_id]))

    def test_creates_summary_in_db(self):
        """
        Given un modérateur authentifié
        When il poste sur la vue summarize_document pour un document existant
        Then un objet Summary est créé en BDD avec le contenu généré par l'IA
        """
        with (
            patch("ia.views.get_object_or_404") as mock_get,
            patch("ia.views.ai_utils.summarize_document", return_value="Résumé IA"),
            patch("ia.views.Summary.objects.create") as mock_create,
        ):
            mock_get.return_value = MagicMock(pk=1)
            mock_create.return_value = MagicMock(content="Résumé IA")
            response = self._post(doc_id=1)

        self.assertEqual(response.status_code, 200)
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        self.assertEqual(kwargs["content"], "Résumé IA")

    def test_requires_login(self):
        """
        Given un visiteur non authentifié
        When il poste sur la vue summarize_document
        Then l'accès est refusé (non 200)
        """
        self.client.logout()
        response = self._post()
        self.assertNotEqual(response.status_code, 200)

    def test_get_not_allowed(self):
        """
        Given un modérateur authentifié
        When il accède à summarize_document via GET
        Then la réponse est 405 Method Not Allowed
        """
        response = self.client.get(reverse("ia:summarize_document", args=[1]))
        self.assertEqual(response.status_code, 405)


# ---------------------------------------------------------------------------
# Tests : vue global_analyze
# ---------------------------------------------------------------------------

class GlobalAnalyzeViewTests(TestCase):

    def setUp(self):
        self.user = _make_moderator()
        self.client.force_login(self.user)

    def test_empty_query_returns_error(self):
        """
        Given un modérateur authentifié
        When il poste une question vide sur global_analyze
        Then la réponse contient un message d'erreur et aucun Summary n'est créé
        """
        response = self.client.post(reverse("ia:global_analyze"), data={"query": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "saisir une question")
        self.assertEqual(Summary.objects.count(), 0)

    def test_whitespace_query_returns_error(self):
        """
        Given un modérateur authentifié
        When il poste une question composée uniquement d'espaces
        Then la réponse contient un message d'erreur et aucun Summary n'est créé
        """
        response = self.client.post(reverse("ia:global_analyze"), data={"query": "   "})
        self.assertContains(response, "saisir une question")
        self.assertEqual(Summary.objects.count(), 0)

    def test_valid_query_creates_summary(self):
        """
        Given un modérateur authentifié
        When il poste une question valide sur global_analyze
        Then un Summary est créé en BDD avec la question et la réponse de l'IA
        """
        with patch(
            "ia.views.ai_utils.analyze_all_documents",
            return_value="Voici une synthèse des achats.",
        ):
            response = self.client.post(
                reverse("ia:global_analyze"),
                data={"query": "Quelles sont les factures EDF ?"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Summary.objects.count(), 1)
        s = Summary.objects.first()
        self.assertIsNone(s.document)
        self.assertEqual(s.query, "Quelles sont les factures EDF ?")
        self.assertEqual(s.content, "Voici une synthèse des achats.")

    def test_get_not_allowed(self):
        """
        Given un modérateur authentifié
        When il accède à global_analyze via GET
        Then la réponse est 405 Method Not Allowed
        """
        response = self.client.get(reverse("ia:global_analyze"))
        self.assertEqual(response.status_code, 405)

    def test_requires_login(self):
        """
        Given un visiteur non authentifié
        When il poste sur la vue global_analyze
        Then l'accès est refusé (non 200)
        """
        self.client.logout()
        response = self.client.post(
            reverse("ia:global_analyze"),
            data={"query": "test"},
        )
        self.assertNotEqual(response.status_code, 200)

