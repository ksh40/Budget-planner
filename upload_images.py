from django.apps import apps
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

DRY_RUN = False
local = FileSystemStorage(location=settings.MEDIA_ROOT)

for model in apps.get_models():
    for field in model._meta.get_fields():
        if not isinstance(field, models.ImageField):
            continue
        for obj in model.objects.all():
            current = getattr(obj, field.name)
            if not current or current.name.startswith("verification_docs"):
                continue
            if not local.exists(current.name):
                print(f"MISSING LOCALLY: {model.__name__}.{field.name} -> {current.name}")
                continue
            print(f"{model.__name__}.{field.name}: {current.name}")
            if not DRY_RUN:
                with local.open(current.name) as f:
                    new_name = field.storage.save(current.name, f)
                model.objects.filter(pk=obj.pk).update(**{field.name: new_name})

print("\nDry run only." if DRY_RUN else "\nDone.")