#!/usr/bin/env python3
"""Build Aakalan Agent icon assets from the generated 2048x2048 source."""
from PIL import Image
import pathlib

BASE = pathlib.Path(r"C:\Users\LAPTOP PC\Desktop\3_Apps_and_Development\aakalan agent\apps\desktop")
SRC = BASE / "assets" / "aakalan-source.png"
img = Image.open(SRC).convert("RGBA")

# 1. assets/icon.png — electron-builder macOS icon source (usually 512x512 @2x = 1024)
img.resize((1024, 1024), Image.LANCZOS).save(BASE / "assets" / "icon.png", "PNG")
print("icon.png 1024 done")

# 2. assets/icon.ico — Windows multi-size icon (16..256)
ico_sizes = [16, 24, 32, 48, 64, 128, 256]
img.resize((256, 256), Image.LANCZOS).save(
    BASE / "assets" / "icon.ico",
    format="ICO",
    sizes=[(s, s) for s in ico_sizes],
)
print("icon.ico done")

# 3. assets/icon.icns — macOS (best-effort; PIL supports ICNS write)
try:
    img.resize((1024, 1024), Image.LANCZOS).save(BASE / "assets" / "icon.icns", "ICNS")
    print("icon.icns done")
except Exception as e:
    print("icns failed (non-fatal):", e)

# 4. public/apple-touch-icon.png — 180x180 favicon
img.resize((180, 180), Image.LANCZOS).save(BASE / "public" / "apple-touch-icon.png", "PNG")
print("apple-touch-icon.png done")

# 5. public/nous-girl.jpg -> public/aakalan-brand.jpg (new brand mark tile, white bg)
white = Image.new("RGBA", (512, 512), (255, 255, 255, 255))
white.paste(img.resize((460, 460), Image.LANCZOS), (26, 26))
white.convert("RGB").save(BASE / "public" / "aakalan-brand.jpg", "JPEG", quality=92)
print("aakalan-brand.jpg done")

# 6. Legacy public logos: replace content (filenames kept to avoid breaking refs)
img.resize((512, 512), Image.LANCZOS).save(BASE / "public" / "hermes.png", "PNG")
img.resize((512, 512), Image.LANCZOS).save(BASE / "public" / "hermes-sprite.png", "PNG")
print("legacy public logos replaced")

print("ALL DONE")
