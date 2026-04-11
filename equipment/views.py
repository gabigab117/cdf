from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from core.utils import is_moderator

from .forms import EquipmentForm, EquipmentLoanForm, LoanItemForm
from .models import Equipment, EquipmentLoan, LoanItem


def _trigger_equipment_updated(response):
    """Ajoute le header HX-Trigger pour rafraîchir la liste matériel."""
    response["HX-Trigger"] = "equipmentUpdated"
    return response


def _equipments():
    return Equipment.objects.all()


def _active_loans():
    return EquipmentLoan.objects.prefetch_related("items__equipment").filter(is_finalized=False)


def _finalized_loans():
    return EquipmentLoan.objects.prefetch_related("items__equipment").filter(is_finalized=True)


def _loan_context(form=None):
    """Contexte commun pour les sections de prêts."""
    return {
        "loan_form": form or EquipmentLoanForm(),
        "loan_item_form": LoanItemForm(),
        "active_loans": _active_loans(),
        "finalized_loans": _finalized_loans(),
    }


@user_passes_test(is_moderator)
def equipment_board(request):
    """Vue principale : inventaire du matériel et prêts en cours."""
    return render(
        request,
        "equipment/equipment_board.html",
        {
            "equipment_form": EquipmentForm(),
            "equipments": _equipments(),
            **_loan_context(),
        },
    )


@user_passes_test(is_moderator)
def equipment_list(request):
    """Retourne le partial de la liste matériel (GET, pour HTMX)."""
    return render(
        request,
        "equipment/partials/equipment_list.html",
        {"equipments": _equipments()},
    )


@user_passes_test(is_moderator)
@require_POST
def equipment_create(request):
    """Ajouter du matériel (HTMX)."""
    form = EquipmentForm(request.POST)
    if form.is_valid():
        form.save()
        form = EquipmentForm()
    return render(
        request,
        "equipment/partials/equipment_section.html",
        {"equipment_form": form, "equipments": _equipments()},
    )


@user_passes_test(is_moderator)
@require_POST
def equipment_delete(request, equipment_pk):
    """Supprimer du matériel (HTMX)."""
    get_object_or_404(Equipment, pk=equipment_pk).delete()
    return render(
        request,
        "equipment/partials/equipment_list.html",
        {"equipments": _equipments()},
    )


@user_passes_test(is_moderator)
@require_POST
def loan_create(request):
    """Créer un prêt (HTMX)."""
    form = EquipmentLoanForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        form = EquipmentLoanForm()
    return render(
        request,
        "equipment/partials/loan_section.html",
        _loan_context(form),
    )


@user_passes_test(is_moderator)
@require_POST
def loan_delete(request, loan_pk):
    """Supprimer un prêt (HTMX)."""
    get_object_or_404(EquipmentLoan, pk=loan_pk).delete()
    response = render(
        request,
        "equipment/partials/loan_section.html",
        _loan_context(),
    )
    return _trigger_equipment_updated(response)


@user_passes_test(is_moderator)
@require_POST
def loan_finalize(request, loan_pk):
    """Finaliser un prêt (HTMX)."""
    loan = get_object_or_404(EquipmentLoan, pk=loan_pk)
    loan.is_finalized = True
    loan.save(update_fields=["is_finalized"])
    response = render(
        request,
        "equipment/partials/loan_section.html",
        _loan_context(),
    )
    return _trigger_equipment_updated(response)


@user_passes_test(is_moderator)
@require_POST
def loan_item_add(request, loan_pk):
    """Ajouter du matériel à un prêt (HTMX)."""
    loan = get_object_or_404(EquipmentLoan.objects.prefetch_related("items__equipment"), pk=loan_pk)
    form = LoanItemForm(request.POST, loan=loan)
    if form.is_valid():
        item = form.save(commit=False)
        item.loan = loan
        item.save()
        loan.refresh_from_db()
        response = render(
            request,
            "equipment/partials/loan_card.html",
            {"loan": loan, "loan_item_form": LoanItemForm(loan=loan), "show_actions": True},
        )
        return _trigger_equipment_updated(response)
    return render(
        request,
        "equipment/partials/loan_card.html",
        {"loan": loan, "loan_item_form": form, "show_actions": True},
    )


@user_passes_test(is_moderator)
@require_POST
def loan_item_remove(request, item_pk):
    """Retirer du matériel d'un prêt (HTMX)."""
    item = get_object_or_404(LoanItem.objects.select_related("loan"), pk=item_pk)
    loan = item.loan
    item.delete()
    loan.refresh_from_db()
    response = render(
        request,
        "equipment/partials/loan_card.html",
        {"loan": loan, "loan_item_form": LoanItemForm(), "show_actions": True},
    )
    return _trigger_equipment_updated(response)
