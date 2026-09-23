import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch

import portal


class HandoutRecipientsTest(unittest.TestCase):
    def test_recipient_access_edits_and_legacy_handouts(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(portal, 'DB', Path(directory) / 'test.sqlite3'), patch.object(portal.portal_security, '_requests', {}):
            ids = {}
            with portal.database() as db:
                for name, role in (('dm', 'dm'), ('alice', 'player'), ('bob', 'player'), ('cara', 'player')):
                    ids[name] = db.execute('INSERT INTO users(username,password,role) VALUES(?,?,?)', (name, portal.password_hash('test-password-123'), role)).lastrowid
                db.execute("INSERT INTO handouts(title,body,published,created_by,updated_at) VALUES('Alt','Altinhalt',1,?,0)", (ids['dm'],))
            server = portal.ThreadingHTTPServer(('127.0.0.1', 0), portal.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            def request(method, path, data=None, cookie=None):
                conn = http.client.HTTPConnection('127.0.0.1', server.server_port)
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                if cookie: headers['Cookie'] = cookie
                try:
                    conn.request(method, path, urlencode(data or {}), headers)
                    response = conn.getresponse()
                    return response.status, dict(response.getheaders()), response.read().decode()
                finally:
                    conn.close()
            try:
                cookies = {}
                for name in ids:
                    status, headers, _ = request('POST', '/login', {'username': name, 'password': 'test-password-123'})
                    self.assertEqual(status, 303)
                    cookies[name] = headers['Set-Cookie'].split(';')[0]
                self.assertEqual(request('GET', '/handouts')[0], 303)
                self.assertIn('Altinhalt', request('GET', '/handouts', cookie=cookies['bob'])[2])
                data = {'title': 'Geheimes Siegel', 'body': 'Nur für A und B', 'published': '1', 'audience': 'selected', f'recipient_{ids["alice"]}': '1', f'recipient_{ids["bob"]}': '1'}
                self.assertEqual(request('POST', '/dm/handouts', data, cookies['alice'])[0], 403)
                self.assertEqual(request('POST', '/dm/handouts', data, cookies['dm'])[0], 303)
                with portal.database() as db:
                    item = db.execute("SELECT id FROM handouts WHERE title='Geheimes Siegel'").fetchone()[0]
                edit = f'/dm/handouts/edit/{item}'
                for name in ('dm', 'alice', 'bob'):
                    self.assertIn('Nur für A und B', request('GET', '/handouts', cookie=cookies[name])[2])
                hidden = request('GET', '/handouts', cookie=cookies['cara'])[2]
                self.assertNotIn('Geheimes Siegel', hidden)
                self.assertNotIn('Nur für A und B', hidden)
                self.assertEqual(request('GET', edit, cookie=cookies['cara'])[0], 403)
                form = request('GET', edit, cookie=cookies['dm'])[2]
                self.assertIn(f'name="recipient_{ids["alice"]}" value="1" checked', form)
                del data[f'recipient_{ids["alice"]}']
                self.assertEqual(request('POST', edit, data, cookies['dm'])[0], 303)
                self.assertNotIn('Geheimes Siegel', request('GET', '/handouts', cookie=cookies['alice'])[2])
                self.assertIn('Geheimes Siegel', request('GET', '/handouts', cookie=cookies['bob'])[2])
                for invalid in ({'audience': 'selected'}, {'audience': 'selected', 'recipient_999999': '1'}, {'audience': 'selected', f'recipient_{ids["dm"]}': '1'}, {}):
                    bad = {'title': 'Invalid', 'body': 'Invalid body', 'published': '1', **invalid}
                    self.assertEqual(request('POST', edit, bad, cookies['dm'])[0], 400)
                self.assertIn('Geheimes Siegel', request('GET', '/handouts', cookie=cookies['bob'])[2])
                data['audience'] = 'all'
                self.assertEqual(request('POST', edit, data, cookies['dm'])[0], 303)
                self.assertIn('Geheimes Siegel', request('GET', '/handouts', cookie=cookies['cara'])[2])
                data.pop('published')
                self.assertEqual(request('POST', edit, data, cookies['dm'])[0], 303)
                self.assertNotIn('Geheimes Siegel', request('GET', '/handouts', cookie=cookies['bob'])[2])
                self.assertIn('Geheimes Siegel', request('GET', '/handouts', cookie=cookies['dm'])[2])
                self.assertEqual(request('POST', f'/dm/handouts/delete/{item}', cookie=cookies['dm'])[0], 303)
                data['published'] = '1'
                self.assertEqual(request('POST', edit, data, cookies['dm'])[0], 400)
                self.assertNotIn('Geheimes Siegel', request('GET', '/handouts', cookie=cookies['dm'])[2])
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
