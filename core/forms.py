from django.core.exceptions import ValidationError
from django.forms.models import InlineForeignKeyField
from django.forms.models import construct_instance

from wagtail.admin.widgets import AdminDateInput
from wagtail.documents.forms import BaseDocumentForm


class CustomDocumentForm(BaseDocumentForm):
    def _post_clean(self):
        opts = self._meta
        exclude = self._get_validation_exclusions()

        for name, field in self.fields.items():
            if isinstance(field, InlineForeignKeyField):
                exclude.add(name)

        try:
            self.instance = construct_instance(
                self, self.instance, opts.fields, opts.exclude
            )
        except ValidationError as e:
            self._update_errors(e)

        try:
            self.instance.full_clean(
                exclude=exclude, validate_unique=False, validate_constraints=False
            )
        except ValidationError as e:
            # Filter out errors for fields not present in the form
            # (e.g. 'file' during multi-upload) to avoid ValueError
            filtered = {}
            for field, messages in e.message_dict.items():
                if field in self.fields or field == '__all__':
                    filtered[field] = messages
                # else: silently drop – the field will be set later (e.g. save_object)
            if filtered:
                self._update_errors(ValidationError(filtered))

        if self._validate_unique:
            self.validate_unique()
        if self._validate_constraints:
            self.validate_constraints()

    class Meta(BaseDocumentForm.Meta):
        widgets = {
            **BaseDocumentForm.Meta.widgets,
            'document_date': AdminDateInput,
        }
