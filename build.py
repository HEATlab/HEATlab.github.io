#!/usr/bin/env python3
"""Build index.html from template.html, data/alumni.json, data/themes.json and Jim's publications .bib.

    python3 build.py                      fetch the .bib from Jim's homepage
    python3 build.py --bib path/to.bib    use a local copy (e.g. ../personal_homepage/cv/boerkoel_pubs.bib)

The .bib (https://www.cs.hmc.edu/~boerkoel/boerkoel_pubs.bib) is the single source for publications,
shared with Jim's homepage and CV. A paper appears here when an alumnus is among its authors; those
authors are shown in bold. No third-party packages needed (curl is used to fetch the .bib).
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BIB_URL = "https://www.cs.hmc.edu/~boerkoel/boerkoel_pubs.bib"
PDF_BASE = "https://www.cs.hmc.edu/~boerkoel/"
COLLEGE_NAMES = {None: "Harvey Mudd", "Pomona": "Pomona", "Scripps": "Scripps", "Olin": "Olin", "CMC": "Claremont McKenna"}
I = " " * 16


def esc(s):
    return html.escape(s, quote=True)


# --- .bib ---------------------------------------------------------------------------------------
def parse_bib(text):
    """Return {key: (type, {field: value})}. Handles nested braces."""
    entries = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        typ, key, pos, fields = m.group(1).lower(), m.group(2), m.end(), {}
        while (fm := re.compile(r"\s*(\w+)\s*=\s*").match(text, pos)):
            name, pos = fm.group(1).lower(), fm.end()
            if text[pos] == "{":
                depth, j = 0, pos
                while True:
                    depth += {"{": 1, "}": -1}.get(text[j], 0)
                    if depth == 0:
                        break
                    j += 1
                value, pos = text[pos + 1:j], j + 1
            else:
                vm = re.compile(r"[^,}\s]+").match(text, pos)
                value, pos = vm.group(0), vm.end()
            fields[name] = re.sub(r"\s+", " ", value).strip()
            if (cm := re.compile(r"\s*,").match(text, pos)):
                pos = cm.end()
        entries[key] = (typ, fields)
    return entries


TEX = [(r'{\"o}', "ö"), (r'\"{o}', "ö"), (r'{\"u}', "ü"), (r"{\'e}", "é"), (r"\&", "&"), ("`", "‘"), ("'", "’")]


def tex(s):
    for a, b in TEX:
        s = s.replace(a, b)
    return s.replace("{", "").replace("}", "").replace("--", "–")


def authors_of(f):
    """[(first, last)] from 'Last, First and ...' ('Last, Jr., First' keeps the suffix on the last name)."""
    out = []
    for n in re.split(r"\s+and\s+", f.get("author", "")):
        if n.strip() == "others":
            continue
        parts = [tex(p.strip()) for p in n.split(",")]
        out.append((parts[2], f"{parts[0]} {parts[1]}") if len(parts) == 3 else
                   (parts[1], parts[0]) if len(parts) == 2 else (" ".join(n.split()[:-1]), n.split()[-1]))
    return out


# --- Matching students to authors ----------------------------------------------------------------
def student_matcher(alumni):
    """A function (first, last) -> alumnus or None. Same last name and same first initial."""
    keys = {}
    for a in alumni:
        for full in [a["name"]] + a.get("published_as", []):
            words = full.split()
            for i in range(1, len(words)):  # "Maya Abo Dominguez" -> last "Dominguez" or "Abo Dominguez"
                keys.setdefault((" ".join(words[i:]).lower(), words[0][0].lower()), a)
    return lambda first, last: keys.get((last.replace(" Jr.", "").lower(), first[:1].lower()))


# --- Sections ------------------------------------------------------------------------------------
def venue(typ, f):
    v = f.get("booktitle") or f.get("journal") or f.get("howpublished") or ""
    return tex(v)


def pub_html(key, typ, f, is_student, theme_ids):
    names = []
    for first, last in authors_of(f):
        n = esc(f"{first} {last}".strip())
        names.append(f"<b>{n}</b>" if is_student(first, last) else n)
    au = ", ".join(names[:-1]) + (", and " if len(names) > 2 else " and ") + names[-1] if len(names) > 1 else names[0]
    links = []
    if f.get("file"):
        links.append(f'<a href="{PDF_BASE}{esc(f["file"])}">PDF</a>')
    if f.get("doi"):
        links.append(f'<a href="https://doi.org/{esc(f["doi"])}">DOI</a>')
    elif f.get("url"):
        links.append(f'<a href="{esc(f["url"])}">Link</a>')
    return (f'{I}<article class="pub" id="pub-{key}" data-themes="{" ".join(theme_ids)}">\n'
            f'{I}    <h4>{esc(tex(f["title"]))}</h4>\n'
            f'{I}    <p class="pub-authors">{au}</p>\n'
            f'{I}    <p class="pub-venue"><i>{esc(venue(typ, f))}</i>, {f["year"]}'
            + (f' · {" · ".join(links)}' if links else "") + "</p>\n"
            f"{I}</article>")


def themes_html(themes, bib, match):
    out = []
    for t in themes:
        projects = []
        for p in t["projects"]:
            papers = "".join(
                f'<li><a href="#pub-{k}">{esc(tex(bib[k][1]["title"]))}</a> <span>({bib[k][1]["year"]})</span></li>'
                for k in p["papers"] if k in bib)
            people = []
            for k in p["papers"]:
                for first, last in authors_of(bib[k][1]) if k in bib else []:
                    a = match(first, last)
                    if a and a["name"] not in people:
                        people.append(a["name"])
            projects.append(
                f'{I}        <details>\n{I}            <summary>{esc(p["name"])}</summary>\n'
                f'{I}            <p>{esc(p["text"])}</p>\n'
                + (f'{I}            <p class="project-people">Students: {esc(", ".join(people))}</p>\n' if people else "")
                + (f'{I}            <ul class="project-papers">{papers}</ul>\n' if papers else "")
                + f"{I}        </details>")
        out.append(
            f'{I}<article class="theme">\n'
            f'{I}    <img src="assets/img/themes/{t["image"]}" alt="{esc(t["image_alt"])}" loading="lazy">\n'
            f'{I}    <div class="theme-body">\n'
            f'{I}        <h3>{esc(t["title"])}</h3>\n'
            f'{I}        <p>{esc(t["blurb"])}</p>\n'
            f'{I}        <p class="theme-projects-label">Past projects</p>\n'
            + "\n".join(projects) + "\n"
            f'{I}        <button type="button" class="theme-papers" data-theme="{t["id"]}">See the papers →</button>\n'
            f"{I}    </div>\n{I}</article>")
    return "\n".join(out)


GALLERY_ALTS = [
    "HEATlab students wearing conference badges, posed around a stone sphere sculpture",
    "A student working on the wrist of a red robot arm in the lab",
    "A NAO humanoid robot on a desk while a student works at a computer",
    "HEATlab group photo outdoors, with a student holding a NAO robot",
    "Two lab members watching an experiment in the robotics lab",
    "HEATlab group photo in the lab, with the lab's panda mascot wearing a HEATlab T-shirt",
    "Jim with the lab's robots: a Sawyer robot arm, a NAO humanoid, and a Jibo social robot",
    "HEATlab group photo in a sunny courtyard garden",
]


def gallery_html():
    return "\n".join(
        f'{I}<a href="assets/img/gallery/heatlab{i}.jpg" class="gallery-item">'
        f'<img src="assets/img/gallery/heatlab{i}-thumb.jpg" alt="{esc(alt)}" loading="lazy"></a>'
        for i, alt in enumerate(GALLERY_ALTS, 1))


def initials(name):
    parts = name.replace("-", " ").split()
    return (parts[0][0] + parts[-1][0]).upper()


def alumni_html(alumni):
    out = []
    for year in sorted({a["year"] for a in alumni}, reverse=True):
        cards = []
        for a in sorted((a for a in alumni if a["year"] == year), key=lambda a: a["name"].split()[-1]):
            avatar = (f'<img src="assets/img/team/{Path(a["photo"]).stem}.jpg" alt="" width="64" height="64" loading="lazy">'
                      if a.get("photo") else f'<span class="initials" aria-hidden="true">{initials(a["name"])}</span>')
            college = f' · {esc(COLLEGE_NAMES[a["college"]])}' if a.get("college") else ""
            now = f'<p class="alum-now">{esc(a["now"])}</p>' if a.get("now") else ""
            degrees = "".join(f'<p class="alum-degree">{esc(d)}</p>' for d in a.get("degrees", []))
            cards.append(
                f'{I}    <li class="alum">{avatar}<div><p class="alum-name">{esc(a["name"])}{college}</p>'
                f'<p class="alum-project">{esc(" · ".join(a["projects"]))}</p>{now}{degrees}</div></li>')
        out.append(f'{I}<h3 class="year">Class of {year}</h3>\n{I}<ul class="alumni">\n' + "\n".join(cards) + f"\n{I}</ul>")
    return "\n".join(out)


def main():
    if "--bib" in sys.argv:
        text = Path(sys.argv[sys.argv.index("--bib") + 1]).read_text(encoding="utf-8")
    else:
        text = subprocess.run(["curl", "-sfL", BIB_URL], check=True, capture_output=True, text=True).stdout
    bib = parse_bib(text)
    alumni = json.loads((ROOT / "data" / "alumni.json").read_text(encoding="utf-8"))["alumni"]
    themes = json.loads((ROOT / "data" / "themes.json").read_text(encoding="utf-8"))["themes"]
    match = student_matcher(alumni)

    student_pubs, coauthors = [], set()
    for key, (typ, f) in bib.items():
        if f.get("keywords", "") in ("grant", "patent"):
            continue
        hits = [match(first, last) for first, last in authors_of(f)]
        hits = [h for h in hits if h]
        if hits:
            student_pubs.append((key, typ, f))
            coauthors.update(h["name"] for h in hits)
    student_pubs.sort(key=lambda e: (e[2]["year"], e[0]), reverse=True)

    # A paper belongs to a theme when one of the theme's projects lists it (data/themes.json).
    themes_of = {}
    for t in themes:
        for p in t["projects"]:
            for k in p["papers"]:
                themes_of.setdefault(k, []).append(t["id"]) if t["id"] not in themes_of.get(k, []) else None
    pubs, last_year = [], None
    for key, typ, f in student_pubs:
        if f["year"] != last_year:
            pubs.append(f'{I}<h3 class="year pub-year">{f["year"]}</h3>')
            last_year = f["year"]
        pubs.append(pub_html(key, typ, f, lambda a, b: match(a, b) is not None, themes_of.get(key, [])))
    chips = [f'{I}<button type="button" class="chip active" data-theme="">All <span>{len(student_pubs)}</span></button>']
    for t in themes:
        n = sum(1 for k, _, _ in student_pubs if t["id"] in themes_of.get(k, []))
        chips.append(f'{I}<button type="button" class="chip" data-theme="{t["id"]}">{esc(t["title"])} <span>{n}</span></button>')

    colleges = sorted({a.get("college") for a in alumni}, key=lambda c: (c is not None, COLLEGE_NAMES[c]))
    fill = {
        "N_ALUMNI": str(len(alumni)), "FIRST_YEAR": str(min(a["year"] for a in alumni)),
        "N_COAUTHORS": str(len(coauthors)), "N_PAPERS": str(len(student_pubs)),
        "N_COLLEGES": str(len(colleges)), "COLLEGES": esc(", ".join(COLLEGE_NAMES[c] for c in colleges)),
        "THEMES": themes_html(themes, bib, match), "GALLERY": gallery_html(),
        "ALUMNI": alumni_html(alumni), "PUB_CHIPS": "\n".join(chips), "PUBS": "\n".join(pubs),
    }
    page = (ROOT / "template.html").read_text(encoding="utf-8")
    for k, v in fill.items():
        page = page.replace("{{" + k + "}}", v)
    if (left := re.findall(r"\{\{\w+\}\}", page)):
        sys.exit(f"Unfilled placeholders: {left}")
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print(f"index.html: {len(alumni)} alumni, {len(coauthors)} student co-authors, {len(student_pubs)} papers")
    missing = [k for t in themes for p in t["projects"] for k in p["papers"] if k not in bib]
    if missing:
        print("Warning: paper keys in data/themes.json not found in the .bib:", ", ".join(missing))


if __name__ == "__main__":
    main()
