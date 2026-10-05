import tempfile
from pathlib import Path
import unittest

from scripts.build_research import START, END, build, read_entries, render


class ResearchBuilderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.bib = Path(self.directory.name) / 'research.bib'
        self.page = Path(self.directory.name) / 'research.html'
        self.page.write_text(f'HEADER{START}\n{END}FOOTER', encoding='utf-8')

    def entries(self, bib):
        self.bib.write_text(bib, encoding='utf-8')
        return read_entries(self.bib)

    def test_bibtex_accents_names_macros_and_html_escaping(self):
        entries = self.entries(r'''
@string{venue = "Example conference"}
@inproceedings{one,
 title = {{Graph} theory \& <script>},
 author = {M{\"u}ller, Ada and {Research and Development}},
 year = {2025}, booktitle = venue,
 url = {https://example.org/paper?a=1&b=2}}
''')
        html = render(entries)
        self.assertIn('Ada Müller, Research and Development', html)
        self.assertIn('Graph theory &amp; &lt;script&gt;', html)
        self.assertIn('Example conference', html)
        self.assertIn('?a=1&amp;b=2', html)

    def test_routing_sorting_and_optional_fields(self):
        html = render(self.entries('''
@article{old, title={Old paper}, year={2020}}
@article{new, title={New paper}, year={2026}}
@talk{talk, title={Invited talk}, year={2024}, slides={https://example.org/slides}}
@misc{draft, title={A poster}, website_section={miscellaneous}}
@unpublished{preprint, title={Preprint}, year={2025}}
'''))
        self.assertLess(html.index('New paper'), html.index('Old paper'))
        self.assertLess(html.index('id="talks"'), html.index('Invited talk'))
        self.assertLess(html.index('id="miscellaneous"'), html.index('A poster'))
        self.assertLess(html.index('id="miscellaneous"'), html.index('Preprint'))
        self.assertIn('Undated', html)
        self.assertIn('Slides', html)

    def test_invalid_input_does_not_overwrite_page(self):
        original = self.page.read_bytes()
        for bib in ['@article{x, title={Unclosed}',
                    '@article{x, year={2025}}',
                    '@misc{x, title={A}, website_section={wrong}}',
                    '@misc{x, title={A}, year={forthcoming}}',
                    '@misc{x, title={A}}\n@misc{x, title={B}}',
                    '@misc{x, title={A}, url={javascript:alert(1)}}']:
            with self.subTest(bib=bib):
                self.bib.write_text(bib, encoding='utf-8')
                with self.assertRaises(Exception):
                    build(self.bib, self.page)
                self.assertEqual(original, self.page.read_bytes())

    def test_build_is_repeatable_and_check_does_not_write(self):
        self.entries('@article{x, title={Example}, doi={10.1234/example}}')
        original = self.page.read_bytes()
        self.assertTrue(build(self.bib, self.page, check=True))
        self.assertEqual(original, self.page.read_bytes())
        self.assertTrue(build(self.bib, self.page))
        self.assertFalse(build(self.bib, self.page, check=True))
        self.assertFalse(build(self.bib, self.page))
        html = self.page.read_text(encoding='utf-8')
        self.assertTrue(html.startswith('HEADER'))
        self.assertTrue(html.endswith('FOOTER'))
        self.assertIn('https://doi.org/10.1234/example', html)

    def test_empty_bibliography_has_all_sections(self):
        html = render(self.entries('% Nothing to list yet.'))
        self.assertIn('Publications will be added here.', html)
        self.assertIn('Talks and presentations will be added here.', html)
        self.assertIn('Posters, short work, and other research material will be added here.', html)

    def test_metadata_join_defaults_and_html_escaping(self):
        self.entries('''
@article{x, title={Example}, url={https://example.org}, website_link_label={Old label}}
@article{y, title={Other}, doi={10.1234/other}}
''')
        self.bib.with_suffix('.json').write_text(
            '{"x": {"website_link_label": "Read <paper> & notes"}}', encoding='utf-8')
        build(self.bib, self.page)
        html = self.page.read_text(encoding='utf-8')
        self.assertIn('Read &lt;paper&gt; &amp; notes', html)
        self.assertNotIn('Old label', html)
        self.assertIn('Paper &amp; details', html)
        self.assertFalse(build(self.bib, self.page, check=True))

    def test_explicit_metadata_and_doi_label(self):
        self.entries('@article{x, title={Example}, doi={10.1234/example}}')
        metadata = self.bib.parent / 'custom.json'
        metadata.write_text('{"x": {"website_link_label": "Read paper"}}', encoding='utf-8')
        build(self.bib, self.page, metadata_path=metadata)
        self.assertIn('Read paper', self.page.read_text(encoding='utf-8'))
        with self.assertRaises(FileNotFoundError):
            build(self.bib, self.page, metadata_path=self.bib.parent / 'missing.json')

    def test_invalid_metadata_preserves_page(self):
        self.entries('@article{x, title={Example}}')
        original = self.page.read_bytes()
        for value in ['{', '[]', '{"unknown": {}}', '{"x": []}',
                      '{"x": {"website_link_label": 42}}',
                      '{"x": {"website_link_label": " "}}',
                      '{"x": {"typo": "Label"}}', '{"x": {}, "x": {}}']:
            with self.subTest(value=value):
                self.bib.with_suffix('.json').write_text(value, encoding='utf-8')
                with self.assertRaises(ValueError):
                    build(self.bib, self.page)
                self.assertEqual(original, self.page.read_bytes())


if __name__ == '__main__':
    unittest.main()
