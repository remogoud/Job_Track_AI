"""Generate assets/app.ico (a simple placeholder app icon).
Run: python assets/app_icon_generator.py
"""
from __future__ import annotations
from pathlib import Path


def main() -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not installed (pip install Pillow). Skipping icon.")
        return
    out = Path(__file__).resolve().parent / "app.ico"
    img = Image.new("RGBA", (256, 256), (30, 60, 120, 255))
    d = ImageDraw.Draw(img)
    d.ellipse((40, 40, 216, 216), fill=(255, 200, 60, 255))
    d.rectangle((70, 90, 186, 100), fill=(30, 60, 120, 255))
    d.rectangle((70, 120, 160, 130), fill=(30, 60, 120, 255))
    d.rectangle((70, 150, 130, 160), fill=(30, 60, 120, 255))
    img.save(out, format="ICO")
    print("Wrote", out)


if __name__ == "__main__":
    main()
