import http.client
import re
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import portal
import test_portal_session


class AccessRegressionTest(unittest.TestCase):
    setUp = test_portal_session.SessionFeaturesTest.setUp
    tearDown = test_portal_session.SessionFeaturesTest.tearDown
    request = test_portal_session.SessionFeaturesTest.request

    def test_first_code_retry_copying_and_single_use(self):
        with patch.object(portal.portal_security, '_requests', {}):
            status, html, _ = self.request('POST', '/dm', 'dm')
            self.assertEqual(status, 200)
            code = re.search(r'<h2>([A-F0-9]+)</h2>', html)[1]
            data = {'code': code, 'username': 'new_player', 'password': 'short'}
            status, html, _ = self.request('POST', '/register', data=data)
            self.assertEqual(status, 400)
            self.assertIn('mindestens 12 Zeichen', html)
            self.assertIn(code, html)
            self.assertNotIn('value="short"', html)
            data.update(password='valid-password-123', username='alice')
            self.assertEqual(self.request('POST', '/register', data=data)[0], 409)
            with portal.database() as db:
                self.assertEqual(db.execute('SELECT uses_left FROM invites WHERE code_hash=?', (portal.digest(code),)).fetchone()[0], 1)
            # The exact same first invitation works after a failed form, even copied with formatting.
            data.update(username='new_player', code=code[:4].lower() + '\u200b\u00a0-\n' + code[4:].lower())
            self.assertEqual(self.request('POST', '/register', data=data)[0], 303)
            data['username'] = 'another_player'
            status, html, _ = self.request('POST', '/register', data=data)
            self.assertEqual(status, 400)
            self.assertIn('bereits eingelöst', html)
            with portal.database() as db:
                self.assertEqual(db.execute('SELECT uses_left FROM invites WHERE code_hash=?', (portal.digest(code),)).fetchone()[0], 0)
                self.assertIsNone(db.execute("SELECT id FROM users WHERE username='another_player'").fetchone())

    def test_expired_code_is_not_consumed(self):
        code = '0123456789ABCDEF'
        with portal.database() as db:
            db.execute('INSERT INTO invites VALUES(?,?,1,?)', (portal.digest(code), int(time.time()) - 1, self.ids['dm']))
        with patch.object(portal.portal_security, '_requests', {}):
            status, html, _ = self.request('POST', '/register', data={'code': code, 'username': 'new_player', 'password': 'long-password-123'})
        self.assertEqual(status, 400)
        self.assertIn('ist abgelaufen', html)
        with portal.database() as db:
            self.assertEqual(db.execute('SELECT uses_left FROM invites').fetchone()[0], 1)

    def multipart(self, path, fields, who='dm', attachment=False):
        boundary = 'test-handout-boundary'
        chunks = []
        for key, value in fields.items():
            chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
        if attachment:
            chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="attachment"; filename="map.pdf"\r\nContent-Type: application/pdf\r\n\r\n'.encode() + b'%PDF-1.4 test\r\n')
        chunks.append(f'--{boundary}--\r\n'.encode())
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        try:
            conn.request('POST', path, b''.join(chunks), {'Content-Type': 'multipart/form-data; boundary=' + boundary, 'Cookie': 'tormentor_session=' + who})
            response = conn.getresponse()
            result = response.status, response.read()
            return result
        finally:
            conn.close()

    def test_browser_handout_draft_publish_and_attachment_isolation(self):
        with patch.object(portal.portal_handouts, 'ROOT', Path(self.temp.name) / 'attachments'):
            data = {'title': 'Private map', 'body': 'Secret route', 'audience': 'selected', f'recipient_{self.ids["alice"]}': '1', 'publication': 'draft'}
            self.assertEqual(self.multipart('/dm/handouts', data, attachment=True)[0], 303)
            with portal.database() as db:
                uid = db.execute('SELECT id FROM handouts').fetchone()[0]
            path = f'/dm/handouts/edit/{uid}'
            file = f'/handouts/{uid}/file'
            self.assertNotIn('Secret route', self.request('GET', '/handouts', 'alice')[1])
            self.assertEqual(self.request('GET', file, 'alice')[0], 404)
            html = self.request('GET', path, 'dm')[1]
            self.assertIn('Privater Entwurf', html)
            self.assertIn('Speichern und freigeben', html)
            data['publication'] = 'publish'
            self.assertEqual(self.multipart(path, data, 'alice')[0], 403)
            self.assertEqual(self.multipart(path, data)[0], 303)
            self.assertIn('Secret route', self.request('GET', '/handouts', 'alice')[1])
            self.assertEqual(self.request('GET', file, 'alice')[0], 200)
            self.assertNotIn('Secret route', self.request('GET', '/handouts', 'bob')[1])
            self.assertEqual(self.request('GET', file, 'bob')[0], 404)
            data['publication'] = 'draft'
            self.assertEqual(self.multipart(path, data)[0], 303)
            self.assertEqual(self.request('GET', file, 'alice')[0], 404)

    def test_dm_points_shown_on_sheet_and_cannot_be_forged(self):
        uid = self.ids['alice']
        path = f'/dm/players/{uid}/inspiration'
        for who in (None, 'alice', 'bob'):
            self.assertEqual(self.request('POST', path, who, {'revision': '0', 'kind': 'heroic', 'delta': '1'})[0], 403)
        self.assertEqual(self.request('GET', f'/dm/players/{uid}', 'alice')[0], 403)
        for revision, kind in enumerate(('inspiration', 'heroic')):
            self.assertEqual(self.request('POST', path, 'dm', {'revision': str(revision), 'kind': kind, 'delta': '1'})[0], 303)
        self.assertEqual(self.request('POST', path, 'dm', {'revision': '1', 'kind': 'heroic', 'delta': '1'})[0], 409)
        html = self.request('GET', '/character', 'alice')[1]
        self.assertIn('Inspirationspunkte', html)
        self.assertIn('Heldenhafte Inspiration', html)
        self.assertNotIn('name="inspiration"', html)
        self.assertNotIn('name="delta"', html)
        self.assertEqual(self.request('POST', '/character', 'alice', {'revision': '0', 'inspiration': '999', 'heroic': '999'})[0], 303)
        with portal.database() as db:
            row = db.execute('SELECT * FROM player_inspiration WHERE user_id=?', (uid,)).fetchone()
            self.assertEqual((row['inspiration'], row['heroic']), (1, 1))
            stored, _ = portal.portal_character.load(db, uid)
            self.assertNotIn('inspiration', stored)


if __name__ == '__main__':
    unittest.main()
