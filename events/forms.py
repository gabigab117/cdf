from django import forms

from .models import EventStation, StationAssignment

_INPUT_CSS = (
    "w-full rounded-xl border-0 bg-slate-50 px-4 py-2.5 text-sm text-slate-800 "
    "ring-1 ring-slate-200 placeholder:text-slate-400 focus:bg-white focus:ring-2 "
    "focus:ring-blason-400 transition-all"
)


class EventStationForm(forms.ModelForm):
    class Meta:
        model = EventStation
        fields = ["name", "description", "required_count"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Ex : Frites, BBQ…", "class": _INPUT_CSS},
            ),
            "description": forms.TextInput(
                attrs={"placeholder": "Horaires, consignes…", "class": _INPUT_CSS},
            ),
            "required_count": forms.NumberInput(
                attrs={"min": "1", "class": _INPUT_CSS},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["required_count"].min_value = 1
        self.fields["required_count"].initial = 1


class StationAssignmentForm(forms.ModelForm):
    class Meta:
        model = StationAssignment
        fields = ["name", "role"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Nom", "class": _INPUT_CSS},
            ),
            "role": forms.TextInput(
                attrs={"placeholder": "Rôle (optionnel)", "class": _INPUT_CSS},
            ),
        }
