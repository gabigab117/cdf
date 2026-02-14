from django.db import models
from wagtail.models import Page, Orderable
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.documents import get_document_model
from wagtail.admin.panels import FieldPanel, InlinePanel
from modelcluster.fields import ParentalKey


class EventPage(Page):
    
    date_event = models.DateTimeField("Date de l'événement")
    
    notes = StreamField([
        ('heading', blocks.CharBlock(form_classname="title", label="Titre de section")),
        ('paragraph', blocks.RichTextBlock(label="Texte/Note")),
        ('todo_list', blocks.ListBlock(blocks.CharBlock(), label="Liste de tâches")),
        ('document', DocumentChooserBlock(label="Document annexe")),
    ], use_json_field=True, blank=True, verbose_name="Notes et Comptes-rendus")

    content_panels = Page.content_panels + [
        FieldPanel('date_event'),
        FieldPanel('notes'),
        InlinePanel('event_documents', label="Documents rattachés"),
    ]

    class Meta:
        verbose_name = "Événement"

    def get_context(self, request):
        """Ajoute des infos au contexte du template"""
        context = super().get_context(request)
        context['documents_by_category'] = self.get_documents_by_category()
        return context
    
    def get_documents_by_category(self):
        """Groupe les documents par catégorie"""
        docs = dict()
        for event_doc in self.event_documents.select_related('document__category'):
            if event_doc.document.category:
                cat_name = event_doc.document.category.name
                if cat_name not in docs:
                    docs[cat_name] = []
                docs[cat_name].append(event_doc)
        return docs


class EventDocument(Orderable):
    page = ParentalKey(EventPage, related_name='event_documents')
    document = models.ForeignKey(
        get_document_model(), 
        on_delete=models.CASCADE,
        verbose_name="Document"
    )
    notes = models.TextField(
        blank=True, 
        help_text="Remarques spécifiques à cet événement"
    )

    panels = [
        FieldPanel('document'),
        FieldPanel('notes'),
    ]
    
    class Meta:
        ordering = ['document__document_date']
        verbose_name = "Document de l'événement"
