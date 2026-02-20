from django.db import models
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel
from wagtail.documents.models import Document, AbstractDocument


@register_snippet
class DocumentCategory(models.Model):
    name = models.CharField("Nom", max_length=100)
    
    panels = [
        FieldPanel('name'), 
    ]
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Catégorie de document"
        verbose_name_plural = "Catégories de documents"
        ordering = ['name']


class CustomDocument(AbstractDocument):    
    document_date = models.DateField(
        "Date du document", 
        null=True, 
        blank=True,
        help_text="Date du document (mois du relevé, date de facture, etc.)"
    )
    
    category = models.ForeignKey(
        'core.DocumentCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Catégorie",
        related_name='documents'
    )
    
    notes = models.TextField(
        "Notes", 
        blank=True,
        help_text="Remarques ou contexte sur ce document"
    )
    
    admin_form_fields = Document.admin_form_fields + (
        'document_date',
        'category',
        'notes',
    )
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return self.title
