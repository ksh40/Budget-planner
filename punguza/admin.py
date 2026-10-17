from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Punguza


class PunguzaResource(resources.ModelResource):
    class Meta:
        model = Punguza
        import_id_fields = ('name', 'place')
        fields = ('name', 'price', 'place', 'area', 'image')
        skip_unchanged = True
        report_skipped = True


@admin.register(Punguza)
class PunguzaAdmin(ImportExportModelAdmin):
    resource_classes = [PunguzaResource]
    list_display = ('name', 'price', 'place')