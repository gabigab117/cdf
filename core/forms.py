from wagtail.admin.widgets import AdminDateInput
from wagtail.documents.forms import BaseDocumentForm


class CustomDocumentForm(BaseDocumentForm):
    class Meta(BaseDocumentForm.Meta):
        widgets = {
            **BaseDocumentForm.Meta.widgets,
            'document_date': AdminDateInput,
        }
