from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from core.utils import is_moderator

from .forms import EventStationForm, StationAssignmentForm
from .models import EventPage, EventStation, StationAssignment


@user_passes_test(is_moderator)
def station_board(request, event_pk):
    """Vue principale : tableau des postes d'un événement."""
    event = get_object_or_404(EventPage, pk=event_pk)
    return render(request, 'events/station_board.html', {
        'event': event,
        'station_form': EventStationForm(),
        'assignment_form': StationAssignmentForm(),
    })


@user_passes_test(is_moderator)
@require_POST
def station_create(request, event_pk):
    """Créer un nouveau poste (HTMX)."""
    event = get_object_or_404(EventPage, pk=event_pk)
    form = EventStationForm(request.POST)
    if form.is_valid():
        station = form.save(commit=False)
        station.event = event
        station.save()
        form = EventStationForm()
    return render(request, 'events/partials/station_section.html', {
        'event': event,
        'station_form': form,
        'assignment_form': StationAssignmentForm(),
    })


@user_passes_test(is_moderator)
@require_POST
def station_delete(request, station_pk):
    """Supprimer un poste (HTMX)."""
    station = get_object_or_404(EventStation, pk=station_pk)
    event = station.event
    station.delete()
    return render(request, 'events/partials/station_list.html', {
        'event': event,
        'assignment_form': StationAssignmentForm(),
    })


@user_passes_test(is_moderator)
@require_POST
def assignment_add(request, station_pk):
    """Ajouter une personne à un poste (HTMX)."""
    station = get_object_or_404(EventStation.objects.select_related('event'), pk=station_pk)
    form = StationAssignmentForm(request.POST)
    if form.is_valid():
        assignment = form.save(commit=False)
        assignment.station = station
        assignment.save()
        station.refresh_from_db()
        form = StationAssignmentForm()
    return render(request, 'events/partials/station_card.html', {
        'station': station,
        'event': station.event,
        'assignment_form': form,
    })


@user_passes_test(is_moderator)
@require_POST
def assignment_remove(request, assignment_pk):
    """Retirer une personne d'un poste (HTMX)."""
    assignment = get_object_or_404(
        StationAssignment.objects.select_related('station__event'),
        pk=assignment_pk,
    )
    station = assignment.station
    assignment.delete()
    station.refresh_from_db()

    return render(request, 'events/partials/station_card.html', {
        'station': station,
        'event': station.event,
        'assignment_form': StationAssignmentForm(),
    })
