import io
from pathlib import Path

from django.apps import apps
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

DRY_RUN = True
EXTS = (".jpg", ".jpeg", ".png", ".webp")

# (app, model, image field, folder name saved on Cloudinary)
TARGETS = [
    ("food", "Item", "image", "food_items"),
    ("activities", "Activity", "image", "activities"),
    ("eventful", "Eventful", "image", "eventful"),
]


def find_file(name):
    p = Path(name)
    if p.suffix.lower() in EXTS and p.exists():
        return p
    for ext in EXTS:
        candidate = Path(str(name) + ext)
        if candidate.exists():
            return candidate
    return None


for app_label, model_name, field_name, prefix in TARGETS:
    Model = apps.get_model(app_label, model_name)
    field = Model._meta.get_field(field_name)
    qs = Model.objects.filter(**{field_name + "__startswith": "img/"})
    print(f"\n--- {model_name}: {qs.count()} record(s) to process ---")
    for obj in qs:
        current = getattr(obj, field_name).name
        path = find_file(current)
        if not path:
            print(f"FILE NOT FOUND: {obj} -> {current}")
            continue
        print(f"{obj} <- {path}")
        if DRY_RUN:
            continue
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            if img.width > 1200:
                img = img.resize((1200, int(img.height * 1200 / img.width)), Image.LANCZOS)
            buf = io.BytesIO()
            img.convert("RGB").save(buf, "WEBP", quality=78, method=6)
        new_name = field.storage.save(f"{prefix}/{path.stem}.webp", ContentFile(buf.getvalue()))
        Model.objects.filter(pk=obj.pk).update(**{field_name: new_name})

print("\nDry run only." if DRY_RUN else "\nDone.")
