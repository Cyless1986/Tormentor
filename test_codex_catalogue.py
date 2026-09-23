import http.client
import tempfile
import threading
import unittest
from collections import Counter
from pathlib import Path

import codex_expansions
import portal


class CodexCatalogueTest(unittest.TestCase):
    def test_book_coverage_and_separate_editions(self):
        entries = codex_expansions.catalogue(portal.EXTRA_SPECIES)
        subclasses = [e for e in entries if e['kind'].startswith('Unterklasse')]
        counts = Counter(e['code'] for e in subclasses)
        self.assertEqual(dict(counts), {'tcoe': 30, 'rthw': 7, 'phb-2014': 40, 'phb-2024': 48, 'xgte': 31})
        self.assertEqual(len({e['key'] for e in entries}), len(entries))
        modern = [e for e in subclasses if e['code'] == 'phb-2024']
        self.assertEqual(set(Counter(e['kind'] for e in modern).values()), {4})
        champions = [e for e in subclasses if e['name'] == 'Champion']
        self.assertEqual({e['edition'] for e in champions}, {'2014', '2024'})
        self.assertEqual(len({e['key'] for e in champions}), 2)

    def test_public_routes_details_and_background_visibility(self):
        with tempfile.TemporaryDirectory() as directory:
            old_db = portal.DB
            portal.DB = Path(directory) / 'test.sqlite3'
            server = portal.ThreadingHTTPServer(('127.0.0.1', 0), portal.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            def get(path):
                connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
                try:
                    connection.request('GET', path)
                    response = connection.getresponse()
                    return response.status, response.read().decode('utf-8')
                finally:
                    connection.close()

            try:
                for path in ('/codex', '/codex/2014', '/codex/2024'):
                    status, body = get(path)
                    self.assertEqual(status, 200)
                    self.assertIn('/codex/herkuenfte', body)
                for edition in ('2014', '2024'):
                    for key in portal.codex_2014.CLASSES:
                        status, body = get(f'/codex/{edition}/klasse/{key}')
                        self.assertEqual(status, 200)
                        self.assertIn('id="unterklassen"', body)
                    status, body = get(f'/codex/{edition}/klasse/barbar')
                    self.assertIn(f'/codex/quelle/phb-{edition}-path-of-the-berserker', body)
                    self.assertNotIn('-college-of-lore', body)
                    other = '2014' if edition == '2024' else '2024'
                    self.assertNotIn(f'/codex/quelle/phb-{other}-', body)
                for path in ('/', '/login'):
                    status, body = get(path)
                    self.assertEqual(status, 200)
                    self.assertIn('Rising Moon — RandomMind', body)
                    self.assertIn('https://creativecommons.org/publicdomain/zero/1.0/', body)
                    self.assertIn('/media/portal-music.js', body)
                    self.assertNotIn('HydroGene', body)
                for entry in codex_expansions.catalogue(portal.EXTRA_SPECIES):
                    if not entry['kind'].startswith('Unterklasse'):
                        continue
                    path = '/codex/quelle/' + entry['key']
                    status, body = get(path)
                    self.assertEqual(status, 200, path)
                    self.assertIn('Regelfassung ' + entry['edition'], body)
                    self.assertIn('/sources/dnd/' + entry['code'], body)
                with portal.database() as db:
                    for title, published, deleted in (('Öffentliche Herkunft', 1, 0), ('Geheime Herkunft', 0, 0), ('Entfernte Herkunft', 1, 1)):
                        db.execute("INSERT INTO codex_entries(title,kind,edition,body,published,deleted,created_by,updated_at) VALUES(?,'Hintergrund','Homebrew','Beispiel',?,?,1,0)", (title, published, deleted))
                    db.commit()
                    dm_body = portal.backgrounds_page(db, {'role': 'dm'})
                    self.assertIn('Geheime Herkunft', dm_body)
                    self.assertNotIn('Entfernte Herkunft', dm_body)
                status, body = get('/codex/herkuenfte')
                self.assertEqual(status, 200)
                self.assertIn('Öffentliche Herkunft', body)
                self.assertNotIn('Geheime Herkunft', body)
                self.assertNotIn('Entfernte Herkunft', body)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
                portal.DB = old_db
