from django.urls import path

from . import views

app_name = "ia"

urlpatterns = [
    path("documents/<int:doc_id>/resumer/", views.summarize_document, name="summarize_document"),
    path("analyser/", views.global_analyze, name="global_analyze"),
]
