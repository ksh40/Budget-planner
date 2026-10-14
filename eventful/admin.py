from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Eventful

@admin.register(Eventful)
class EventfulAdmin(ImportExportModelAdmin):

    list_display = ('name', 'price', 'location', 'one_time', 'event_date')
    list_filter = ('one_time',)