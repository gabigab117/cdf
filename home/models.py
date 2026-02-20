from django.db import models

from wagtail.models import Page


class HomePage(Page):
    # Modèle non utilisé, mais je le garde pour une éventuelle utilisation future
    subpage_types = ['events.EventIndexPage']
