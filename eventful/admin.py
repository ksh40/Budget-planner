from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Eventful

@admin.register(Eventful)
class ActivityAdmin(ImportExportModelAdmin):
    list_display = ('name', 'price', 'location')