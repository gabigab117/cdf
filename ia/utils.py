"""Wrappers Mistral pour l'analyse de documents."""

import base64
import logging
from pathlib import Path

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MISTRAL_OCR_URL = "https://api.mistral.ai/v1/ocr"
MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
CHAT_MODEL = "mistral-small-latest"
OCR_MODEL = "mistral-ocr-latest"

UNREADABLE_MSG = (
    "Ce fichier a été scanné comme un bourrin par Gab, donc illisible 🐴"
)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }


def _call_ocr(pdf_b64: str) -> str:
    """Extrait le texte d'un PDF via l'API OCR Mistral."""
    response = requests.post(
        MISTRAL_OCR_URL,
        headers=_headers(),
        json={
            "model": OCR_MODEL,
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_b64}",
            },
        },
        timeout=60,
    )
    response.raise_for_status()
    pages = response.json().get("pages", [])
    return "\n\n".join(page.get("markdown", "") for page in pages).strip()


def _call_chat(messages: list[dict]) -> str:
    """Appelle le modèle de chat Mistral."""
    response = requests.post(
        MISTRAL_CHAT_URL,
        headers=_headers(),
        json={
            "model": CHAT_MODEL,
            "messages": messages,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def summarize_document(document) -> str:
    """Résume un document individuel via OCR + Chat.

    Retourne UNREADABLE_MSG si le document est illisible.
    """
    file_path = Path(document.file.path)
    pdf_b64 = base64.b64encode(file_path.read_bytes()).decode()

    text = _call_ocr(pdf_b64)

    if len(text) < 30:
        return UNREADABLE_MSG

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant qui analyse des factures et documents "
                "pour une association. Réponds toujours en français, de façon "
                "concise et structurée."
            ),
        },
        {
            "role": "user",
            "content": (
                "Voici le contenu extrait d'un document. "
                "Fais un résumé court : objet, fournisseur/émetteur, "
                "montant si présent, date si présente.\n\n"
                f"{text}"
            ),
        },
    ]
    return _call_chat(messages)


def analyze_all_documents(documents, query: str) -> str:
    """Analyse un ensemble de documents en répondant à la question posée.

    Chaque document est OCR-isé individuellement puis le contexte
    est envoyé en un seul appel Chat.
    """
    context_parts: list[str] = []

    for doc in documents:
        try:
            file_path = Path(doc.file.path)
            pdf_b64 = base64.b64encode(file_path.read_bytes()).decode()
            text = _call_ocr(pdf_b64)
            if len(text) < 30:
                text = "[contenu illisible]"
        except Exception:
            logger.warning("Impossible de lire le fichier : %s", doc.title)
            text = "[fichier introuvable ou illisible]"

        context_parts.append(
            f"--- Document : {doc.title} "
            f"(date : {doc.document_date or 'inconnue'}) ---\n{text}"
        )

    full_context = "\n\n".join(context_parts)

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant qui analyse des factures et documents "
                "pour une association. Réponds toujours en français."
            ),
        },
        {
            "role": "user",
            "content": (
                "Voici le contenu de tous les documents disponibles :\n\n"
                f"{full_context}\n\n"
                f"Question : {query}"
            ),
        },
    ]
    return _call_chat(messages)
