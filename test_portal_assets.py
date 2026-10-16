"""Public asset caching, compression and negotiated image formats."""
import gzip
import http.client
import tempfile
import threading
import unittest
from pathlib import Path
import portal


class PortalAssetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.old_db = portal.DB
        portal.DB = Path(cls.temporary.name) / 'test.sqlite3'
        cls.server = portal.ThreadingHTTPServer(('127.0.0.1', 0), portal.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
        portal.DB = cls.old_db
        cls.temporary.cleanup()

    def get(self, path, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        try:
            connection.request('GET', path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_html_compressed_but_not_cached(self):
        status, headers, data = self.get('/codex', {'Accept-Encoding': 'gzip'})
        self.assertEqual(status, 200)
        self.assertEqual(headers['Content-Encoding'], 'gzip')
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertIn(b'portal-navigation.js', gzip.decompress(data))
        _, plain_headers, plain = self.get('/codex', {'Accept-Encoding': 'gzip;q=0'})
        self.assertNotIn('Content-Encoding', plain_headers)
        self.assertLess(len(data), len(plain))

    def test_script_query_and_conditional_cache(self):
        path = '/media/portal-navigation.js?page=example'
        status, headers, data = self.get(path, {'Accept-Encoding': 'gzip'})
        self.assertEqual(status, 200)
        self.assertEqual(headers['Content-Type'], 'text/javascript; charset=utf-8')
        self.assertIn(b'tormentorNavigation', gzip.decompress(data))
        status, _, data = self.get(path, {'If-None-Match': headers['ETag']})
        self.assertEqual(status, 304)
        self.assertEqual(data, b'')

    def test_negotiated_background_image(self):
        path = '/media/classes-guild-v1.png'
        status, headers, webp = self.get(path, {'Accept': 'image/webp'})
        self.assertEqual(status, 200)
        self.assertEqual(headers['Content-Type'], 'image/webp')
        self.assertEqual(headers['Vary'], 'Accept')
        self.assertTrue(webp.startswith(b'RIFF'))
        _, original_headers, png = self.get(path)
        self.assertEqual(original_headers['Content-Type'], 'image/png')
        self.assertTrue(png.startswith(b'\x89PNG'))
        self.assertLess(len(webp), len(png))
        self.assertNotEqual(headers['ETag'], original_headers['ETag'])
        status, _, _ = self.get(path, {'Accept': 'image/webp', 'If-None-Match': headers['ETag']})
        self.assertEqual(status, 304)
