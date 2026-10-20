#!/usr/bin/env python3
"""Build the HEATlab brand files (logo, robot "A", icon, wink animation) into assets/img/brand/.

    python3 tools/build_logo.py          SVGs only (no other tools needed beyond Pillow + fontTools)
    python3 tools/build_logo.py --png    also PNG/ICO/GIF/WebP exports (renders the SVGs with headless Chrome)

The letters are Montserrat (tools/fonts, SIL Open Font License) converted to outlines, so the SVGs need
no fonts. The robot's body is Harvey Mudd College's own mark, embedded unmodified:
    img/logos/hmc-bgw.png   black box, gold + white type (light backgrounds)
    img/logos/hmc-gbw.png   gold box, black + white type (HMC's alternate, for dark backgrounds)
from HMC's 2014 logo package (WEB/SCREEN, 2 Color, RGB). The robot was measured from the original
HEATlab logo and modernized in 2026: gear eye, LED-pill eye that winks (a rounded caret), a solid smile,
and an antenna with a gold LED tip.
"""
import base64
import io
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "brand"
FONT = Path(__file__).resolve().parent / "fonts" / "Montserrat.ttf"
GOLD, INK, LIGHT, DARK_BG = "#FDB913", "#1d2126", "#e6e9ed", "#15171a"
TAGLINE = "human experience & agent teamwork laboratory @ harvey mudd"


# ---------------------------------------------------------------- letters
def instance(weight):
    return instantiateVariableFont(TTFont(FONT), {"wght": weight})


HEAVY, THIN, REGULAR = instance(800), instance(300), instance(400)


def text_path(font, text, x, baseline, size, tracking=0):
    """SVG path data for text set in `font`, and the x where it ends."""
    glyphs, cmap, upm = font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm
    s, parts = size / upm, []
    for ch in text:
        name = cmap[ord(ch)]
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
        parts.append(pen.getCommands())
        x += glyphs[name].width * s + tracking
    return " ".join(parts), x


def embed(path, size=360):
    im = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


BODY = {"light": embed(ROOT / "img/logos/hmc-bgw.png"), "dark": embed(ROOT / "img/logos/hmc-gbw.png")}
CAP, BASE = 170, 236                 # cap height and baseline, in SVG units
SIZE = CAP / 0.70                    # Montserrat's cap height is 0.70 em


# ---------------------------------------------------------------- the robot
def gear(cx, cy, r_out, r_in, teeth, hole):
    pts = []
    for i in range(teeth * 2):
        for k in (0, 1):
            a = (i + k * 0.55) * math.pi / teeth - math.pi / 2
            r = r_out if i % 2 == 0 else r_in
            pts.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    return (f"M{pts[0]} L" + " L".join(pts[1:]) + " Z "
            f"M{cx - hole},{cy} a{hole},{hole} 0 1,0 {2 * hole},0 a{hole},{hole} 0 1,0 {-2 * hole},0 Z")


def wink_eye(x, ey, face):
    """The winking eye: a rounded caret ^, drawn with the smile's stroke."""
    return (f'<path d="M{x - 9} {ey + 2.75} L{x} {ey - 2.75} L{x + 9} {ey + 2.75}" fill="none" stroke="{face}" '
            f'stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>')


def open_eye(x, ey, face):
    """The open eye: a thin flat LED pill with the caret's stroke weight and span (the wink animation's rest state)."""
    return (f'<path d="M{x - 6.5} {ey} L{x + 6.5} {ey}" fill="none" stroke="{face}" stroke-width="5" '
            f'stroke-linecap="round"/>')


def robot(x0, ink, face, body, eye="wink", animate=False):
    """The robot "A"; x0 is where the E ends. eye: "wink" (logo) or "open". animate: blink the wink."""
    bx = x0 + 45                     # left edge of the HMC body
    hx, hy = bx + 55, 60             # head center
    ey = hy - 9                      # eye line
    line = lambda x1, y1, x2, y2: (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{ink}" '
                                   f'stroke-width="20" stroke-linecap="round"/>')
    if animate:                      # open pill most of the time, a quick caret wink every few seconds
        right_eye = (f'<g class="eye-open">{open_eye(hx + 16, ey, face)}</g>'
                     f'<g class="eye-wink">{wink_eye(hx + 16, ey, face)}</g>')
    else:
        right_eye = wink_eye(hx + 16, ey, face) if eye == "wink" else open_eye(hx + 16, ey, face)
    return f'''<g class="robot">
  <g transform="rotate(-7 {hx} {hy})">
    <line x1="{hx + 4}" y1="{hy - 29}" x2="{hx + 8}" y2="{hy - 48}" stroke="{ink}" stroke-width="6" stroke-linecap="round"/>
    <circle cx="{hx + 9}" cy="{hy - 53}" r="7.5" fill="{face}"/>
    <rect x="{hx - 48}" y="{hy - 29}" width="96" height="58" rx="17" fill="{ink}"/>
    <path d="{gear(hx - 15, ey, 11.5, 8.3, 8, 3.8)}" fill="{face}" fill-rule="evenodd"/>
    {right_eye}
    <path d="M{hx - 10} {ey + 20} Q{hx + 1} {ey + 29} {hx + 12} {ey + 20}" fill="none" stroke="{face}" stroke-width="5" stroke-linecap="round"/>
  </g>
  {line(bx - 11, 114, bx - 27, 186)}
  {line(bx + 122, 112, bx + 139, 180)}
  {line(bx + 21, 222, bx + 18, 248)}
  {line(bx + 88, 222, bx + 92, 248)}
  <image href="{body}" x="{bx - 1}" y="92" width="112" height="112"/>
</g>'''


# Wink timing for the animated SVGs: open for 2.6 s, wink for 0.4 s. Two complementary hard switches
# (step-end), so exactly one eye shows at every moment: no fade, no blank frame.
WINK_CSS = ("<style>.eye-open{animation:eye-open 3s step-end infinite}.eye-wink{animation:eye-wink 3s step-end infinite}"
            "@keyframes eye-open{0%{opacity:1}86.67%{opacity:0}100%{opacity:0}}"
            "@keyframes eye-wink{0%{opacity:0}86.67%{opacity:1}100%{opacity:1}}"
            "@media (prefers-reduced-motion:reduce){.eye-open{animation:none;opacity:0}.eye-wink{animation:none;opacity:1}}</style>")


# ---------------------------------------------------------------- lockups
def layout():
    he, x = text_path(HEAVY, "HE", 0, BASE, SIZE, tracking=16)
    rx = x - 16                                          # end of the E
    t, x = text_path(HEAVY, "T", rx + 179, BASE, SIZE)
    lab, x = text_path(THIN, "lab", x + 4, BASE, SIZE)
    _, tw = text_path(REGULAR, TAGLINE, 0, 0, 100)
    tsize = 100 * x * 0.9 / tw                           # tagline spans 90% of the width, as in the original
    tag, _ = text_path(REGULAR, TAGLINE, x * 0.05, 316, tsize)
    return he, rx, t, lab, tag, x


HE, RX, T, LAB, TAG, WIDTH = layout()
MODES = {"light": dict(letters=INK, ink=INK, tag=INK, body=BODY["light"]),
         "dark": dict(letters="#ffffff", ink=LIGHT, tag="#c9ced6", body=BODY["dark"])}


def logo_svg(mode, animate=False):
    m = MODES[mode]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 -12 {WIDTH + 20:.0f} 357" role="img" '
            f'aria-label="HEATlab: human experience &amp; agent teamwork laboratory @ harvey mudd">'
            + (WINK_CSS if animate else "") +
            f'<path d="{HE}" fill="{m["letters"]}"/>{robot(RX, m["ink"], GOLD, m["body"], animate=animate)}'
            f'<path d="{T}" fill="{m["letters"]}"/><path d="{LAB}" fill="{m["letters"]}"/><path d="{TAG}" fill="{m["tag"]}"/></svg>')


def robot_svg(mode, animate=False, eye="wink"):
    m = MODES[mode]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{RX + 4:.0f} -8 210 270" role="img" aria-label="A">'
            + (WINK_CSS if animate else "") + robot(RX, m["ink"], GOLD, m["body"], eye=eye, animate=animate) + '</svg>')


def icon_svg(bg, ink, eye="wink"):
    """Square icon: the head only (favicon, avatar). bg "none" for transparent."""
    hx, hy = 60, 64
    ey = hy - 9
    right = wink_eye(hx + 16, ey, GOLD) if eye == "wink" else open_eye(hx + 16, ey, GOLD)
    tile = f'<rect width="120" height="120" rx="26" fill="{bg}"/>' if bg != "none" else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" role="img" aria-label="HEATlab">{tile}'
            f'<g transform="translate(60 62) scale(1.05) translate(-60 -62)">'
            f'<rect x="{hx - 48}" y="{hy - 29}" width="96" height="58" rx="17" fill="{ink}"/>'
            f'<path d="{gear(hx - 15, ey, 11.5, 8.3, 8, 3.8)}" fill="{GOLD}" fill-rule="evenodd"/>{right}'
            f'<path d="M{hx - 10} {ey + 20} Q{hx + 1} {ey + 29} {hx + 12} {ey + 20}" fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>'
            f'</g></svg>')


def svgs():
    files = {
        "heatlab-logo.svg": logo_svg("light"),
        "heatlab-logo-dark.svg": logo_svg("dark"),
        "heatlab-logo-wink.svg": logo_svg("light", animate=True),
        "heatlab-logo-wink-dark.svg": logo_svg("dark", animate=True),
        "heatbot.svg": robot_svg("light"),
        "heatbot-dark.svg": robot_svg("dark"),
        "heatbot-wink.svg": robot_svg("light", animate=True),
        "heatbot-wink-dark.svg": robot_svg("dark", animate=True),
        "heatlab-icon.svg": icon_svg(GOLD, INK),
        "heatlab-icon-dark.svg": icon_svg(DARK_BG, LIGHT),
        "heatlab-icon-plain.svg": icon_svg("none", INK),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in files.items():
        (OUT / name).write_text(svg + "\n", encoding="utf-8")
    return files


# ---------------------------------------------------------------- raster exports (--png)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def render(svg, width, height, bg="transparent"):
    """Render an SVG string to a PIL image with headless Chrome."""
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "p.html"
        page.write_text(f'<!doctype html><html><body style="margin:0;background:{bg}">'
                        f'<img src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}" '
                        f'style="display:block;width:{width}px;height:{height}px"></body></html>')
        shot = Path(d) / "s.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                        f"--window-size={width},{height}", f"--screenshot={shot}", page.as_uri()],
                       check=True, capture_output=True)
        return Image.open(shot).convert("RGBA").crop((0, 0, width, height))


def rasters():
    if not Path(CHROME).exists():
        sys.exit("PNG exports need Google Chrome (headless).")
    lw = 2000; lh = round(lw * 357 / (WIDTH + 20))
    for mode, suffix in (("light", ""), ("dark", "-dark")):
        render(logo_svg(mode), lw, lh).save(OUT / f"heatlab-logo{suffix}.png", optimize=True)
        render(robot_svg(mode), 420, 540).save(OUT / f"heatbot{suffix}.png", optimize=True)
    icon = render(icon_svg(GOLD, INK), 512, 512)
    icon.save(OUT / "heatlab-icon-512.png", optimize=True)
    icon.resize((192, 192), Image.LANCZOS).save(OUT / "heatlab-icon-192.png", optimize=True)
    icon.resize((180, 180), Image.LANCZOS).save(OUT / "apple-touch-icon.png", optimize=True)
    icon.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    render(icon_svg(DARK_BG, LIGHT), 512, 512).save(OUT / "heatlab-icon-dark-512.png", optimize=True)

    # The wink animation as GIF and WebP (open ~2.6 s, wink ~0.4 s), for email, Slack and slides.
    logo_h = round(1200 * 357 / (WIDTH + 20))
    for mode, suffix, bg in (("light", "", "#ffffff"), ("dark", "-dark", DARK_BG)):
        animations = {
            "heatbot-wink": ((420, 540), robot_svg(mode, eye="open"), robot_svg(mode, eye="wink")),
            "heatlab-logo-wink": ((1200, logo_h), open_logo(mode), logo_svg(mode)),
        }
        for name, ((w, h), open_svg, wink_svg) in animations.items():
            seq, durations = [render(open_svg, w, h), render(wink_svg, w, h)], [2600, 400]
            seq[0].save(OUT / f"{name}{suffix}.webp", save_all=True, append_images=seq[1:], duration=durations, loop=0, lossless=True)
            flat = []
            for f in seq:                              # GIF has no partial transparency: flatten onto the page color
                base = Image.new("RGBA", f.size, bg); base.alpha_composite(f); flat.append(base.convert("RGB").quantize(colors=128))
            flat[0].save(OUT / f"{name}{suffix}.gif", save_all=True, append_images=flat[1:], duration=durations, loop=0, optimize=True)


def open_logo(mode):
    """The full logo with the open (pill) eye: the wink animation's other frame."""
    m = MODES[mode]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 -12 {WIDTH + 20:.0f} 357">'
            f'<path d="{HE}" fill="{m["letters"]}"/>{robot(RX, m["ink"], GOLD, m["body"], eye="open")}'
            f'<path d="{T}" fill="{m["letters"]}"/><path d="{LAB}" fill="{m["letters"]}"/><path d="{TAG}" fill="{m["tag"]}"/></svg>')


if __name__ == "__main__":
    made = svgs()
    print(f"{len(made)} SVGs -> {OUT.relative_to(ROOT)}/")
    if "--png" in sys.argv:
        rasters()
        print("PNG, ICO, GIF and WebP exports done.")
