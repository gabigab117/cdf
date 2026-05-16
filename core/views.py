from django.contrib.auth.decorators import user_passes_test
from django.db.models import F
from django.shortcuts import render
from wagtail.documents import get_document_model
from wagtail.models import Collection

from core.utils import is_moderator


def legal(request):
    return render(request, "core/legal.html")


@user_passes_test(is_moderator)
def document_list(request):
    """Liste en lecture seule de tous les documents, triés par date décroissante."""
    Document = get_document_model()

    documents = Document.objects.select_related("collection").order_by(
        F("document_date").desc(nulls_last=True),
        "-created_at",
    )

    query = request.GET.get("q", "").strip()
    if query:
        documents = documents.filter(title__icontains=query)

    selected_collection = request.GET.get("collection", "").strip()
    if selected_collection.isdigit():
        documents = documents.filter(collection_id=int(selected_collection))

    collections = Collection.objects.all().order_by("path")

    context = {
        "documents": documents,
        "collections": collections,
        "q": query,
        "selected_collection": selected_collection,
    }

    if request.headers.get("HX-Request") == "true":
        template = "core/partials/document_results.html"
    else:
        template = "core/document_list.html"

    return render(request, template, context)
