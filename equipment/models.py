from django.db import models
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
        """Quantité actuellement prêtée."""
        total = self.loan_items.aggregate(total=models.Sum("quantity"))["total"]
        return total or 0

    @property
    def available_quantity(self):
        """Quantité disponible (stock − prêts en cours)."""
        return self.quantity - self.loaned_quantity


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
    date = models.DateField(
        auto_now_add=True,
        verbose_name="Date du prêt",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
    )

    class Meta:
        verbose_name = "Prêt"
        verbose_name_plural = "Prêts"
        ordering = ["-date"]

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
