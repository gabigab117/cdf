from django import forms
from wagtail.documents import get_document_model

from .models import Equipment, EquipmentLoan, LoanItem

_INPUT_CSS = (
    "w-full rounded-xl border-0 bg-slate-50 px-4 py-2.5 text-sm text-slate-800 "
    "ring-1 ring-slate-200 placeholder:text-slate-400 focus:bg-white focus:ring-2 "
    "focus:ring-blason-400 transition-all"
)


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ["name", "quantity"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Ex : Barnums, Tables…", "class": _INPUT_CSS},
            ),
            "quantity": forms.NumberInput(attrs={"min": "1", "class": _INPUT_CSS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity"].min_value = 1
        self.fields["quantity"].initial = 1


class EquipmentLoanForm(forms.ModelForm):
    agreement = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": (
                    "w-full rounded-xl border-0 bg-slate-50 px-4 py-2 text-sm text-slate-800 "
                    "ring-1 ring-slate-200 file:mr-3 file:rounded-lg file:border-0 "
                    "file:bg-blason-50 file:px-3 file:py-1 file:text-xs file:font-semibold "
                    "file:text-blason-700 hover:file:bg-blason-100 transition-all"
                ),
            },
        ),
    )

    class Meta:
        model = EquipmentLoan
        fields = ["borrower_name", "start_date", "end_date", "notes"]
        widgets = {
            "borrower_name": forms.TextInput(
                attrs={"placeholder": "Nom de l'emprunteur", "class": _INPUT_CSS},
            ),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CSS},
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": _INPUT_CSS},
            ),
            "notes": forms.Textarea(
                attrs={"placeholder": "Notes…", "rows": 2, "class": _INPUT_CSS},
            ),
        }

    def save(self, commit=True):
        loan = super().save(commit=False)
        agreement_file = self.cleaned_data.get("agreement")
        if agreement_file:
            Document = get_document_model()
            doc = Document(title=agreement_file.name, file=agreement_file)
            doc.save()
            loan.agreement = doc
        if commit:
            loan.save()
        return loan


_ITEM_INPUT_CSS = (
    "rounded-xl border-0 bg-slate-50 px-3 py-2 text-sm ring-1 ring-slate-200 "
    "focus:bg-white focus:ring-2 focus:ring-blason-400 transition-all"
)


class LoanItemForm(forms.ModelForm):
    class Meta:
        model = LoanItem
        fields = ["equipment", "quantity"]
        error_messages = {
            "equipment": {"required": "Sélectionnez un matériel."},
        }
        widgets = {
            "equipment": forms.Select(
                attrs={"class": f"min-w-0 flex-1 {_ITEM_INPUT_CSS}"},
            ),
            "quantity": forms.NumberInput(
                attrs={"min": "1", "placeholder": "Qté", "class": f"w-20 {_ITEM_INPUT_CSS}"},
            ),
        }

    def __init__(self, *args, **kwargs):
        self.loan = kwargs.pop("loan", None)
        super().__init__(*args, **kwargs)
        self.fields["quantity"].min_value = 1
        self.fields["quantity"].initial = 1
        self.fields["equipment"].empty_label = "Matériel…"

    def clean(self):
        cleaned_data = super().clean()
        equipment = cleaned_data.get("equipment")
        quantity = cleaned_data.get("quantity")
        if equipment and quantity:
            if self.loan and self.loan.start_date and self.loan.end_date:
                avail = equipment.available_quantity_for_period(
                    self.loan.start_date,
                    self.loan.end_date,
                    exclude_loan=self.loan,
                )
            else:
                avail = equipment.available_quantity
            if quantity > avail:
                raise forms.ValidationError(
                    f"Stock insuffisant pour « {equipment.name} » "
                    f"({avail} disponible{'s' if avail > 1 else ''})."
                )
        return cleaned_data
