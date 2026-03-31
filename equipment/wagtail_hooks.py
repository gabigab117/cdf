from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Equipment, EquipmentLoan


class EquipmentViewSet(SnippetViewSet):
    model = Equipment
    icon = "cube"
    menu_label = "Matériel"
    menu_name = "equipment"
    menu_order = 300
    add_to_admin_menu = True
    list_display = ["name", "quantity"]
    search_fields = ["name"]


class EquipmentLoanViewSet(SnippetViewSet):
    model = EquipmentLoan
    icon = "doc-full-inverse"
    menu_label = "Prêts"
    menu_name = "loans"
    menu_order = 310
    add_to_admin_menu = True
    list_display = ["borrower_name", "date"]
    search_fields = ["borrower_name"]


register_snippet(EquipmentViewSet)
register_snippet(EquipmentLoanViewSet)
