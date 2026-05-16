from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("documents/", views.document_list, name="document_list"),
]
