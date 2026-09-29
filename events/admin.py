from django.contrib import admin
from .models import Event, EventUpdate, EventEvidence


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organiser', 'category', 'date', 'status')
    list_filter = ('status', 'category')
    search_fields = ('title', 'organiser__username')
    readonly_fields = ('status',)  # status now only changes via the investigation workflow


@admin.register(EventUpdate)
class EventUpdateAdmin(admin.ModelAdmin):
    list_display = ('event', 'created_at')


@admin.register(EventEvidence)
class EventEvidenceAdmin(admin.ModelAdmin):
    list_display = ('event', 'evidence_type', 'admin', 'created_at')
    list_filter = ('evidence_type',)