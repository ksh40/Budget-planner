from django.contrib import admin
from import_export import resources 
from import_export.admin import ImportExportModelAdmin
from .models import Students

class StudentsResource(resources.ModelResource):
    class Meta:
        model = Students
        import_id_fields = ('name', 'location')
        fields = ('name', 'price', 'og_price', 'discount','discount_note',
                  'location', 'area', 'description', 'website', 'image')
        skip_unchanged = True
        report_skipped = True

@admin.register(Students)
class StudentsAdmin(ImportExportModelAdmin):
    resource_classes = [StudentsResource]
    list_display = ('name', 'price','og_price', 'discount', 'location')
  