import http.client
import unittest
from pathlib import Path
from unittest.mock import patch
import portal
import test_portal_session

class CodexDownloadTest(unittest.TestCase):
    setUp = test_portal_session.SessionFeaturesTest.setUp
    tearDown = test_portal_session.SessionFeaturesTest.tearDown
    request = test_portal_session.SessionFeaturesTest.request

    def test_books_require_dm_including_range_requests(self):
        root = Path(self.temp.name)
        (root / 'print').mkdir()
        names = ['Tormentor-Codex-2024.pdf', 'Tormentor-Codex-2014-Quellen.pdf', 'Tormentor-Codex-Homebrew.pdf']
        for name in names:
            (root / 'print' / name).write_bytes(b'%PDF-test-book')
        with patch.object(portal, 'ROOT', root):
            for name in names:
                for who in (None, 'alice', 'bob', 'dm'):
                    for ranged in (False, True):
                        with self.subTest(name=name, who=who, ranged=ranged):
                            conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
                            headers = {'Cookie': 'tormentor_session=' + who} if who else {}
                            if ranged: headers['Range'] = 'bytes=0-3'
                            conn.request('GET', '/media/' + name, headers=headers)
                            response = conn.getresponse()
                            body = response.read()
                            self.assertEqual(response.status, (206 if ranged else 200) if who == 'dm' else 403)
                            if who == 'dm':
                                self.assertEqual(body, b'%PDF' if ranged else b'%PDF-test-book')
                                self.assertEqual(response.getheader('Cache-Control'), 'private, no-store')
                            else:
                                self.assertNotIn(b'%PDF', body)
                            conn.close()

    def test_download_links_only_visible_to_dm(self):
        for who in (None, 'alice', 'bob', 'dm'):
            status, html, _ = self.request('GET', '/codex', who)
            self.assertEqual(status, 200)
            self.assertEqual('2024 herunterladen' in html, who == 'dm')
            self.assertIn('Buch öffnen', html)

if __name__ == '__main__':
    unittest.main()
