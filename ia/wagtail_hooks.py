from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Summary


class SummaryViewSet(SnippetViewSet):
    model = Summary
    icon = "pick"
    menu_label = "Résumés IA"
    menu_name = "ia_summaries"
    menu_order = 500
    add_to_admin_menu = True
    list_display = ["__str__", "query", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["content", "query", "document__title"]
    ordering = ["-created_at"]


register_snippet(SummaryViewSet)
