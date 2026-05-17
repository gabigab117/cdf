from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from wagtail.documents import get_document_model

from core.utils import is_moderator
from ia import utils as ai_utils
from ia.models import Summary


@require_POST
@user_passes_test(is_moderator)
def summarize_document(request, doc_id: int):
    """Résume un document individuel et stocke le résultat en BDD."""
    Document = get_document_model()
    doc = get_object_or_404(Document, pk=doc_id)

    content = ai_utils.summarize_document(doc)
    summary = Summary.objects.create(document=doc, content=content)

    return render(
        request,
        "ia/partials/document_summary.html",
        {"summary": summary},
    )


@require_POST
@user_passes_test(is_moderator)
def global_analyze(request):
    """Analyse l'ensemble des documents en répondant à la question posée."""
    query = request.POST.get("query", "").strip()
    if not query:
        return render(
            request,
            "ia/partials/global_analysis.html",
            {"error": "Merci de saisir une question."},
        )

    Document = get_document_model()
    documents = Document.objects.order_by(
        "-document_date",
        "-created_at",
    )

    content = ai_utils.analyze_all_documents(documents, query)
    summary = Summary.objects.create(document=None, query=query, content=content)

    return render(
        request,
        "ia/partials/global_analysis.html",
        {"summary": summary},
    )

