import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.rows, self.row = [], [], None

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        for key in ('src', 'href'):
            if key in data:
                self.links.append(data[key])
        if tag == 'td' and self.row is None:
            self.row = []
        if tag == 'a' and self.row is not None:
            self.row.append(data['href'])

    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


class Site(unittest.TestCase):
    def test_links(self):
        for page in [Path('index.html'), *Path('docs').glob('*.html')]:
            doc = Links()
            doc.feed(page.read_text())
            for link in doc.links:
                u = urlsplit(link)
                if not u.scheme:
                    target = page.parent / u.path if u.path else page
                    if target.is_dir():
                        target /= 'index.html'
                    self.assertTrue(target.is_file(), f'{page}: {link}')
            if page.name == 'audit.html':
                self.assertEqual(len(doc.rows), 41)
                for row in doc.rows:
                    self.assertTrue(any(urlsplit(url).netloc == 'statsapi.mlb.com' for url in row))

    def test_viewer_modules(self):
        """The module layout the original README documents is present and linked."""
        for name in ('api.js', 'app.js', 'eventlog.js', 'format.js'):
            self.assertTrue(Path('docs/js', name).is_file(), f'docs/js/{name}')
        self.assertEqual(list(Path('docs').glob('*.js')), [])
        for module in Path('docs/js').glob('*.js'):
            for target in re.findall(r'from\s+"(\./[^"]+)"', module.read_text()):
                self.assertTrue((module.parent / target).is_file(), f'{module}: {target}')
