from django.conf import settings
from django.db import models


class Summary(models.Model):
    """Résultat d'une analyse IA.

    - document renseigné  → résumé d'un document individuel
    - document null       → analyse globale (query obligatoire)

    Chaque appel crée un nouvel enregistrement (historique complet).
    """

    document = models.ForeignKey(
        settings.WAGTAILDOCS_DOCUMENT_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="ai_summaries",
        verbose_name="Document",
    )
    query = models.TextField(
        "Question",
        blank=True,
        help_text="Question posée à l'IA (analyse globale).",
    )
    content = models.TextField("Réponse de l'IA")
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Résumé IA"
        verbose_name_plural = "Résumés IA"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        if self.document:
            return f"Résumé — {self.document.title}"
        return f"Analyse globale — {self.created_at:%d/%m/%Y %H:%M}"

