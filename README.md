# David Fairbairn — personal portfolio

A responsive, multi-page portfolio for GitHub Pages. Plain HTML and CSS with a small optional JavaScript controller for the home-page hero media: no packages or build step required. All pages load three font families from Google Fonts: Open Sans for body text; Inter for navigation, labels, buttons, and supporting interface text; and Cormorant Garamond for headings, publication titles, and introductory display text. Shared font variables in `assets/style.css` keep these roles consistent, with system sans-serif and Georgia fallbacks. The decorative graph illustration is inline SVG.

## AI assistance and attribution

This website was created with assistance from OpenAI Codex, an AI coding assistant. AI was used to generate and refine page layouts, HTML, CSS, JavaScript, and website copy in response to David Fairbairn’s instructions, including typography and the home-page hero media implementation.

Biographical and professional information was adapted from David’s existing website and CV. Research publications retain their named authorship and link to their original sources.

Every page includes a visible AI credit linking to the fuller disclosure at `about.html#ai-disclosure`, including on mobile. Keep these credits and this description accurate when updating the site, and identify any future AI-generated photographs, illustrations, or video alongside those assets.

## Pages

- `index.html` — introduction and links to the main areas.
- `about.html` — biography and interests.
- `research.html` — publications, talks, and miscellaneous research material generated from BibTeX.
- `work.html` — industry experience and personal projects.
- `side-projects/index.html` — placeholder cards for future side projects.
- `photography.html` — space for the forthcoming photo collection.
- `contact.html` — LinkedIn.

All pages share `assets/style.css`. Navigation and footers are plain HTML in each page; update all pages when changing shared links. Each page has its own title, description, and active navigation state.

## Preview locally

From this folder, run `python -m http.server 8000`, then open http://localhost:8000.

## Home-page hero banner

The front-page title sits over a full-width media layer with a dark contrast overlay. The graph illustration is the fallback when no media is configured, JavaScript is disabled, or files fail to load. Add your media files under `assets/hero/` and edit the attributes on `<section class="hero hero-banner wrap">` in `index.html`:

- **Image slideshow:** set `data-hero-images='["assets/hero/image-1.jpg", "assets/hero/image-2.jpg"]'`. Images crossfade every six seconds. One image produces a static banner. The array order determines the sequence; failed images are skipped.
- **Video:** set `data-hero-video="assets/hero/banner.mp4"` and optionally `data-hero-poster="assets/hero/poster.jpg"`. Video plays muted, loops, and works inline on mobile. A configured video takes priority over the slideshow; the poster and images remain available as fallbacks.
- **Timing:** set `data-hero-interval="6000"` to the duration in milliseconds between slides (minimum 3000).
- **Cropping:** adjust `object-position` on `.hero-slide,.hero-video` in `assets/style.css` if the focal point needs moving.

Use landscape images and a compressed browser-compatible MP4. Media URLs are relative to the home page. The visible pause/play button controls animation; reduced-motion users start with a still image or video frame, and playback pauses when the tab is hidden. Keep the media decorative because its visual contents are hidden from screen readers; the title, description, and links remain normal accessible HTML.

## Personalise

- **Introduction and biography:** edit `index.html` and `about.html` respectively.
- **Research and professional work:** edit `data/research.bib` and its `data/research.json` metadata, then run the Python builder below; edit industry cards in `work.html`. Duplicate an `<article class="work-card">` for additional projects.
- **Side projects:** replace the placeholder cards in `side-projects/index.html` with your projects. Keep shared asset and navigation links relative to the parent directory (`../`).
- **Contact:** the site links to LinkedIn. Update the profile URL when needed.
- **Photography:** add your photographs to `assets/photos/`. In `photography.html`, replace the `photo-placeholder` div and its contents with an image, for example `<img class="photo-image" src="assets/photos/landscape.jpg" alt="Describe the actual photograph" width="1200" height="800" loading="lazy">`. Adjust the dimensions to match your image. Use compressed JPEG or WebP files and meaningful alt text.
- **Colours and layout:** edit the variables and styles in `assets/style.css`.
- **Site metadata:** update each page's title and description, and the general metadata in `_config.yml`.

Background, roles, publications, and contact information were adapted from your existing website and linked 2025 CV on 20 September 2026. Check these are still current before publishing, especially your Durham affiliation and industry roles. Research links point directly to external publication records. The GitHub Pages site does not depend on the retired site. Photography is an explicitly labelled placeholder.

## Publish on GitHub Pages

Rebuild the research page after bibliography changes, then commit the bibliography, JSON metadata, and generated `research.html`. GitHub Pages serves the generated HTML; no Python is required on the server.

Commit and push these files to the repository. In repository **Settings → Pages**, choose **Deploy from a branch**, then your chosen branch and **/ (root)**. The site will be served at https://david-fairbairn.github.io once the Pages deployment finishes. The HTML works directly with GitHub Pages; `_config.yml` supplies metadata and excludes this README from the published files.

## Build the research page

Requires Python 3.10 or later. Set up once from the repository root (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Replace or extend `data/research.bib`, and set custom website link labels in `data/research.json`, then run:

```powershell
.\.venv\Scripts\python.exe scripts/build_research.py
# Or use a bibliography elsewhere:
.\.venv\Scripts\python.exe scripts/build_research.py --bib "C:\path\to\research.bib"
# Verify the generated page is current without changing it:
.\.venv\Scripts\python.exe scripts/build_research.py --check
# Run the builder tests:
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`.

The builder replaces only the content between `BEGIN GENERATED RESEARCH` and `END GENERATED RESEARCH` in `research.html`. Edit the surrounding introduction, navigation, and styling normally. Generated lists should be edited through the bibliography. The starter file preserves the two publications already on the site; empty talks and miscellaneous sections display a short placeholder instead of invented entries.

Entries are sorted newest year first, then by title. Missing years appear as “Undated”. Standard entries default to Publications; `@talk` and `@presentation` go to Talks; `@misc`, `@unpublished`, and `@poster` go to Miscellaneous. Use `website_section` to override this when needed.

| Field | Use |
| --- | --- |
| `title` | Required; braces and common LaTeX accents/commands supported |
| `author` | Optional; BibTeX `and` separators, `Last, First`, and braced organisation names supported |
| `year` | Optional four-digit year |
| `website_section` | Optional `publications`, `talks`, or `miscellaneous` |
| `eventtitle`, `booktitle`, `journal` | Venue, in that order of preference |
| `note` | Optional public description or status |
| `url` | Primary link; takes priority over `doi` |
| `doi` | Creates a DOI link when `url` is absent |
| `slides`, `video`, `pdf` | Optional additional links |

### Website metadata

Website link labels live in a separate JSON object keyed by the exact, case-sensitive BibTeX citation key (the label after `@inproceedings{`, for example):

```json
{
  "fairbairn2025distance": {
    "website_link_label": "Related preprint on arXiv"
  }
}
```

The builder automatically reads the `.json` file alongside the `.bib` file with the same base name. You can select a different metadata file with `--metadata path/to/metadata.json`. An absent automatic sidecar is allowed; an explicitly supplied missing file is an error. Entries without metadata use “Details” for URLs and “Paper & details” for DOIs. Custom labels apply to either primary link and are plain text, escaped for HTML. The old BibTeX `website_link_label` field is ignored. Other bibliography fields, including `website_section`, remain unchanged.

Malformed JSON, duplicate keys, unmatched citation keys, unknown fields, and invalid labels stop the build without changing the page. Remove or rename corresponding JSON keys when removing or renaming BibTeX entries. Metadata entries are optional.

All link fields must use absolute HTTP(S) URLs. Text is escaped as HTML; LaTeX is converted to plain Unicode text, not executed or rendered as mathematical typesetting. Missing titles, duplicate keys, invalid sections/years/links, and detected malformed entries stop the build without overwriting the page. An empty bibliography is allowed. `--check` exits 0 when current, 1 when stale, and 2 on an error.

Example entries to adapt (illustrative only; not included in the generated page):

```bibtex
@misc{example-talk,
  title = {Title of your talk},
  author = {Fairbairn, David},
  year = {2026},
  eventtitle = {Event name},
  website_section = {talks},
  slides = {https://example.org/slides.pdf}
}

@misc{example-poster,
  title = {Title of your poster or short work},
  author = {Fairbairn, David},
  note = {Poster presented at Event name}
}
```

Every bibliography entry is displayed; keep private work in a separate file. The input bibliography and Python tooling are excluded from the Pages output by `_config.yml`, but committed files remain visible in the GitHub repository. Python environments, caches, build outputs, and local `.env` files are excluded from Git by `.gitignore`.
