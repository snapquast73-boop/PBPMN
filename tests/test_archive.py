import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from mlb_pbp.archive import save, verified
from mlb_pbp.client import Client
from mlb_pbp.formatter import render


class Archive(unittest.TestCase):
    def test_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = b'synthetic test fixture'
            file = save(root, 'raw/sample.gz', gzip.compress(raw))
            row = dict(files={'raw': file}, sha256=hashlib.sha256(raw).hexdigest())
            self.assertTrue(verified(root, row))
            (root/file['path']).write_bytes(b'corrupt')
            self.assertFalse(verified(root, row))

    def test_events(self):
        data = {'gamePk': 0, 'liveData': {'plays': {'allPlays': [{'playEvents': [{}]}]}}}
        rows = render('events', b'', data, {}).splitlines()
        self.assertEqual([json.loads(r)['recordType'] for r in rows], ['metadata', 'play', 'event'])

    def test_host(self):
        with self.assertRaises(ValueError):
            Client().get('https://example.org/')
