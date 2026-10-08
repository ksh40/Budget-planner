from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Item, Bundle

@admin.register(Item)
class ItemAdmin(ImportExportModelAdmin):
    list_display = ('name', 'price', 'category', 'place')
admin.site.register(Bundle)