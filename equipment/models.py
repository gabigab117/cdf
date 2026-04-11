from django.db import models
from django.utils import timezone
from wagtail.documents import get_document_model


class Equipment(models.Model):
    """Matériel répertorié dans l'inventaire."""

    name = models.CharField(
        max_length=200,
        verbose_name="Nom du matériel",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantité en stock",
    )

    class Meta:
        verbose_name = "Matériel"
        verbose_name_plural = "Matériels"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def loaned_quantity(self):
        """Quantité actuellement prêtée (emprunts non finalisés uniquement)."""
        total = self.loan_items.filter(loan__is_finalized=False).aggregate(
            total=models.Sum("quantity")
        )["total"]
        return total or 0

    @property
    def available_quantity(self):
        """Quantité disponible (stock − prêts en cours)."""
        return self.quantity - self.loaned_quantity

    def _loaned_quantity_for_period(self, start_date, end_date, exclude_loan=None):
        """Quantité prêtée sur une période donnée (chevauchement de dates)."""
        qs = self.loan_items.filter(
            loan__is_finalized=False,
            loan__start_date__lte=end_date,
            loan__end_date__gte=start_date,
        )
        if exclude_loan is not None:
            qs = qs.exclude(loan=exclude_loan)
        total = qs.aggregate(total=models.Sum("quantity"))["total"]
        return total or 0

    def available_quantity_for_period(self, start_date, end_date, exclude_loan=None):
        """Quantité disponible sur une période donnée."""
        return self.quantity - self._loaned_quantity_for_period(
            start_date, end_date, exclude_loan=exclude_loan
        )


class EquipmentLoan(models.Model):
    """Prêt de matériel à un emprunteur."""

    borrower_name = models.CharField(
        max_length=200,
        verbose_name="Nom de l'emprunteur",
    )
    agreement = models.ForeignKey(
        get_document_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Convention de prêt",
    )
    start_date = models.DateField(
        default=timezone.now,
        verbose_name="Date de début",
    )
    end_date = models.DateField(
        default=timezone.now,
        verbose_name="Date de fin",
    )
    is_finalized = models.BooleanField(
        default=False,
        verbose_name="Finalisé",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
    )

    class Meta:
        verbose_name = "Prêt"
        verbose_name_plural = "Prêts"
        ordering = ["-start_date"]

    def __str__(self):
        return f"Prêt à {self.borrower_name}"

    @property
    def total_items(self):
        return self.items.count()

    @property
    def total_quantity(self):
        total = self.items.aggregate(total=models.Sum("quantity"))["total"]
        return total or 0


class LoanItem(models.Model):
    """Ligne de matériel dans un prêt."""

    loan = models.ForeignKey(
        EquipmentLoan,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Prêt",
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name="loan_items",
        verbose_name="Matériel",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantité prêtée",
    )

    class Meta:
        verbose_name = "Ligne de prêt"
        verbose_name_plural = "Lignes de prêt"
        ordering = ["equipment__name"]

    def __str__(self):
        return f"{self.equipment.name} ×{self.quantity}"
