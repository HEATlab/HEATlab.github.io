# HEATlab.github.io

Website for the Human Experience & Agent Teamwork Lab at Harvey Mudd College, served by GitHub Pages at https://www.heatlab.org.

`index.html` is generated, so don't edit it by hand. Edit these and rebuild:

| To change | Edit |
|---|---|
| Page text, sections, the "not recruiting" notice and FAQ | `template.html` |
| Alumni: names, class years, projects, photos, where they are now, further degrees | `data/alumni.json` |
| Research themes and past projects (and which papers each lists) | `data/themes.json` |
| Publications | Jim's `boerkoel_pubs.bib` (shared with his homepage and CV) |
| Styles / behavior | `assets/css/site.css`, `assets/js/site.js` |

Then:

```
python3 tools/make_images.py   # only after adding or changing photos (needs Pillow)
python3 build.py               # fetches the .bib from Jim's homepage; or: --bib path/to/boerkoel_pubs.bib
```

Commit and push `main`; GitHub Pages publishes within a minute or two.

Notes:
- A publication appears when one of its authors is an alumnus; those names are bolded. If a student published under a different name, add it to that person's `published_as` in `data/alumni.json`.
- Alumni photos go in `img/team/` (any size); `make_images.py` makes the small web versions in `assets/img/`.
- `css/`, `js/`, `papers/` and most of `img/` belong to the previous site and aren't used by the new page.
