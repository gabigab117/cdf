from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.urls import reverse
from modelcluster.fields import ParentalKey
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.documents import get_document_model
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model
from wagtail.models import Orderable, Page


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

        user = request.user
        if user.is_authenticated:
            user_perms = self.permissions_for_user(user)
            context['can_view_details'] = user_perms.can_edit() or user_perms.can_publish()
        else:
            context['can_view_details'] = False

        return context


class EventPage(Page):
    
    date_event = models.DateTimeField("Date de l'événement")
    
    notes = StreamField([
        ('richtext', blocks.RichTextBlock(label="Texte")),
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

    @property
    def stations_with_counts(self):
        return self.stations.prefetch_related('assignments').all()

    @property
    def total_required(self):
        return sum(s.required_count for s in self.stations_with_counts)

    @property
    def total_assigned(self):
        return sum(s.assigned_count for s in self.stations_with_counts)

    def get_context(self, request):
        """Ajoute des infos au contexte du template"""
        context = super().get_context(request)
        context['event_images'] = self.event_images.select_related('image')
        context['event_documents'] = self.event_documents.select_related('document__collection').order_by('document__collection__name', 'document__document_date')

        user = request.user
        if user.is_authenticated:
            user_perms = self.permissions_for_user(user)
            context['can_edit'] = user_perms.can_edit()
            context['wagtail_edit_url'] = reverse('wagtailadmin_pages:edit', args=[self.pk])
        else:
            context['can_edit'] = False

        return context


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


class EventStation(models.Model):
    """Un poste de travail pour un événement (Frites, BBQ, Caisse, etc.)."""
    event = models.ForeignKey(
        EventPage,
        on_delete=models.CASCADE,
        related_name='stations',
        verbose_name="Événement",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Nom du poste",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Détails sur le poste (horaires, consignes…)",
    )
    required_count = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre de personnes requises",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
    )

    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} — {self.event.title}"

    @property
    def assigned_count(self):
        return self.assignments.count()

    @property
    def is_complete(self):
        return self.assigned_count >= self.required_count


class StationAssignment(models.Model):
    """Une personne assignée à un poste."""
    station = models.ForeignKey(
        EventStation,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="Poste",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Nom de la personne",
    )
    role = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Rôle spécifique",
        help_text="Ex : bière uniquement, navette frigo…",
    )

    class Meta:
        verbose_name = "Affectation"
        verbose_name_plural = "Affectations"
        ordering = ['name']

    def __str__(self):
        if self.role:
            return f"{self.name} ({self.role})"
        return self.name
