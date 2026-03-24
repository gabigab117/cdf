from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import EventPage, EventStation, StationAssignment


def _is_moderator(user):
    """Vérifie que l'utilisateur est modérateur Wagtail ou superuser."""
    return user.is_superuser or user.groups.filter(name='Moderators').exists()



@user_passes_test(_is_moderator)
def station_board(request, event_pk):
    """Vue principale : tableau des postes d'un événement."""
    event = get_object_or_404(EventPage, pk=event_pk)
    return render(request, 'events/station_board.html', {'event': event})


@user_passes_test(_is_moderator)
@require_POST
def station_create(request, event_pk):
    """Créer un nouveau poste (HTMX)."""
    event = get_object_or_404(EventPage, pk=event_pk)

    name = request.POST.get('name', '').strip()
    if not name:
        return render(request, 'events/partials/station_form.html', {
            'event': event,
            'error': 'Le nom du poste est requis.',
        })

    description = request.POST.get('description', '').strip()
    try:
        required_count = max(1, int(request.POST.get('required_count', 1)))
    except (ValueError, TypeError):
        required_count = 1

    EventStation.objects.create(
        event=event,
        name=name,
        description=description,
        required_count=required_count,
    )
    return render(request, 'events/partials/station_list.html', {'event': event})


@user_passes_test(_is_moderator)
@require_POST
def station_delete(request, station_pk):
    """Supprimer un poste (HTMX)."""
    station = get_object_or_404(EventStation, pk=station_pk)
    event = station.event
    station.delete()
    return render(request, 'events/partials/station_list.html', {'event': event})


@user_passes_test(_is_moderator)
@require_POST
def assignment_add(request, station_pk):
    """Ajouter une personne à un poste (HTMX)."""
    station = get_object_or_404(EventStation.objects.select_related('event'), pk=station_pk)

    name = request.POST.get('name', '').strip()
    if not name:
        return render(request, 'events/partials/station_card.html', {
            'station': station,
            'event': station.event,
            'error': 'Le nom est requis.',
        })

    role = request.POST.get('role', '').strip()
    StationAssignment.objects.create(station=station, name=name, role=role)
    station.refresh_from_db()

    return render(request, 'events/partials/station_card.html', {
        'station': station,
        'event': station.event,
    })


@user_passes_test(_is_moderator)
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
    })
