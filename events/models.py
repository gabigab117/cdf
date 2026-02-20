from django.db import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseForbidden
from django.urls import reverse
from wagtail.models import Page, Orderable
from wagtail.fields import StreamField, RichTextField
from wagtail import blocks
from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.admin.panels import FieldPanel, InlinePanel
from modelcluster.fields import ParentalKey


class EventIndexPage(Page):
    """Page d'index listant tous les événements (front-office, lecture seule)."""

    intro = RichTextField(
        blank=True,
        verbose_name="Introduction",
        help_text="Texte d'introduction affiché en haut de la page.",
    )
    events_per_page = models.PositiveIntegerField(
        default=10,
        verbose_name="Événements par page",
        help_text="Nombre d'événements affichés par page.",
    )

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('events_per_page'),
    ]

    subpage_types = ['events.EventPage']

    class Meta:
        verbose_name = "Index des événements"

    def get_context(self, request):
        context = super().get_context(request)
        all_events = (
            EventPage.objects
            .child_of(self)
            .live()
            .order_by('-date_event')
        )
        paginator = Paginator(all_events, self.events_per_page)
        page_number = request.GET.get('page', 1)
        try:
            events = paginator.page(page_number)
        except PageNotAnInteger:
            events = paginator.page(1)
        except EmptyPage:
            events = paginator.page(paginator.num_pages)
        context['events'] = events
        return context


class EventPage(Page):
    
    date_event = models.DateTimeField("Date de l'événement")

    def serve(self, request):
        """Seuls les utilisateurs staff peuvent accéder à cette page."""
        if not request.user.is_authenticated or not request.user.is_staff:
            return HttpResponseForbidden("Accès réservé aux membres du staff.")
        return super().serve(request)
    
    notes = StreamField([
        ('richtext', blocks.RichTextBlock(label="Texte")),
        ('heading', blocks.CharBlock(label="Titre", form_classname="title", icon="title")),
        ('url', blocks.URLBlock(label="Lien", help_text="URL externe")),
    ], use_json_field=True, blank=True, verbose_name="Notes et Comptes-rendus")

    content_panels = Page.content_panels + [
        FieldPanel('date_event'),
        FieldPanel('notes'),
        InlinePanel('event_images', label="Images rattachées"),
        InlinePanel('event_documents', label="Documents rattachés"),
    ]

    parent_page_types = ['events.EventIndexPage']
    subpage_types = []

    class Meta:
        verbose_name = "Événement"
        ordering = ['-date_event']

    def get_context(self, request):
        """Ajoute des infos au contexte du template"""
        context = super().get_context(request)
        context['event_images'] = self.event_images.select_related('image')
        context['documents_by_category'] = self.get_documents_by_category()

        user = request.user
        if user.is_authenticated:
            user_perms = self.permissions_for_user(user)
            context['can_edit'] = user_perms.can_edit()
            context['wagtail_edit_url'] = reverse('wagtailadmin_pages:edit', args=[self.pk])
        else:
            context['can_edit'] = False

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


class EventImage(Orderable):
    page = ParentalKey(EventPage, related_name='event_images')
    image = models.ForeignKey(
        get_image_model(),
        on_delete=models.CASCADE,
        verbose_name="Image",
        related_name='+',
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Légende",
    )

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
    ]

    class Meta:
        verbose_name = "Image de l'événement"


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
