from django.urls import path

from . import views

app_name = "equipment"

urlpatterns = [
    path("", views.equipment_board, name="equipment_board"),
    path("liste/", views.equipment_list, name="equipment_list"),
    path("creer/", views.equipment_create, name="equipment_create"),
    path("<int:equipment_pk>/supprimer/", views.equipment_delete, name="equipment_delete"),
    path("prets/creer/", views.loan_create, name="loan_create"),
    path("prets/<int:loan_pk>/supprimer/", views.loan_delete, name="loan_delete"),
    path("prets/<int:loan_pk>/ajouter/", views.loan_item_add, name="loan_item_add"),
    path("prets/lignes/<int:item_pk>/retirer/", views.loan_item_remove, name="loan_item_remove"),
]
