from pathlib import Path
from PIL import Image, ImageOps

MEDIA_DIR = Path("media")
MAX_WIDTH = 1200
QUALITY = 78

converted, saved = 0, 0

for jpg in list(MEDIA_DIR.rglob("*.jpg")) + list(MEDIA_DIR.rglob("*.jpeg")):
    if "verification_docs" in jpg.parts:
        continue

    out = jpg.with_suffix(".webp")
    before = jpg.stat().st_size

    with Image.open(jpg) as img:
        img = ImageOps.exif_transpose(img)
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            img = img.resize((MAX_WIDTH, int(img.height * ratio)), Image.LANCZOS)
        img.convert("RGB").save(out, "WEBP", quality=QUALITY, method=6)

    after = out.stat().st_size
    saved += before - after
    converted += 1
    print(f"{jpg}  {before//1024} KB -> {after//1024} KB")

print(f"\nConverted {converted} images, saved {saved/1024/1024:.1f} MB")