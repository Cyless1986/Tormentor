import http.client
import secrets
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch

import portal


class SessionFeaturesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patches = [patch.object(portal, 'DB', Path(self.temp.name) / 'test.db'), patch.object(portal.portal_security, 'PUBLIC_ORIGIN', '')]
        for item in self.patches: item.start()
        self.ids = {}
        with portal.database() as db:
            for name, role in [('dm', 'dm'), ('alice', 'player'), ('bob', 'player')]:
                uid = db.execute('INSERT INTO users(username,password,role) VALUES(?,?,?)', (name, 'unused', role)).lastrowid
                self.ids[name] = uid
                db.execute('INSERT INTO sessions VALUES(?,?,?)', (portal.digest(name), uid, int(time.time()) + 3600))
        self.server = portal.ThreadingHTTPServer(('127.0.0.1', 0), portal.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        for item in reversed(self.patches): item.stop()
        self.temp.cleanup()

    def request(self, method, path, who=None, data=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        if who: headers['Cookie'] = 'tormentor_session=' + who
        conn.request(method, path, urlencode(data or {}), headers)
        response = conn.getresponse()
        result = response.status, response.read().decode(), dict(response.getheaders())
        conn.close()
        return result

    def test_character_pages_keep_all_saved_fields_in_one_form(self):
        from html.parser import HTMLParser
        from collections import Counter
        class Fields(HTMLParser):
            def __init__(self):
                super().__init__()
                self.inside = False
                self.names = []
                self.panels = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'form':
                    self.inside = attrs.get('id') == 'character-sheet'
                if self.inside and tag in ('input', 'textarea', 'select') and 'name' in attrs:
                    self.names.append(attrs['name'])
                if attrs.get('class') == 'sheet-panel':
                    self.panels.append(attrs['id'])
            def handle_endtag(self, tag):
                if tag == 'form': self.inside = False
        status, html, _ = self.request('GET', '/character', 'alice')
        self.assertEqual(status, 200)
        fields = Fields(); fields.feed(html)
        sheet = portal.portal_character
        expected = ['revision', 'spell_ability']
        expected += [key for key, _ in sheet.ABILITIES]
        expected += ['save_' + key for key, _ in sheet.ABILITIES]
        expected += [key for key, _, _ in sheet.SKILLS]
        expected += list(sheet.NUMBERS | sheet.COMPANION_NUMBERS) + [key for key, _ in sheet.TEXTS + sheet.COMPANION_TEXTS]
        expected += [f'{prefix}_{level}' for level in range(1, 10) for prefix in ('slots', 'used')]
        self.assertEqual(Counter(fields.names), Counter(expected))
        self.assertEqual(len(fields.panels), 6)
        status, css, headers = self.request('GET', '/media/character.css')
        self.assertEqual(status, 200)
        self.assertIn('text/css', headers['Content-Type'])
        self.assertIn('.sheet-hero', css)

    def test_companions_save_and_isolation(self):
        data = {'revision': '0', 'companion_1_name': 'Fenn', 'companion_1_kind': 'Wolf',
                'companion_1_hp': '12', 'companion_1_hp_max': '18', 'companion_1_ac': '13',
                'companion_1_abilities': '<b>Biss</b>', 'companion_3_name': 'Rabe'}
        self.assertEqual(self.request('POST', '/character', 'alice', data)[0], 303)
        html = self.request('GET', '/character', 'alice')[1]
        self.assertIn('Fenn', html)
        self.assertIn('&lt;b&gt;Biss&lt;/b&gt;', html)
        self.assertNotIn('Fenn', self.request('GET', '/character', 'bob')[1])
        with portal.database() as db:
            stored, revision = portal.portal_character.load(db, self.ids['alice'])
        self.assertEqual(stored['companion_1_hp'], 12)
        self.assertEqual(stored['companion_3_name'], 'Rabe')
        data.update(revision=str(revision), companion_1_hp='-1')
        self.assertEqual(self.request('POST', '/character', 'alice', data)[0], 400)

    def test_dm_inspiration_permissions_balances_and_stale_submit(self):
        uid = self.ids['alice']
        path = f'/dm/players/{uid}/inspiration'
        data = {'kind': 'inspiration', 'delta': '1', 'revision': '0'}
        for who in (None, 'alice', 'bob'):
            self.assertEqual(self.request('POST', path, who, data)[0], 403)
        self.assertEqual(self.request('GET', f'/dm/players/{uid}', 'alice')[0], 403)
        self.assertEqual(self.request('POST', path, 'dm', data)[0], 303)
        self.assertEqual(self.request('POST', path, 'dm', data)[0], 409)
        data.update(kind='heroic', revision='1')
        self.assertEqual(self.request('POST', path, 'dm', data)[0], 303)
        data.update(kind='inspiration', delta='-1', revision='2')
        self.assertEqual(self.request('POST', path, 'dm', data)[0], 303)
        data.update(revision='3')
        self.assertEqual(self.request('POST', path, 'dm', data)[0], 409)
        self.request('POST', '/profil', 'alice', {'level': '1', 'heroic': '99', 'inspiration': '99'})
        with portal.database() as db:
            row = db.execute('SELECT * FROM player_inspiration WHERE user_id=?', (uid,)).fetchone()
            self.assertEqual((row['inspiration'], row['heroic'], row['revision']), (0, 1, 3))
            self.assertIsNone(db.execute('SELECT * FROM player_inspiration WHERE user_id=?', (self.ids['bob'],)).fetchone())
        html = self.request('GET', '/profil', 'alice')[1]
        self.assertIn('Heldenhafte Inspiration', html)
        self.assertNotIn('name="delta"', html)
        self.assertNotIn('name="inspiration"', self.request('GET', '/character', 'alice')[1])
        self.assertEqual(self.request('GET', f'/dm/players/{uid}', 'dm')[0], 200)
        self.assertEqual(self.request('POST', '/dm/players/999999/inspiration', 'dm', data)[0], 404)

    def test_messages_recipient_isolation_and_later_registration(self):
        data = {'body': '<script>Geheim</script>', 'audience': 'selected', 'nonce': secrets.token_hex(16), f'recipient_{self.ids["alice"]}': '1'}
        self.assertEqual(self.request('POST', '/messages', 'alice', data)[0], 400)
        self.assertEqual(self.request('GET', '/messages/feed')[0], 401)
        for _ in range(2): self.assertEqual(self.request('POST', '/messages', 'dm', data)[0], 303)
        alice = self.request('GET', '/messages/feed', 'alice')[1]
        self.assertEqual(alice.count('Geheim'), 1)
        self.assertIn('&lt;script&gt;', alice)
        self.assertNotIn('Geheim', self.request('GET', '/messages/feed', 'bob')[1])
        self.assertIn('Geheim', self.request('GET', '/messages/feed', 'dm')[1])
        data.update(body='An alle', audience='all', nonce=secrets.token_hex(16))
        self.assertEqual(self.request('POST', '/messages', 'dm', data)[0], 303)
        self.assertIn('An alle', self.request('GET', '/messages/feed', 'bob')[1])
        with portal.database() as db:
            uid = db.execute("INSERT INTO users(username,password,role) VALUES('cara','unused','player')").lastrowid
            db.execute('INSERT INTO sessions VALUES(?,?,?)', (portal.digest('cara'), uid, int(time.time()) + 3600))
        self.assertIn('cara', self.request('GET', '/messages', 'dm')[1])
        self.assertNotIn('An alle', self.request('GET', '/messages/feed', 'cara')[1])
        data.update(audience='selected', nonce=secrets.token_hex(16), recipient_99999='1')
        self.assertEqual(self.request('POST', '/messages', 'dm', data)[0], 400)
        self.assertIn("connect-src 'self'", self.request('GET', '/messages', 'alice')[2]['Content-Security-Policy'])

    def test_login_reuses_session_and_logout_revokes_it(self):
        status, body, _ = self.request('GET', '/login')
        self.assertEqual(status, 200)
        self.assertIn('autocomplete="username"', body)
        self.assertIn('autocomplete="current-password"', body)
        status, _, headers = self.request('GET', '/login', 'alice')
        self.assertEqual(status, 303)
        self.assertEqual(headers['Location'], '/dashboard')
        self.assertEqual(self.request('GET', '/dashboard', 'alice')[0], 200)
        self.assertEqual(self.request('POST', '/logout', 'alice')[0], 303)
        self.assertEqual(self.request('GET', '/login', 'alice')[0], 200)
        self.assertEqual(self.request('GET', '/dashboard', 'alice')[0], 303)
        with portal.database() as db:
            db.execute('UPDATE sessions SET expires_at=0 WHERE user_id=?', (self.ids['bob'],))
        self.assertEqual(self.request('GET', '/login', 'bob')[0], 200)

    def test_unread_counts_are_private_and_read_marker_is_bounded(self):
        self.assertEqual(self.request('GET', '/messages/unread')[0], 401)
        self.assertEqual(self.request('POST', '/messages/read', data={'through': '1'})[0], 403)
        def send(text):
            data = {'body': text, 'audience': 'selected', 'nonce': secrets.token_hex(16), f'recipient_{self.ids["alice"]}': '1'}
            self.assertEqual(self.request('POST', '/messages', 'dm', data)[0], 303)
        send('Erste')
        self.assertEqual(self.request('GET', '/messages/unread', 'alice')[1], '1')
        for who in ('dm', 'bob'):
            self.assertEqual(self.request('GET', '/messages/unread', who)[1], '0')
        with portal.database() as db:
            first = db.execute('SELECT MAX(id) FROM chat_messages').fetchone()[0]
        send('Zweite')
        self.assertEqual(self.request('POST', '/messages/read', 'alice', {'through': str(first)})[0], 200)
        self.assertEqual(self.request('GET', '/messages/unread', 'alice')[1], '1')
        self.assertEqual(self.request('POST', '/messages/read', 'alice', {'through': '999999'})[0], 200)
        self.assertEqual(self.request('GET', '/messages/unread', 'alice')[1], '0')
        send('Dritte')
        self.assertEqual(self.request('GET', '/messages/unread', 'alice')[1], '1')
        self.request('POST', '/messages/read', 'alice', {'through': '0'})
        self.assertEqual(self.request('GET', '/messages/unread', 'alice')[1], '1')
        for invalid in ('-1', 'x', '999999999999999999999999999'):
            self.assertEqual(self.request('POST', '/messages/read', 'alice', {'through': invalid})[0], 400)
        reply = {'body': 'Antwort', 'audience': 'dm', 'dm_id': str(self.ids['dm']), 'nonce': secrets.token_hex(16)}
        self.assertEqual(self.request('POST', '/messages', 'alice', reply)[0], 303)
        self.assertEqual(self.request('GET', '/messages/unread', 'dm')[1], '1')
        self.assertEqual(self.request('GET', '/messages/unread', 'bob')[1], '0')

    def test_private_player_replies(self):
        data = {'audience': 'dm', 'dm_id': str(self.ids['dm']), 'nonce': secrets.token_hex(16), 'body': 'Meine geheime Antwort'}
        self.assertIn('Privat an den DM antworten', self.request('GET', '/messages', 'alice')[1])
        self.assertEqual(self.request('POST', '/messages', None, data)[0], 403)
        for _ in range(2):
            self.assertEqual(self.request('POST', '/messages', 'alice', data)[0], 303)
        for name in ('alice', 'dm'):
            self.assertEqual(self.request('GET', '/messages/feed', name)[1].count('Meine geheime Antwort'), 1)
        self.assertIn('Private Nachricht von: alice', self.request('GET', '/messages/feed', 'dm')[1])
        self.assertNotIn('Meine geheime Antwort', self.request('GET', '/messages/feed', 'bob')[1])
        data.update(nonce=secrets.token_hex(16), dm_id=str(self.ids['bob']))
        self.assertEqual(self.request('POST', '/messages', 'alice', data)[0], 400)
        data.update(dm_id='999999')
        self.assertEqual(self.request('POST', '/messages', 'alice', data)[0], 400)
        data.update(audience='all')
        self.assertEqual(self.request('POST', '/messages', 'alice', data)[0], 400)

    def test_character_save_validation_isolation_and_conflict(self):
        data = {'revision': '0', 'name': '<b>Alice</b>', 'str': '18', 'notes': 'Geheime Geschichte', 'spell_ability': 'wis', 'slots_1': '2', 'used_1': '1'}
        self.assertEqual(self.request('POST', '/character', None, data)[0], 403)
        self.assertEqual(self.request('POST', '/character', 'alice', data)[0], 303)
        saved = self.request('GET', '/character', 'alice')[1]
        self.assertIn('&lt;b&gt;Alice&lt;/b&gt;', saved)
        self.assertIn('Geheime Geschichte', saved)
        self.assertNotIn('Geheime Geschichte', self.request('GET', '/character', 'bob')[1])
        self.assertNotIn('Geheime Geschichte', self.request('GET', '/character', 'dm')[1])
        self.assertEqual(self.request('POST', '/character', 'alice', data)[0], 400)
        data.update(revision='1', str='31')
        self.assertEqual(self.request('POST', '/character', 'alice', data)[0], 400)
        data.update(str='20', used_1='3')
        self.assertEqual(self.request('POST', '/character', 'alice', data)[0], 400)
        data.update(used_1='2')
        self.assertEqual(self.request('POST', '/character', 'alice', data)[0], 303)
        with portal.database() as db:
            stored, revision = portal.portal_character.load(db, self.ids['alice'])
            self.assertEqual((stored['str'], revision), (20, 2))


if __name__ == '__main__': unittest.main()
