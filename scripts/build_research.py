"""Generate the research page's marked content from a UTF-8 BibTeX file."""
from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
import re
import sys
from urllib.parse import quote, urlsplit

import bibtexparser
from bibtexparser.bparser import BibTexParser
from pylatexenc.latex2text import LatexNodes2Text

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- BEGIN GENERATED RESEARCH -->'
END = '<!-- END GENERATED RESEARCH -->'
SECTIONS = {
    'publications': ('Publications', 'Publications will be added here.'),
    'talks': ('Talks', 'Talks and presentations will be added here.'),
    'miscellaneous': ('Miscellaneous', 'Posters, short work, and other research material will be added here.'),
}
LABELS = {'inproceedings': 'Conference paper', 'article': 'Journal article',
          'book': 'Book', 'phdthesis': 'PhD thesis', 'mastersthesis': 'Thesis',
          'techreport': 'Technical report', 'unpublished': 'Unpublished work',
          'talk': 'Talk', 'presentation': 'Presentation', 'misc': 'Miscellaneous',
          'poster': 'Poster'}


def plain(value: str) -> str:
    """Convert common LaTeX commands/accents without running TeX."""
    return ' '.join(LatexNodes2Text().latex_to_text(value).split())


def authors(value: str) -> str:
    # Split only at top-level `and`, preserving braced organisation names.
    parts, start, depth = [], 0, 0
    for match in re.finditer(r'(?<!\\)[{}]|\s+and\s+', value):
        token = match.group()
        if token == '{':
            depth += 1
        elif token == '}':
            depth -= 1
        elif depth == 0:
            parts.append(value[start:match.start()])
            start = match.end()
    parts.append(value[start:])
    result = []
    for part in parts:
        name = part.strip()
        if not (name.startswith('{') and name.endswith('}')):
            pieces = [x.strip() for x in name.split(',')]
            if len(pieces) == 2:
                name = f'{pieces[1]} {pieces[0]}'
            elif len(pieces) == 3:
                name = f'{pieces[2]} {pieces[0]}, {pieces[1]}'
        result.append(plain(name))
    return ', '.join(result)


def section_for(entry: dict) -> str:
    section = entry.get('website_section', '').strip().lower()
    if not section:
        kind = entry['ENTRYTYPE']
        section = ('talks' if kind in ('talk', 'presentation') else
                   'miscellaneous' if kind in ('misc', 'unpublished', 'poster') else 'publications')
    if section not in SECTIONS:
        raise ValueError(f"{entry['ID']}: website_section must be publications, talks, or miscellaneous")
    return section


def safe_url(value: str, key: str) -> str:
    value = value.strip().replace(r'\&', '&').replace(r'\_', '_').replace(r'\%', '%')
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or any(c.isspace() for c in value):
        raise ValueError(f'{key}: links must be absolute HTTP(S) URLs')
    return value


def read_entries(path: Path) -> list[dict]:
    parser = BibTexParser(common_strings=True, ignore_nonstandard_types=False,
                          add_missing_from_crossref=True)
    database = bibtexparser.loads(path.read_text(encoding='utf-8-sig'), parser=parser)
    # Bibtexparser can treat malformed entries as implicit comments.
    if any(re.search(r'@\w+\s*[({]', comment) for comment in database.comments):
        raise ValueError('Malformed BibTeX entry found; check braces, commas, and field values')
    seen = set()
    for entry in database.entries:
        key = entry['ID']
        if key in seen:
            raise ValueError(f'Duplicate citation key: {key}')
        seen.add(key)
        if not plain(entry.get('title', '')):
            raise ValueError(f'{key}: title is required')
        section_for(entry)
        if entry.get('year') and not re.fullmatch(r'\d{4}', entry['year'].strip()):
            raise ValueError(f'{key}: year must contain four digits (or be omitted)')
    return database.entries


def read_metadata(path: Path, entries: list[dict]) -> dict:
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate metadata key: {key}')
            result[key] = value
        return result

    metadata = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)
    if not isinstance(metadata, dict):
        raise ValueError('Metadata must be a JSON object keyed by BibTeX citation key')
    keys = {entry['ID'] for entry in entries}
    for key, fields in metadata.items():
        if key not in keys:
            raise ValueError(f'{key}: metadata has no matching BibTeX citation key')
        if not isinstance(fields, dict):
            raise ValueError(f'{key}: metadata must be an object')
        if set(fields) - {'website_link_label'}:
            raise ValueError(f'{key}: unsupported metadata field; expected website_link_label')
        if 'website_link_label' in fields:
            label = fields['website_link_label']
            if not isinstance(label, str) or not label.strip():
                raise ValueError(f'{key}: website_link_label must be a non-empty string')
    return metadata


def render_entry(entry: dict, section: str, metadata: dict) -> str:
    key = entry['ID']
    title = escape(plain(entry['title']))
    year = escape(entry.get('year', '').strip() or 'Undated')
    venue = entry.get('eventtitle') or entry.get('booktitle') or entry.get('journal') or ''
    label = ('Talk' if section == 'talks' else 'Miscellaneous' if section == 'miscellaneous'
             else LABELS.get(entry['ENTRYTYPE'], 'Publication'))
    venue_label = escape(' · '.join(filter(None, [plain(venue), label])))
    link_label = metadata.get('website_link_label')
    details = f'<p>{escape(authors(entry["author"]))}</p>' if entry.get('author') else ''
    if entry.get('note'):
        details += f'<p>{escape(plain(entry["note"]))}</p>'
    links = []
    if entry.get('url'):
        links.append((entry['url'], link_label or 'Details'))
    elif entry.get('doi'):
        doi = entry['doi'].strip()
        links.append((doi if doi.startswith('https://doi.org/') else
                      'https://doi.org/' + quote(doi, safe='/():.'), link_label or 'Paper & details'))
    for field, name in [('slides', 'Slides'), ('video', 'Video'), ('pdf', 'PDF')]:
        if entry.get(field):
            links.append((entry[field], name))
    anchors = ''.join(f'<a class="text-link" href="{escape(safe_url(url, key), quote=True)}">'
                      f'{escape(name)} <span aria-hidden="true">↗</span></a>' for url, name in links)
    if anchors:
        details += f'<div class="research-links">{anchors}</div>'
    return (f'        <li id="ref-{escape(quote(key, safe=""), quote=True)}">'
            f'<span class="publication-year">{year}</span><div>'
            f'<p class="eyebrow">{venue_label}</p><h3 class="item-title">{title}</h3>'
            f'{details}</div></li>')


def render(entries: list[dict], metadata: dict | None = None) -> str:
    metadata = metadata or {}
    output = []
    for section, (title, empty) in SECTIONS.items():
        items = sorted((e for e in entries if section_for(e) == section),
                       key=lambda e: (-int(e.get('year') or 0), plain(e['title']).casefold(), e['ID']))
        output.append(f'      <section class="research-group" id="{section}" aria-labelledby="{section}-title">')
        output.append(f'        <h2 id="{section}-title">{title}</h2>')
        if items:
            output.append('        <ol class="publication-list">')
            output.extend(render_entry(e, section, metadata.get(e['ID'], {})) for e in items)
            output.append('        </ol>')
        else:
            output.append(f'        <p class="research-intro">{empty}</p>')
        output.append('      </section>')
    return '\n'.join(output)


def build(bib: Path, page: Path, check: bool = False, metadata_path: Path | None = None) -> bool:
    existing = page.read_text(encoding='utf-8')
    if existing.count(START) != 1 or existing.count(END) != 1:
        raise ValueError('Research page must contain exactly one pair of generated-content markers')
    before, rest = existing.split(START)
    _, after = rest.split(END)
    entries = read_entries(bib)
    # Auto-discover a sibling JSON file; an explicitly requested file must exist.
    sidecar = metadata_path if metadata_path is not None else bib.with_suffix('.json')
    metadata = read_metadata(sidecar, entries) if metadata_path is not None or sidecar.exists() else {}
    updated = before + START + '\n' + render(entries, metadata) + '\n      ' + END + after
    changed = updated != existing
    if changed and not check:
        # Write only after the entire bibliography has parsed and validated.
        temporary = page.with_suffix(page.suffix + '.tmp')
        temporary.write_text(updated, encoding='utf-8', newline='\n')
        temporary.replace(page)
    return changed


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--bib', type=Path, default=ROOT / 'data/research.bib', help='Input bibliography')
    cli.add_argument('--page', type=Path, default=ROOT / 'research.html', help='Existing page with content markers')
    cli.add_argument('--metadata', type=Path, help='JSON metadata keyed by citation key; defaults to a sibling .json file if present')
    cli.add_argument('--check', action='store_true', help='Exit 1 if generated content is stale; do not write')
    args = cli.parse_args()
    try:
        changed = build(args.bib, args.page, args.check, args.metadata)
    except Exception as exc:
        print(f'Research build failed: {exc}', file=sys.stderr)
        return 2
    print('Research page is stale.' if changed and args.check else
          'Research page updated.' if changed else 'Research page is up to date.')
    return 1 if changed and args.check else 0


if __name__ == '__main__':
    raise SystemExit(main())
