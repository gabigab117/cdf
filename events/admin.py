from django.contrib import admin

from .models import EventStation, StationAssignment


class StationAssignmentInline(admin.TabularInline):
    model = StationAssignment
    extra = 1


@admin.register(EventStation)
class EventStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'required_count', 'assigned_count', 'is_complete')
    list_filter = ('event',)
    inlines = [StationAssignmentInline]
