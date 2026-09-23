import http.client
import re
import tempfile
import threading
import unittest
from contextlib import closing
from pathlib import Path

import codex_2014
import portal


class Codex2014Test(unittest.TestCase):
    def test_source_tables_keep_edition_specific_resources(self):
        data = codex_2014.LEVELS
        self.assertEqual(len(data), 12)
        for key, item in data.items():
            self.assertEqual([r['level'] for r in item['rows']], list(range(1, 21)), key)
            for row in item['rows']:
                self.assertEqual(len(row['slots']), item['slot_grades'])
                self.assertEqual(len(row['values']), len(item['headers']))
                self.assertEqual(row['bonus'], '+' + str(2 + (row['level'] - 1) // 4))
        self.assertEqual(data['barbar']['rows'][-1]['values'], ['Unbegrenzt', '+4'])
        self.assertEqual(data['hexenmeister']['rows'][4]['values'][2:4], ['2', '3.'])
        self.assertEqual(data['moench']['rows'][0]['values'], ['1W4', '−', '−'])
        self.assertEqual(data['schurke']['rows'][-1]['values'], ['10W6'])
        self.assertEqual(data['paladin']['rows'][0]['slots'], ['−'] * 5)
        self.assertIn('ganze Aktion', codex_2014.species_page('drachenbluetiger'))
        self.assertIn('gegen Magie', codex_2014.species_page('gnom'))

    def test_all_2014_index_links_and_source_work_over_http(self):
        with tempfile.TemporaryDirectory() as directory:
            old_db = portal.DB
            portal.DB = Path(directory) / 'portal.sqlite3'
            server = portal.ThreadingHTTPServer(('127.0.0.1', 0), portal.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            def get(path):
                with closing(http.client.HTTPConnection('127.0.0.1', server.server_port)) as conn:
                    conn.request('GET', path)
                    response = conn.getresponse()
                    return response.status, response.read()
            try:
                status, raw = get('/codex/2014')
                self.assertEqual(status, 200)
                links = re.findall(r'href="(/codex/2014/(?:klasse|spezies)/[a-z]+)"', raw.decode())
                self.assertEqual(len(set(links)), 21)
                for link in links:
                    status, raw = get(link)
                    self.assertEqual(status, 200, link)
                    self.assertIn(b'SRD 5.1', raw, link)
                self.assertEqual(get('/codex/2014/klasse/unbekannt')[0], 404)
                self.assertEqual(get('/codex/2014/spezies/unbekannt')[0], 404)
                status, raw = get('/media/SRD-5.1-DE.pdf')
                self.assertEqual(status, 200)
                self.assertTrue(raw.startswith(b'%PDF'))
                self.assertEqual(get('/codex/2024/klasse/barbar')[0], 200)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
                portal.DB = old_db


if __name__ == '__main__':
    unittest.main()
