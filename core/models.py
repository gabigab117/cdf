from django.db import models
from wagtail.documents.models import Document, AbstractDocument


class CustomDocument(AbstractDocument):    
    document_date = models.DateField(
        "Date du document", 
        null=True, 
        blank=True,
        help_text="Date du document (mois du relevé, date de facture, etc.)"
    )
    
    notes = models.TextField(
        "Notes", 
        blank=True,
        help_text="Remarques ou contexte sur ce document"
    )
    
    admin_form_fields = Document.admin_form_fields + (
        'document_date',
        'notes',
    )
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return self.title
