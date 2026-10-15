#!/usr/bin/env python3
"""Make the web-sized images in assets/img/ from the originals in img/ (originals are untouched).

    python3 tools/make_images.py

Needs Pillow. Re-run after adding an alumni photo to img/team/ or changing data/alumni.json.
"""
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "img", ROOT / "assets" / "img"


def save(im, path, width, quality=78):
    im = ImageOps.exif_transpose(im)
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".png":
        im.save(path, optimize=True)
    else:
        im.convert("RGB").save(path, quality=quality, optimize=True, progressive=True)


def white_to_alpha(im):
    """Make a white background transparent, keeping anti-aliased edges and exact colors
    (each pixel becomes the least-transparent color that, over white, looks the same)."""
    im = im.convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, _ = px[x, y]
            a = 255 - min(r, g, b)
            if a == 0:
                px[x, y] = (255, 255, 255, 0)
            else:
                f = 255 / a
                px[x, y] = tuple(max(0, min(255, round(255 - (255 - c) * f))) for c in (r, g, b)) + (a,)
    return im


def square(im, size):
    """Center-crop to a square (biased toward the top, where faces are) and resize."""
    im = ImageOps.exif_transpose(im).convert("RGB")
    side = min(im.size)
    left, top = (im.width - side) // 2, min((im.height - side) // 2, im.height // 10)
    return im.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)


def main():
    save(Image.open(SRC / "heatlab-bg.jpg"), OUT / "hero.jpg", 2000, quality=72)
    logo = white_to_alpha(Image.open(SRC / "logos" / "HEATlab_logo.png"))
    logo.resize((520, round(logo.height * 520 / logo.width)), Image.LANCZOS).save(OUT / "logo.png", optimize=True)
    save(Image.open(SRC / "logos" / "hmc.png"), OUT / "hmc.png", 240)
    themes = {"teamwork.jpg": "projects/conavigation_action.jpg", "uncertainty.png": "projects/prob_ctrl.png",
              "multirobot.jpg": "projects/robotbrunch_action.jpg"}
    for out, src in themes.items():
        save(Image.open(SRC / src), OUT / "themes" / out, 800)
    for i in range(1, 9):
        im = Image.open(SRC / "team" / f"heatlab{i}.jpg")
        save(im, OUT / "gallery" / f"heatlab{i}.jpg", 1600)
        save(im, OUT / "gallery" / f"heatlab{i}-thumb.jpg", 600)
    square(Image.open(SRC / "team" / "jim.png"), 320).save(OUT / "team" / "jim.jpg", quality=82, optimize=True)
    for a in json.loads((ROOT / "data" / "alumni.json").read_text())["alumni"]:
        if a.get("photo"):
            out = OUT / "team" / (Path(a["photo"]).stem + ".jpg")
            square(Image.open(SRC / "team" / a["photo"]), 160).save(out, quality=82, optimize=True)
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"assets/img: {sum(1 for f in OUT.rglob('*') if f.is_file())} files, {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
